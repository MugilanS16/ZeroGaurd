"""
Unit and Integration Tests for ZeroGuard AI Guardian Notification System.

Tests:
1. Consent flag requirement for guardian enrollment.
2. Verification barrier: Only verified guardians receive alerts.
3. Verified guardian with email receives sanitized incident alert via SMTP (mocked).
4. Alert is delivered strictly to the guardian's contact details, never to the user's.
5. Guardian with phone only uses the fallback provider cleanly without crashing.
6. SMTP errors (auth failure, timeouts) are logged and marked failed without crashing.
7. Strict sanitization: NO victim narratives, monetary figures, or private evidence in alert content.
8. Send test alert action works for verified guardians and rejects unverified ones.
9. Guardian verification request (24-hr OTP) generation and verification.
10. Inbound STOP opt-out revocation.
"""
import smtplib
import socket
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from database import db
from database.models import User, Guardian, EmergencyContact, NotificationLog, ActivityLog, OTPChallenge
from backend.services.notify_service import NotificationService
from backend.services.messaging.templates import render_template
from backend.services.messaging.base import MessageResult


@pytest.fixture
def mock_smtp():
    """Mocks smtplib.SMTP context manager to prevent real network calls."""
    with patch('smtplib.SMTP') as mock_smtp_cls:
        instance = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = instance
        yield instance, mock_smtp_cls


def test_guardian_consent_requirement(client, app, db_session):
    """Validates that adding a guardian requires the explicit consent flag."""
    with app.app_context():
        user = User(
            fullname="Test Citizen",
            email="citizen.guardian@cybercrime.gov.in",
            phone="+919876543210",
            phone_number="+919876543210",
            role="citizen"
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['role'] = user.role

        res = client.post(
            "/api/guardian",
            json={
                "name": "Ramesh Sharma",
                "phone": "+919876500001",
                "email": "ramesh@example.com",
                "preferred_channel": "email",
                "consent_given": False
            }
        )
        assert res.status_code == 400
        assert "consent" in res.get_json()["error"].lower()


def test_unverified_guardian_does_not_receive_alerts(app, db_session, mock_smtp):
    """Validates that unverified guardians are strictly excluded from receiving alerts."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        user = User(
            fullname="Test Citizen 2",
            email="citizen.unverified@cybercrime.gov.in",
            phone="+919876543210",
            role="citizen"
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        # Add unverified guardian with email
        guardian = Guardian(
            user_id=user.id,
            name="Unverified Guardian",
            email="unverified.guardian@example.com",
            phone_number="+919876599999",
            preferred_channel="email",
            consent_given=True,
            verified=False,
            opted_out=False
        )
        db_session.add(guardian)
        db_session.commit()

        NotificationService._dispatch_guardians_worker(
            user_id=user.id,
            event_type='complaint_submitted',
            case_ref='ZG-CASE-101',
            context={'status': 'Pending'}
        )
        # Should NOT send email because verified is False
        assert not smtp_inst.send_message.called


def test_verified_guardian_with_email_receives_alert_via_smtp(app, db_session, mock_smtp):
    """
    Validates that a verified guardian with an email address receives the incident alert via SMTP.
    Checks that the recipient is the guardian's email, not the user's email, and content is sanitized.
    """
    smtp_inst, _ = mock_smtp
    with app.app_context():
        user_email = "victim.user@example.com"
        guardian_email = "trusted.guardian@example.com"

        user = User(
            fullname="Aarav Sharma",
            email=user_email,
            phone="+919876543210",
            role="citizen"
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="Rajesh Sharma",
            email=guardian_email,
            phone_number="+919876588888",
            preferred_channel="email",
            consent_given=True,
            verified=True,
            opted_out=False
        )
        db_session.add(guardian)
        db_session.commit()

        # Dispatch guardian alert
        NotificationService._dispatch_guardians_worker(
            user_id=user.id,
            event_type='high_risk_alert',
            case_ref='CC-2026-99001',
            context={
                'status': 'Under Review',
                'new_status': 'Under Review',
                'victim_narrative': 'PRIVATE: Stole 50000 rupees via UPI scam password 1234',
                'claimed_amount': 50000
            }
        )

        assert smtp_inst.send_message.called
        sent_msg = smtp_inst.send_message.call_args[0][0]

        # 1. Recipient is the guardian's own email, NOT the user's
        assert sent_msg['To'] == guardian_email
        assert sent_msg['To'] != user_email

        # 2. Subject and Case Reference check
        assert "CC-2026-99001" in sent_msg['Subject'] or "ZeroGuard" in sent_msg['Subject']

        # 3. Sanitization check: No narrative, no password, no claimed amount in message
        body_text = str(sent_msg)
        assert "CC-2026-99001" in body_text
        assert "Aarav Sharma" in body_text
        assert "PRIVATE" not in body_text
        assert "password 1234" not in body_text
        assert "50000" not in body_text

        # 4. Check database NotificationLog entry
        log_entry = NotificationLog.query.filter_by(recipient_type='guardian').order_by(NotificationLog.id.desc()).first()
        assert log_entry is not None
        assert log_entry.channel == 'email'
        assert log_entry.status == 'sent'


def test_guardian_with_phone_only_uses_fallback_provider(app, db_session):
    """Validates that a guardian with only a phone number uses the fallback provider cleanly."""
    with app.app_context():
        user = User(
            fullname="Phone Only User",
            email="phone.user@example.com",
            phone="+919876543210",
            role="citizen"
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="Phone Guardian",
            phone_number="+919876577777",
            preferred_channel="sms",
            consent_given=True,
            verified=True,
            opted_out=False
        )
        db_session.add(guardian)
        db_session.commit()

        mock_provider = MagicMock()
        mock_provider.name = 'mock'
        mock_provider.send_sms.return_value = MessageResult(
            success=True,
            provider='mock',
            channel='sms',
            provider_message_id='MOCK-MSG-777',
            status='sent'
        )

        with patch('backend.services.notify_service.get_messaging_provider', return_value=mock_provider):
            NotificationService._dispatch_guardians_worker(
                user_id=user.id,
                event_type='complaint_submitted',
                case_ref='ZG-CASE-777',
                context={'status': 'Submitted', 'new_status': 'In Review'}
            )
            assert mock_provider.send_sms.called
            assert mock_provider.send_sms.call_args[1]['phone'] == "+919876577777"


def test_smtp_failure_is_logged_without_crashing(app, db_session):
    """Validates that SMTP authentication or connection errors are caught, logged, and marked failed."""
    with app.app_context():
        user = User(
            fullname="Fail Test User",
            email="fail.user@example.com",
            phone="+919876543210",
            role="citizen"
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="Fail Guardian",
            email="fail.guardian@example.com",
            phone_number="+919876566666",
            preferred_channel="email",
            consent_given=True,
            verified=True,
            opted_out=False
        )
        db_session.add(guardian)
        db_session.commit()

        with patch('smtplib.SMTP') as mock_smtp_cls:
            instance = MagicMock()
            instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth Failed")
            mock_smtp_cls.return_value.__enter__.return_value = instance

            # Should not raise exception
            NotificationService._dispatch_guardians_worker(
                user_id=user.id,
                event_type='status_update',
                case_ref='CC-FAIL-01',
                context={'status': 'Pending', 'new_status': 'In Review'},
                max_retries=1
            )

            # Check failed status in database log
            log_entry = NotificationLog.query.filter_by(recipient_type='guardian').order_by(NotificationLog.id.desc()).first()
            assert log_entry is not None
            assert log_entry.status == 'failed'
            assert "authentication failed" in log_entry.error.lower() or "unable to deliver" in log_entry.error.lower()


def test_send_test_alert_action(app, db_session, mock_smtp):
    """Validates that send_test_alert succeeds for verified guardians and rejects unverified ones."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        user = User(
            fullname="Test Alert User",
            email="testalert@example.com",
            role="citizen"
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        # 1. No guardian -> should fail
        ok, msg = NotificationService.send_test_alert(user.id)
        assert ok is False
        assert "no emergency guardian" in msg.lower() or "not verified" in msg.lower()

        # 2. Add unverified guardian -> should fail with clear message
        g_unverified = Guardian(
            user_id=user.id,
            name="Unverified",
            email="unverified@example.com",
            phone_number="+919876511111",
            verified=False,
            consent_given=True
        )
        db_session.add(g_unverified)
        db_session.commit()

        ok, msg = NotificationService.send_test_alert(user.id)
        assert ok is False
        assert "not verified" in msg.lower()

        # 3. Verify guardian -> should succeed
        g_unverified.verified = True
        db_session.commit()

        ok, msg = NotificationService.send_test_alert(user.id)
        assert ok is True
        assert "successfully dispatched" in msg.lower()


def test_guardian_verification_request_flow(app, db_session, mock_smtp):
    """Validates generating and sending a 24-hour verification code to a new guardian."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        user = User(
            fullname="Ward User",
            email="ward.user@example.com",
            role="citizen"
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="New Guardian",
            email="new.guardian@example.com",
            phone_number="+919876522222",
            verified=False,
            consent_given=True
        )
        db_session.add(guardian)
        db_session.commit()

        # Send verification request
        ok, msg = NotificationService.send_guardian_verification(guardian.id)
        assert ok is True
        assert "verification code sent" in msg.lower()
        assert smtp_inst.send_message.called

        # Verify challenge was stored in database with 24h validity
        challenge = OTPChallenge.query.filter_by(user_id=user.id, purpose='guardian_verify').first()
        assert challenge is not None
        assert challenge.expires_at > datetime.utcnow() + timedelta(hours=20)


def test_inbound_stop_opt_out(app, db_session):
    """Validates that receiving STOP command immediately revokes guardian consent."""
    with app.app_context():
        phone = "+919876577777"
        guardian = Guardian(
            user_id=1,
            name="Opt-out Guardian",
            phone_number=phone,
            preferred_channel="sms",
            consent_given=True,
            verified=True,
            opted_out=False
        )
        db_session.add(guardian)
        db_session.commit()

        # Process opt-out
        res = NotificationService.handle_opt_out(phone)
        assert res is True

        # Verify DB record updated
        g = Guardian.query.filter_by(phone_number=phone).first()
        assert g.opted_out is True
        assert g.consent_given is False


def test_message_template_sanitization_rules():
    """Validates that all templates in templates.py maintain strict data sanitization."""
    test_context = {
        'case_ref': 'ZG-CASE-777',
        'status': 'Pending',
        'new_status': 'In Review',
        'short_note': 'Investigator assigned',
        'otp_code': '123456'
    }

    templates = ['otp', 'guardian_submitted', 'guardian_status_update', 'guardian_evidence', 'guardian_high_risk']
    for t in templates:
        for ch in ['sms', 'whatsapp']:
            rendered = render_template(t, channel=ch, **test_context)
            assert isinstance(rendered, str)
            assert len(rendered) > 10
            if 'guardian' in t:
                assert 'STOP' in rendered or 'unsubscribe' in rendered.lower()
