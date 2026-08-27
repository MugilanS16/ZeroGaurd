import re

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf', 'mp3', 'wav', 'm4a', 'ogg', 'txt', 'csv'}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 # 5 MB per file

def is_allowed_file(filename: str) -> bool:
    """Checks if file extension is permitted."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_incident_text(text: str) -> tuple[bool, str]:
    """Validates raw incident description minimum requirements."""
    if not text or len(text.strip()) < 15:
        return False, "Please provide at least 15 characters describing what happened."
    if len(text) > 10000:
        return False, "Incident description is too long (maximum 10,000 characters)."
    return True, ""
