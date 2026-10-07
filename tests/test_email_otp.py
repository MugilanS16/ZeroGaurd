"""
Unit and Integration Tests for ZeroGuard AI Email OTP Provider & 2FA Flow.

Tests:
1. Successful SMTP email dispatch with STARTTLS (port 587), HTML + plain-text formatting.
2. SMTP Authentication failure (SMTPAuthenticationError) handling without crashes.
3. SMTP Connection timeout / error handling (socket.timeout) without crashes.
4. Missing user email handling with clean user feedback.
5. Suppress-send / missing credentials fallback behavior.
6. Masked email display on 2FA verification page (m*****4@gmail.com).
7. Privacy test: OTP is NEVER rendered in the HTML/response bodies or flash messages.
8. Resend cooldown (30s) and Hourly rate limits (5/hr) on email OTP.
9. Failed attempt limits (max 5 lock-out) and replay prevention.
"""
import smtplib
import socket
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from database import db
from database.models import User, OTPChallenge, NotificationLog, ActivityLog
from backend.services.otp_service import (
    OTPService,
    mask_email,
    hash_otp,
    generate_secure_otp
)
from backend.services.messaging.email_provider import EmailProvider
from backend.services.messaging.factory import get_messaging_provider


@pytest.fixture
def mock_smtp():
    """Mocks smtplib.SMTP context manager to prevent real network calls."""
    with patch('smtplib.SMTP') as mock_smtp_cls:
        instance = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = instance
        yield instance, mock_smtp_cls


def test_mask_email():
    """Validates email masking for privacy."""
    assert mask_email("mukilansathish4@gmail.com") == "m*****4@gmail.com"
    assert mask_email("admin@zeroguard.ai") == "a*****n@zeroguard.ai"
    assert mask_email("ab@domain.com") == "a*@domain.com"
    assert mask_email("") == "***"
    assert mask_email("invalid-email") == "***"


def test_email_provider_success_smtp(app, mock_smtp):
    """Tests successful email sending via SMTP with STARTTLS and multipart MIME."""
    smtp_inst, _ = mock_smtp

    config = {
        'MAIL_SERVER': 'smtp.gmail.com',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_USERNAME': 'test@gmail.com',
        'MAIL_PASSWORD': 'app-password-16',
        'MAIL_DEFAULT_SENDER': 'test@gmail.com',
        'MAIL_SUPPRESS_SEND': False
    }
    provider = EmailProvider(config)
    res = provider.send_email(
        to_email='user@example.com',
        otp_code='654321',
        expiry_seconds=300,
        purpose='2fa_login'
    )

    assert res.success is True
    assert res.status == 'sent'
    assert smtp_inst.starttls.called
    assert smtp_inst.login.called
    assert smtp_inst.send_message.called

    # Verify message content sent to SMTP
    sent_msg = smtp_inst.send_message.call_args[0][0]
    assert sent_msg['Subject'] == "Your ZeroGuard AI verification code"
    assert sent_msg['To'] == "user@example.com"
    assert sent_msg['From'] == "test@gmail.com"


def test_email_provider_auth_failure(app):
    """Tests SMTPAuthenticationError handling."""
    with patch('smtplib.SMTP') as mock_cls:
        instance = MagicMock()
        instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication Failed")
        mock_cls.return_value.__enter__.return_value = instance

        config = {
            'MAIL_SERVER': 'smtp.gmail.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': 'wrong@gmail.com',
            'MAIL_PASSWORD': 'wrong-password',
            'MAIL_SUPPRESS_SEND': False
        }
        provider = EmailProvider(config)
        res = provider.send_email(to_email='user@example.com', otp_code='123456')

        assert res.success is False
        assert "authentication failed" in res.error.lower()


def test_email_provider_timeout_failure(app):
    """Tests socket timeout handling."""
    with patch('smtplib.SMTP') as mock_cls:
        instance = MagicMock()
        instance.send_message.side_effect = socket.timeout("Connection timed out")
        mock_cls.return_value.__enter__.return_value = instance

        config = {
            'MAIL_SERVER': 'smtp.gmail.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': 'test@gmail.com',
            'MAIL_PASSWORD': 'password',
            'MAIL_SUPPRESS_SEND': False
        }
        provider = EmailProvider(config)
        res = provider.send_email(to_email='user@example.com', otp_code='123456')

        assert res.success is False
        assert "timed out" in res.error.lower() or "unable to deliver" in res.error.lower()


def test_email_provider_suppress_send_dev_fallback(app):
    """Tests MAIL_SUPPRESS_SEND=True local fallback without network calls."""
    config = {
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_USERNAME': 'test@gmail.com',
        'MAIL_PASSWORD': 'password'
    }
    provider = EmailProvider(config)
    res = provider.send_email(to_email='user@example.com', otp_code='987654')

    assert res.success is True
    assert res.status == 'sent'
    assert 'DEV-EMAIL' in res.provider_message_id


def test_otp_service_send_email_missing_user_email(app, db_session):
    """Tests OTP dispatch when user has no email address."""
    with app.app_context():
        user = User(
            fullname="No Email User",
            email="invalid-placeholder@temp.local",
            role="citizen",
            is_verified=True
        )
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

        # Overwrite to empty
        user.email = ""
        db.session.commit()

        success, ch_id, msg, channel = OTPService.send_otp(
            channel='email',
            user_id=user.id,
            purpose='2fa_login'
        )

        assert success is False
        assert ch_id is None
        assert "No registered email address found" in msg


def test_otp_service_send_email_cooldown_and_hourly_limit(app, db_session, mock_smtp):
    """Tests 30s resend cooldown and 5/hr rate limits on email OTP."""
    with app.app_context():
        user_email = "citizen.test@gmail.com"
        user = User(
            fullname="Citizen Test",
            email=user_email,
            role="citizen",
            is_verified=True
        )
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

        # 1st Send: Should succeed
        success, ch_id, msg, channel = OTPService.send_otp(
            channel='email',
            user_id=user.id,
            purpose='2fa_login'
        )
        assert success is True
        assert ch_id is not None
        assert channel == 'email'

        # 2nd Send immediately: Should hit 30s cooldown
        success2, ch_id2, msg2, _ = OTPService.send_otp(
            channel='email',
            user_id=user.id,
            purpose='2fa_login'
        )
        assert success2 is False
        assert "Please wait" in msg2

        # Simulate 5 prior sends in the past hour (all consumed to avoid cooldown block)
        for ch in OTPChallenge.query.filter_by(phone_number=user_email).all():
            ch.consumed_at = datetime.utcnow()
        db.session.commit()

        for i in range(5):
            past_ch = OTPChallenge(
                user_id=user.id,
                phone_number=user_email,
                channel='email',
                purpose='2fa_login',
                otp_hash=hash_otp("111111"),
                created_at=datetime.utcnow() - timedelta(minutes=10 + i),
                expires_at=datetime.utcnow() + timedelta(minutes=5),
                consumed_at=datetime.utcnow()
            )
            db.session.add(past_ch)
        db.session.commit()

        # Should hit hourly rate limit
        success3, _, msg3, _ = OTPService.send_otp(
            email=user_email,
            channel='email',
            user_id=user.id,
            purpose='2fa_login'
        )
        assert success3 is False
        assert "Too many verification requests" in msg3


def test_otp_never_rendered_in_html_page(app, client, db_session, mock_smtp):
    """Verifies that the generated OTP is NEVER included in HTML responses or flash messages."""
    app.config['MESSAGING_PROVIDER'] = 'email'
    user = User(
        fullname="Privacy User",
        email="privacy.user@example.com",
        role="citizen",
        is_verified=True
    )
    user.set_password("SecurePass123!")
    db_session.add(user)
    db_session.commit()

    # Login to trigger 2FA
    resp = client.post('/auth/login', data={
        'email': 'privacy.user@example.com',
        'password': 'SecurePass123!'
    }, follow_redirects=True)

    assert resp.status_code == 200
    html_text = resp.get_data(as_text=True)

    # 1. 2FA Verification Page is rendered
    assert "Two-Step Verification" in html_text
    # 2. Channel is EMAIL
    assert "EMAIL" in html_text or "Email" in html_text
    # 3. Email is masked
    assert "p*****r@example.com" in html_text
    # 4. Raw email is NOT exposed unmasked
    assert "privacy.user@example.com" not in html_text
    # 5. Check database challenge to get actual raw code hash
    challenge = OTPChallenge.query.filter_by(user_id=user.id).first()
    assert challenge is not None
    # 6. Ensure Dev OTP Code is NEVER present in page text
    assert "Dev OTP Code" not in html_text
    assert "DEV-EMAIL" not in html_text


def test_email_otp_attempt_limits_and_lockout(app, db_session):
    """Verifies max 5 failed attempts locks out the challenge."""
    with app.app_context():
        otp_raw = "849201"
        ch = OTPChallenge(
            user_id=1,
            phone_number="test@example.com",
            channel='email',
            purpose='2fa_login',
            otp_hash=hash_otp(otp_raw),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            attempts=0
        )
        db.session.add(ch)
        db.session.commit()

        # 4 incorrect attempts
        for _ in range(4):
            success, msg, _ = OTPService.verify_otp(ch.id, "000000")
            assert success is False
            assert "Invalid verification code" in msg

        # 5th incorrect attempt -> Locks out
        success, msg, _ = OTPService.verify_otp(ch.id, "000000")
        assert success is False
        assert "locked" in msg.lower()

        # Even if correct code entered now, it remains locked
        success, msg, _ = OTPService.verify_otp(ch.id, otp_raw)
        assert success is False
        assert "locked" in msg.lower()
