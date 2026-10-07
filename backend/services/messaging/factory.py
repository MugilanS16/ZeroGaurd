"""
Factory module for instantiating the configured MessageProvider for ZeroGuard AI.
"""
import os
from flask import current_app
from backend.services.messaging.base import MessageProvider
from backend.services.messaging.twilio_provider import TwilioProvider
from backend.services.messaging.msg91_provider import MSG91Provider
from backend.services.messaging.fast2sms_provider import Fast2SMSProvider
from backend.services.messaging.email_provider import EmailProvider
from backend.services.messaging.console_provider import ConsoleProvider


def get_messaging_provider(provider_name: str = None) -> MessageProvider:
    """
    Returns an instance of MessageProvider based on environment configuration or explicit name.
    Supported: 'email', 'twilio', 'fast2sms', 'msg91', 'console'.
    """
    config = {}
    if current_app:
        config = current_app.config
        name = (provider_name or config.get('MESSAGING_PROVIDER') or 'email').lower()
    else:
        name = (provider_name or os.environ.get('MESSAGING_PROVIDER', 'email')).lower()
        config = {
            'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
            'MAIL_PORT': os.environ.get('MAIL_PORT', 587),
            'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'True'),
            'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),
            'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),
            'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', ''),
            'MAIL_SUPPRESS_SEND': os.environ.get('MAIL_SUPPRESS_SEND', 'False'),
            'TWILIO_ACCOUNT_SID': os.environ.get('TWILIO_ACCOUNT_SID', ''),
            'TWILIO_AUTH_TOKEN': os.environ.get('TWILIO_AUTH_TOKEN', ''),
            'TWILIO_PHONE_NUMBER': os.environ.get('TWILIO_PHONE_NUMBER', ''),
            'TWILIO_WHATSAPP_NUMBER': os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886'),
            'FAST2SMS_API_KEY': os.environ.get('FAST2SMS_API_KEY', ''),
            'MSG91_AUTH_KEY': os.environ.get('MSG91_AUTH_KEY', ''),
            'MSG91_SENDER_ID': os.environ.get('MSG91_SENDER_ID', 'ZEROGD'),
            'DLT_SENDER_ID': os.environ.get('DLT_SENDER_ID', 'ZEROGD'),
            'DLT_TEMPLATE_ID_OTP': os.environ.get('DLT_TEMPLATE_ID_OTP', ''),
            'DLT_TEMPLATE_ID_GUARDIAN': os.environ.get('DLT_TEMPLATE_ID_GUARDIAN', '')
        }

    if name == 'email':
        return EmailProvider(config)
    elif name == 'twilio':
        return TwilioProvider(config)
    elif name == 'fast2sms':
        return Fast2SMSProvider(config)
    elif name == 'msg91':
        return MSG91Provider(config)
    elif name == 'console':
        return ConsoleProvider(config)
    else:
        return EmailProvider(config)
