import os
from flask import current_app, render_template_string
from flask_mail import Message
from extensions import mail

SUBMISSION_EMAIL_TEMPLATE = """
Dear {{ user_name }},

Thank you for reporting your cyber incident via ZeroGuard AI.
Your official Cybercrime Incident Complaint has been successfully compiled and registered.

============================================================
COMPLAINT REFERENCE NUMBER: {{ ref_number }}
OFFENSE CATEGORY: {{ crime_type }}
EVALUATED RISK LEVEL: {{ risk_level }}
DATE FILED: {{ date_str }}
============================================================

WHAT HAPPENS NEXT:
1. Your complaint dossier is now available to the Nodal Cyber Crime Cell.
2. In case of financial fraud, ensure you have also dialed 1930 within the golden hour.
3. You can track ongoing investigation progress at any time using your Reference Number at:
   http://127.0.0.1:5000/track

A copy of your verified PDF Complaint Letter is attached to this notification.

PRIVACY NOTE:
All temporary evidence uploads have been permanently purged from our server following PDF compilation.

Stay Safe,
ZeroGuard AI Incident Assistance Team
National Cybercrime Reporting Initiative
"""

STATUS_UPDATE_EMAIL_TEMPLATE = """
Dear {{ user_name }},

There is an update regarding your Cybercrime Complaint (Ref: {{ ref_number }}).

============================================================
STATUS UPDATE: {{ new_status }}
PREVIOUS STATUS: {{ prev_status }}
CYBER-CELL OFFICER NOTE:
"{{ officer_note }}"
============================================================

You can review complete case details on your ZeroGuard AI Dashboard or by visiting:
http://127.0.0.1:5000/track

Regards,
Cyber Crime Investigation Unit & ZeroGuard AI
"""

def send_submission_notification(recipient_email: str, user_name: str, ref_number: str, crime_type: str, risk_level: str, pdf_path: str = None):
    """Dispatches confirmation email with attached PDF upon complaint filing."""
    if not recipient_email:
        return False
        
    try:
        from datetime import datetime
        body = render_template_string(
            SUBMISSION_EMAIL_TEMPLATE,
            user_name=user_name or 'Citizen',
            ref_number=ref_number,
            crime_type=crime_type,
            risk_level=risk_level,
            date_str=datetime.now().strftime('%d %b %Y, %I:%M %p')
        )
        
        msg = Message(
            subject=f"[ZeroGuard AI] Cybercrime Complaint Registered - Ref: {ref_number}",
            recipients=[recipient_email],
            body=body
        )
        
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                msg.attach(
                    filename=f"{ref_number}_Formal_Complaint.pdf",
                    content_type="application/pdf",
                    data=f.read()
                )

        if not current_app.config.get('MAIL_SUPPRESS_SEND', True) and current_app.config.get('MAIL_USERNAME'):
            mail.send(msg)
            current_app.logger.info(f"Dispatched SMTP email to {recipient_email} for complaint {ref_number}")
        else:
            # Console / Log output
            print("\n" + "="*70)
            print(f"[SIMULATED EMAIL DISPATCH TO: {recipient_email}]")
            print(f"SUBJECT: {msg.subject}")
            print(body)
            if pdf_path:
                print(f"[ATTACHMENT: {pdf_path}]")
            print("="*70 + "\n")

        return True
    except Exception as e:
        current_app.logger.error(f"Error sending submission email: {e}")
        return False

def send_status_update_notification(recipient_email: str, user_name: str, ref_number: str, new_status: str, prev_status: str, officer_note: str):
    """Dispatches status update email when admin modifies complaint status."""
    if not recipient_email:
        return False

    try:
        body = render_template_string(
            STATUS_UPDATE_EMAIL_TEMPLATE,
            user_name=user_name or 'Citizen',
            ref_number=ref_number,
            new_status=new_status,
            prev_status=prev_status,
            officer_note=officer_note or 'Status updated during investigation review.'
        )

        msg = Message(
            subject=f"[ZeroGuard AI] Status Update for Complaint {ref_number} -> {new_status}",
            recipients=[recipient_email],
            body=body
        )

        if not current_app.config.get('MAIL_SUPPRESS_SEND', True) and current_app.config.get('MAIL_USERNAME'):
            mail.send(msg)
        else:
            print("\n" + "="*70)
            print(f"[SIMULATED EMAIL UPDATE TO: {recipient_email}]")
            print(f"SUBJECT: {msg.subject}")
            print(body)
            print("="*70 + "\n")

        return True
    except Exception as e:
        current_app.logger.error(f"Error sending status email: {e}")
        return False


TRUSTED_CONTACT_ADDED_EMAIL_TEMPLATE = """
Dear {{ contact_name }},

You are receiving this notification because {{ user_name }} has designated you as their Emergency Trusted Contact on ZeroGuard AI, an Indian National Cybercrime Reporting and Safety Platform.

============================================================
EMERGENCY TRUSTED CONTACT DESIGNATION
Designated By : {{ user_name }}
Relationship  : {{ relationship }}
User Email    : {{ user_email }}
User Phone    : {{ user_phone }}
============================================================

WHAT THIS MEANS:
In a critical situation — for example, if {{ user_name }} reports being a victim of a serious cybercrime, loses access to their account, or is otherwise unreachable during an active investigation — ZeroGuard AI's support team or law enforcement officers may reach out to you to help ensure their safety and provide urgent assistance.

WHAT YOU SHOULD DO:
• Keep {{ user_name }}'s registered contact details handy.
• If {{ user_name }} alerts you to a cyber incident (such as financial fraud), remind them to call the National Cyber Crime Helpline at 1930 immediately.

REASSURANCE NOTE:
If you did not expect this or believe you were added in error, no action is required on your part. You may also reply directly to this email or contact us at support@zeroguard.ai if you have any questions or concerns.

Regards,
ZeroGuard AI Safety & Emergency Unit
National Cybercrime Assistance Initiative
"""

TRUSTED_CONTACT_REMOVED_EMAIL_TEMPLATE = """
Dear {{ contact_name }},

This is a brief notification to inform you that you are no longer designated as {{ user_name }}'s Emergency Trusted Contact on ZeroGuard AI.

No action is required from you.

Regards,
ZeroGuard AI Safety Team
"""

def send_trusted_contact_added_notification(contact_email: str, contact_name: str, user_name: str, user_email: str, user_phone: str, relationship: str, is_update: bool = False):
    """Dispatches email notification to newly added/updated emergency trusted contact."""
    if not contact_email:
        return False

    try:
        subject = f"You've been added as an Emergency Trusted Contact on ZeroGuard AI"
        if is_update:
            subject = f"Emergency Trusted Contact Designation Updated on ZeroGuard AI"

        body = render_template_string(
            TRUSTED_CONTACT_ADDED_EMAIL_TEMPLATE,
            contact_name=contact_name or 'Trusted Contact',
            user_name=user_name or 'Citizen',
            user_email=user_email or 'N/A',
            user_phone=user_phone or 'N/A',
            relationship=relationship or 'Trusted Contact'
        )

        msg = Message(
            subject=subject,
            recipients=[contact_email],
            body=body
        )

        if not current_app.config.get('MAIL_SUPPRESS_SEND', True) and current_app.config.get('MAIL_USERNAME'):
            mail.send(msg)
            current_app.logger.info(f"Dispatched trusted contact email to {contact_email} for user {user_name}")
        else:
            print("\n" + "="*70)
            print(f"[SIMULATED TRUSTED CONTACT EMAIL TO: {contact_email}]")
            print(f"SUBJECT: {msg.subject}")
            print(body)
            print("="*70 + "\n")

        return True
    except Exception as e:
        current_app.logger.error(f"Error sending trusted contact email: {e}")
        return False

def send_trusted_contact_removed_notification(contact_email: str, contact_name: str, user_name: str):
    """Dispatches brief email notification when a trusted contact is removed."""
    if not contact_email:
        return False

    try:
        body = render_template_string(
            TRUSTED_CONTACT_REMOVED_EMAIL_TEMPLATE,
            contact_name=contact_name or 'Trusted Contact',
            user_name=user_name or 'Citizen'
        )

        msg = Message(
            subject=f"Emergency Trusted Contact Designation Removed on ZeroGuard AI",
            recipients=[contact_email],
            body=body
        )

        if not current_app.config.get('MAIL_SUPPRESS_SEND', True) and current_app.config.get('MAIL_USERNAME'):
            mail.send(msg)
            current_app.logger.info(f"Dispatched trusted contact removal email to {contact_email}")
        else:
            print("\n" + "="*70)
            print(f"[SIMULATED TRUSTED CONTACT REMOVAL EMAIL TO: {contact_email}]")
            print(f"SUBJECT: {msg.subject}")
            print(body)
            print("="*70 + "\n")

        return True
    except Exception as e:
        current_app.logger.error(f"Error sending trusted contact removal email: {e}")
        return False

