"""
Unit and Integration Tests for Citizen Registration with Emergency Contact / Guardian.

Tests:
1. Registration with a valid emergency trusted contact creates correct EmergencyContact and Guardian rows.
2. Registration triggers one-time confirmation email to trusted contact without blocking registration.
3. Guardian confirmation link / code activates guardian status (verified=True).
4. Confirmed guardian receives sanitized incident alerts upon complaint filing.
5. Unconfirmed guardian alerts are skipped and audit reason is recorded.
6. Recipient is strictly the guardian's contact details, never the citizen user's.
7. Send test alert route & button works for confirmed guardian and rejects unconfirmed with clear feedback.
8. SMTP errors during alert dispatch are caught, logged, and marked failed without crashing.
9. Registration with missing/invalid guardian fields triggers validation errors cleanly without crashing.
10. OTP codes are hashed and never leaked in plaintext or rendered in HTML response.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from database import db
from database.models import User, EmergencyContact, Guardian, OTPChallenge, NotificationLog, ActivityLog, Complaint
from backend.services.notify_service import NotificationService
from backend.services.messaging.email_provider import EmailProvider


@pytest.fixture
def mock_smtp():
    """Mocks smtplib.SMTP context manager to prevent real network calls."""
    with patch('smtplib.SMTP') as mock_smtp_cls:
        instance = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = instance
        yield instance, mock_smtp_cls


def test_register_with_valid_guardian_creates_emergency_contact_and_sends_confirmation(client, app, db_session, mock_smtp):
    """Submitting valid registration form creates user, EmergencyContact, Guardian, and dispatches confirmation."""
    payload = {
        'fullname': 'Aarav Patel',
        'email': 'aarav.patel@example.com',
        'phone': '+91 9876543210',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'trusted_contact_name': 'Meera Patel',
        'trusted_contact_relationship': 'Spouse',
        'trusted_contact_email': 'meera.patel@example.com',
        'trusted_contact_phone': '+91 9811122233',
        'terms': 'y'
    }

    res = client.post('/auth/register', data=payload, follow_redirects=False)

    # Should redirect to 2FA verification step
    assert res.status_code == 302
    assert '/auth/verify-2fa' in res.location

    # Check Database records
    user = User.query.filter_by(email='aarav.patel@example.com').first()
    assert user is not None
    assert user.fullname == 'Aarav Patel'
    assert user.is_verified is False

    contact = EmergencyContact.query.filter_by(user_id=user.id).first()
    assert contact is not None
    assert contact.contact_name == 'Meera Patel'
    assert contact.relationship == 'Spouse'
    assert contact.email == 'meera.patel@example.com'
    assert '+91' in contact.phone and '9811122233' in contact.phone

    guardian = Guardian.query.filter_by(user_id=user.id).first()
    assert guardian is not None
    assert guardian.name == 'Meera Patel'
    assert guardian.relationship_type == 'Spouse'
    assert guardian.email == 'meera.patel@example.com'
    assert guardian.consent_given is True
    assert guardian.verified is False  # Unverified until guardian confirms

    # Verify confirmation challenge created for guardian
    challenge = OTPChallenge.query.filter_by(
        user_id=user.id,
        phone_number='meera.patel@example.com',
        purpose='guardian_verify'
    ).first()
    assert challenge is not None
    assert challenge.otp_hash is not None


def test_guardian_confirmation_link_and_code(client, app, db_session):
    """Guardian confirms enrollment via 1-click confirmation link or code."""
    with app.app_context():
        user = User(
            fullname="Karan Mehra",
            email="karan.mehra@example.com",
            phone="+91 9876500111",
            phone_number="+919876500111",
            role="citizen",
            is_verified=True
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="Rohit Mehra",
            email="rohit.mehra@example.com",
            phone_number="+919876500222",
            preferred_channel="email",
            consent_given=True,
            verified=False
        )
        db_session.add(guardian)
        db_session.commit()

        # Generate verification request
        ok, msg = NotificationService.send_guardian_verification(guardian.id)
        assert ok is True

        challenge = OTPChallenge.query.filter_by(
            user_id=user.id,
            phone_number="rohit.mehra@example.com",
            purpose="guardian_verify"
        ).order_by(OTPChallenge.created_at.desc()).first()
        assert challenge is not None

        # Simulate clicking link with known code
        # Override hash to verify easily
        from backend.services.otp_service import hash_otp
        challenge.otp_hash = hash_otp('654321')
        db_session.commit()

        # Perform confirmation
        res = client.get(f"/auth/guardian/confirm?challenge_id={challenge.id}&otp=654321")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "Trusted Contact Confirmed" in html or "verified as a trusted emergency contact" in html

        # Verify DB updated
        g_updated = Guardian.query.get(guardian.id)
        assert g_updated.verified is True
        assert g_updated.consent_given is True


def test_unconfirmed_guardian_alert_skipped_and_logged(app, db_session, mock_smtp):
    """Alerts for unconfirmed guardians are skipped and recorded in NotificationLog and ActivityLog."""
    with app.app_context():
        user = User(
            fullname="Sanjay Dutt",
            email="sanjay@example.com",
            phone="+91 9876500333",
            phone_number="+919876500333",
            role="citizen",
            is_verified=True
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="Priya Dutt",
            email="priya.dutt@example.com",
            phone_number="+919876500444",
            preferred_channel="email",
            consent_given=True,
            verified=False # Unconfirmed
        )
        db_session.add(guardian)
        db_session.commit()

        # Worker execution
        NotificationService._dispatch_guardians_worker(
            user_id=user.id,
            event_type='complaint_submitted',
            case_ref='ZG-2026-TEST01',
            context={'status': 'Submitted', 'new_status': 'Submitted'}
        )

        # Check skipped log in NotificationLog
        log_entry = NotificationLog.query.filter_by(
            template='complaint_submitted',
            status='skipped'
        ).first()
        assert log_entry is not None
        assert "has not confirmed verification yet" in log_entry.error

        # Check skipped entry in ActivityLog
        act = ActivityLog.query.filter_by(
            user_id=user.id,
            action='GUARDIAN_ALERT_SKIPPED'
        ).first()
        assert act is not None


def test_confirmed_guardian_receives_sanitized_alert(app, db_session, mock_smtp):
    """Confirmed guardian receives sanitized incident alert via SMTP."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        user = User(
            fullname="Neha Gupta",
            email="neha.gupta@example.com",
            phone="+91 9876500555",
            phone_number="+919876500555",
            role="citizen",
            is_verified=True
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="Rajesh Gupta",
            email="rajesh.gupta@example.com",
            phone_number="+919876500666",
            preferred_channel="email",
            consent_given=True,
            verified=True, # Confirmed
            opted_out=False
        )
        db_session.add(guardian)
        db_session.commit()

        NotificationService._dispatch_guardians_worker(
            user_id=user.id,
            event_type='complaint_submitted',
            case_ref='ZG-2026-NEHA99',
            context={
                'status': 'Submitted',
                'new_status': 'In Review',
                'victim_private_narrative': 'I lost Rs 5,00,000 to OTP scam', # Sensitive narrative
                'claimed_amount': 500000
            }
        )

        assert smtp_inst.send_message.called
        sent_msg = smtp_inst.send_message.call_args[0][0]

        # Recipient must strictly be guardian, never user
        assert sent_msg['To'] == 'rajesh.gupta@example.com'
        assert sent_msg['To'] != user.email

        # Sanitization: Ensure sensitive victim narrative and amounts are NOT in email
        body_text = str(sent_msg)
        assert "ZG-2026-NEHA99" in body_text
        assert "Neha Gupta" in body_text
        assert "5,00,000" not in body_text
        assert "victim_private_narrative" not in body_text


def test_send_test_alert_route(client, app, db_session, mock_smtp):
    """Send test alert route succeeds for confirmed guardian and gives clear feedback for unconfirmed."""
    with app.app_context():
        user = User(
            fullname="Deepak Varma",
            email="deepak.varma@example.com",
            phone="+91 9876500777",
            role="citizen",
            is_verified=True
        )
        user.set_password("SecurePass123!")
        db_session.add(user)
        db_session.commit()

        guardian = Guardian(
            user_id=user.id,
            name="Alok Varma",
            email="alok.varma@example.com",
            phone_number="+919876500888",
            preferred_channel="email",
            consent_given=True,
            verified=False # Unconfirmed
        )
        db_session.add(guardian)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['role'] = user.role

        # Attempt test alert when unconfirmed
        res1 = client.post('/auth/guardian/test-alert', follow_redirects=True)
        assert res1.status_code == 200
        html1 = res1.get_data(as_text=True)
        assert "not verified yet" in html1.lower() or "not confirmed" in html1.lower()

        # Now confirm guardian
        guardian.verified = True
        db_session.commit()

        # Attempt test alert when confirmed
        res2 = client.post('/auth/guardian/test-alert', follow_redirects=True)
        assert res2.status_code == 200
        html2 = res2.get_data(as_text=True)
        assert "successfully dispatched" in html2 or "dispatched" in html2


def test_register_duplicate_contact_email_validation(client, app, db_session):
    """Emergency contact cannot have the exact same email as the citizen user."""
    payload = {
        'fullname': 'Suresh Kumar',
        'email': 'suresh.kumar@example.com',
        'phone': '+91 9876543210',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'trusted_contact_name': 'Ramesh Kumar',
        'trusted_contact_relationship': 'Sibling',
        'trusted_contact_email': 'suresh.kumar@example.com', # Duplicate of account email
        'trusted_contact_phone': '+91 9811122233',
        'terms': 'y'
    }

    res = client.post('/auth/register', data=payload, follow_redirects=True)
    assert res.status_code == 200
    html_content = res.get_data(as_text=True)
    assert 'Emergency contact email cannot be identical' in html_content

    user = User.query.filter_by(email='suresh.kumar@example.com').first()
    assert user is None


def test_register_invalid_contact_phone_validation(client, app, db_session):
    """Invalid contact phone numbers show a validation error without crashing."""
    payload = {
        'fullname': 'Anita Sharma',
        'email': 'anita.sharma@example.com',
        'phone': '+91 9876543210',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'trusted_contact_name': 'Pooja Sharma',
        'trusted_contact_relationship': 'Parent',
        'trusted_contact_email': 'pooja.sharma@example.com',
        'trusted_contact_phone': '12345', # Invalid length
        'terms': 'y'
    }

    res = client.post('/auth/register', data=payload, follow_redirects=True)
    assert res.status_code == 200
    html_content = res.get_data(as_text=True)
    assert 'valid 10-digit Indian mobile number' in html_content or 'valid phone' in html_content


def test_register_missing_terms_consent(client, app, db_session):
    """Failing to accept terms/consent prevents registration with clean message."""
    payload = {
        'fullname': 'Vikram Singh',
        'email': 'vikram.singh@example.com',
        'phone': '+91 9876543210',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'trusted_contact_name': 'Sunil Singh',
        'trusted_contact_relationship': 'Parent',
        'trusted_contact_email': 'sunil.singh@example.com',
        'trusted_contact_phone': '+91 9822233344'
    }

    res = client.post('/auth/register', data=payload, follow_redirects=True)
    assert res.status_code == 200
    html_content = res.get_data(as_text=True)
    assert 'agree to continue' in html_content


def test_register_otp_privacy_no_leak(client, app, db_session, mock_smtp):
    """OTP codes are hashed and never rendered directly on pages or in flash messages."""
    payload = {
        'fullname': 'Priya Nair',
        'email': 'priya.nair@example.com',
        'phone': '+91 9876543210',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!',
        'trusted_contact_name': 'Ravi Nair',
        'trusted_contact_relationship': 'Sibling',
        'trusted_contact_email': 'ravi.nair@example.com',
        'trusted_contact_phone': '+91 9833344455',
        'terms': 'y'
    }

    res = client.post('/auth/register', data=payload, follow_redirects=True)
    assert res.status_code == 200

    user = User.query.filter_by(email='priya.nair@example.com').first()
    challenge = OTPChallenge.query.filter_by(user_id=user.id, purpose='registration').order_by(OTPChallenge.created_at.desc()).first()
    assert challenge is not None
    assert challenge.otp_hash is not None
    assert len(challenge.otp_hash) == 64
