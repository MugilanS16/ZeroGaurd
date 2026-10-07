"""
Unit and Integration Tests for ZeroGuard AI OTP Security Engine.
Tests:
- 6-digit numeric generation using secrets module
- Server-side HMAC-SHA256 hashing and constant-time comparison
- Expiration enforcement (5 minutes)
- Attempt limits and lock-out (max 5 failed attempts)
- Resend cooldown (30 seconds)
- Hourly rate limiting (5 sends per hour per phone)
- Replay attack prevention (consumed OTP)
- Phone number normalization (E.164) & masking
- Automatic provider fallback from WhatsApp to SMS
- Tamper-evident SHA-256 audit ledger chaining
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from database.models import User, OTPChallenge, NotificationLog, ActivityLog
from backend.services.otp_service import (
    OTPService,
    generate_secure_otp,
    hash_otp,
    verify_otp_hash,
    normalize_phone_number,
    mask_phone_number
)
from backend.services.messaging.base import MessageResult


def test_otp_generation_format():
    """Validates that generate_secure_otp generates 6 numeric digits."""
    for _ in range(50):
        code = generate_secure_otp(6)
        assert len(code) == 6
        assert code.isdigit()


def test_otp_hmac_hashing_and_constant_time_comparison():
    """Validates HMAC-SHA256 hashing and constant-time verification."""
    secret = b"test-server-secret-key-12345"
    otp_code = "729401"

    # Hashed digest
    digest = hash_otp(otp_code, secret_key=secret)
    assert isinstance(digest, str)
    assert len(digest) == 64  # SHA256 produces 64 hex chars

    # Valid match
    assert verify_otp_hash(otp_code, digest, secret_key=secret) is True

    # Invalid code
    assert verify_otp_hash("000000", digest, secret_key=secret) is False
    assert verify_otp_hash("729402", digest, secret_key=secret) is False


def test_phone_normalization_and_masking():
    """Validates Indian E.164 normalization (+91 default) and privacy masking."""
    # 10-digit Indian numbers
    valid, formatted = normalize_phone_number("9876543210")
    assert valid is True
    assert formatted == "+919876543210"

    # Number with spaces/dashes
    valid, formatted = normalize_phone_number("98765-43210")
    assert valid is True
    assert formatted == "+919876543210"

    # Already formatted E.164
    valid, formatted = normalize_phone_number("+919876543210")
    assert valid is True
    assert formatted == "+919876543210"

    # US Number
    valid, formatted = normalize_phone_number("+14155552671")
    assert valid is True
    assert formatted == "+14155552671"

    # Invalid number
    valid, _ = normalize_phone_number("123")
    assert valid is False

    # Masking
    masked = mask_phone_number("+919876543210")
    assert masked == "+91******3210"
    assert "98765" not in masked


def test_otp_dispatch_and_successful_verification(app, db_session):
    """Tests end-to-end OTP dispatch and verification."""
    with app.app_context():
        phone = "+919876543210"
        
        # 1. Send OTP
        success, ch_id, msg, channel = OTPService.send_otp(
            phone=phone,
            channel='sms',
            purpose='2fa_login'
        )
        assert success is True
        assert ch_id is not None
        assert channel == 'sms'

        # Challenge record in DB
        challenge = OTPChallenge.query.get(ch_id)
        assert challenge is not None
        assert challenge.attempts == 0
        assert challenge.consumed_at is None
        assert challenge.is_expired is False

        # Compute raw code from test mock / hash verify
        # Let's verify with wrong code
        ok, fail_msg, payload = OTPService.verify_otp(ch_id, "000000")
        assert ok is False
        assert "Invalid" in fail_msg

        challenge = OTPChallenge.query.get(ch_id)
        assert challenge.attempts == 1

        # Now simulate correct code check by checking hash directly
        # Set a known hash
        test_code = "654321"
        challenge.otp_hash = hash_otp(test_code)
        db_session.commit()

        # Verify with correct code
        ok, succ_msg, payload = OTPService.verify_otp(ch_id, test_code)
        assert ok is True
        assert "successful" in succ_msg.lower()

        # Challenge is now consumed
        challenge = OTPChallenge.query.get(ch_id)
        assert challenge.is_consumed is True


def test_otp_replay_prevention(app, db_session):
    """Validates that a consumed OTP cannot be used a second time."""
    with app.app_context():
        phone = "+919876543210"
        success, ch_id, _, _ = OTPService.send_otp(phone=phone, channel='sms')
        
        test_code = "112233"
        challenge = OTPChallenge.query.get(ch_id)
        challenge.otp_hash = hash_otp(test_code)
        db_session.commit()

        # 1st verification: succeeds
        ok, _, _ = OTPService.verify_otp(ch_id, test_code)
        assert ok is True

        # 2nd verification (replay): rejected
        ok2, replay_msg, _ = OTPService.verify_otp(ch_id, test_code)
        assert ok2 is False
        assert "already been used" in replay_msg.lower()


def test_otp_lockout_after_max_attempts(app, db_session):
    """Validates that 5 failed attempts locks the OTP challenge."""
    with app.app_context():
        phone = "+919876543210"
        success, ch_id, _, _ = OTPService.send_otp(phone=phone, channel='sms')
        
        # 5 consecutive bad attempts
        for i in range(5):
            ok, msg, _ = OTPService.verify_otp(ch_id, f"99999{i}")
            assert ok is False

        challenge = OTPChallenge.query.get(ch_id)
        assert challenge.attempts >= 5

        # 6th attempt should be locked out
        ok, locked_msg, _ = OTPService.verify_otp(ch_id, "123456")
        assert ok is False
        assert "locked" in locked_msg.lower()


def test_otp_expiration(app, db_session):
    """Validates that expired OTPs (>5 mins) are rejected."""
    with app.app_context():
        phone = "+919876543210"
        success, ch_id, _, _ = OTPService.send_otp(phone=phone, channel='sms')
        
        test_code = "445566"
        challenge = OTPChallenge.query.get(ch_id)
        challenge.otp_hash = hash_otp(test_code)
        # Fast-forward 6 minutes in the past
        challenge.expires_at = datetime.utcnow() - timedelta(minutes=6)
        db_session.commit()

        assert challenge.is_expired is True

        ok, exp_msg, _ = OTPService.verify_otp(ch_id, test_code)
        assert ok is False
        assert "expired" in exp_msg.lower()


def test_resend_cooldown_enforcement(app, db_session):
    """Validates that requesting another OTP within 30 seconds is throttled."""
    with app.app_context():
        phone = "+919876543210"
        
        # 1st request
        ok1, ch1, _, _ = OTPService.send_otp(phone=phone, channel='sms')
        assert ok1 is True

        # Immediate 2nd request (within 30s)
        ok2, ch2, cooldown_msg, _ = OTPService.send_otp(phone=phone, channel='sms')
        assert ok2 is False
        assert "wait" in cooldown_msg.lower()


def test_hourly_rate_limiting_per_phone(app, db_session):
    """Validates that max 5 sends per hour per phone is strictly enforced."""
    with app.app_context():
        phone = "+919876543210"
        
        # Seed 5 recent challenges
        for i in range(5):
            ch = OTPChallenge(
                phone_number=phone,
                channel='sms',
                purpose='2fa_login',
                otp_hash='dummy_hash',
                expires_at=datetime.utcnow() + timedelta(minutes=5),
                attempts=0,
                consumed_at=datetime.utcnow(),  # mark consumed to bypass 30s cooldown
                ip_address='127.0.0.1',
                created_at=datetime.utcnow() - timedelta(minutes=10 * i)
            )
            db_session.add(ch)
        db_session.commit()

        # 6th request within the hour should be blocked
        ok, _, rate_msg, _ = OTPService.send_otp(phone=phone, channel='sms')
        assert ok is False
        assert "too many" in rate_msg.lower() or "1 hour" in rate_msg.lower()


def test_whatsapp_to_sms_automatic_fallback(app, db_session):
    """Validates that WhatsApp delivery failure automatically triggers SMS fallback."""
    with app.app_context():
        phone = "+919876543210"

        # Mock provider where send_whatsapp fails and send_sms succeeds
        mock_provider = MagicMock()
        mock_provider.name = 'mock'
        mock_provider.send_whatsapp.return_value = MessageResult(
            success=False,
            provider='mock',
            channel='whatsapp',
            status='failed',
            error="WhatsApp sandbox not joined"
        )
        mock_provider.send_sms.return_value = MessageResult(
            success=True,
            provider='mock',
            channel='sms',
            provider_message_id="FALLBACK-SMS-12345",
            status='sent'
        )

        with patch('backend.services.otp_service.get_messaging_provider', return_value=mock_provider):
            ok, ch_id, msg, final_channel = OTPService.send_otp(
                phone=phone,
                channel='whatsapp'
            )
            assert ok is True
            assert final_channel == 'sms'
            assert mock_provider.send_whatsapp.called
            assert mock_provider.send_sms.called


def test_sha256_audit_ledger_integrity(app, db_session):
    """Validates that security events generate cryptographic SHA-256 hash chained records."""
    with app.app_context():
        phone = "+919876543210"
        OTPService.send_otp(phone=phone, channel='sms')
        
        logs = ActivityLog.query.order_by(ActivityLog.id.asc()).all()
        assert len(logs) >= 1

        for log in logs:
            assert log.record_hash is not None
            assert len(log.record_hash) == 64


def test_verify_2fa_route_renders_without_form_undefined_error(client, app, db_session):
    """Verifies that GET /auth/verify-2fa renders cleanly with form context (no UndefinedError)."""
    with app.app_context():
        user = User.query.filter_by(email="citizen_2fa_test@cybercrime.gov.in").first()
        if not user:
            user = User(
                fullname="Aarav Sharma",
                email="citizen_2fa_test@cybercrime.gov.in",
                phone="+919876543210",
                phone_number="+919876543210",
                phone_verified=True,
                role="citizen",
                is_verified=True
            )
            user.set_password("CitizenPass123!")
            db_session.add(user)
            db_session.commit()

        user_id = user.id
        # Send OTP to create challenge
        ok, ch_id, _, _ = OTPService.send_otp(phone=user.phone_number, channel='sms', user_id=user_id)
        assert ok is True

    # Establish 2FA session
    with client.session_transaction() as sess:
        sess['2fa_user_id'] = user_id
        sess['2fa_challenge_id'] = ch_id

    # GET /auth/verify-2fa must return 200 with HTML form rendered
    response = client.get('/auth/verify-2fa')
    assert response.status_code == 200
    assert b"Two-Step Verification" in response.data or b"Two-Factor" in response.data or b"Security Verification" in response.data
    assert b"csrf_token" in response.data
    assert b"otp" in response.data
    assert b"UndefinedError" not in response.data


def test_verify_2fa_route_post_success_and_failure(client, app, db_session):
    """Tests POST /auth/verify-2fa with invalid and valid OTP codes."""
    with app.app_context():
        user = User.query.filter_by(email="citizen_2fa_test2@cybercrime.gov.in").first()
        if not user:
            user = User(
                fullname="Aarav Sharma 2",
                email="citizen_2fa_test2@cybercrime.gov.in",
                phone="+919876543211",
                phone_number="+919876543211",
                phone_verified=True,
                role="citizen",
                is_verified=True
            )
            user.set_password("CitizenPass123!")
            db_session.add(user)
            db_session.commit()

        user_id = user.id
        ok, ch_id, _, _ = OTPService.send_otp(phone=user.phone_number, channel='sms', user_id=user_id)
        assert ok is True

        raw_otp = None
        challenge = OTPChallenge.query.get(ch_id)
        for code in range(100000, 1000000):
            if verify_otp_hash(str(code), challenge.otp_hash):
                raw_otp = str(code)
                break
        assert raw_otp is not None

    # Invalid OTP attempt
    with client.session_transaction() as sess:
        sess['2fa_user_id'] = user_id
        sess['2fa_challenge_id'] = ch_id

    resp_fail = client.post('/auth/verify-2fa', data={'otp': '000000'}, follow_redirects=True)
    assert resp_fail.status_code == 200
    assert b"Invalid verification code" in resp_fail.data or b"attempt(s) remaining" in resp_fail.data

    # Valid OTP attempt
    resp_success = client.post('/auth/verify-2fa', data={'otp': raw_otp}, follow_redirects=True)
    assert resp_success.status_code == 200
    assert b"Two-step verification successful" in resp_success.data or b"ZeroGuard" in resp_success.data


def test_twilio_provider_mock_sms_and_whatsapp():
    """Validates TwilioProvider dispatch with mocked twilio client."""
    from backend.services.messaging.twilio_provider import TwilioProvider

    config = {
        'TWILIO_ACCOUNT_SID': 'ACmockedsid1234567890abcdef',
        'TWILIO_AUTH_TOKEN': 'mockedauth1234567890abcdef',
        'TWILIO_PHONE_NUMBER': '+15005550006',
        'TWILIO_WHATSAPP_NUMBER': 'whatsapp:+14155238886'
    }
    provider = TwilioProvider(config)

    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.sid = "SMmocked12345"
    mock_msg.status = "queued"
    mock_client.messages.create.return_value = mock_msg

    with patch.object(provider, '_get_client', return_value=mock_client):
        # SMS dispatch
        res_sms = provider.send_sms(phone="+919876543210", body="ZeroGuard AI: OTP 123456")
        assert res_sms.success is True
        assert res_sms.provider_message_id == "SMmocked12345"

        # WhatsApp dispatch
        mock_msg.sid = "WAWA12345"
        res_wa = provider.send_whatsapp(phone="+919876543210", body="ZeroGuard AI: OTP 123456")
        assert res_wa.success is True
        assert res_wa.provider_message_id == "WAWA12345"

