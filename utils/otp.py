import os
import random
from datetime import datetime, timedelta, timezone
from flask import current_app, render_template_string
from flask_mail import Message
from extensions import mail
from database import db
from database.models import OTPVerification

OTP_EMAIL_TEMPLATE = """Dear Citizen,

Your verification code for ZeroGuard AI ({{ purpose | capitalize }}) is:

============================================================
                     {{ otp_code }}
============================================================

This code is valid for 5 minutes. Do NOT share this code with anyone.

If you did not initiate this request, please ignore this email.

Stay Safe,
ZeroGuard AI Incident Assistance Team
National Cybercrime Reporting Initiative
"""

def generate_otp() -> str:
    """Generates a random 6-digit numeric OTP code string."""
    return f"{random.randint(0, 999999):06d}"

def send_otp_email(recipient_email: str, otp_code: str, purpose: str = 'registration') -> bool:
    """Dispatches real SMTP email containing the 6-digit OTP code."""
    if not recipient_email:
        return False

    try:
        body = render_template_string(
            OTP_EMAIL_TEMPLATE,
            otp_code=otp_code,
            purpose=purpose
        )

        msg = Message(
            subject=f"[ZeroGuard AI] Verification Code: {otp_code}",
            recipients=[recipient_email],
            body=body
        )

        suppress_send = current_app.config.get('MAIL_SUPPRESS_SEND', True)
        mail_user = current_app.config.get('MAIL_USERNAME', '')

        if not suppress_send and mail_user:
            try:
                print(f"[SMTP SENDING] Attempting real SMTP email dispatch to {recipient_email} via {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')}...")
                mail.send(msg)
                print(f"[SMTP SUCCESS] Dispatched real SMTP OTP email to {recipient_email}")
                current_app.logger.info(f"Dispatched real SMTP OTP email to {recipient_email}")
            except Exception as smtp_err:
                import traceback
                print("\n" + "!"*70)
                print(f"[SMTP FAILURE EXCEPTION] Failed to send email to {recipient_email}: {smtp_err}")
                traceback.print_exc()
                print("!"*70 + "\n")
                raise smtp_err
        else:
            # Console logger fallback if SMTP credentials not yet provided in .env
            print("\n" + "="*70)
            print(f"[OTP EMAIL DISPATCH (SIMULATED CONSOLE - MAIL_USERNAME IS EMPTY OR MAIL_SUPPRESS_SEND IS TRUE)]")
            print(f"RECIPIENT: {recipient_email}")
            print(f"SUBJECT: {msg.subject}")
            print(body)
            print("="*70 + "\n")

        return True
    except Exception as e:
        import traceback
        print(f"[SEND_OTP_EMAIL ERROR] {e}")
        traceback.print_exc()
        current_app.logger.error(f"Error sending OTP email: {e}")
        return False

def create_and_send_otp(email: str, purpose: str = 'registration'):
    """
    Generates a 6-digit OTP, stores its hash in database with 5-min expiration,
    enforces 60-second rate limiting, and dispatches the OTP via email.
    
    Returns: (success: bool, message: str)
    """
    email = email.lower().strip()
    now = datetime.utcnow()
    
    # 1. Enforce 60-second rate limit
    recent_otp = OTPVerification.query.filter(
        OTPVerification.email == email,
        OTPVerification.purpose == purpose,
        OTPVerification.created_at > now - timedelta(seconds=60)
    ).order_by(OTPVerification.created_at.desc()).first()

    if recent_otp:
        time_left = 60 - int((now - recent_otp.created_at).total_seconds())
        return False, f"Please wait {max(1, time_left)} seconds before requesting a new verification code."

    # 2. Generate new OTP and store hash
    otp_code = generate_otp()
    expires_at = now + timedelta(minutes=5)

    otp_record = OTPVerification(
        email=email,
        purpose=purpose,
        expires_at=expires_at,
        is_used=False,
        created_at=now
    )
    otp_record.set_otp(otp_code)

    try:
        db.session.add(otp_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to save OTP record: {e}")
        return False, "Database error while generating verification code."

    # 3. Send real email with OTP code
    email_sent = send_otp_email(email, otp_code, purpose)
    if not email_sent:
        return False, "Failed to send verification email. Please check server mail settings."

    return True, f"A 6-digit verification code has been sent to {email}."
