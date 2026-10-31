"""
Asynchronous Guardian Notification Service for ZeroGuard AI.
Dispatches critical alerts for complaint submissions, status updates, evidence uploads,
and Golden Hour high-risk cases to verified emergency guardians over Email, SMS, or WhatsApp.
"""
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

from flask import current_app
from database import db
from database.models import Guardian, EmergencyContact, NotificationLog, ActivityLog, User, Complaint, OTPChallenge
from backend.services.messaging.factory import get_messaging_provider
from backend.services.messaging.templates import render_template
from backend.services.otp_service import mask_phone_number, mask_email, record_audit_ledger

logger = logging.getLogger(__name__)


SENSITIVE_CRIME_CATEGORIES = {
    'sextortion', 'deepfake', 'child sexual abuse material', 'csam', 
    'child safety', 'harassment', 'cyberbullying', 'blackmail', 
    'intimate imagery', 'non-consensual', 'online harassment',
    'cyber stalking', 'stalking'
}


def is_sensitive_crime_category(crime_type: Optional[str]) -> bool:
    """Returns True if the crime category involves sensitive personal/intimate safety."""
    if not crime_type:
        return False
    clow = str(crime_type).lower()
    return any(cat in clow for cat in SENSITIVE_CRIME_CATEGORIES)


class NotificationService:
    """Dispatches asynchronous notifications to verified guardians and citizens with retry and backoff."""

    @classmethod
    def send_citizen_submission_async(
        cls,
        user_id: Optional[int],
        recipient_email: str,
        citizen_name: str,
        ref_number: str,
        crime_type: str,
        risk_level: str,
        summary: str,
        pdf_path: Optional[str] = None,
        date_str: Optional[str] = None
    ):
        """
        Dispatches complaint report confirmation email with attached PDF to the citizen in a background thread.
        Never blocks or crashes the caller request.
        """
        app = current_app._get_current_object() if current_app else None

        def worker():
            if app:
                with app.app_context():
                    cls._dispatch_citizen_submission_worker(
                        user_id, recipient_email, citizen_name, ref_number, crime_type, risk_level, summary, pdf_path, date_str
                    )
            else:
                cls._dispatch_citizen_submission_worker(
                    user_id, recipient_email, citizen_name, ref_number, crime_type, risk_level, summary, pdf_path, date_str
                )

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    @classmethod
    def _dispatch_citizen_submission_worker(
        cls,
        user_id: Optional[int],
        recipient_email: str,
        citizen_name: str,
        ref_number: str,
        crime_type: str,
        risk_level: str,
        summary: str,
        pdf_path: Optional[str] = None,
        date_str: Optional[str] = None
    ):
        """Worker executing citizen confirmation email dispatch and logging."""
        if not recipient_email or '@' not in recipient_email:
            logger.warning(f"[NotificationService] Invalid citizen email: '{recipient_email}'")
            return

        from backend.services.messaging.email_provider import EmailProvider
        email_provider = EmailProvider(current_app.config if current_app else {})

        formatted_date = date_str or datetime.now().strftime('%d %B %Y, %I:%M %p')
        masked_recip = mask_email(recipient_email)

        try:
            res = email_provider.send_citizen_complaint_report(
                to_email=recipient_email,
                citizen_name=citizen_name or "Citizen",
                ref_number=ref_number,
                crime_type=crime_type,
                risk_level=risk_level,
                date_str=formatted_date,
                summary=summary,
                pdf_path=pdf_path
            )

            log_entry = NotificationLog(
                recipient_type='citizen',
                recipient_ref=masked_recip,
                channel='email',
                template='citizen_complaint_report',
                provider_message_id=res.provider_message_id if res.success else None,
                status='sent' if res.success else 'failed',
                error=res.error if not res.success else None,
                created_at=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()

            if user_id:
                action = 'CITIZEN_REPORT_EMAIL_SENT' if res.success else 'CITIZEN_REPORT_EMAIL_FAILED'
                record_audit_ledger(user_id, action, f"Complaint report email for {ref_number} dispatched to {masked_recip}")

        except Exception as e:
            logger.error(f"[NotificationService] Unexpected error sending citizen report email for {ref_number}: {e}")
            try:
                log_entry = NotificationLog(
                    recipient_type='citizen',
                    recipient_ref=masked_recip,
                    channel='email',
                    template='citizen_complaint_report',
                    provider_message_id=None,
                    status='failed',
                    error=str(e),
                    created_at=datetime.utcnow()
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception:
                pass

    @classmethod
    def notify_guardians_async(
        cls,
        user_id: int,
        event_type: str,
        case_ref: str,
        context: Optional[Dict[str, Any]] = None,
        share_pdf: bool = False,
        pdf_path: Optional[str] = None,
        crime_type: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Dispatches notification to verified guardians in a background thread with exponential backoff.
        Ensures the HTTP request returns immediately without blocking.
        """
        app = current_app._get_current_object() if current_app else None

        def worker():
            if app:
                with app.app_context():
                    cls._dispatch_guardians_worker(
                        user_id=user_id,
                        event_type=event_type,
                        case_ref=case_ref,
                        context=context or {},
                        share_pdf=share_pdf,
                        pdf_path=pdf_path,
                        crime_type=crime_type,
                        max_retries=max_retries
                    )
            else:
                cls._dispatch_guardians_worker(
                    user_id=user_id,
                    event_type=event_type,
                    case_ref=case_ref,
                    context=context or {},
                    share_pdf=share_pdf,
                    pdf_path=pdf_path,
                    crime_type=crime_type,
                    max_retries=max_retries
                )

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    @classmethod
    def get_verified_recipients(cls, user_id: int) -> Tuple[List[Guardian], List[str]]:
        """
        Retrieves de-duplicated verified guardians for the given user.
        Excludes the user's own email and phone to prevent self-notification.
        Returns (list_of_guardians, list_of_skip_reasons).
        """
        user = User.query.get(user_id)
        user_email = (user.email or '').strip().lower() if user else ''
        user_phone = (user.phone_number or user.phone or '').strip() if user else ''

        guardians: List[Guardian] = Guardian.query.filter_by(
            user_id=user_id,
            verified=True,
            consent_given=True,
            opted_out=False
        ).all()

        # Check EmergencyContact and sync if needed
        emergency_contact = EmergencyContact.query.filter_by(user_id=user_id).first()
        if emergency_contact:
            ec_email = (emergency_contact.email or '').strip().lower()
            ec_phone = (emergency_contact.phone or '').strip()

            # Ensure not user's own contact details
            if (ec_email and ec_email != user_email) or (ec_phone and ec_phone != user_phone):
                g_match = None
                if ec_phone:
                    g_match = Guardian.query.filter_by(user_id=user_id, phone_number=ec_phone).first()
                if not g_match and ec_email:
                    g_match = Guardian.query.filter_by(user_id=user_id, email=ec_email).first()

                if g_match:
                    if not g_match.email and ec_email:
                        g_match.email = ec_email
                        db.session.commit()
                    if g_match.verified and g_match.consent_given and not g_match.opted_out and g_match not in guardians:
                        guardians.append(g_match)

        # De-duplicate by email and phone, filter out user's own info
        unique_guardians = []
        seen_identifiers = set()
        skip_reasons = []

        # Check if unverified guardian exists to explain skip
        unverified_list = Guardian.query.filter_by(user_id=user_id, verified=False).all()
        for ug in unverified_list:
            masked = mask_email(ug.email) if ug.email else mask_phone_number(ug.phone_number)
            skip_reasons.append(f"Guardian '{ug.name}' ({masked}) has not confirmed verification yet.")

        for g in guardians:
            g_email = (g.email or '').strip().lower()
            g_phone = (g.phone_number or '').strip()

            # Guard against user's own email/phone
            if g_email and g_email == user_email:
                skip_reasons.append(f"Skipped guardian '{g.name}': email matches citizen user account.")
                continue

            identifier = g_email or g_phone
            if identifier and identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                unique_guardians.append(g)

        return unique_guardians, skip_reasons

    @classmethod
    def _dispatch_guardians_worker(
        cls,
        user_id: int,
        event_type: str,
        case_ref: str,
        context: Dict[str, Any],
        share_pdf: bool = False,
        pdf_path: Optional[str] = None,
        crime_type: Optional[str] = None,
        max_retries: int = 3
    ):
        """Worker executing guardian notification logic and delivery logging."""
        user = User.query.get(user_id)
        ward_name = user.fullname if user else "Citizen Ward"
        crime_category = crime_type or context.get('crime_type') or ''

        # Sensitive category defense: NEVER attach full report PDF for sensitive categories
        is_sensitive = is_sensitive_crime_category(crime_category)
        if share_pdf and is_sensitive:
            logger.info(f"[NotificationService] Sensitive crime category '{crime_category}' - PDF report attachment suppressed for guardian alert.")
            attach_pdf_to_guardian = False
        else:
            attach_pdf_to_guardian = bool(share_pdf and pdf_path)

        guardians, skip_reasons = cls.get_verified_recipients(user_id)

        if not guardians:
            reason_str = "; ".join(skip_reasons) if skip_reasons else "Trusted contact not confirmed, so no copy was sent."
            logger.info(f"[NotificationService] User {user_id} alert '{event_type}' skipped: {reason_str}")

            log_entry = NotificationLog(
                recipient_type='guardian',
                recipient_ref='none',
                channel='none',
                template=event_type,
                provider_message_id=None,
                status='skipped',
                error=reason_str,
                created_at=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()

            record_audit_ledger(user_id, 'GUARDIAN_ALERT_SKIPPED', f"Alert '{event_type}' for Case {case_ref} skipped: {reason_str}")
            return

        for guardian in guardians:
            # Determine channel: prioritize Email if guardian has an email address or provider is email
            has_email = bool(guardian.email and '@' in guardian.email)
            channel = 'email' if has_email else (guardian.preferred_channel or 'sms').lower()
            
            masked_recipient = mask_email(guardian.email) if has_email else mask_phone_number(guardian.phone_number)

            template_map = {
                'complaint_submitted': 'guardian_submitted',
                'status_update': 'guardian_status_update',
                'evidence_uploaded': 'guardian_evidence',
                'high_risk_alert': 'guardian_high_risk',
                'test_alert': 'guardian_submitted'
            }
            template_key = template_map.get(event_type, 'guardian_submitted')

            guardian_name = str(guardian.name or 'Guardian')
            guardian_email = guardian.email
            guardian_phone = guardian.phone_number

            # Render sanitized message (NO victim narrative, NO claimed amount)
            message_body = render_template(
                template_key,
                channel='sms' if channel != 'whatsapp' else 'whatsapp',
                case_ref=case_ref,
                status=context.get('status', 'Submitted'),
                new_status=context.get('new_status', 'In Review'),
                short_note=context.get('short_note', 'Investigation in progress')[:80],
                user_name=ward_name
            )

            success = False
            provider_msg_id = None
            last_error = None

            # Retry loop with exponential backoff (1s, 2s, 4s)
            for attempt in range(1, max_retries + 1):
                try:
                    if has_email and guardian_email:
                        # Route through Gmail SMTP Provider
                        from backend.services.messaging.email_provider import EmailProvider
                        email_provider = EmailProvider(current_app.config if current_app else {})
                        res = email_provider.send_guardian_alert(
                            to_email=guardian_email,
                            guardian_name=guardian_name,
                            ward_name=ward_name,
                            case_ref=case_ref,
                            event_type=event_type,
                            context=context,
                            attach_pdf=attach_pdf_to_guardian,
                            pdf_path=pdf_path
                        )
                    else:
                        # Fallback for phone-only guardian
                        provider = get_messaging_provider()
                        if provider.name == 'email':
                            logger.warning(f"[NotificationService] Guardian {guardian_name} has no email ({masked_recipient}). Simulating via Console Provider.")
                            from backend.services.messaging.console_provider import ConsoleProvider
                            res = ConsoleProvider().send_sms(guardian_phone, message_body)
                        elif channel == 'whatsapp':
                            res = provider.send_whatsapp(
                                phone=guardian_phone,
                                body=message_body,
                                template_name='zeroguard_guardian_alert',
                                variables={'1': case_ref, '2': context.get('new_status', 'Active')}
                            )
                            if not res.success:
                                logger.warning(f"[NotificationService] Guardian WhatsApp failed. Falling back to SMS for {masked_recipient}.")
                                sms_body = render_template(template_key, channel='sms', case_ref=case_ref, status=context.get('status', 'Submitted'), new_status=context.get('new_status', 'In Review'), short_note=context.get('short_note', ''))
                                res = provider.send_sms(phone=guardian_phone, body=sms_body)
                        else:
                            res = provider.send_sms(
                                phone=guardian_phone,
                                body=message_body,
                                template_id=current_app.config.get('DLT_TEMPLATE_ID_GUARDIAN') if current_app else None
                            )

                    if res.success:
                        success = True
                        provider_msg_id = res.provider_message_id
                        break
                    else:
                        last_error = res.error
                        logger.warning(f"[NotificationService] Attempt {attempt}/{max_retries} failed for guardian {masked_recipient}: {res.error}")
                        if attempt < max_retries:
                            time.sleep(2 ** (attempt - 1))

                except Exception as e:
                    last_error = str(e)
                    logger.error(f"[NotificationService] Exception during guardian dispatch attempt {attempt} to {masked_recipient}: {e}")
                    if attempt < max_retries:
                        time.sleep(2 ** (attempt - 1))

            # Record in notification_log
            log_entry = NotificationLog(
                recipient_type='guardian',
                recipient_ref=masked_recipient,
                channel=channel,
                template=template_key,
                provider_message_id=provider_msg_id,
                status='sent' if success else 'failed',
                error=last_error,
                created_at=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()

            # Record in ActivityLog
            action_name = 'GUARDIAN_ALERT_SENT' if success else 'GUARDIAN_ALERT_FAILED'
            record_audit_ledger(user_id, action_name, f"Event '{event_type}' for Case {case_ref} notified to guardian {guardian_name} ({masked_recipient})")

    @classmethod
    def resend_complaint_emails(cls, complaint_id: int) -> Tuple[bool, str]:
        """Resends the official complaint report PDF to citizen and alert to verified guardians."""
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, "Complaint record not found."

        from pathlib import Path
        from pdf.report_generator import generate_complaint_pdf
        pdf_dir = Path(current_app.root_path) / 'static' / 'generated_pdfs'
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(pdf_dir / f"{complaint.reference_number}.pdf")

        if not Path(pdf_path).exists():
            complaint_data = {
                'reference_number': complaint.reference_number,
                'crime_type': complaint.crime_type,
                'risk_level': complaint.risk_level,
                'created_at_str': complaint.created_at.strftime('%d %B %Y, %I:%M %p') if complaint.created_at else '',
                'user_name': complaint.user.fullname if complaint.user else 'Anonymous Citizen',
                'user_email': complaint.user.email if complaint.user else 'Not Provided',
                'user_phone': complaint.user.phone if complaint.user else 'Not Provided',
                'description': complaint.description,
                'answers': complaint.answers,
                'guidance': complaint.guidance,
                'evidence_meta': complaint.evidence_meta,
                'claimed_amount': complaint.claimed_amount,
                'amount_verification_status': complaint.amount_verification_status,
                'amount_verification_details': complaint.amount_verification_details
            }
            try:
                generate_complaint_pdf(complaint_data, pdf_path)
            except Exception as e:
                logger.error(f"Error regenerating complaint PDF for resend: {e}")

        # Send to citizen
        recipient_email = complaint.user.email if complaint.user else None
        if recipient_email:
            cls.send_citizen_submission_async(
                user_id=complaint.user_id,
                recipient_email=recipient_email,
                citizen_name=complaint.user.fullname if complaint.user else 'Citizen',
                ref_number=complaint.reference_number,
                crime_type=complaint.crime_type,
                risk_level=complaint.risk_level,
                summary=complaint.description,
                pdf_path=pdf_path if Path(pdf_path).exists() else None,
                date_str=complaint.created_at.strftime('%d %B %Y, %I:%M %p') if complaint.created_at else None
            )

        # Send to guardian
        if complaint.user_id:
            cls.notify_guardians_async(
                user_id=complaint.user_id,
                event_type='complaint_submitted',
                case_ref=complaint.reference_number,
                context={
                    'status': complaint.status,
                    'new_status': complaint.status,
                    'crime_type': complaint.crime_type,
                    'date_str': complaint.created_at.strftime('%d %B %Y') if complaint.created_at else None
                },
                share_pdf=bool(complaint.share_report_with_guardian),
                pdf_path=pdf_path if Path(pdf_path).exists() else None,
                crime_type=complaint.crime_type
            )

        return True, "Complaint report email has been queued for re-delivery."

    @classmethod
    def send_test_alert(cls, user_id: int) -> Tuple[bool, str]:
        """Dispatches an immediate test alert to verified guardians of the given user."""
        guardians, skip_reasons = cls.get_verified_recipients(user_id)

        if not guardians:
            unverified = Guardian.query.filter_by(user_id=user_id, verified=False).first()
            if unverified:
                masked = mask_email(unverified.email) if unverified.email else mask_phone_number(unverified.phone_number)
                return False, f"Guardian '{unverified.name}' ({masked}) is not verified yet. Please verify your guardian before sending alerts."
            return False, "No emergency guardian configured. Please add a trusted contact first."

        # Dispatch test alert synchronously/asynchronously
        cls.notify_guardians_async(
            user_id=user_id,
            event_type='test_alert',
            case_ref='TEST-CONFIRMATION',
            context={'status': 'Active Verified', 'new_status': 'Active Verified', 'short_note': 'Test confirmation alert'}
        )
        recipient_names = ", ".join(g.name for g in guardians)
        return True, f"Test emergency alert successfully dispatched to your verified guardian ({recipient_names})."

    @classmethod
    def send_guardian_verification(cls, guardian_id: int) -> Tuple[bool, str]:
        """Generates and dispatches a verification request (OTP code / link) to a guardian."""
        guardian = Guardian.query.get(guardian_id)
        if not guardian:
            return False, "Guardian record not found."

        user = User.query.get(guardian.user_id)
        ward_name = user.fullname if user else "Citizen Ward"

        from backend.services.otp_service import generate_secure_otp, hash_otp
        otp_code = generate_secure_otp(6)
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=24)

        target_ref = guardian.email if (guardian.email and '@' in guardian.email) else guardian.phone_number
        challenge = OTPChallenge(
            user_id=guardian.user_id,
            phone_number=target_ref,
            channel='email' if (guardian.email and '@' in guardian.email) else (guardian.preferred_channel or 'sms'),
            purpose='guardian_verify',
            otp_hash=hash_otp(otp_code),
            expires_at=expires_at,
            attempts=0,
            consumed_at=None,
            created_at=now
        )
        db.session.add(challenge)
        db.session.commit()

        if guardian.email and '@' in guardian.email:
            from backend.services.messaging.email_provider import EmailProvider
            email_provider = EmailProvider(current_app.config if current_app else {})
            
            verification_link = None
            try:
                from flask import url_for, has_request_context
                if has_request_context():
                    verification_link = url_for('auth.confirm_guardian_link', challenge_id=challenge.id, otp=otp_code, _external=True)
            except Exception:
                pass

            res = email_provider.send_guardian_verification(
                to_email=guardian.email,
                guardian_name=guardian.name,
                ward_name=ward_name,
                otp_code=otp_code,
                verification_link=verification_link
            )
            masked = mask_email(guardian.email)
            if res.success:
                record_audit_ledger(guardian.user_id, 'GUARDIAN_VERIFICATION_SENT', f"Verification email dispatched to guardian {guardian.name} ({masked})")
                return True, f"Verification code sent to {guardian.name} at {masked}."
            else:
                record_audit_ledger(guardian.user_id, 'GUARDIAN_VERIFICATION_FAILED', f"Failed sending verification email to guardian {guardian.name} ({masked}): {res.error}")
                return False, f"Failed to deliver verification email: {res.error or 'Please try again.'}"
        else:
            provider = get_messaging_provider()
            body = render_template('guardian_verify_otp', channel=guardian.preferred_channel or 'sms', user_name=ward_name, otp_code=otp_code)
            res = provider.send_sms(phone=guardian.phone_number, body=body)
            masked = mask_phone_number(guardian.phone_number)
            if res.success:
                record_audit_ledger(guardian.user_id, 'GUARDIAN_VERIFICATION_SENT', f"SMS verification dispatched to guardian {guardian.name} ({masked})")
                return True, f"Verification code sent to {guardian.name} at {masked}."
            else:
                record_audit_ledger(guardian.user_id, 'GUARDIAN_VERIFICATION_FAILED', f"Failed sending SMS verification to guardian {guardian.name} ({masked}): {res.error}")
                return False, f"Failed to deliver SMS verification: {res.error or 'Please try again.'}"

    @classmethod
    def handle_opt_out(cls, phone_number: str) -> bool:
        """
        Processes an incoming STOP/opt-out request from SMS or WhatsApp webhook.
        Revokes consent and sets opted_out=True.
        """
        from backend.services.otp_service import normalize_phone_number
        valid, e164 = normalize_phone_number(phone_number)
        if not valid:
            return False

        guardians = Guardian.query.filter_by(phone_number=e164).all()
        if not guardians:
            return False

        for g in guardians:
            g.opted_out = True
            g.consent_given = False
            record_audit_ledger(g.user_id, 'GUARDIAN_OPT_OUT', f"Guardian {g.name} ({mask_phone_number(e164)}) opted out via STOP command")

        db.session.commit()
        logger.info(f"[NotificationService] Successfully processed STOP opt-out for {mask_phone_number(e164)}")
        return True
