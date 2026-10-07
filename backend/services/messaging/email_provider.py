"""
Email Messaging Provider Implementation for ZeroGuard AI.
Sends 6-digit OTP codes, Guardian Alerts, and Verification Messages via Gmail SMTP (STARTTLS port 587)
with clean HTML and plain-text formatting.
"""
import smtplib
import socket
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any
from flask import current_app
from backend.services.messaging.base import MessageProvider, MessageResult

logger = logging.getLogger(__name__)


class EmailProvider(MessageProvider):
    """SMTP Email Provider for ZeroGuard AI OTP and Guardian Alert delivery."""

    @property
    def name(self) -> str:
        return 'email'

    def send_email(
        self,
        to_email: str,
        otp_code: Optional[str] = None,
        subject: Optional[str] = None,
        html_body: Optional[str] = None,
        plain_text_body: Optional[str] = None,
        expiry_seconds: int = 300,
        purpose: str = '2fa_login'
    ) -> MessageResult:
        """
        Sends HTML + plain-text email via SMTP with STARTTLS (port 587, 10s timeout).
        Can be used for OTP verification codes or general alerts.
        """
        if not to_email or '@' not in to_email:
            return MessageResult(
                success=False,
                provider=self.name,
                channel='email',
                status='failed',
                error="Recipient email address is missing or invalid."
            )

        to_email = to_email.strip().lower()

        # Mask email for logging: m*****4@gmail.com
        parts = to_email.split('@')
        user_part = parts[0]
        domain_part = parts[1] if len(parts) > 1 else ''
        masked_email = f"{user_part[0]}*****{user_part[-1]}@{domain_part}" if len(user_part) > 2 else f"***@{domain_part}"

        # Read configuration exclusively from environment / current_app
        config = self.config or {}
        server_host = config.get('MAIL_SERVER') or 'smtp.gmail.com'
        port = int(config.get('MAIL_PORT') or 587)
        use_tls = str(config.get('MAIL_USE_TLS', 'True')).lower() in ('true', '1', 'yes')
        username = (config.get('MAIL_USERNAME') or '').strip()
        password = (config.get('MAIL_PASSWORD') or '').strip()
        sender = (config.get('MAIL_DEFAULT_SENDER') or username or 'noreply@zeroguard.ai').strip()
        suppress_send = str(config.get('MAIL_SUPPRESS_SEND', 'False')).lower() in ('true', '1', 'yes')

        # Dev / Suppress Send Fallback
        is_debug = False
        if current_app:
            is_debug = bool(current_app.config.get('DEBUG') or current_app.config.get('FLASK_ENV') == 'development')

        # Fallback template if bodies not explicitly passed
        if not subject:
            subject = "Your ZeroGuard AI verification code"

        if not plain_text_body or not html_body:
            expiry_minutes = max(1, expiry_seconds // 60)
            code_str = otp_code or "123456"
            plain_text_body = f"""Dear Citizen,

Your verification code for ZeroGuard AI ({purpose.replace('_', ' ').title()}) is:

{code_str}

This code is valid for {expiry_minutes} minutes. Never share this code with anyone. ZeroGuard AI will never ask for it.

If you did not request this verification code, please secure your account immediately.

Stay Safe,
ZeroGuard AI Security Team
"""
            html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0b1120; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table width="100%" max-width="500" border="0" cellspacing="0" cellpadding="0" style="max-width: 500px; background-color: #1e293b; border-radius: 16px; border: 1px solid #334155; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
          <tr>
            <td style="padding: 30px 30px 20px; text-align: center; background: linear-gradient(180deg, rgba(37,99,235,0.15) 0%, rgba(30,41,59,0) 100%);">
              <div style="font-size: 24px; font-weight: 800; color: #60a5fa; letter-spacing: -0.5px;">
                🛡️ ZeroGuard <span style="color: #38bdf8; font-size: 14px; background: rgba(56,189,248,0.15); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(56,189,248,0.3);">AI</span>
              </div>
              <h2 style="font-size: 20px; font-weight: 700; color: #ffffff; margin: 15px 0 5px;">Security Verification</h2>
              <p style="font-size: 14px; color: #94a3b8; margin: 0;">Use the code below to proceed.</p>
            </td>
          </tr>
          <tr>
            <td style="padding: 10px 30px 25px; text-align: center;">
              <div style="background-color: #0f172a; border: 2px dashed #3b82f6; border-radius: 12px; padding: 20px; margin: 10px 0 20px;">
                <span style="font-size: 34px; font-weight: 800; letter-spacing: 10px; color: #38bdf8; font-family: 'Courier New', monospace;">{code_str}</span>
              </div>
              <p style="font-size: 13px; color: #94a3b8; margin: 0 0 10px;">
                ⏱️ This code will expire in <strong style="color: #cbd5e1;">{expiry_minutes} minutes</strong>.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 30px 30px;">
              <div style="background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 6px;">
                <p style="font-size: 13px; color: #fca5a5; margin: 0; line-height: 1.4;">
                  <strong>Security Notice:</strong> Never share this code with anyone. ZeroGuard will never ask for it.
                </p>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding: 20px 30px; background-color: #0f172a; border-top: 1px solid #334155; text-align: center;">
              <p style="font-size: 12px; color: #64748b; margin: 0;">
                National Cybercrime Reporting & Preservation Initiative • ZeroGuard AI
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        if suppress_send or not username or not password:
            if is_debug:
                logger.info(f"\n" + "="*65 + f"\n[CONSOLE EMAIL DISPATCH - {masked_email}]\nSubject: {subject}\n" + "="*65)
            else:
                logger.info(f"[EmailProvider] Simulated email dispatch to {masked_email} (MAIL_SUPPRESS_SEND=True or credentials missing)")

            return MessageResult(
                success=True,
                provider=self.name,
                channel='email',
                provider_message_id=f"DEV-EMAIL-{otp_code or 'MSG'}",
                status='sent'
            )

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email
        msg.attach(MIMEText(plain_text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # SMTP Dispatch with STARTTLS & 10s Timeout
        try:
            logger.info(f"[EmailProvider] Dispatching SMTP email to {masked_email} via {server_host}:{port}...")
            with smtplib.SMTP(server_host, port, timeout=10.0) as server:
                server.ehlo()
                if use_tls:
                    server.starttls()
                    server.ehlo()
                server.login(username, password)
                server.send_message(msg)

            logger.info(f"[EmailProvider] Successfully sent email to {masked_email}")
            return MessageResult(
                success=True,
                provider=self.name,
                channel='email',
                provider_message_id=f"SMTP-{to_email}",
                status='sent'
            )
        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error(f"[EmailProvider] SMTP Authentication failed for {masked_email}: {auth_err}")
            return MessageResult(
                success=False,
                provider=self.name,
                channel='email',
                status='failed',
                error="SMTP authentication failed. Please check Gmail App Password."
            )
        except (smtplib.SMTPConnectError, socket.timeout) as conn_err:
            logger.error(f"[EmailProvider] SMTP Connection timeout/error to {server_host}:{port}: {conn_err}")
            return MessageResult(
                success=False,
                provider=self.name,
                channel='email',
                status='failed',
                error="SMTP connection timed out. Please try again."
            )
        except Exception as e:
            logger.error(f"[EmailProvider] Unexpected SMTP failure to {masked_email}: {e}")
            return MessageResult(
                success=False,
                provider=self.name,
                channel='email',
                status='failed',
                error="Unable to deliver verification code. Please try again."
            )

    def send_guardian_alert(
        self,
        to_email: str,
        guardian_name: str,
        ward_name: str,
        case_ref: str,
        event_type: str,
        context: Dict[str, Any]
    ) -> MessageResult:
        """
        Dispatches a sanitized incident alert to a verified guardian's email address.
        Guarantees strict privacy: NO victim narrative, NO claimed financial amounts.
        """
        status = context.get('status', 'Submitted')
        new_status = context.get('new_status', status)
        short_note = context.get('short_note', 'Investigation in progress')[:120]

        is_high_risk = (event_type == 'high_risk_alert')
        is_test = (event_type == 'test_alert')

        if is_test:
            subject = f"🛡️ ZeroGuard AI: Test Guardian Alert Confirmation for {ward_name}"
            header_title = "Test Emergency Alert"
            status_desc = f"This is a confirmation test alert. You are active as a trusted emergency contact for {ward_name}."
        elif is_high_risk:
            subject = f"🚨 URGENT: High-Risk Incident Alert for Case {case_ref} - ZeroGuard AI"
            header_title = "Urgent High-Risk Incident Alert"
            status_desc = f"A high-priority incident (Case Ref: {case_ref}) was reported by {ward_name}. The Golden Hour window is active."
        else:
            subject = f"🛡️ ZeroGuard AI Incident Notification: Case {case_ref} ({new_status})"
            header_title = "Incident Status Update"
            status_desc = f"An update was posted for Case Ref: {case_ref} submitted by {ward_name}."

        plain_text = f"""Dear {guardian_name},

{status_desc}

Case Reference: {case_ref}
Current Status: {new_status}
Update Note: {short_note}

Privacy & Security Notice:
To protect sensitive evidence, specific complaint narratives and transaction data are not transmitted over email.
Please check in with {ward_name} or assist them in reaching official helpline 1930 if urgent financial intervention is needed.

Stay Safe,
ZeroGuard AI National Incident Coordination Team
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0b1120; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table width="100%" max-width="540" border="0" cellspacing="0" cellpadding="0" style="max-width: 540px; background-color: #1e293b; border-radius: 16px; border: 1px solid #334155; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
          <!-- Header -->
          <tr>
            <td style="padding: 25px 30px 20px; text-align: center; background: linear-gradient(180deg, rgba(37,99,235,0.2) 0%, rgba(30,41,59,0) 100%);">
              <div style="font-size: 22px; font-weight: 800; color: #60a5fa; letter-spacing: -0.5px;">
                🛡️ ZeroGuard <span style="color: #38bdf8; font-size: 13px; background: rgba(56,189,248,0.15); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(56,189,248,0.3);">AI</span>
              </div>
              <h2 style="font-size: 18px; font-weight: 700; color: {'#f87171' if is_high_risk else '#ffffff'}; margin: 12px 0 4px;">{header_title}</h2>
              <p style="font-size: 13px; color: #94a3b8; margin: 0;">Trusted Emergency Contact Dispatch</p>
            </td>
          </tr>
          <!-- Body Content -->
          <tr>
            <td style="padding: 20px 30px;">
              <p style="font-size: 14px; color: #e2e8f0; line-height: 1.5; margin: 0 0 16px;">
                Hello <strong>{guardian_name}</strong>,
              </p>
              <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5; margin: 0 0 20px;">
                {status_desc}
              </p>

              <!-- Sanitized Meta Box -->
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0f172a; border: 1px solid #334155; border-radius: 10px; margin-bottom: 20px; overflow: hidden;">
                <tr>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #1e293b; font-size: 13px; color: #94a3b8; width: 40%;">Citizen Ward:</td>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #1e293b; font-size: 13px; font-weight: 600; color: #f8fafc;">{ward_name}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #1e293b; font-size: 13px; color: #94a3b8;">Case Reference:</td>
                  <td style="padding: 12px 16px; border-bottom: 1px solid #1e293b; font-size: 13px; font-weight: 700; color: #38bdf8; font-family: monospace;">{case_ref}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 16px; font-size: 13px; color: #94a3b8;">Status:</td>
                  <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #34d399;">{new_status}</td>
                </tr>
              </table>

              <!-- Privacy Notice -->
              <div style="background-color: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 12px 14px; border-radius: 6px; margin-bottom: 15px;">
                <p style="font-size: 12px; color: #93c5fd; margin: 0; line-height: 1.4;">
                  🔒 <strong>Privacy Protection:</strong> Case narratives and sensitive financial details are strictly redacted to safeguard citizen data.
                </p>
              </div>

              {'<div style="background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 12px 14px; border-radius: 6px; margin-bottom: 15px;"><p style="font-size: 12px; color: #fca5a5; margin: 0; line-height: 1.4;">🚨 <strong>Urgent Action:</strong> If money was stolen, ensure the National Cybercrime Helpline <strong>1930</strong> is dialed immediately within the first 2 hours.</p></div>' if is_high_risk else ''}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 18px 30px; background-color: #0f172a; border-top: 1px solid #334155; text-align: center;">
              <p style="font-size: 12px; color: #64748b; margin: 0;">
                National Cybercrime Reporting & Preservation Initiative • ZeroGuard AI
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_content,
            plain_text_body=plain_text
        )

    def send_guardian_verification(
        self,
        to_email: str,
        guardian_name: str,
        ward_name: str,
        otp_code: str,
        verification_link: Optional[str] = None
    ) -> MessageResult:
        """
        Dispatches a 24-hour verification request email to a newly added emergency contact / guardian.
        """
        subject = f"🤝 ZeroGuard AI: Trusted Emergency Contact Request from {ward_name}"

        plain_text = f"""Dear {guardian_name},

{ward_name} has designated you as their trusted emergency guardian on ZeroGuard AI.

As a trusted guardian, you will receive timely safety notifications if a cybercrime or high-risk financial fraud incident is reported by {ward_name}.

Your 6-Digit Verification Code (Valid for 24 hours):
{otp_code}

{f"Or click here to verify instantly: {verification_link}" if verification_link else ""}

If you do not know {ward_name} or do not wish to receive alerts, you may ignore this email.

Stay Safe,
ZeroGuard AI Security Team
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b1120; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f1f5f9;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0b1120; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table width="100%" max-width="520" border="0" cellspacing="0" cellpadding="0" style="max-width: 520px; background-color: #1e293b; border-radius: 16px; border: 1px solid #334155; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
          <tr>
            <td style="padding: 25px 30px 20px; text-align: center; background: linear-gradient(180deg, rgba(37,99,235,0.2) 0%, rgba(30,41,59,0) 100%);">
              <div style="font-size: 22px; font-weight: 800; color: #60a5fa; letter-spacing: -0.5px;">
                🛡️ ZeroGuard <span style="color: #38bdf8; font-size: 13px; background: rgba(56,189,248,0.15); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(56,189,248,0.3);">AI</span>
              </div>
              <h2 style="font-size: 19px; font-weight: 700; color: #ffffff; margin: 12px 0 4px;">Emergency Contact Enrollment</h2>
              <p style="font-size: 13px; color: #94a3b8; margin: 0;">Verification & Consent Request</p>
            </td>
          </tr>
          <tr>
            <td style="padding: 20px 30px;">
              <p style="font-size: 14px; color: #e2e8f0; line-height: 1.5; margin: 0 0 14px;">
                Hello <strong>{guardian_name}</strong>,
              </p>
              <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5; margin: 0 0 18px;">
                <strong>{ward_name}</strong> has added you as their trusted emergency guardian on ZeroGuard AI.
              </p>

              <!-- OTP Box -->
              <div style="background-color: #0f172a; border: 2px dashed #3b82f6; border-radius: 12px; padding: 18px; margin: 15px 0 20px; text-align: center;">
                <span style="font-size: 30px; font-weight: 800; letter-spacing: 8px; color: #38bdf8; font-family: monospace;">{otp_code}</span>
                <p style="font-size: 12px; color: #94a3b8; margin: 8px 0 0;">⏱️ Valid for 24 Hours</p>
              </div>

              {f'<div style="text-align: center; margin-bottom: 20px;"><a href="{verification_link}" style="background-color: #2563eb; color: #ffffff; padding: 10px 22px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px; display: inline-block;">Verify Guardian Status &rarr;</a></div>' if verification_link else ''}

              <div style="background-color: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 12px 14px; border-radius: 6px;">
                <p style="font-size: 12px; color: #93c5fd; margin: 0; line-height: 1.4;">
                  🛡️ <strong>What this means:</strong> You will only receive critical incident notifications if {ward_name} files an urgent complaint. You can opt out at any time.
                </p>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding: 16px 30px; background-color: #0f172a; border-top: 1px solid #334155; text-align: center;">
              <p style="font-size: 12px; color: #64748b; margin: 0;">
                National Cybercrime Reporting & Preservation Initiative • ZeroGuard AI
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_content,
            plain_text_body=plain_text,
            expiry_seconds=86400,
            purpose='guardian_verification'
        )

    def send_sms(
        self,
        phone: str,
        body: str,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Alias redirecting SMS calls to email if phone is actually an email."""
        if '@' in phone:
            otp_val = (variables or {}).get('otp') or (variables or {}).get('1') or "123456"
            return self.send_email(to_email=phone, otp_code=otp_val)
        return MessageResult(
            success=False,
            provider=self.name,
            channel='email',
            status='failed',
            error="Email provider requires a valid email recipient."
        )

    def send_whatsapp(
        self,
        phone: str,
        body: str,
        template_name: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> MessageResult:
        """Fallback for WhatsApp calls."""
        return self.send_sms(phone=phone, body=body, variables=variables)

    def verify_webhook(
        self,
        request_headers: Dict[str, str],
        request_body: bytes,
        request_data: Dict[str, Any]
    ) -> bool:
        return True
