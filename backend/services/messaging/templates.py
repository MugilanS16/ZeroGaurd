"""
Centralized Message Template Registry for ZeroGuard AI.
Configured for Indian DLT standards and Meta-approved WhatsApp HSM templates.
"""
from typing import Dict, Any


class MessageTemplates:
    """Standardized message copy and variable placeholders."""

    # 1. OTP Verification Templates
    OTP_SMS = "Your ZeroGuard AI verification code is {otp_code}. Valid for 5 mins. Do not share this code with anyone. - ZeroGuard AI"
    OTP_WHATSAPP = "🔒 *ZeroGuard AI Verification*\n\nYour one-time verification code is: *{otp_code}*\n\nThis code is valid for 5 minutes. Do not share it with anyone for security purposes."

    # 2. Guardian Alert Templates (Sanitized, NO victim narrative/amounts)
    GUARDIAN_COMPLAINT_SUBMITTED_SMS = "ZeroGuard AI: Case {case_ref} has been submitted by your ward. Status: {status}. Log in to view details. Reply STOP to opt out."
    GUARDIAN_COMPLAINT_SUBMITTED_WHATSAPP = "🛡️ *ZeroGuard AI Incident Alert*\n\nCase reference *{case_ref}* has been submitted by your ward.\nCurrent Status: *{status}*\n\nLog in to your ZeroGuard portal to view updates. Reply STOP to unsubscribe."

    GUARDIAN_STATUS_UPDATE_SMS = "ZeroGuard AI: Case {case_ref} status updated to '{new_status}'. Log in to view updates. Reply STOP to opt out."
    GUARDIAN_STATUS_UPDATE_WHATSAPP = "📋 *ZeroGuard AI Case Update*\n\nCase *{case_ref}* status has changed to: *{new_status}*\nOfficer Note: {short_note}\n\nLog in to view complete case records. Reply STOP to unsubscribe."

    GUARDIAN_EVIDENCE_UPLOADED_SMS = "ZeroGuard AI: Additional verified evidence uploaded for Case {case_ref}. Log in to view details. Reply STOP to opt out."
    GUARDIAN_EVIDENCE_UPLOADED_WHATSAPP = "📁 *ZeroGuard AI Evidence Alert*\n\nNew evidence has been attached to Case *{case_ref}*.\n\nLog in to review case files. Reply STOP to unsubscribe."

    GUARDIAN_HIGH_RISK_ALERT_SMS = "ZeroGuard AI URGENT: High-risk Case {case_ref} reported in Golden Hour. Please assist or call 1930 if funds debited. Reply STOP to opt out."
    GUARDIAN_HIGH_RISK_ALERT_WHATSAPP = "🚨 *ZeroGuard AI Critical Golden-Hour Alert*\n\nA high-priority incident (Case *{case_ref}*) was recently reported.\nThe first 2 hours are critical to freeze illicit financial transfers. Call *1930* immediately if needed.\n\nReply STOP to unsubscribe."

    GUARDIAN_VERIFY_OTP_SMS = "ZeroGuard AI: You were added as a trusted guardian by {user_name}. Your verification OTP is {otp_code}. Valid for 5 mins."
    GUARDIAN_VERIFY_OTP_WHATSAPP = "🤝 *ZeroGuard AI Guardian Verification*\n\n{user_name} has designated you as a trusted emergency contact.\n\nYour verification code is: *{otp_code}*\nValid for 5 minutes."


def render_template(template_name: str, channel: str = 'sms', **kwargs) -> str:
    """Renders formatted message text for the requested template and channel."""
    if template_name == 'otp':
        tmpl = MessageTemplates.OTP_WHATSAPP if channel == 'whatsapp' else MessageTemplates.OTP_SMS
    elif template_name == 'guardian_submitted':
        tmpl = MessageTemplates.GUARDIAN_COMPLAINT_SUBMITTED_WHATSAPP if channel == 'whatsapp' else MessageTemplates.GUARDIAN_COMPLAINT_SUBMITTED_SMS
    elif template_name == 'guardian_status_update':
        tmpl = MessageTemplates.GUARDIAN_STATUS_UPDATE_WHATSAPP if channel == 'whatsapp' else MessageTemplates.GUARDIAN_STATUS_UPDATE_SMS
    elif template_name == 'guardian_evidence':
        tmpl = MessageTemplates.GUARDIAN_EVIDENCE_UPLOADED_WHATSAPP if channel == 'whatsapp' else MessageTemplates.GUARDIAN_EVIDENCE_UPLOADED_SMS
    elif template_name == 'guardian_high_risk':
        tmpl = MessageTemplates.GUARDIAN_HIGH_RISK_ALERT_WHATSAPP if channel == 'whatsapp' else MessageTemplates.GUARDIAN_HIGH_RISK_ALERT_SMS
    elif template_name == 'guardian_verify_otp':
        tmpl = MessageTemplates.GUARDIAN_VERIFY_OTP_WHATSAPP if channel == 'whatsapp' else MessageTemplates.GUARDIAN_VERIFY_OTP_SMS
    else:
        tmpl = kwargs.get('raw_body', 'ZeroGuard AI Notification')

    # Safe placeholder formatting
    safe_kwargs = {k: str(v) if v is not None else '' for k, v in kwargs.items()}
    # Provide default fallbacks for missing keys
    safe_kwargs.setdefault('otp_code', '000000')
    safe_kwargs.setdefault('case_ref', 'ZG-CASE')
    safe_kwargs.setdefault('status', 'Pending')
    safe_kwargs.setdefault('new_status', 'In Review')
    safe_kwargs.setdefault('short_note', 'Investigation in progress')
    safe_kwargs.setdefault('user_name', 'Citizen')

    try:
        return tmpl.format(**safe_kwargs)
    except KeyError:
        return tmpl
