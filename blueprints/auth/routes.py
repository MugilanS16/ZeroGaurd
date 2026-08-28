from datetime import datetime, timezone
import random
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, session, abort
from blueprints.auth import auth_bp
from blueprints.auth.forms import LoginForm, RegisterForm, OTPForm, ChangePasswordForm
from database import db
from database.models import User, LoginHistory, Complaint, OTPVerification
from utils.otp import create_and_send_otp

def login_required(f):
    """Decorator to require user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require cyber-cell administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Access denied. Admin authentication required.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('role') != 'admin' and session.get('user_role') != 'admin':
            flash('Access denied. You do not have administrator privileges.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def record_login(user_id, email, status, req):
    """Helper to log security login attempts."""
    try:
        ip = req.headers.get('X-Forwarded-For', req.remote_addr) or '127.0.0.1'
        ua = req.headers.get('User-Agent', '')[:250]
        log = LoginHistory(
            user_id=user_id,
            email_attempted=email,
            ip_address=ip,
            user_agent=ua,
            status=status,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

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
            # Block login for unverified users
            if not user.is_verified:
                session['verify_email'] = email
                create_and_send_otp(email, purpose='registration')
                flash('Your account email has not been verified yet. A 6-digit verification code has been dispatched to your email.', 'warning')
                return redirect(url_for('auth.verify_otp'))

            session['user_id'] = user.id
            session['role'] = user.role
            session['user_role'] = user.role
            session['user_name'] = user.fullname
            try:
                user.last_login = datetime.now(timezone.utc)
                db.session.commit()
            except Exception:
                db.session.rollback()

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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        
        user = User.query.filter_by(email=email).first()
        if user and user.is_verified:
            flash('An account with this email already exists. Please sign in.', 'warning')
            return redirect(url_for('auth.login'))

        if not user:
            user = User(
                fullname=form.fullname.data.strip(),
                email=email,
                phone=form.phone.data.strip(),
                role='citizen',
                is_verified=False,
                created_at=datetime.now(timezone.utc)
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
        else:
            user.fullname = form.fullname.data.strip()
            user.phone = form.phone.data.strip()
            user.set_password(form.password.data)
            db.session.commit()

        # Save trusted contact data in session pending OTP verification
        tc_phone_digits = re.sub(r'\D', '', form.trusted_contact_phone.data or '')
        if len(tc_phone_digits) == 12 and tc_phone_digits.startswith('91'):
            tc_phone_digits = tc_phone_digits[2:]
        formatted_tc_phone = f"+91 {tc_phone_digits}"

        session['registration_trusted_contact'] = {
            'contact_name': form.trusted_contact_name.data.strip(),
            'relationship': form.trusted_contact_relationship.data.strip(),
            'email': form.trusted_contact_email.data.lower().strip(),
            'phone': formatted_tc_phone
        }

        session['verify_email'] = email
        success, msg = create_and_send_otp(email, purpose='registration')

        if success:
            flash(msg, 'info')
        else:
            flash(msg, 'warning')

        return redirect(url_for('auth.verify_otp'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    target_email = session.get('verify_email')
    if not target_email:
        flash('No email pending verification. Please register or sign in.', 'warning')
        return redirect(url_for('auth.register'))

    user = User.query.filter_by(email=target_email).first()
    if not user:
        flash('User account not found. Please register.', 'danger')
        return redirect(url_for('auth.register'))

    if user.is_verified:
        flash('Your email is already verified. Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    form = OTPForm()
    if form.validate_on_submit():
        entered_otp = form.otp.data.strip()

        # Query latest unused OTP record for this email
        otp_record = OTPVerification.query.filter_by(
            email=target_email,
            purpose='registration',
            is_used=False
        ).order_by(OTPVerification.created_at.desc()).first()

        now = datetime.utcnow()
        if not otp_record:
            flash('No active verification code found. Please click Resend OTP.', 'danger')
        elif now > otp_record.expires_at:
            flash('The verification code has expired (5 minute limit). Please click Resend OTP.', 'danger')
        elif not otp_record.check_otp(entered_otp):
            flash('Invalid OTP code. Please check your email and try again.', 'danger')
        else:
            # Mark OTP as used and user as verified
            otp_record.is_used = True
            user.is_verified = True
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

            session.pop('verify_email', None)

            # Create emergency contact if provided during registration
            tc_data = session.pop('registration_trusted_contact', None)
            if tc_data:
                existing_tc = EmergencyContact.query.filter_by(user_id=user.id).first()
                if not existing_tc:
                    new_contact = EmergencyContact(
                        user_id=user.id,
                        contact_name=tc_data['contact_name'],
                        relationship=tc_data['relationship'],
                        email=tc_data['email'],
                        phone=tc_data['phone'],
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(new_contact)
                    db.session.commit()

                    log_activity(user.id, 'ADD_EMERGENCY_CONTACT', f"Emergency Contact registered at signup: {tc_data['contact_name']} ({tc_data['relationship']})", request)

                    try:
                        from utils.mailer import send_trusted_contact_added_notification
                        send_trusted_contact_added_notification(
                            contact_email=tc_data['email'],
                            contact_name=tc_data['contact_name'],
                            user_name=user.fullname,
                            user_email=user.email,
                            user_phone=user.phone or 'Not Provided',
                            relationship=tc_data['relationship'],
                            is_update=False
                        )
                    except Exception as e:
                        print(f"[MAIL WARNING] Failed to send registration trusted contact email: {e}")

            # Auto log in
            session['user_id'] = user.id
            session['role'] = user.role
            session['user_role'] = user.role
            session['user_name'] = user.fullname

            record_login(user.id, user.email, 'SUCCESS', request)
            flash('Email verification successful! Welcome to ZeroGuard AI.', 'success')
            return redirect(url_for('dashboard.index'))


    return render_template('auth/verify_otp.html', form=form, target_email=target_email)

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    target_email = session.get('verify_email')
    if not target_email:
        flash('No registration or verification in progress.', 'warning')
        return redirect(url_for('auth.register'))

    success, msg = create_and_send_otp(target_email, purpose='registration')
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'warning')

    return redirect(url_for('auth.verify_otp'))

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
        record_login(user.id, user.email, 'SUCCESS', request)
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

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                fullname=fullname,
                email=email,
                phone=phone or None,
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
            user.is_verified = True
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()

        session['user_id'] = user.id
        session['role'] = user.role
        session['user_role'] = user.role
        session['user_name'] = user.fullname
        record_login(user.id, user.email, 'SUCCESS', request)
        flash(f'Successfully verified via DigiLocker as {user.fullname}.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/sso_prompt.html', provider='digilocker', provider_title='DigiLocker Identity Verification', form_action=url_for('auth.sso_digilocker'))

import re
from database.models import User, LoginHistory, Complaint, OTPVerification, EmergencyContact, ActivityLog

ALLOWED_RELATIONSHIPS = {'Parent', 'Guardian', 'Spouse', 'Sibling', 'Other Family Member', 'Close Friend'}

def log_activity(user_id, action, details, req):
    """Helper to record user security and profile activity logs."""
    try:
        ip = req.headers.get('X-Forwarded-For', req.remote_addr) or '127.0.0.1'
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

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
    emergency_contact = EmergencyContact.query.filter_by(user_id=user.id).first()
    return render_template('account_security.html', user=user, form=password_form, recent_logins=recent_logins, emergency_contact=emergency_contact, allowed_relationships=sorted(list(ALLOWED_RELATIONSHIPS)))

@auth_bp.route('/emergency-contact/save', methods=['POST'])
@login_required
def save_emergency_contact():
    user = User.query.get_or_404(session['user_id'])
    contact_name = request.form.get('contact_name', '').strip()
    relationship = request.form.get('relationship', '').strip()
    email = request.form.get('email', '').lower().strip()
    phone = request.form.get('phone', '').strip()

    # Validation 1: Both contact_name and relationship must be provided together
    if not contact_name or not relationship:
        flash('⚠️ Contact full name and a valid relationship must both be provided.', 'danger')
        return redirect(url_for('auth.account_security'))

    if relationship not in ALLOWED_RELATIONSHIPS:
        flash('⚠️ Please select a valid relationship option from the dropdown.', 'danger')
        return redirect(url_for('auth.account_security'))

    # Validation 2: Email format & self-comparison
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        flash('⚠️ Please enter a valid email address for your trusted contact.', 'danger')
        return redirect(url_for('auth.account_security'))

    if email == user.email.lower().strip():
        flash('⚠️ Emergency contact email cannot be identical to your own account email.', 'danger')
        return redirect(url_for('auth.account_security'))

    # Validation 3: 10-digit Indian Phone format & self-comparison
    digits_only = re.sub(r'\D', '', phone)
    if len(digits_only) == 12 and digits_only.startswith('91'):
        digits_only = digits_only[2:]

    if len(digits_only) != 10 or not digits_only[0] in '6789':
        flash('⚠️ Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.', 'danger')
        return redirect(url_for('auth.account_security'))

    user_phone_digits = re.sub(r'\D', '', user.phone or '')
    if user_phone_digits and len(user_phone_digits) >= 10 and digits_only == user_phone_digits[-10:]:
        flash('⚠️ Emergency contact phone number cannot be identical to your own mobile number.', 'danger')
        return redirect(url_for('auth.account_security'))

    formatted_phone = f"+91 {digits_only}"

    from utils.mailer import send_trusted_contact_added_notification, send_trusted_contact_removed_notification

    existing = EmergencyContact.query.filter_by(user_id=user.id).first()
    is_update = existing is not None

    if existing:
        existing.contact_name = contact_name
        existing.relationship = relationship
        existing.email = email
        existing.phone = formatted_phone
        existing.updated_at = datetime.now(timezone.utc)
        action_name = 'EDIT_EMERGENCY_CONTACT'
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
        action_name = 'ADD_EMERGENCY_CONTACT'

    db.session.commit()
    log_activity(user.id, action_name, f"Emergency Contact set to {contact_name} ({relationship})", request)

    # Safe email notification dispatch (non-blocking try/except)
    try:
        send_trusted_contact_added_notification(
            contact_email=email,
            contact_name=contact_name,
            user_name=user.fullname,
            user_email=user.email,
            user_phone=user.phone or 'Not Provided',
            relationship=relationship,
            is_update=is_update
        )
    except Exception as e:
        print(f"[MAIL WARNING] Failed to send trusted contact email: {e}")

    msg = f"✅ Emergency trusted contact '{contact_name}' ({relationship}) successfully saved and notified via email."
    flash(msg, 'success')
    return redirect(url_for('auth.account_security'))

@auth_bp.route('/emergency-contact/delete', methods=['POST'])
@login_required
def delete_emergency_contact():
    from utils.mailer import send_trusted_contact_removed_notification
    user = User.query.get_or_404(session['user_id'])
    contact = EmergencyContact.query.filter_by(user_id=user.id).first()

    if contact:
        name = contact.contact_name
        old_email = contact.email
        db.session.delete(contact)
        db.session.commit()
        log_activity(user.id, 'REMOVE_EMERGENCY_CONTACT', f"Removed emergency contact {name}", request)

        # Safe removal email dispatch
        try:
            send_trusted_contact_removed_notification(
                contact_email=old_email,
                contact_name=name,
                user_name=user.fullname
            )
        except Exception as e:
            print(f"[MAIL WARNING] Failed to send trusted contact removal email: {e}")

        flash('Emergency trusted contact has been removed.', 'info')
    else:
        flash('No emergency contact found to delete.', 'warning')

    return redirect(url_for('auth.account_security'))


@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get_or_404(session['user_id'])
    # Anonymize complaints or cascade delete based on privacy selection
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

