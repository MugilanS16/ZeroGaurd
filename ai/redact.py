import re

# Regex patterns for sensitive PII
AADHAAR_PATTERN = re.compile(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}\b')
PAN_PATTERN = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', re.IGNORECASE)
CARD_PATTERN = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13})\b')
PHONE_PATTERN = re.compile(r'(?:\+?91[\s-]?)?[6-9]\d{9}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
OTP_PATTERN = re.compile(r'\b(?:otp|one time password|code|pin)[\s:]*(\d{4,6})\b', re.IGNORECASE)
PASSWORD_PATTERN = re.compile(r'\b(?:password|passwd|pwd)[\s:=]+([^\s,]+)', re.IGNORECASE)

def redact_pii(text: str) -> str:
    """
    Redacts sensitive Personally Identifiable Information (PII) from user text
    before sending to AI or displaying in unprivileged contexts.
    """
    if not text or not isinstance(text, str):
        return text

    redacted = text
    
    # 1. Redact OTPs and passwords first
    redacted = OTP_PATTERN.sub(r'OTP: [REDACTED_OTP]', redacted)
    redacted = PASSWORD_PATTERN.sub(r'Password: [REDACTED_SECRET]', redacted)
    
    # 2. Redact Credit / Debit Card Numbers (16 digits)
    redacted = CARD_PATTERN.sub(r'[REDACTED_CARD_NUMBER]', redacted)
    
    # 3. Redact Aadhaar Number (12 digits)
    redacted = AADHAAR_PATTERN.sub(r'[REDACTED_AADHAAR_ID]', redacted)
    
    # 4. Redact PAN Card Number (10 alphanumeric)
    redacted = PAN_PATTERN.sub(r'[REDACTED_PAN_ID]', redacted)
    
    # 5. Redact Email addresses (masking local part partially or fully)
    def mask_email(match):
        email = match.group(0)
        parts = email.split('@')
        if len(parts) == 2:
            name, domain = parts
            masked_name = name[0] + '***' if len(name) > 1 else '***'
            return f"{masked_name}@{domain}"
        return '[REDACTED_EMAIL]'
        
    redacted = EMAIL_PATTERN.sub(mask_email, redacted)
    
    # 6. Redact Mobile Numbers (Keep last 3 digits for user reference)
    def mask_phone(match):
        phone = match.group(0).replace(' ', '').replace('-', '')
        if len(phone) >= 10:
            return f"+91-XXXXX-XX{phone[-3:]}"
        return '[REDACTED_PHONE]'
        
    redacted = PHONE_PATTERN.sub(mask_phone, redacted)

    return redacted

def has_sensitive_data(text: str) -> bool:
    """Checks if text contains any high-risk confidential credentials."""
    if not text:
        return False
    return bool(
        CARD_PATTERN.search(text) or 
        AADHAAR_PATTERN.search(text) or 
        OTP_PATTERN.search(text) or 
        PASSWORD_PATTERN.search(text)
    )
