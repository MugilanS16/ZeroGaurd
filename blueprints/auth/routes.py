from datetime import datetime, timezone, timedelta
import random
import re
import json
import logging
import jwt

logger = logging.getLogger(__name__)
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort, jsonify, current_app

from blueprints.auth import auth_bp

# Dedicated API Blueprint for top-level /api/* routing
api_bp = Blueprint('api_v2', __name__)

from blueprints.auth.forms import LoginForm, RegisterForm, OTPForm, ChangePasswordForm

from database import db
from database.models import User, LoginHistory, Complaint, OTPVerification, OTPChallenge, Guardian, EmergencyContact, ActivityLog, NotificationLog
from backend.services.otp_service import OTPService, normalize_phone_number, mask_phone_number, mask_email, record_audit_ledger
from backend.services.notify_service import NotificationService
from backend.services.messaging.factory import get_messaging_provider
from utils.otp import create_and_send_otp

# ---------------------------------------------------------------------
# Decorators & Auth Helpers
# ---------------------------------------------------------------------
def get_current_user_from_token():
    """Extracts and verifies JWT token from Authorization header or session."""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            secret = current_app.config['SECRET_KEY']
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            user_id = payload.get('user_id') or payload.get('sub')
            if user_id:
                return User.query.get(user_id)
        except Exception:
            return None
    elif 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def login_required(f):
    """Decorator to require user login via session or JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_token()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            session['user_role'] = user.role
            session['user_name'] = user.fullname
            return f(*args, **kwargs)

        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Authentication required. Please provide a valid Bearer token.'}), 401
        
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    return decorated_function


def admin_required(f):
    """Decorator to require cyber-cell administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_token()
        if not user:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Admin authentication required.'}), 401
            flash('Access denied. Admin authentication required.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        
        if not user.is_admin:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Forbidden. Administrator privileges required.'}), 403
            flash('Access denied. You do not have administrator privileges.', 'danger')
            return redirect(url_for('dashboard.index'))
            
        session['user_id'] = user.id
        session['role'] = user.role
        session['user_role'] = user.role
        return f(*args, **kwargs)
    return decorated_function


def generate_jwt_token(user: User) -> str:
    """Generates a signed JWT access token valid for 7 days."""
    secret = current_app.config['SECRET_KEY']
    payload = {
        'sub': str(user.id),
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(days=7),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, secret, algorithm='HS256')



def record_login(user_id, email, status, req, method='password', phone=None):
    """Helper to log security login attempts."""
    try:
        ip = req.headers.get('X-Forwarded-For', req.remote_addr) or '127.0.0.1'
        ua = req.headers.get('User-Agent', '')[:250]
        success = (status == 'SUCCESS')
        log = LoginHistory(
            user_id=user_id,
            email_attempted=email,
            phone_attempted=phone,
            login_method=method,
            ip_address=ip,
            user_agent=ua,
            status=status,
            success=success,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()


def log_activity(user_id, action, details, req):
    """Helper to record user security and profile activity logs."""
    try:
        ip = req.headers.get('X-Forwarded-For', req.remote_addr) or '127.0.0.1'
        record_audit_ledger(user_id, action, details, ip)
    except Exception as e:
        pass


# =====================================================================
# REST API 2FA & OTP ENDPOINTS
# =====================================================================

@api_bp.route('/api/auth/otp/send', methods=['POST'])
@auth_bp.route('/api/auth/otp/send', methods=['POST'])
def api_otp_send():
    """
    POST /api/auth/otp/send
    Body: { phone: str, channel?: 'sms' | 'whatsapp' }
    Normalizes phone to E.164, rate-limits, and sends 6-digit OTP via requested channel.
    """
    data = request.get_json() or {}
    phone = data.get('phone') or data.get('phone_number', '')
    channel = data.get('channel', 'sms').lower().strip()
    purpose = data.get('purpose', '2fa_login')

    if not phone:
        return jsonify({'error': 'Phone number is required.'}), 400

    # Locate user if exists (generic error messages on failure)
    valid, e164 = normalize_phone_number(phone)
    if not valid:
        return jsonify({'error': 'Invalid mobile number format. Please provide a valid 10-digit Indian number or E.164 phone.'}), 400

    user = User.query.filter(
        (User.phone_number == e164) | (User.phone == e164) | (User.phone == phone)
    ).first()
    user_id = user.id if user else session.get('user_id')

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
    success, challenge_id, msg, final_channel = OTPService.send_otp(
        phone=e164,
        channel=channel,
        user_id=user_id,
        purpose=purpose,
        ip_address=ip
    )

    if not success:
        status_code = 429 if "wait" in msg.lower() or "too many" in msg.lower() else 400
        return jsonify({'error': msg, 'channel': final_channel}), status_code

    return jsonify({
        'success': True,
        'challenge_id': challenge_id,
        'channel': final_channel,
        'expires_in': current_app.config.get('OTP_EXPIRY_SECONDS', 300),
        'cooldown_seconds': current_app.config.get('OTP_RESEND_COOLDOWN_SECONDS', 30),
        'message': msg
    }), 200


@api_bp.route('/api/auth/otp/verify', methods=['POST'])
@auth_bp.route('/api/auth/otp/verify', methods=['POST'])
def api_otp_verify():
    """
    POST /api/auth/otp/verify
    Body: { challenge_id: int, otp: str }
    Verifies 6-digit OTP in constant time, marks challenge consumed, and issues session/JWT.
    """
    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    entered_otp = str(data.get('otp', '')).strip()

    if not challenge_id or not entered_otp:
        return jsonify({'error': 'Both challenge_id and otp are required.'}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
    success, msg, payload = OTPService.verify_otp(
        challenge_id=int(challenge_id),
        entered_otp=entered_otp,
        ip_address=ip
    )

    if not success:
        status_code = 429 if "locked" in msg.lower() else 401
        return jsonify({'error': msg}), status_code

    user_data = payload.get('user')
    access_token = None
    if user_data:
        user = User.query.get(user_data['id'])
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            session['user_role'] = user.role
            session['user_name'] = user.fullname
            access_token = generate_jwt_token(user)
            record_login(user.id, user.email, 'SUCCESS', request, method='otp_2fa', phone=payload.get('phone_number'))

    return jsonify({
        'success': True,
        'message': msg,
        'access_token': access_token,
        'user': user_data,
        'purpose': payload.get('purpose')
    }), 200


@api_bp.route('/api/auth/otp/resend', methods=['POST'])
@auth_bp.route('/api/auth/otp/resend', methods=['POST'])
def api_otp_resend():
    """
    POST /api/auth/otp/resend
    Body: { challenge_id: int }
    Enforces 30-second cooldown and dispatches a fresh OTP challenge.
    """
    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')

    if not challenge_id:
        return jsonify({'error': 'challenge_id is required.'}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
    success, new_challenge_id, msg, final_channel = OTPService.resend_otp(
        challenge_id=int(challenge_id),
        ip_address=ip
    )

    if not success:
        status_code = 429 if "wait" in msg.lower() or "too many" in msg.lower() else 400
        return jsonify({'error': msg}), status_code

    return jsonify({
        'success': True,
        'challenge_id': new_challenge_id,
        'channel': final_channel,
        'expires_in': current_app.config.get('OTP_EXPIRY_SECONDS', 300),
        'cooldown_seconds': current_app.config.get('OTP_RESEND_COOLDOWN_SECONDS', 30),
        'message': msg
    }), 200


# =====================================================================
# REST API GUARDIAN ENDPOINTS
# =====================================================================

@api_bp.route('/api/guardian', methods=['GET', 'POST'])
@auth_bp.route('/api/guardian', methods=['GET', 'POST'])
@login_required
def api_guardian_manage():
    """
    GET /api/guardian -> Returns all guardians for current user.
    POST /api/guardian -> Adds or updates guardian (requires consent flag), triggers verification OTP.
    """
    user = get_current_user_from_token() or (User.query.get(session.get('user_id')) if 'user_id' in session else None)
    if not user:
        return jsonify({'error': 'User authentication required.'}), 401
    user_id = user.id

    if request.method == 'GET':
        guardians = Guardian.query.filter_by(user_id=user_id).order_by(Guardian.created_at.desc()).all()
        return jsonify({
            'success': True,
            'guardians': [g.to_dict() for g in guardians]
        }), 200

    # POST: Add or Update Guardian
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip().lower()
    preferred_channel = data.get('preferred_channel', 'email' if email else 'sms').lower().strip()
    relationship = data.get('relationship', 'Guardian').strip()
    consent_given = data.get('consent_given', False)

    if not name:
        return jsonify({'error': 'Guardian name is required.'}), 400

    if not phone and not email:
        return jsonify({'error': 'Either phone number or email address is required for guardian.'}), 400

    if not consent_given:
        return jsonify({'error': 'Guardian consent flag is required before enrolling for emergency alerts.'}), 400

    valid, e164 = normalize_phone_number(phone) if phone else (False, '')
    if phone and not valid:
        return jsonify({'error': 'Invalid guardian mobile number. Please provide a valid 10-digit Indian number.'}), 400

    if user and e164 and (user.phone_number == e164 or user.phone == e164):
        return jsonify({'error': 'Guardian phone number cannot be identical to your own account number.'}), 400

    if user and email and user.email == email:
        return jsonify({'error': 'Guardian email cannot be identical to your own account email.'}), 400

    # Create or update guardian
    existing = None
    if e164:
        existing = Guardian.query.filter_by(user_id=user_id, phone_number=e164).first()
    if not existing and email:
        existing = Guardian.query.filter_by(user_id=user_id, email=email).first()

    if existing:
        guardian = existing
        guardian.name = name
        guardian.email = email or guardian.email
        guardian.phone_number = e164 or guardian.phone_number
        guardian.preferred_channel = preferred_channel
        guardian.relationship_type = relationship
        guardian.consent_given = True
        guardian.consent_at = datetime.utcnow()
        guardian.opted_out = False
    else:
        guardian = Guardian(
            user_id=user_id,
            name=name,
            email=email or None,
            phone_number=e164 or (user.phone_number or '+910000000000'),
            preferred_channel=preferred_channel,
            relationship_type=relationship,
            consent_given=True,
            consent_at=datetime.utcnow(),
            verified=False,
            opted_out=False
        )
        db.session.add(guardian)

    db.session.commit()
    log_activity(user_id, 'ADD_GUARDIAN', f"Guardian {name} ({mask_email(email) if email else mask_phone_number(e164)}) added with consent", request)

    # Trigger verification challenge directly to guardian contact
    sent, v_msg = NotificationService.send_guardian_verification(guardian.id)

    return jsonify({
        'success': True,
        'guardian': guardian.to_dict(),
        'channel': preferred_channel,
        'message': v_msg or f"Guardian '{name}' saved. Verification sent."
    }), 201


@api_bp.route('/api/guardian/test-alert', methods=['POST'])
@auth_bp.route('/api/guardian/test-alert', methods=['POST'])
@login_required
def api_guardian_test_alert():
    """POST /api/guardian/test-alert -> Triggers a test alert to verified guardians."""
    user = get_current_user_from_token() or (User.query.get(session.get('user_id')) if 'user_id' in session else None)
    if not user:
        return jsonify({'error': 'User authentication required.'}), 401

    success, msg = NotificationService.send_test_alert(user.id)
    return jsonify({
        'success': success,
        'message': msg
    }), (200 if success else 400)


@api_bp.route('/api/guardian/resend-verification', methods=['POST'])
@auth_bp.route('/api/guardian/resend-verification', methods=['POST'])
@login_required
def api_guardian_resend_verification():
    """POST /api/guardian/resend-verification -> Resends verification code to guardian."""
    user = get_current_user_from_token() or (User.query.get(session.get('user_id')) if 'user_id' in session else None)
    if not user:
        return jsonify({'error': 'User authentication required.'}), 401

    data = request.get_json() or {}
    guardian_id = data.get('guardian_id')
    if not guardian_id:
        return jsonify({'error': 'guardian_id is required.'}), 400

    guardian = Guardian.query.filter_by(id=guardian_id, user_id=user.id).first()
    if not guardian:
        return jsonify({'error': 'Guardian record not found.'}), 404

    success, msg = NotificationService.send_guardian_verification(guardian.id)
    return jsonify({
        'success': success,
        'message': msg
    }), (200 if success else 400)


@api_bp.route('/api/guardian/verify', methods=['POST'])
@auth_bp.route('/api/guardian/verify', methods=['POST'])
@login_required
def api_guardian_verify():
    """
    POST /api/guardian/verify
    Body: { guardian_id: int, challenge_id: int, otp: str }
    Verifies guardian phone number via OTP and activates alert eligibility.
    """
    user = get_current_user_from_token() or (User.query.get(session.get('user_id')) if 'user_id' in session else None)
    if not user:
        return jsonify({'error': 'User authentication required.'}), 401

    data = request.get_json() or {}
    guardian_id = data.get('guardian_id')
    challenge_id = data.get('challenge_id')
    entered_otp = str(data.get('otp', '')).strip()

    if not guardian_id or not challenge_id or not entered_otp:
        return jsonify({'error': 'guardian_id, challenge_id, and otp are required.'}), 400

    guardian = Guardian.query.filter_by(id=guardian_id, user_id=user.id).first()
    if not guardian:
        return jsonify({'error': 'Guardian record not found.'}), 404

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
    success, msg, payload = OTPService.verify_otp(
        challenge_id=int(challenge_id),
        entered_otp=entered_otp,
        ip_address=ip
    )

    if not success:
        return jsonify({'error': msg}), 400

    guardian.verified = True
    guardian.consent_at = datetime.utcnow()
    db.session.commit()

    log_activity(user.id, 'GUARDIAN_VERIFIED', f"Guardian {guardian.name} verified successfully", request)

    return jsonify({
        'success': True,
        'guardian': guardian.to_dict(),
        'message': f"Guardian '{guardian.name}' successfully verified and registered for emergency alerts."
    }), 200


@api_bp.route('/api/guardian/<int:guardian_id>', methods=['DELETE'])
@auth_bp.route('/api/guardian/<int:guardian_id>', methods=['DELETE'])
@login_required
def api_guardian_delete(guardian_id):
    """DELETE /api/guardian/<id> -> Deletes a guardian."""
    user = get_current_user_from_token() or (User.query.get(session.get('user_id')) if 'user_id' in session else None)
    if not user:
        return jsonify({'error': 'User authentication required.'}), 401

    guardian = Guardian.query.filter_by(id=guardian_id, user_id=user.id).first()
    if not guardian:
        return jsonify({'error': 'Guardian not found.'}), 404

    name = guardian.name
    db.session.delete(guardian)
    db.session.commit()
    log_activity(user.id, 'REMOVE_GUARDIAN', f"Removed guardian {name}", request)
    return jsonify({'success': True, 'message': f"Guardian '{name}' removed successfully."}), 200


@api_bp.route('/api/auth/me', methods=['GET'])
@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required
def api_me():
    """Hydrates authenticated user details from session or JWT."""
    user = get_current_user_from_token() or (User.query.get(session.get('user_id')) if 'user_id' in session else None)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200



# =====================================================================
# REST API WEBHOOKS
# =====================================================================

@api_bp.route('/api/webhooks/messaging', methods=['POST', 'GET'])
@auth_bp.route('/api/webhooks/messaging', methods=['POST', 'GET'])
def api_messaging_webhook():
    """
    POST /api/webhooks/messaging
    Handles status callbacks and inbound STOP keywords from Twilio / MSG91.
    """
    provider = get_messaging_provider()
    headers = dict(request.headers)
    body = request.get_data()
    form_data = request.form.to_dict() if request.form else (request.get_json(silent=True) or {})

    # Validate Webhook Signature
    if not provider.verify_webhook(headers, body, form_data):
        return jsonify({'error': 'Invalid webhook signature'}), 403

    # Check for Inbound STOP / Opt-Out
    inbound_body = (form_data.get('Body') or form_data.get('body') or form_data.get('message') or '').strip().upper()
    from_phone = form_data.get('From') or form_data.get('from') or form_data.get('mobile') or ''

    if inbound_body in ('STOP', 'UNSUBSCRIBE', 'CANCEL', 'OPT-OUT', 'OPTOUT') and from_phone:
        NotificationService.handle_opt_out(from_phone)

    # Check for Delivery Status Callback
    msg_sid = form_data.get('MessageSid') or form_data.get('SmsSid') or form_data.get('message_id')
    msg_status = form_data.get('MessageStatus') or form_data.get('status')

    if msg_sid and msg_status:
        log_record = NotificationLog.query.filter_by(provider_message_id=msg_sid).first()
        if log_record:
            log_record.status = msg_status.lower()
            db.session.commit()

    return jsonify({'status': 'ok'}), 200


# =====================================================================
# STANDARD REST API AUTH ENDPOINTS (For React Frontend)
# =====================================================================

@api_bp.route('/api/auth/login', methods=['POST'])
@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """Citizen and admin JSON login endpoint."""
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'message': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['role'] = user.role
        session['user_role'] = user.role
        session['user_name'] = user.fullname
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        token = generate_jwt_token(user)
        record_login(user.id, email, 'SUCCESS', request)
        log_activity(user.id, 'login', f"Citizen authenticated: {user.fullname}", request)

        resp_payload = {
            'access_token': token,
            'user': user.to_dict(),
            'message': f'Welcome back, {user.fullname}!'
        }

        configured_provider = (current_app.config.get('MESSAGING_PROVIDER') or 'email').lower()
        if configured_provider == 'email' or (user.phone_number and user.phone_verified) or user.preferred_otp_channel == 'email':
            ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
            channel = 'email' if configured_provider == 'email' else (user.preferred_otp_channel or 'sms')
            success, challenge_id, msg, final_channel = OTPService.send_otp(
                phone=user.email if channel == 'email' else user.phone_number,
                channel=channel,
                user_id=user.id,
                purpose='2fa_login',
                ip_address=ip,
                email=user.email
            )
            if challenge_id:
                resp_payload.update({
                    'requires_2fa': True,
                    'challenge_id': challenge_id,
                    'channel': final_channel,
                    'masked_recipient': mask_email(user.email) if final_channel == 'email' else mask_phone_number(user.phone_number or ''),
                    'masked_phone': mask_email(user.email) if final_channel == 'email' else mask_phone_number(user.phone_number or ''),
                    'otp_message': msg
                })

        return jsonify(resp_payload), 200

    else:
        record_login(user.id if user else None, email, 'FAILED', request)
        log_activity(user.id if user else None, 'login_failed', f"Failed login attempt for {email}", request)
        return jsonify({'message': 'Invalid email or password.'}), 401


@api_bp.route('/api/auth/register', methods=['POST'])
@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """Citizen JSON registration endpoint."""
    data = request.get_json() or {}
    fullname = data.get('fullname', '').strip()
    email = data.get('email', '').lower().strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    preferred_channel = data.get('preferred_otp_channel', 'sms').lower().strip()

    if not fullname or not email or not password:
        return jsonify({'message': 'Full name, email, and password are required.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'An account with this email already exists.'}), 409

    valid_phone, e164 = normalize_phone_number(phone) if phone else (False, None)

    user = User(
        fullname=fullname,
        email=email,
        phone=phone or None,
        phone_number=e164,
        preferred_otp_channel=preferred_channel if preferred_channel in ('sms', 'whatsapp') else 'sms',
        role='citizen',
        is_verified=True,
        phone_verified=False,
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_jwt_token(user)
    record_login(user.id, email, 'SUCCESS', request)
    log_activity(user.id, 'register', f"Registered citizen account: {fullname}", request)

    return jsonify({
        'access_token': token,
        'user': user.to_dict(),
        'message': 'Registration successful!'
    }), 201



@api_bp.route('/api/auth/logout', methods=['POST'])
@auth_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Clears user session."""
    session.clear()
    return jsonify({'message': 'Signed out successfully.'}), 200



# =====================================================================
# SSR WEB ROUTES (HTML Templates)
# =====================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin' or session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            configured_provider = (current_app.config.get('MESSAGING_PROVIDER') or 'email').lower()
            # Check if 2FA is required (Email provider, or phone 2FA configured, or email preferred)
            if configured_provider == 'email' or (user.phone_number and user.phone_verified) or user.preferred_otp_channel == 'email':
                ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
                channel = 'email' if configured_provider == 'email' else (user.preferred_otp_channel or 'sms')
                
                if channel == 'email' and not user.email:
                    flash('No registered email address found for this user account. Please contact support.', 'danger')
                    return render_template('auth/login.html', form=form)

                success, challenge_id, msg, final_channel = OTPService.send_otp(
                    phone=user.email if channel == 'email' else user.phone_number,
                    channel=channel,
                    user_id=user.id,
                    purpose='2fa_login',
                    ip_address=ip,
                    email=user.email
                )

                if challenge_id:
                    session['2fa_user_id'] = user.id
                    session['2fa_challenge_id'] = challenge_id
                    flash(msg, 'info' if success else 'warning')
                    return redirect(url_for('auth.verify_2fa'))
                else:
                    flash(msg or 'Unable to initiate verification code. Please try again.', 'danger')
                    return render_template('auth/login.html', form=form)

            session['user_id'] = user.id
            session['role'] = user.role
            session['user_role'] = user.role
            session['user_name'] = user.fullname
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

            record_login(user.id, email, 'SUCCESS', request)
            flash(f'Welcome back, {user.fullname}!', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            if session.get('role') == 'admin' or user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('dashboard.index'))
        else:
            record_login(user.id if user else None, email, 'FAILED', request)
            flash('Invalid email or password. Please verify your credentials.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """2FA Verification route for HTML template sessions."""
    challenge_id = session.get('2fa_challenge_id')
    user_id = session.get('2fa_user_id')

    if not challenge_id or not user_id:
        flash('No 2FA session in progress. Please sign in.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    challenge = OTPChallenge.query.get(challenge_id)
    if not challenge or not user:
        flash('Verification session expired or invalid. Please sign in again.', 'warning')
        return redirect(url_for('auth.login'))

    form = OTPForm()
    
    # Determine channel and masked recipient
    channel_raw = (challenge.channel or user.preferred_otp_channel or current_app.config.get('MESSAGING_PROVIDER') or 'email').lower()
    is_email = (channel_raw == 'email') or ('@' in str(challenge.phone_number or ''))
    
    if is_email:
        target_display = mask_email(challenge.phone_number or user.email or '')
        channel_name = 'Email'
    else:
        target_display = mask_phone_number(challenge.phone_number or (user.phone_number or ''))
        channel_name = 'WhatsApp' if channel_raw == 'whatsapp' else 'SMS'

    if form.validate_on_submit() or (request.method == 'POST' and request.form.get('otp')):
        entered_otp = (form.otp.data or request.form.get('otp', '')).strip()
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
        success, msg, payload = OTPService.verify_otp(
            challenge_id=int(challenge_id),
            entered_otp=entered_otp,
            ip_address=ip
        )

        if success:
            session.pop('2fa_user_id', None)
            session.pop('2fa_challenge_id', None)
            session['user_id'] = user.id
            session['role'] = user.role
            session['user_role'] = user.role
            session['user_name'] = user.fullname

            # Mark user and verification channels as verified
            user.is_verified = True
            if is_email:
                user.email_verified = True
            else:
                user.phone_verified = True
            db.session.commit()

            record_login(user.id, user.email, 'SUCCESS', request, method=f"{channel_raw}_otp", phone=challenge.phone_number)
            flash(f'Two-step verification successful! Welcome back, {user.fullname}.', 'success')

            if user.role == 'admin' or user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('dashboard.index'))
        else:
            flash(msg, 'danger')

    return render_template(
        'auth/verify_2fa.html',
        form=form,
        target_email=target_display,
        masked_phone=target_display,
        channel=channel_name,
        challenge_id=challenge_id
    )


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session and request.method == 'GET':
        # If already logged in and visiting register, clear previous session to allow registering fresh account
        session.clear()

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        raw_phone = form.phone.data.strip() if form.phone.data else ''
        valid_phone, e164 = normalize_phone_number(raw_phone) if raw_phone else (False, None)

        try:
            if not user:
                user = User(
                    fullname=form.fullname.data.strip(),
                    email=email,
                    phone=raw_phone,
                    phone_number=e164,
                    preferred_otp_channel='sms',
                    role='citizen',
                    is_verified=False,
                    phone_verified=False,
                    created_at=datetime.now(timezone.utc)
                )
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
            else:
                user.fullname = form.fullname.data.strip()
                user.phone = raw_phone
                user.phone_number = e164
                user.set_password(form.password.data)
                user.is_verified = False
                db.session.commit()

            # Save or update emergency contact and guardian if provided
            if hasattr(form, 'trusted_contact_name') and form.trusted_contact_name.data:
                rel = (form.trusted_contact_relationship.data or 'Guardian').strip() if hasattr(form, 'trusted_contact_relationship') and form.trusted_contact_relationship.data else 'Guardian'
                tc_name = form.trusted_contact_name.data.strip()
                tc_email = form.trusted_contact_email.data.strip().lower() if hasattr(form, 'trusted_contact_email') and form.trusted_contact_email.data else ''
                tc_phone = form.trusted_contact_phone.data.strip() if hasattr(form, 'trusted_contact_phone') and form.trusted_contact_phone.data else ''
                tc_valid, tc_e164 = normalize_phone_number(tc_phone) if tc_phone else (False, None)
                formatted_tc_phone = f"+91 {tc_e164[3:]}" if (tc_e164 and tc_e164.startswith("+91") and len(tc_e164) == 13) else (tc_e164 or tc_phone)

                contact = EmergencyContact.query.filter_by(user_id=user.id).first()
                if not contact:
                    contact = EmergencyContact(
                        user_id=user.id,
                        contact_name=tc_name,
                        relationship=rel,
                        phone=formatted_tc_phone,
                        email=tc_email,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.session.add(contact)
                else:
                    contact.contact_name = tc_name
                    contact.relationship = rel
                    contact.phone = formatted_tc_phone
                    contact.email = tc_email
                    contact.updated_at = datetime.now(timezone.utc)

                # Sync to Guardian table
                guardian = Guardian.query.filter_by(user_id=user.id).first()
                if not guardian:
                    guardian = Guardian(
                        user_id=user.id,
                        name=tc_name,
                        relationship_type=rel,
                        email=tc_email or None,
                        phone_number=tc_e164 or formatted_tc_phone or (user.phone_number or '+910000000000'),
                        preferred_channel='email' if tc_email else 'sms',
                        consent_given=True,
                        consent_at=datetime.now(timezone.utc),
                        verified=False,
                        opted_out=False,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.session.add(guardian)
                else:
                    guardian.name = tc_name
                    guardian.relationship_type = rel
                    guardian.email = tc_email or None
                    guardian.phone_number = tc_e164 or formatted_tc_phone or guardian.phone_number
                    guardian.preferred_channel = 'email' if tc_email else 'sms'
                    guardian.consent_given = True
                    guardian.consent_at = datetime.now(timezone.utc)
                    guardian.opted_out = False
                    guardian.updated_at = datetime.now(timezone.utc)

                db.session.commit()
                log_activity(user.id, 'ADD_EMERGENCY_CONTACT', f"Emergency Contact set to {tc_name} ({rel})", request)

                # Send one-time confirmation email directly to guardian (does not block registration)
                try:
                    NotificationService.send_guardian_verification(guardian.id)
                except Exception as g_err:
                    logger.warning(f"Could not dispatch initial guardian verification on registration: {g_err}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving registration details: {e}", exc_info=True)
            flash('An unexpected error occurred while setting up your account. Please try again.', 'danger')
            return render_template('auth/register.html', form=form)

        # Send initial OTP via configured provider (Email or SMS/WhatsApp)
        configured_provider = (current_app.config.get('MESSAGING_PROVIDER') or 'email').lower()
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'

        try:
            if configured_provider == 'email':
                success, ch_id, msg, ch = OTPService.send_otp(
                    phone=user.email,
                    channel='email',
                    user_id=user.id,
                    purpose='registration',
                    ip_address=ip,
                    email=user.email
                )
                if ch_id:
                    session['2fa_challenge_id'] = ch_id
                    session['2fa_user_id'] = user.id
                    flash(msg, 'info' if success else 'warning')
                    return redirect(url_for('auth.verify_2fa'))
                else:
                    flash(msg or 'Unable to dispatch verification code. Please try again.', 'danger')
                    return render_template('auth/register.html', form=form)
            elif e164:
                success, ch_id, msg, ch = OTPService.send_otp(
                    phone=e164,
                    channel=user.preferred_otp_channel or 'sms',
                    user_id=user.id,
                    purpose='registration',
                    ip_address=ip
                )
                if ch_id:
                    session['2fa_challenge_id'] = ch_id
                    session['2fa_user_id'] = user.id
                    flash(msg, 'info' if success else 'warning')
                    return redirect(url_for('auth.verify_2fa'))
                else:
                    flash(msg or 'Unable to dispatch verification code. Please try again.', 'danger')
                    return render_template('auth/register.html', form=form)
        except Exception as e:
            logger.error(f"Error dispatching OTP code during registration: {e}", exc_info=True)
            flash('Unable to dispatch verification code at this time. Please try again.', 'danger')
            return render_template('auth/register.html', form=form)

        session['user_id'] = user.id
        session['role'] = user.role
        session['user_role'] = user.role
        session['user_name'] = user.fullname
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    return redirect(url_for('auth.verify_2fa'))


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    ch_id = session.get('2fa_challenge_id')
    if not ch_id:
        flash('No registration or verification in progress.', 'warning')
        return redirect(url_for('auth.register'))

    ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
    success, new_ch_id, msg, ch = OTPService.resend_otp(ch_id, ip_address=ip)
    session['2fa_challenge_id'] = new_ch_id
    flash(msg, 'success' if success else 'warning')
    return redirect(url_for('auth.verify_2fa'))


@auth_bp.route('/sso/google', methods=['GET', 'POST'])
def sso_google():
    """Simulated Google OAuth authentication requiring genuine user details."""
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').lower().strip()

        if not fullname or not email or '@' not in email:
            flash('Please provide a valid full name and email address.', 'danger')
            return render_template('auth/sso_prompt.html', provider='google', provider_title='Google Account Verification', form_action=url_for('auth.sso_google'))

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                fullname=fullname,
                email=email,
                role='citizen',
                is_verified=True,
                created_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc)
            )
            user.set_password(f"SSO_{random.randint(10000000, 99999999)}")
            db.session.add(user)
            db.session.commit()
        else:
            user.is_verified = True
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

        session['user_id'] = user.id
        session['role'] = user.role
        session['user_role'] = user.role
        session['user_name'] = user.fullname
        record_login(user.id, user.email, 'SUCCESS', request, method='sso_google')
        flash(f'Successfully authenticated via Google as {user.fullname}.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/sso_prompt.html', provider='google', provider_title='Google Account Verification', form_action=url_for('auth.sso_google'))


@auth_bp.route('/sso/digilocker', methods=['GET', 'POST'])
def sso_digilocker():
    """Simulated DigiLocker e-KYC authentication requiring genuine user details."""
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').lower().strip()
        phone = request.form.get('phone', '').strip()

        if not fullname or not email or '@' not in email:
            flash('Please provide a valid full name and email address.', 'danger')
            return render_template('auth/sso_prompt.html', provider='digilocker', provider_title='DigiLocker Identity Verification', form_action=url_for('auth.sso_digilocker'))

        valid_phone, e164 = normalize_phone_number(phone) if phone else (False, None)
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                fullname=fullname,
                email=email,
                phone=phone or None,
                phone_number=e164,
                role='citizen',
                is_verified=True,
                created_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc)
            )
            user.set_password(f"Digi_{random.randint(10000000, 99999999)}")
            db.session.add(user)
            db.session.commit()
        else:
            if phone and not user.phone:
                user.phone = phone
                user.phone_number = e164
            user.is_verified = True
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

        session['user_id'] = user.id
        session['role'] = user.role
        session['user_role'] = user.role
        session['user_name'] = user.fullname
        record_login(user.id, user.email, 'SUCCESS', request, method='sso_digilocker')
        flash(f'Successfully verified via DigiLocker as {user.fullname}.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/sso_prompt.html', provider='digilocker', provider_title='DigiLocker Identity Verification', form_action=url_for('auth.sso_digilocker'))


ALLOWED_RELATIONSHIPS = {'Parent', 'Guardian', 'Spouse', 'Sibling', 'Other Family Member', 'Close Friend'}

@auth_bp.route('/account-security', methods=['GET', 'POST'])
@login_required
def account_security():
    user = User.query.get_or_404(session['user_id'])
    password_form = ChangePasswordForm()

    if password_form.validate_on_submit():
        if user.check_password(password_form.current_password.data):
            user.set_password(password_form.new_password.data)
            db.session.commit()
            log_activity(user.id, 'CHANGE_PASSWORD', 'User updated password', request)
            flash('Your password has been successfully updated.', 'success')
            return redirect(url_for('auth.account_security'))
        else:
            flash('Current password incorrect. Please verify and try again.', 'danger')

    recent_logins = LoginHistory.query.filter_by(user_id=user.id).order_by(LoginHistory.timestamp.desc()).limit(10).all()
    guardians = Guardian.query.filter_by(user_id=user.id).order_by(Guardian.created_at.desc()).all()
    emergency_contact = EmergencyContact.query.filter_by(user_id=user.id).first()
    return render_template(
        'account_security.html',
        user=user,
        form=password_form,
        recent_logins=recent_logins,
        guardians=guardians,
        emergency_contact=emergency_contact,
        allowed_relationships=sorted(list(ALLOWED_RELATIONSHIPS))
    )


@auth_bp.route('/emergency-contact/save', methods=['POST'])
@login_required
def save_emergency_contact():
    user = User.query.get_or_404(session['user_id'])
    contact_name = request.form.get('contact_name', '').strip()
    relationship = request.form.get('relationship', '').strip()
    email = request.form.get('email', '').lower().strip()
    phone = request.form.get('phone', '').strip()

    if not contact_name or not relationship:
        flash('⚠️ Contact full name and a valid relationship must both be provided.', 'danger')
        return redirect(url_for('auth.account_security'))

    if not email or '@' not in email:
        flash('⚠️ Please enter a valid email address for your trusted contact.', 'danger')
        return redirect(url_for('auth.account_security'))

    valid_phone, e164 = normalize_phone_number(phone)
    if not valid_phone:
        flash('⚠️ Please enter a valid 10-digit Indian mobile number.', 'danger')
        return redirect(url_for('auth.account_security'))

    formatted_phone = f"+91 {e164[3:]}" if (e164 and e164.startswith("+91") and len(e164) == 13) else (e164 or phone)
    existing = EmergencyContact.query.filter_by(user_id=user.id).first()
    if existing:
        existing.contact_name = contact_name
        existing.relationship = relationship
        existing.email = email
        existing.phone = formatted_phone
        existing.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        log_activity(user.id, 'EDIT_EMERGENCY_CONTACT', f"Updated Emergency Contact: {contact_name}", request)
    else:
        new_contact = EmergencyContact(
            user_id=user.id,
            contact_name=contact_name,
            relationship=relationship,
            email=email,
            phone=formatted_phone,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_contact)
        db.session.commit()
        log_activity(user.id, 'ADD_EMERGENCY_CONTACT', f"Emergency Contact set to {contact_name} ({relationship})", request)

    # Sync into Guardian table for emergency notification dispatch
    guardian = Guardian.query.filter_by(user_id=user.id).first()
    if not guardian:
        guardian = Guardian(
            user_id=user.id,
            name=contact_name,
            relationship_type=relationship,
            email=email,
            phone_number=e164 or formatted_phone,
            preferred_channel='email' if email else 'sms',
            consent_given=True,
            consent_at=datetime.utcnow(),
            verified=False,
            opted_out=False
        )
        db.session.add(guardian)
    else:
        guardian.name = contact_name
        guardian.relationship_type = relationship
        guardian.email = email
        guardian.phone_number = e164 or formatted_phone
        guardian.preferred_channel = 'email' if email else 'sms'
        guardian.consent_given = True
        guardian.consent_at = datetime.utcnow()
        guardian.verified = False
        guardian.opted_out = False
    db.session.commit()

    # Dispatch guardian verification request directly to contact
    try:
        NotificationService.send_guardian_verification(guardian.id)
    except Exception as err:
        logger.warning(f"Could not send guardian confirmation email: {err}")

    flash(f"✅ Emergency trusted contact '{contact_name}' saved. A confirmation email has been dispatched to {email}.", 'success')
    return redirect(url_for('auth.account_security'))


@auth_bp.route('/guardian/confirm', methods=['GET', 'POST'])
@auth_bp.route('/confirm-guardian-link', methods=['GET', 'POST'])
def confirm_guardian_link():
    """
    Public landing route for a trusted contact / guardian to confirm enrollment.
    Can be verified via 1-click token/OTP query parameters or form submission.
    """
    challenge_id = request.args.get('challenge_id') or request.form.get('challenge_id')
    otp = request.args.get('otp') or request.form.get('otp')

    if request.method == 'POST' and not (challenge_id and otp):
        entered_otp = request.form.get('otp', '').strip()
        g_id = request.form.get('guardian_id')
        if g_id and entered_otp:
            g = Guardian.query.get(g_id)
            if g:
                target_ref = g.email if (g.email and '@' in g.email) else g.phone_number
                ch = OTPChallenge.query.filter_by(
                    user_id=g.user_id,
                    phone_number=target_ref,
                    purpose='guardian_verify',
                    consumed_at=None
                ).order_by(OTPChallenge.created_at.desc()).first()
                if ch:
                    challenge_id = ch.id
                    otp = entered_otp

    if challenge_id and otp:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or '127.0.0.1'
        success, msg, payload = OTPService.verify_otp(
            challenge_id=int(challenge_id),
            entered_otp=str(otp).strip(),
            ip_address=ip
        )

        if success:
            challenge = OTPChallenge.query.get(int(challenge_id))
            guardian = None
            if challenge:
                guardian = Guardian.query.filter_by(user_id=challenge.user_id).filter(
                    (Guardian.email == challenge.phone_number) | (Guardian.phone_number == challenge.phone_number)
                ).first()
                if not guardian:
                    guardian = Guardian.query.filter_by(user_id=challenge.user_id).first()

            if guardian:
                guardian.verified = True
                guardian.consent_given = True
                guardian.consent_at = datetime.utcnow()
                guardian.opted_out = False
                db.session.commit()

                ward = User.query.get(guardian.user_id)
                ward_name = ward.fullname if ward else "Citizen"
                record_audit_ledger(guardian.user_id, 'GUARDIAN_CONFIRMED', f"Guardian {guardian.name} confirmed emergency contact enrollment")

                return render_template(
                    'auth/guardian_confirmed.html',
                    guardian=guardian,
                    ward_name=ward_name,
                    success=True,
                    message=f"Thank you, {guardian.name}. You are now verified as a trusted emergency contact for {ward_name}."
                )
            else:
                return render_template(
                    'auth/guardian_confirmed.html',
                    success=True,
                    message="Guardian status confirmed successfully."
                )
        else:
            return render_template(
                'auth/guardian_confirmed.html',
                success=False,
                error=msg or "Invalid or expired confirmation link."
            )

    return render_template('auth/guardian_confirmed.html', show_form=True)


@auth_bp.route('/emergency-contact/delete', methods=['POST'])
@login_required
def delete_emergency_contact():
    user = User.query.get_or_404(session['user_id'])
    contact = EmergencyContact.query.filter_by(user_id=user.id).first()
    if contact:
        name = contact.contact_name
        db.session.delete(contact)
        # Also clean up associated guardian
        guardians = Guardian.query.filter_by(user_id=user.id).all()
        for g in guardians:
            db.session.delete(g)
        db.session.commit()
        log_activity(user.id, 'REMOVE_EMERGENCY_CONTACT', f"Removed emergency contact {name}", request)
        flash('Emergency trusted contact has been removed.', 'info')
    else:
        flash('No emergency contact found to delete.', 'warning')
    return redirect(url_for('auth.account_security'))


@auth_bp.route('/guardian/test-alert', methods=['POST'])
@login_required
def web_guardian_test_alert():
    """Triggers an instant test emergency alert to verified guardians."""
    user_id = session.get('user_id')
    success, msg = NotificationService.send_test_alert(user_id)
    flash(msg, 'success' if success else 'warning')
    return redirect(url_for('auth.account_security'))


@auth_bp.route('/guardian/resend-verification/<int:guardian_id>', methods=['POST'])
@login_required
def web_guardian_resend_verification(guardian_id):
    """Resends the verification request to a guardian."""
    user_id = session.get('user_id')
    guardian = Guardian.query.filter_by(id=guardian_id, user_id=user_id).first()
    if not guardian:
        flash('Guardian record not found.', 'danger')
        return redirect(url_for('auth.account_security'))
    success, msg = NotificationService.send_guardian_verification(guardian.id)
    flash(msg, 'success' if success else 'warning')
    return redirect(url_for('auth.account_security'))


@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get_or_404(session['user_id'])
    anonymize = request.form.get('anonymize_data', 'true') == 'true'
    if anonymize:
        for complaint in user.complaints:
            complaint.user_id = None
        db.session.commit()
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash('Your account and personal data have been completely deleted as per privacy policy.', 'info')
    return redirect(url_for('report.home'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out safely.', 'info')
    return redirect(url_for('auth.login'))
