import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_CATEGORIES = ['Screenshot', 'Bank Statement', 'Call Recording', 'Document', 'Chat Log', 'Other']

def get_upload_dir() -> Path:
    """Returns path to upload directory."""
    path = Path(current_app.config['UPLOAD_FOLDER'])
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_evidence_file(file_storage, category: str = 'Screenshot') -> dict:
    """
    Saves an uploaded evidence file with a unique safe filename and returns metadata.
    """
    if not file_storage or not file_storage.filename:
        return None

    orig_name = secure_filename(file_storage.filename)
    ext = orig_name.rsplit('.', 1)[1].lower() if '.' in orig_name else ''
    
    unique_name = f"{uuid.uuid4().hex[:12]}_{orig_name}"
    save_path = get_upload_dir() / unique_name
    
    file_storage.save(save_path)
    file_size_bytes = os.path.getsize(save_path)
    
    # Format size string
    if file_size_bytes >= 1024 * 1024:
        size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"
    else:
        size_str = f"{file_size_bytes / 1024:.0f} KB"

    meta = {
        'original_name': orig_name,
        'saved_filename': unique_name,
        'category': category if category in ALLOWED_CATEGORIES else 'Document',
        'size': size_str,
        'extension': ext
    }

    # Run automated forensic screening on image evidence
    if ext in {'jpg', 'jpeg', 'png', 'webp'}:
        try:
            from ai.image_forensics import analyze_image_authenticity
            ela_output_dir = Path(current_app.root_path) / 'static' / 'ela_heatmaps'
            forensics_result = analyze_image_authenticity(str(save_path), output_dir=str(ela_output_dir))
            meta['forensics'] = forensics_result
        except Exception as fe:
            current_app.logger.warning(f"Image forensics failed for {unique_name}: {fe}")

    return meta

def purge_evidence_files(evidence_meta_list: list) -> int:
    """
    Privacy-by-design cleaner: Permanently removes temporary evidence files
    from disk immediately after complaint PDF compilation.
    """
    deleted_count = 0
    upload_dir = get_upload_dir()

    for item in evidence_meta_list:
        fname = item.get('saved_filename') if isinstance(item, dict) else item
        if fname:
            target_path = upload_dir / fname
            try:
                if target_path.exists():
                    os.remove(target_path)
                    deleted_count += 1
            except Exception as e:
                current_app.logger.warning(f"Failed to delete temp file {fname}: {e}")

    return deleted_count
