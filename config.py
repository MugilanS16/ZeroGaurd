import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

class Config:
    """Base application configuration for ZeroGuard AI."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'zeroguard-ai-default-dev-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', f'sqlite:///{BASE_DIR / "zeroguard.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 30}
    }
    
    # Upload & Session configuration
    UPLOAD_FOLDER = BASE_DIR / 'session_uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf', 'mp3', 'wav', 'm4a', 'ogg', 'txt', 'csv'}
    
    # CSRF & Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600 * 24  # 24 hours
    
    # Gemini AI
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

    # -----------------------------------------------------------------
    # OTP & 2FA Security Engine Configuration
    # -----------------------------------------------------------------
    OTP_SECRET_KEY = os.environ.get('OTP_SECRET_KEY', os.environ.get('SECRET_KEY', 'zg-otp-hmac-sha256-server-secret-key-2026'))
    OTP_EXPIRY_SECONDS = int(os.environ.get('OTP_EXPIRY_SECONDS', 300))  # 5 minutes
    OTP_RESEND_COOLDOWN_SECONDS = int(os.environ.get('OTP_RESEND_COOLDOWN_SECONDS', 30))  # 30 seconds
    OTP_MAX_ATTEMPTS = int(os.environ.get('OTP_MAX_ATTEMPTS', 5))  # Max 5 attempts
    OTP_MAX_HOURLY_SENDS = int(os.environ.get('OTP_MAX_HOURLY_SENDS', 5))  # Max 5 per hour per phone
    OTP_EMAIL_FALLBACK = os.environ.get('OTP_EMAIL_FALLBACK', 'False').lower() in ('true', '1', 'yes')  # False by default

    # -----------------------------------------------------------------
    # Messaging & Provider Configuration
    # Options: 'twilio', 'msg91', 'console'
    # -----------------------------------------------------------------
    # Messaging provider: 'email' (default Gmail SMTP), 'console', 'twilio', 'msg91'
    MESSAGING_PROVIDER = os.environ.get('MESSAGING_PROVIDER', 'email').lower()

    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_SMS_FROM') or os.environ.get('TWILIO_PHONE_NUMBER', '')
    TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_FROM') or os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
    TWILIO_VERIFY_SERVICE_SID = os.environ.get('TWILIO_VERIFY_SERVICE_SID', '')

    # Fast2SMS Configuration (Instant Indian Mobile SMS OTP)
    FAST2SMS_API_KEY = os.environ.get('FAST2SMS_API_KEY', '')

    # MSG91 Configuration (SMS + WhatsApp, India)
    MSG91_AUTH_KEY = os.environ.get('MSG91_AUTH_KEY', '')
    MSG91_SENDER_ID = os.environ.get('MSG91_SENDER_ID', 'ZEROGD')
    MSG91_WHATSAPP_NUMBER = os.environ.get('MSG91_WHATSAPP_NUMBER', '')
    MSG91_INTEGRATED_NUMBER = os.environ.get('MSG91_INTEGRATED_NUMBER', '')

    # India-Specific DLT (Distributed Ledger Technology) Settings
    DLT_ENTITY_ID = os.environ.get('DLT_ENTITY_ID', '1101452367890123456')
    DLT_SENDER_ID = os.environ.get('DLT_SENDER_ID', 'ZEROGD')
    DLT_TEMPLATE_ID_OTP = os.environ.get('DLT_TEMPLATE_ID_OTP', '1107161829304152637')
    DLT_TEMPLATE_ID_GUARDIAN = os.environ.get('DLT_TEMPLATE_ID_GUARDIAN', '1107161829304152638')

    # WhatsApp Meta HSM Approved Template Names
    WHATSAPP_OTP_TEMPLATE_NAME = os.environ.get('WHATSAPP_OTP_TEMPLATE_NAME', 'zeroguard_otp_verification')
    WHATSAPP_GUARDIAN_TEMPLATE_NAME = os.environ.get('WHATSAPP_GUARDIAN_TEMPLATE_NAME', 'zeroguard_guardian_alert')

    # -----------------------------------------------------------------
    # Mail settings (Preserved as fallback if OTP_EMAIL_FALLBACK=True)
    # -----------------------------------------------------------------
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME') or 'noreply@zeroguard.ai'
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'False').lower() in ('true', '1', 'yes')

    # Redis / Celery Async
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MESSAGING_PROVIDER = 'console'
    OTP_EMAIL_FALLBACK = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
