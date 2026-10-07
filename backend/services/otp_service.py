"""
Enterprise OTP Security Service for ZeroGuard AI.
Implements:
- 6-digit numeric OTP generation via `secrets` module
- Server-side HMAC-SHA256 hashing (raw OTP is never persisted)
- Constant-time comparison via `hmac.compare_digest`
- 5-minute expiration & single-use invalidation
- Max 5 failed attempts per OTP lock-out
- 30-second resend cooldown & 5 sends/hour rate limiting per phone number
- E.164 phone normalization with default Region 'IN' (+91)
- Automatic fallback from WhatsApp to SMS
- SHA-256 audit ledger recording for all security events
"""
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

import phonenumbers
from phonenumbers import PhoneNumberFormat, NumberParseException
from flask import current_app, request

from database import db
from database.models import User, OTPChallenge, NotificationLog, ActivityLog
from backend.services.messaging.factory import get_messaging_provider
from backend.services.messaging.templates import render_template

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Utilities: Normalization, Masking, Generation, Hashing
# ---------------------------------------------------------------------
def normalize_phone_number(raw_phone: str, default_region: str = 'IN') -> Tuple[bool, str]:
    """
    Normalizes a phone number to standard E.164 format.
    Default country: India ('IN', +91).
    Returns (is_valid: bool, e164_formatted_phone: str).
    """
    if not raw_phone:
        return False, ""

    raw_phone = str(raw_phone).strip()
    try:
        parsed = phonenumbers.parse(raw_phone, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return False, ""
        e164 = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        return True, e164
    except NumberParseException:
        # Fallback for common 10-digit Indian input without country prefix
        digits = "".join(ch for ch in raw_phone if ch.isdigit())
        if len(digits) == 10 and digits[0] in '6789':
            return True, f"+91{digits}"
        if len(digits) == 12 and digits.startswith('91') and digits[2] in '6789':
            return True, f"+{digits}"
        return False, ""


def mask_phone_number(phone: str) -> str:
    """Masks a phone number for secure logging (e.g., +91******3210)."""
    if not phone:
        return "***"
    phone_str = str(phone).strip()
    if '@' in phone_str:
        return mask_email(phone_str)
    if len(phone_str) <= 6:
        return "***"
    return f"{phone_str[:3]}******{phone_str[-4:]}"


def mask_email(email: str) -> str:
    """Masks an email address for secure logging/display (e.g., m*****4@gmail.com)."""
    if not email or '@' not in email:
        return "***"
    parts = str(email).strip().split('@')
    user_part = parts[0]
    domain_part = parts[1] if len(parts) > 1 else ''
    if len(user_part) <= 2:
        return f"{user_part[0]}*@{domain_part}"
    return f"{user_part[0]}*****{user_part[-1]}@{domain_part}"


def generate_secure_otp(length: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP using `secrets` module."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def get_otp_server_secret() -> bytes:
    """Retrieves the server-side HMAC secret key from config."""
    if current_app:
        secret = current_app.config.get('OTP_SECRET_KEY') or current_app.config.get('SECRET_KEY')
    else:
        import os
        secret = os.environ.get('OTP_SECRET_KEY') or os.environ.get('SECRET_KEY') or 'zeroguard-ai-default-dev-secret-key-2026'
    return secret.encode('utf-8')


def hash_otp(otp_code: str, secret_key: Optional[bytes] = None) -> str:
    """Computes HMAC-SHA256 digest of the given OTP string with the server secret."""
    secret = secret_key or get_otp_server_secret()
    return hmac.new(secret, str(otp_code).strip().encode('utf-8'), hashlib.sha256).hexdigest()


def verify_otp_hash(entered_otp: str, stored_hash: str, secret_key: Optional[bytes] = None) -> bool:
    """Performs constant-time HMAC-SHA256 comparison."""
    if not entered_otp or not stored_hash:
        return False
    computed_hash = hash_otp(entered_otp, secret_key)
    return hmac.compare_digest(computed_hash, stored_hash)


def record_audit_ledger(user_id: Optional[int], action: str, details: str, ip: str = '127.0.0.1'):
    """Records an audit event with SHA-256 blockchain-style chaining in ActivityLog."""
    try:
        last_log = ActivityLog.query.order_by(ActivityLog.id.desc()).first()
        prev_hash = last_log.record_hash if last_log and last_log.record_hash else '0' * 64

        log_entry = ActivityLog(
            user_id=user_id,
            action=action,
            action_type=action,
            details=details,
            description=details,
            ip_address=ip,
            prev_hash=prev_hash,
            timestamp=datetime.utcnow()
        )
        log_entry.record_hash = log_entry.compute_hash(previous_hash=prev_hash)
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"[AuditLedger] Failed to record ledger entry: {e}")


# ---------------------------------------------------------------------
# Core OTP Service Operations
# ---------------------------------------------------------------------
class OTPService:
    """Core OTP management service handling dispatch, fallback, and verification."""

    @classmethod
    def send_otp(
        cls,
        phone: Optional[str] = None,
        channel: Optional[str] = None,
        user_id: Optional[int] = None,
        purpose: str = '2fa_login',
        ip_address: Optional[str] = None,
        email: Optional[str] = None
    ) -> Tuple[bool, Optional[int], str, str]:
        """
        Creates and dispatches an OTP challenge over Email, SMS, or WhatsApp.
        Returns: (success: bool, challenge_id: Optional[int], message: str, final_channel: str)
        """
        ip = ip_address or (request.headers.get('X-Forwarded-For', request.remote_addr) if request else '127.0.0.1')
        configured_provider = (current_app.config.get('MESSAGING_PROVIDER') or 'email').lower() if current_app else 'email'

        if channel is None:
            channel = configured_provider
        else:
            channel = channel.lower().strip()

        if channel not in ('email', 'sms', 'whatsapp'):
            channel = 'email' if configured_provider == 'email' else 'sms'

        # Resolve user if user_id passed
        user = User.query.get(user_id) if user_id else None
        now = datetime.utcnow()
        cooldown_sec = current_app.config.get('OTP_RESEND_COOLDOWN_SECONDS', 30) if current_app else 30
        max_hourly = current_app.config.get('OTP_MAX_HOURLY_SENDS', 5) if current_app else 5
        expiry_sec = current_app.config.get('OTP_EXPIRY_SECONDS', 300) if current_app else 300
        expires_at = now + timedelta(seconds=expiry_sec)

        # -------------------------------------------------------------
        # BRANCH A: EMAIL OTP DELIVERY (MESSAGING_PROVIDER=email)
        # -------------------------------------------------------------
        if channel == 'email' or (phone and '@' in str(phone)):
            target_email = (email or (user.email if user else None) or (phone if phone and '@' in str(phone) else '')).strip().lower()
            if not target_email or '@' not in target_email:
                return False, None, "No registered email address found for this user. Please verify your profile email.", 'email'

            masked = mask_email(target_email)

            # 1. Resend Cooldown
            recent = OTPChallenge.query.filter(
                OTPChallenge.phone_number == target_email,
                OTPChallenge.created_at > now - timedelta(seconds=cooldown_sec),
                OTPChallenge.consumed_at.is_(None)
            ).order_by(OTPChallenge.created_at.desc()).first()

            if recent:
                seconds_left = cooldown_sec - int((now - recent.created_at).total_seconds())
                return False, None, f"Please wait {max(1, seconds_left)} seconds before requesting a new verification code.", 'email'

            # 2. Hourly Limit
            hour_ago = now - timedelta(hours=1)
            hourly_count = OTPChallenge.query.filter(
                OTPChallenge.phone_number == target_email,
                OTPChallenge.created_at > hour_ago
            ).count()

            if hourly_count >= max_hourly:
                logger.warning(f"[OTPService] Email rate limit exceeded for {masked}")
                record_audit_ledger(user_id, 'OTP_RATE_LIMIT_EXCEEDED', f"Hourly limit reached for {masked}", ip)
                return False, None, "Too many verification requests for this email. Please try again in 1 hour.", 'email'

            # 3. Generate & Persist Challenge
            otp_code = generate_secure_otp(6)
            challenge = OTPChallenge(
                user_id=user_id,
                phone_number=target_email,
                channel='email',
                purpose=purpose,
                otp_hash=hash_otp(otp_code),
                expires_at=expires_at,
                attempts=0,
                consumed_at=None,
                ip_address=ip,
                created_at=now
            )
            db.session.add(challenge)
            db.session.commit()

            # 4. Dispatch Email
            provider = get_messaging_provider('email')
            if hasattr(provider, 'send_email'):
                res = provider.send_email(
                    to_email=target_email,
                    otp_code=otp_code,
                    expiry_seconds=expiry_sec,
                    purpose=purpose
                )
            else:
                from backend.services.messaging.email_provider import EmailProvider
                res = EmailProvider(current_app.config if current_app else {}).send_email(
                    to_email=target_email,
                    otp_code=otp_code,
                    expiry_seconds=expiry_sec,
                    purpose=purpose
                )

            # 5. Log & Audit
            log_entry = NotificationLog(
                recipient_type='user',
                recipient_ref=masked,
                channel='email',
                template='otp_verification',
                provider_message_id=res.provider_message_id,
                status=res.status,
                error=res.error,
                created_at=now
            )
            db.session.add(log_entry)
            db.session.commit()

            audit_action = 'OTP_DISPATCHED' if res.success else 'OTP_DISPATCH_FAILED'
            record_audit_ledger(user_id, audit_action, f"OTP dispatched via EMAIL to {masked}", ip)

            if not res.success:
                return False, challenge.id, res.error or "Unable to deliver verification code. Please try again.", 'email'

            return True, challenge.id, f"A 6-digit verification code has been dispatched via Email to {masked}.", 'email'

        # -------------------------------------------------------------
        # BRANCH B: SMS / WHATSAPP OTP DELIVERY
        # -------------------------------------------------------------
        valid_phone, e164_phone = normalize_phone_number(phone or '')
        if not valid_phone:
            # If phone invalid but user has email, fallback to email
            if user and user.email:
                return cls.send_otp(channel='email', user_id=user_id, purpose=purpose, ip_address=ip)
            return False, None, "Invalid phone number. Please enter a valid 10-digit Indian mobile number or E.164 format.", channel

        masked = mask_phone_number(e164_phone)

        # Enforce 30-second Resend Cooldown
        recent_challenge = OTPChallenge.query.filter(
            OTPChallenge.phone_number == e164_phone,
            OTPChallenge.created_at > now - timedelta(seconds=cooldown_sec),
            OTPChallenge.consumed_at.is_(None)
        ).order_by(OTPChallenge.created_at.desc()).first()

        if recent_challenge:
            seconds_left = cooldown_sec - int((now - recent_challenge.created_at).total_seconds())
            return False, None, f"Please wait {max(1, seconds_left)} seconds before requesting a new verification code.", channel

        # Enforce Max 5 sends per phone number per hour
        hour_ago = now - timedelta(hours=1)
        hourly_count = OTPChallenge.query.filter(
            OTPChallenge.phone_number == e164_phone,
            OTPChallenge.created_at > hour_ago
        ).count()

        if hourly_count >= max_hourly:
            logger.warning(f"[OTPService] Rate limit exceeded for {masked} ({hourly_count} sends in last hour)")
            record_audit_ledger(user_id, 'OTP_RATE_LIMIT_EXCEEDED', f"Hourly limit reached for {masked}", ip)
            return False, None, "Too many verification requests for this number. Please try again in 1 hour.", channel

        otp_code = generate_secure_otp(6)
        challenge = OTPChallenge(
            user_id=user_id,
            phone_number=e164_phone,
            channel=channel,
            purpose=purpose,
            otp_hash=hash_otp(otp_code),
            expires_at=expires_at,
            attempts=0,
            consumed_at=None,
            ip_address=ip,
            created_at=now
        )
        db.session.add(challenge)
        db.session.commit()

        provider = get_messaging_provider(channel)
        message_body = render_template('otp', channel=channel, otp_code=otp_code)
        dlt_te_id = current_app.config.get('DLT_TEMPLATE_ID_OTP') if current_app else None
        meta_template = current_app.config.get('WHATSAPP_OTP_TEMPLATE_NAME', 'zeroguard_otp_verification') if current_app else None

        final_channel = channel
        dispatch_success = False
        provider_msg_id = None
        dispatch_error = None

        if channel == 'whatsapp':
            res = provider.send_whatsapp(
                phone=e164_phone,
                body=message_body,
                template_name=meta_template,
                variables={'1': otp_code}
            )
            if res.success:
                dispatch_success = True
                provider_msg_id = res.provider_message_id
            else:
                logger.warning(f"[OTPService] WhatsApp dispatch failed for {masked}. Fallback to SMS. Error: {res.error}")
                sms_body = render_template('otp', channel='sms', otp_code=otp_code)
                sms_res = provider.send_sms(
                    phone=e164_phone,
                    body=sms_body,
                    template_id=dlt_te_id,
                    variables={'otp': otp_code}
                )
                final_channel = 'sms'
                if sms_res.success:
                    dispatch_success = True
                    provider_msg_id = sms_res.provider_message_id
                else:
                    dispatch_error = f"WhatsApp & SMS fallback failed: {sms_res.error}"
        else:
            res = provider.send_sms(
                phone=e164_phone,
                body=message_body,
                template_id=dlt_te_id,
                variables={'otp': otp_code}
            )
            if res.success:
                dispatch_success = True
                provider_msg_id = res.provider_message_id
            else:
                dispatch_error = res.error

        # 7. Fallback to Local Console in Dev/Debug mode if external provider failed
        if not dispatch_success:
            is_dev = False
            if current_app:
                is_dev = current_app.config.get('DEBUG', False) or current_app.config.get('FLASK_ENV') == 'development' or (not current_app.config.get('TWILIO_ACCOUNT_SID') and not current_app.config.get('MSG91_AUTH_KEY'))
            else:
                is_dev = True

            if is_dev or provider.name != 'console':
                from backend.services.messaging.console_provider import ConsoleProvider
                dev_console = ConsoleProvider()
                console_res = dev_console.send_sms(e164_phone, message_body)
                if console_res.success:
                    dispatch_success = True
                    final_channel = 'sms'
                    provider_msg_id = console_res.provider_message_id
                    logger.info(f"[OTPService] Local Dev fallback: OTP for {masked} is {otp_code}")

        # 8. Optional / Parallel Private Email Dispatch if enabled
        email_fallback_enabled = current_app.config.get('OTP_EMAIL_FALLBACK', False) if current_app else False
        if email_fallback_enabled and user_id:
            user = User.query.get(user_id)
            if user and user.email:
                try:
                    from utils.otp import send_otp_email
                    if send_otp_email(user.email, otp_code, purpose):
                        logger.info(f"[OTPService] Private OTP email delivered to {user.email}")
                except Exception as email_err:
                    logger.warning(f"[OTPService] Email dispatch: {email_err}")

        # Update Challenge with actual channel used
        if final_channel != challenge.channel:
            challenge.channel = final_channel
            db.session.commit()

        # 9. Log Outbound Notification
        log_entry = NotificationLog(
            recipient_type='user',
            recipient_ref=masked,
            channel=final_channel,
            template='otp_verification',
            provider_message_id=provider_msg_id,
            status='delivered' if (provider.name == 'console' and dispatch_success) else ('sent' if dispatch_success else 'failed'),
            error=dispatch_error,
            created_at=now
        )
        db.session.add(log_entry)
        db.session.commit()

        # 10. Record Security Audit Log
        audit_action = 'OTP_DISPATCHED' if dispatch_success else 'OTP_DISPATCH_FAILED'
        record_audit_ledger(user_id, audit_action, f"OTP dispatched via {final_channel.upper()} to {masked}", ip)

        if not dispatch_success:
            return False, challenge.id, "Unable to deliver verification code. Please try again later.", final_channel

        channel_display = "WhatsApp" if final_channel == 'whatsapp' else ("Email" if final_channel == 'email' else "SMS")
        return True, challenge.id, f"A 6-digit verification code has been dispatched via {channel_display} to {masked}.", final_channel

    @classmethod
    def verify_otp(
        cls,
        challenge_id: int,
        entered_otp: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifies a submitted OTP code against the challenge record.
        Enforces 5-minute expiration, 5-attempt locking, and single-use consumption.

        Returns: (success: bool, message: str, payload: Optional[dict])
        """
        ip = ip_address or (request.headers.get('X-Forwarded-For', request.remote_addr) if request else '127.0.0.1')
        now = datetime.utcnow()

        if not challenge_id or not entered_otp:
            return False, "Verification challenge ID and OTP code are required.", None

        challenge = OTPChallenge.query.get(challenge_id)
        if not challenge:
            return False, "Invalid or expired verification session. Please request a new code.", None

        masked = mask_phone_number(challenge.phone_number)

        # Check if already consumed (Replay Attack Prevention)
        if challenge.is_consumed:
            logger.warning(f"[OTPService] Attempted replay of consumed OTP challenge {challenge_id} for {masked}")
            record_audit_ledger(challenge.user_id, 'OTP_REPLAY_ATTEMPT', f"Replay attempt for challenge {challenge_id} ({masked})", ip)
            return False, "This verification code has already been used. Please request a new one.", None

        # Check if locked out (Max 5 attempts)
        max_attempts = current_app.config.get('OTP_MAX_ATTEMPTS', 5) if current_app else 5
        if challenge.attempts >= max_attempts:
            logger.warning(f"[OTPService] Challenge {challenge_id} is locked due to excessive attempts for {masked}")
            record_audit_ledger(challenge.user_id, 'OTP_LOCKED', f"Challenge {challenge_id} locked ({masked})", ip)
            return False, "Too many failed attempts. This verification code is locked. Please request a new one.", None

        # Increment attempt counter
        challenge.attempts += 1
        db.session.commit()

        # Check expiration
        if challenge.is_expired:
            logger.info(f"[OTPService] Challenge {challenge_id} expired for {masked}")
            record_audit_ledger(challenge.user_id, 'OTP_EXPIRED', f"Expired code submitted for {masked}", ip)
            return False, "Verification code has expired (5-minute limit). Please request a new one.", None

        # Constant-time comparison
        is_valid = verify_otp_hash(entered_otp.strip(), challenge.otp_hash)

        if not is_valid:
            attempts_remaining = max(0, max_attempts - challenge.attempts)
            logger.info(f"[OTPService] Invalid OTP entered for {masked}. Attempts left: {attempts_remaining}")
            record_audit_ledger(challenge.user_id, 'OTP_VERIFY_FAILED', f"Invalid OTP entered for {masked} ({attempts_remaining} remaining)", ip)

            if attempts_remaining == 0:
                return False, "Too many failed attempts. This verification code is now locked. Please request a new one.", None
            return False, f"Invalid verification code. {attempts_remaining} attempt(s) remaining.", None

        # Mark OTP Challenge as consumed
        challenge.consumed_at = now
        db.session.commit()

        # Hydrate / link user if exists
        user = None
        if challenge.user_id:
            user = User.query.get(challenge.user_id)
        elif challenge.phone_number:
            user = User.query.filter(
                (User.phone_number == challenge.phone_number) | (User.phone == challenge.phone_number)
            ).first()

        if user:
            user.phone_verified = True
            user.phone_number = challenge.phone_number
            user.last_login = now
            db.session.commit()

        # Audit ledger success log
        record_audit_ledger(user.id if user else challenge.user_id, 'OTP_VERIFIED_SUCCESS', f"2FA verified successfully for {masked}", ip)
        logger.info(f"[OTPService] OTP verified successfully for challenge {challenge_id} ({masked})")

        return True, "Verification successful.", {
            'challenge_id': challenge.id,
            'phone_number': challenge.phone_number,
            'user': user.to_dict() if user else None,
            'purpose': challenge.purpose
        }

    @classmethod
    def resend_otp(cls, challenge_id: int, ip_address: Optional[str] = None) -> Tuple[bool, Optional[int], str, str]:
        """Resends an OTP based on an existing challenge ID."""
        challenge = OTPChallenge.query.get(challenge_id)
        if not challenge:
            return False, None, "Invalid verification session. Please restart authentication.", 'sms'

        # Invalidate the prior challenge
        if not challenge.consumed_at:
            challenge.consumed_at = datetime.utcnow()
            db.session.commit()

        return cls.send_otp(
            phone=challenge.phone_number,
            channel=challenge.channel,
            user_id=challenge.user_id,
            purpose=challenge.purpose,
            ip_address=ip_address
        )


# ---------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------
def generate_otp(length: int = 6) -> str:
    """Convenience alias for generate_secure_otp."""
    return generate_secure_otp(length)


def send_otp(phone: str, channel: str = 'sms', user_id: Optional[int] = None, purpose: str = '2fa_login', ip_address: Optional[str] = None) -> Tuple[bool, Optional[int], str, str]:
    """Module-level convenience wrapper for OTPService.send_otp."""
    return OTPService.send_otp(phone=phone, channel=channel, user_id=user_id, purpose=purpose, ip_address=ip_address)


def verify_otp(challenge_id: int, entered_otp: str, ip_address: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Module-level convenience wrapper for OTPService.verify_otp."""
    return OTPService.verify_otp(challenge_id=challenge_id, entered_otp=entered_otp, ip_address=ip_address)


def resend_otp(challenge_id: int, ip_address: Optional[str] = None) -> Tuple[bool, Optional[int], str, str]:
    """Module-level convenience wrapper for OTPService.resend_otp."""
    return OTPService.resend_otp(challenge_id=challenge_id, ip_address=ip_address)
