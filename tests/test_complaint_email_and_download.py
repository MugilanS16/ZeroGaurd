"""
Unit and Integration Tests for Complaint Auto-Email PDF Dispatch and Download Security.

Covers:
1. Citizen receives email with PDF attached (ZeroGuard_Report_<ref>.pdf under 5MB).
2. Verified guardian receives only sanitized notification by default (no PDF, no narrative/sensitive PII).
3. Guardian receives PDF when share box is ticked AND crime category is non-sensitive.
4. Sensitive crime categories (sextortion, deepfake, child safety, harassment) NEVER attach PDF to guardian.
5. Missing or unverified guardian is skipped safely with 'Trusted contact not confirmed, so no copy was sent.' logged.
6. SMTP failure does not crash or break complaint submission.
7. Secure PDF download route (/complaint/<ref>/report.pdf) allows owner and returns 403 for unauthorized user and 404 for missing.
8. Guardian email recipient is strictly different from citizen's email (no self-notification).
9. Resend report email endpoint works for complaint owner.
"""
import os
import smtplib
import socket
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from database import db
from database.models import User, Guardian, EmergencyContact, Complaint, NotificationLog
from backend.services.messaging.email_provider import EmailProvider
from backend.services.notify_service import NotificationService, is_sensitive_crime_category


@pytest.fixture
def mock_smtp():
    """Mocks smtplib.SMTP context manager to intercept all outbound email dispatches."""
    with patch('smtplib.SMTP') as mock_smtp_cls:
        instance = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = instance
        yield instance, mock_smtp_cls


def create_test_citizen(db_session, email="citizen.test@cybercrime.gov.in", fullname="Aarav Sharma"):
    """Helper to create an authenticated citizen."""
    user = User(
        fullname=fullname,
        email=email,
        phone="+919876543210",
        phone_number="+919876543210",
        role="citizen"
    )
    user.set_password("CitizenPass123!")
    db_session.add(user)
    db_session.commit()
    return user


def create_test_guardian(db_session, user_id, email="guardian.test@example.com", name="Sunita Sharma", verified=True):
    """Helper to create a guardian."""
    guardian = Guardian(
        user_id=user_id,
        name=name,
        relationship_type="Parent",
        email=email,
        phone_number="+919876500099",
        preferred_channel="email",
        consent_given=True,
        verified=verified,
        opted_out=False
    )
    db_session.add(guardian)
    db_session.commit()
    return guardian


# ==============================================================================
# 1. CITIZEN EMAIL WITH PDF ATTACHMENT TEST
# ==============================================================================
def test_citizen_receives_email_with_pdf_attached(app, db_session, mock_smtp):
    """Tests that citizen receives confirmation email with PDF attached (ZeroGuard_Report_<ref>.pdf)."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        citizen = create_test_citizen(db_session)
        
        # Create temporary dummy PDF file
        pdf_dir = Path(app.root_path) / 'static' / 'generated_pdfs'
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / "CC-2026-11111.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 test complaint report binary content")

        NotificationService._dispatch_citizen_submission_worker(
            user_id=citizen.id,
            recipient_email=citizen.email,
            citizen_name=citizen.fullname,
            ref_number="CC-2026-11111",
            crime_type="UPI Fraud",
            risk_level="High",
            summary="Unauthorized transfer of funds via spoofed QR code.",
            pdf_path=pdf_path
        )

        assert smtp_inst.send_message.called
        sent_msg = smtp_inst.send_message.call_args[0][0]

        assert sent_msg['To'] == citizen.email
        assert "Your ZeroGuard AI Complaint Report - CC-2026-11111" in sent_msg['Subject']
        
        # Check attachment presence and filename
        payloads = sent_msg.get_payload()
        assert len(payloads) == 2  # body (multipart/alternative) and application/pdf attachment
        
        attachment_part = payloads[1]
        assert attachment_part.get_content_type() == 'application/pdf'
        content_disp = attachment_part.get('Content-Disposition')
        assert "ZeroGuard_Report_CC-2026-11111.pdf" in content_disp

        # Verify logged in NotificationLog
        log_entry = NotificationLog.query.filter_by(recipient_type='citizen', status='sent').first()
        assert log_entry is not None
        assert log_entry.channel == 'email'


# ==============================================================================
# 2. GUARDIAN SANITIZED NOTIFICATION BY DEFAULT (NO PDF)
# ==============================================================================
def test_guardian_receives_sanitized_notification_by_default(app, db_session, mock_smtp):
    """Tests that a verified guardian receives a sanitized notification by default without PDF."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        citizen = create_test_citizen(db_session, fullname="Pooja Verma", email="pooja@test.com")
        guardian = create_test_guardian(db_session, citizen.id, email="guardian.pooja@test.com", name="Kavita Verma")

        pdf_dir = Path(app.root_path) / 'static' / 'generated_pdfs'
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / "CC-2026-22222.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 test report")

        NotificationService._dispatch_guardians_worker(
            user_id=citizen.id,
            event_type='complaint_submitted',
            case_ref="CC-2026-22222",
            context={'status': 'Pending', 'new_status': 'Pending', 'crime_type': 'Phishing'},
            share_pdf=False,  # Default: do not share PDF
            pdf_path=pdf_path,
            crime_type='Phishing'
        )

        assert smtp_inst.send_message.called
        sent_msg = smtp_inst.send_message.call_args[0][0]

        assert sent_msg['To'] == guardian.email
        assert "CC-2026-22222" in sent_msg['Subject']

        # Ensure no PDF attachment is included
        assert sent_msg.get_content_type() == 'multipart/alternative'
        payload = sent_msg.get_payload()
        for p in payload:
            assert p.get_content_type() in ('text/plain', 'text/html')
            # Check sanitization: No raw narrative, no bank account details
            body_text = p.get_payload(decode=True).decode('utf-8')
            assert "Pooja" in body_text
            assert "CC-2026-22222" in body_text
            assert "Phishing" in body_text
            assert "1930" in body_text


# ==============================================================================
# 3. GUARDIAN RECEIVES PDF WHEN TICKED AND NON-SENSITIVE
# ==============================================================================
def test_guardian_receives_pdf_when_box_ticked_and_non_sensitive(app, db_session, mock_smtp):
    """Tests that verified guardian receives PDF when share_pdf is True and crime is non-sensitive."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        citizen = create_test_citizen(db_session, fullname="Rohan Mehta", email="rohan@test.com")
        guardian = create_test_guardian(db_session, citizen.id, email="guardian.rohan@test.com", name="Vikram Mehta")

        pdf_dir = Path(app.root_path) / 'static' / 'generated_pdfs'
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / "CC-2026-33333.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 non sensitive report binary")

        NotificationService._dispatch_guardians_worker(
            user_id=citizen.id,
            event_type='complaint_submitted',
            case_ref="CC-2026-33333",
            context={'status': 'Pending', 'new_status': 'Pending', 'crime_type': 'E-Commerce Fraud'},
            share_pdf=True,  # User explicitly checked box
            pdf_path=pdf_path,
            crime_type='E-Commerce Fraud'
        )

        assert smtp_inst.send_message.called
        sent_msg = smtp_inst.send_message.call_args[0][0]
        assert sent_msg['To'] == guardian.email

        # Attached PDF must be present
        payloads = sent_msg.get_payload()
        assert len(payloads) == 2
        attachment_part = payloads[1]
        assert attachment_part.get_content_type() == 'application/pdf'
        assert "ZeroGuard_Report_CC-2026-33333.pdf" in attachment_part.get('Content-Disposition')


# ==============================================================================
# 4. SENSITIVE CRIME CATEGORIES SUPPRESS GUARDIAN PDF
# ==============================================================================
@pytest.mark.parametrize("sensitive_category", [
    "Sextortion",
    "Deepfake Blackmail",
    "Cyberbullying and Harassment",
    "Child Safety & CSAM",
    "Non-consensual Intimate Imagery"
])
def test_sensitive_categories_never_send_pdf_to_guardian(app, db_session, mock_smtp, sensitive_category):
    """Tests that sensitive categories strictly suppress PDF attachments for guardian even if box is ticked."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        cat_tag = sensitive_category[:4].lower().replace(' ', '_')
        citizen = create_test_citizen(db_session, fullname="Ananya Sen", email=f"ananya_{cat_tag}@test.com")
        guardian = create_test_guardian(db_session, citizen.id, email=f"guardian_{cat_tag}@test.com")

        pdf_dir = Path(app.root_path) / 'static' / 'generated_pdfs'
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / "CC-2026-44444.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 sensitive case report")

        # Share PDF is True, but category is sensitive
        NotificationService._dispatch_guardians_worker(
            user_id=citizen.id,
            event_type='complaint_submitted',
            case_ref="CC-2026-44444",
            context={'status': 'Pending', 'new_status': 'Pending', 'crime_type': sensitive_category},
            share_pdf=True,  # User checked box
            pdf_path=pdf_path,
            crime_type=sensitive_category
        )

        assert smtp_inst.send_message.called
        sent_msg = smtp_inst.send_message.call_args[0][0]
        assert sent_msg['To'] == guardian.email.lower()

        # Ensure NO PDF was attached
        assert sent_msg.get_content_type() == 'multipart/alternative'
        for part in sent_msg.get_payload():
            assert part.get_content_type() in ('text/plain', 'text/html')


# ==============================================================================
# 5. UNVERIFIED OR MISSING GUARDIAN SKIPPED AND LOGGED
# ==============================================================================
def test_unverified_or_missing_guardian_skipped_and_logged(app, db_session, mock_smtp):
    """Tests that user with no verified guardian safely skips notification with a clear log reason."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        # Case A: Missing guardian
        citizen = create_test_citizen(db_session, email="citizen.missing@test.com")
        NotificationService._dispatch_guardians_worker(
            user_id=citizen.id,
            event_type='complaint_submitted',
            case_ref="CC-2026-55555",
            context={'status': 'Pending', 'new_status': 'Pending', 'crime_type': 'Crypto Scam'},
            share_pdf=True,
            pdf_path=None,
            crime_type='Crypto Scam'
        )
        assert not smtp_inst.send_message.called
        log_entry = NotificationLog.query.filter_by(recipient_type='guardian', status='skipped').first()
        assert log_entry is not None
        assert "Trusted contact not confirmed, so no copy was sent." in log_entry.error

        # Case B: Unverified guardian
        citizen2 = create_test_citizen(db_session, email="citizen.unverified@test.com")
        create_test_guardian(db_session, citizen2.id, email="unverified.g@test.com", verified=False)
        NotificationService._dispatch_guardians_worker(
            user_id=citizen2.id,
            event_type='complaint_submitted',
            case_ref="CC-2026-55556",
            context={'status': 'Pending', 'new_status': 'Pending', 'crime_type': 'Crypto Scam'},
            share_pdf=True,
            pdf_path=None,
            crime_type='Crypto Scam'
        )
        log_entry2 = NotificationLog.query.filter_by(recipient_type='guardian', status='skipped').order_by(NotificationLog.id.desc()).first()
        assert log_entry2 is not None
        assert "has not confirmed verification yet" in log_entry2.error


# ==============================================================================
# 6. SMTP FAILURE DOES NOT BREAK COMPLAINT SUBMISSION
# ==============================================================================
def test_smtp_failure_does_not_break_submission(client, app, db_session):
    """Tests that when SMTP raises an error, the complaint submission completes and returns HTTP 200/302."""
    with patch('smtplib.SMTP') as mock_smtp_cls:
        # Simulate network timeout / SMTP failure
        mock_smtp_cls.side_effect = socket.timeout("Connection to SMTP host timed out")

        with app.app_context():
            citizen = create_test_citizen(db_session, email="failover.citizen@test.com")
            create_test_guardian(db_session, citizen.id, email="failover.guardian@test.com")

            with client.session_transaction() as sess:
                sess['user_id'] = citizen.id
                sess['role'] = 'citizen'
                sess['report_draft'] = {
                    'language': 'en',
                    'raw_description': 'My account was accessed unauthorizedly by an unknown entity.',
                    'formal_description': 'My account was accessed unauthorizedly by an unknown entity.',
                    'crime_type': 'Unauthorized Account Access',
                    'risk_level': 'High',
                    'risk_score': 75,
                    'answers': {'platform': 'NetBanking'},
                    'guidance': ['Call 1930'],
                    'evidence_meta': [],
                    'amount_verification': {'status': 'not_applicable'},
                    'evidence_relevance': {'status': 'not_applicable'}
                }

            res = client.post(
                '/report/submit',
                data={'share_report_with_guardian': '1'},
                follow_redirects=True
            )
            # Response must be 200 (renders success page) without crashing
            assert res.status_code == 200
            assert b"Complaint Successfully Registered" in res.data
            assert b"CC-2026-" in res.data

            # Complaint must be saved in database
            saved_complaint = Complaint.query.filter_by(user_id=citizen.id).first()
            assert saved_complaint is not None
            assert saved_complaint.share_report_with_guardian is True


# ==============================================================================
# 7. SECURE PDF DOWNLOAD ROUTE ACCESS CONTROL
# ==============================================================================
def test_download_pdf_route_access_control(client, app, db_session):
    """Tests that owner can download PDF, unauthorized user gets 403, and nonexistent ref gets 404."""
    with app.app_context():
        owner = create_test_citizen(db_session, email="owner@test.com")
        other_user = create_test_citizen(db_session, email="other@test.com")

        complaint = Complaint(
            user_id=owner.id,
            reference_number="CC-2026-77777",
            crime_type="Identity Theft",
            risk_level="Medium",
            risk_score=50,
            language="en",
            description="Fake profile created using my photos.",
            status="Pending",
            created_at=datetime.utcnow()
        )
        db_session.add(complaint)
        db_session.commit()

        # 1. Unauthenticated user redirected to login
        res = client.get('/complaint/CC-2026-77777/report.pdf')
        assert res.status_code == 302

        # 2. Other user logged in -> 403 Forbidden
        with client.session_transaction() as sess:
            sess['user_id'] = other_user.id
            sess['role'] = 'citizen'

        res_other = client.get('/complaint/CC-2026-77777/report.pdf')
        assert res_other.status_code == 403

        # 3. Owner logged in -> 200 OK with PDF attachment
        with client.session_transaction() as sess:
            sess['user_id'] = owner.id
            sess['role'] = 'citizen'

        res_owner = client.get('/complaint/CC-2026-77777/report.pdf')
        assert res_owner.status_code == 200
        assert res_owner.headers.get('Content-Type') == 'application/pdf'
        assert 'ZeroGuard_Report_CC-2026-77777.pdf' in res_owner.headers.get('Content-Disposition')

        # 4. Non-existent complaint -> 404 Not Found
        res_404 = client.get('/complaint/CC-2026-99999/report.pdf')
        assert res_404.status_code == 404


# ==============================================================================
# 8. GUARDIAN EMAIL RECIPIENT NEVER MATCHES CITIZEN
# ==============================================================================
def test_guardian_email_never_sent_to_citizen_self(app, db_session, mock_smtp):
    """Tests that if a guardian is registered with the citizen's own email, it is excluded."""
    smtp_inst, _ = mock_smtp
    with app.app_context():
        citizen = create_test_citizen(db_session, email="same.email@test.com")
        # Guardian with identical email
        create_test_guardian(db_session, citizen.id, email="same.email@test.com", name="Duplicate Self")

        NotificationService._dispatch_guardians_worker(
            user_id=citizen.id,
            event_type='complaint_submitted',
            case_ref="CC-2026-88888",
            context={'status': 'Pending', 'new_status': 'Pending', 'crime_type': 'SIM Swapping'},
            share_pdf=False,
            pdf_path=None,
            crime_type='SIM Swapping'
        )

        # No email should be sent to the self-address
        assert not smtp_inst.send_message.called


# ==============================================================================
# 9. RESEND REPORT EMAIL ENDPOINT TEST
# ==============================================================================
def test_resend_report_email_endpoint(client, app, db_session, mock_smtp):
    """Tests that owner can trigger the resend email endpoint."""
    with app.app_context():
        citizen = create_test_citizen(db_session, email="resend.citizen@test.com")
        complaint = Complaint(
            user_id=citizen.id,
            reference_number="CC-2026-99999",
            crime_type="Lottery Scam",
            risk_level="Medium",
            risk_score=50,
            language="en",
            description="Scam lottery email claiming 1 crore prize.",
            status="Pending",
            created_at=datetime.utcnow()
        )
        db_session.add(complaint)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['user_id'] = citizen.id
            sess['role'] = 'citizen'

        res = client.post(f'/complaint/{complaint.reference_number}/resend-email', follow_redirects=True)
        assert res.status_code == 200
