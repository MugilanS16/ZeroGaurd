import os
import io
import math
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance, ExifTags
import numpy as np

DISCLAIMER_TEXT = (
    "This is an automated preliminary screening tool using standard image forensics techniques "
    "(EXIF metadata extraction, Error Level Analysis, and structural display ratio checks). "
    "It does NOT provide definitive proof of image authenticity or digital manipulation. "
    "Final evidence verification should be performed by a certified cyber forensics examiner."
)

SUSPICIOUS_SOFTWARE_KEYWORDS = [
    'photoshop', 'gimp', 'snapseed', 'paint.net', 'canva', 'pixlr',
    'lightroom', 'after effects', 'facetune', 'picsart', 'affinity'
]

COMMON_ASPECT_RATIOS = [
    (16, 9), (9, 16),
    (19.5, 9), (9, 19.5),
    (20, 9), (9, 20),
    (19.3, 9), (9, 19.3),
    (16, 10), (10, 16),
    (4, 3), (3, 4),
    (1, 1)
]

def analyze_image_authenticity(image_path: str, output_dir: str = None) -> dict:
    """
    Performs multi-stage classical forensic image screening:
    1. EXIF Metadata extraction & software editing checks
    2. Error Level Analysis (ELA) with heatmap generation
    3. Resolution & aspect ratio consistency checks
    
    Returns structured forensic report dictionary.
    """
    if not os.path.exists(image_path):
        return {
            "overall_signal": "Analysis Failed",
            "signal_class": "badge-secondary",
            "checks": [],
            "ela_heatmap_url": None,
            "disclaimer": DISCLAIMER_TEXT
        }

    try:
        img = Image.open(image_path)
    except Exception as e:
        return {
            "overall_signal": "Unsupported Format",
            "signal_class": "badge-secondary",
            "checks": [{"name": "Image Read", "status": "warning", "result": "Failed", "note": str(e)}],
            "ela_heatmap_url": None,
            "disclaimer": DISCLAIMER_TEXT
        }

    checks = []
    warning_count = 0
    info_count = 0

    # -------------------------------------------------------------
    # 1. EXIF METADATA ANALYSIS
    # -------------------------------------------------------------
    exif_data = {}
    software_tag = None
    make_model = None

    try:
        raw_exif = img._getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                exif_data[tag_name] = value

            software_tag = str(exif_data.get('Software', '')).strip()
            make = str(exif_data.get('Make', '')).strip()
            model = str(exif_data.get('Model', '')).strip()
            if make or model:
                make_model = f"{make} {model}".strip()

    except Exception:
        exif_data = {}

    if software_tag:
        soft_lower = software_tag.lower()
        if any(sw in soft_lower for sw in SUSPICIOUS_SOFTWARE_KEYWORDS):
            checks.append({
                "name": "EXIF Metadata",
                "status": "warning",
                "result": f"Editing Software Detected ({software_tag})",
                "note": f"Metadata contains software tag '{software_tag}', indicating image modification in editing software."
            })
            warning_count += 1
        else:
            checks.append({
                "name": "EXIF Metadata",
                "status": "info",
                "result": f"Software Tag Present ({software_tag})",
                "note": f"Metadata lists processing software: {software_tag}."
            })
            info_count += 1
    elif make_model:
        checks.append({
            "name": "EXIF Metadata",
            "status": "pass",
            "result": f"Hardware Camera Specs Found ({make_model})",
            "note": f"Metadata confirms original camera capture details ({make_model})."
        })
    else:
        checks.append({
            "name": "EXIF Metadata",
            "status": "info",
            "result": "EXIF Metadata Absent / Stripped",
            "note": "No camera or software metadata found. Common for mobile screenshots, web downloads, and messaging app re-saves."
        })
        info_count += 1

    # -------------------------------------------------------------
    # 2. ERROR LEVEL ANALYSIS (ELA) & HEATMAP GENERATION
    # -------------------------------------------------------------
    ela_url = None
    ela_status = "pass"
    ela_result = "Uniform Error Levels"
    ela_note = "JPEG compression error distribution is uniform across image regions."

    try:
        # Convert to RGB mode for ELA comparison
        rgb_img = img.convert("RGB")
        width, height = rgb_img.size

        # Re-save image to memory buffer at 90% JPEG quality
        buffer = io.BytesIO()
        rgb_img.save(buffer, 'JPEG', quality=90)
        buffer.seek(0)
        resaved_img = Image.open(buffer)

        # Calculate pixel-by-pixel difference
        diff_img = ImageChops.difference(rgb_img, resaved_img)

        # Convert diff to numpy array for variance & heatmap amplification
        diff_np = np.array(diff_img, dtype=np.float32)
        mean_diff = float(np.mean(diff_np))
        max_diff = float(np.max(diff_np))
        std_diff = float(np.std(diff_np))

        # Local patch analysis (32x32 blocks) to catch localized editing/pasting
        patch_size = 32
        h_blocks = max(1, height // patch_size)
        w_blocks = max(1, width // patch_size)
        block_means = []

        for py in range(h_blocks):
            for px in range(w_blocks):
                block = diff_np[py*patch_size:(py+1)*patch_size, px*patch_size:(px+1)*patch_size]
                block_means.append(np.mean(block))

        max_block_mean = float(np.max(block_means)) if block_means else mean_diff
        mean_block_mean = float(np.mean(block_means)) if block_means else mean_diff
        patch_disparity = max_block_mean - mean_block_mean

        # Amplify difference for visual heatmap (scale by 15x)
        amplified_np = np.clip(diff_np * 15.0, 0, 255).astype(np.uint8)
        ela_visual = Image.fromarray(amplified_np)

        # Save ELA visual heatmap if output directory is accessible
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            base_filename = Path(image_path).stem
            ela_filename = f"ela_{base_filename}.png"
            ela_full_path = out_path / ela_filename
            ela_visual.save(ela_full_path)
            ela_url = f"/static/ela_heatmaps/{ela_filename}"

        # Evaluate ELA statistical threshold
        if patch_disparity > 10.0 or max_diff > 180.0 or std_diff > 15.0:
            ela_status = "warning"
            ela_result = "Inconsistent Compression Errors (Localized ELA Anomaly)"
            ela_note = f"Localized error variance detected (patch disparity: {patch_disparity:.1f}, max diff: {max_diff:.0f}). Bright regions in ELA heatmap indicate potential digital retouching or composite editing."
            warning_count += 1
        elif patch_disparity > 5.0 or std_diff > 8.0:
            ela_status = "info"
            ela_result = "Moderate ELA Disparity"
            ela_note = f"Slight variation in JPEG compression artifacts (patch disparity: {patch_disparity:.1f}). Typical for text overlays or high-contrast graphics."
            info_count += 1
        else:
            ela_note += f" (Uniform distribution, mean diff: {mean_diff:.1f})."

    except Exception as ela_e:
        ela_status = "info"
        ela_result = "ELA Analysis Skipped"
        ela_note = f"Error Level Analysis could not be computed: {ela_e}"

    checks.append({
        "name": "Error Level Analysis (ELA)",
        "status": ela_status,
        "result": ela_result if isinstance(ela_result, str) else ela_result[0],
        "note": ela_note,
        "heatmap_url": ela_url
    })

    # -------------------------------------------------------------
    # 3. DISPLAY RESOLUTION & SCREENSHOT CONSISTENCY
    # -------------------------------------------------------------
    w, h = img.size
    aspect_ratio = max(w, h) / max(1, min(w, h))

    is_standard_aspect = False
    for target_w, target_h in COMMON_ASPECT_RATIOS:
        target_ratio = max(target_w, target_h) / min(target_w, target_h)
        if abs(aspect_ratio - target_ratio) < 0.05:
            is_standard_aspect = True
            break

    if is_standard_aspect:
        checks.append({
            "name": "Display Resolution Consistency",
            "status": "pass",
            "result": "Consistent Screen Aspect Ratio",
            "note": f"Resolution ({w}x{h}, aspect ratio {aspect_ratio:.2f}:1) matches standard mobile or desktop display specifications."
        })
    else:
        checks.append({
            "name": "Display Resolution Consistency",
            "status": "info",
            "result": "Non-Standard / Cropped Dimensions",
            "note": f"Image dimensions ({w}x{h}, aspect ratio {aspect_ratio:.2f}:1) appear cropped or non-standard."
        })
        info_count += 1

    # -------------------------------------------------------------
    # 4. OVERALL SIGNAL ASSESSMENT
    # -------------------------------------------------------------
    if warning_count >= 2:
        overall_signal = "Multiple Signals Present"
        signal_class = "badge-critical"
    elif warning_count == 1:
        overall_signal = "Some Signals Present"
        signal_class = "badge-warning"
    else:
        overall_signal = "Low Concern"
        signal_class = "badge-success"

    return {
        "overall_signal": overall_signal,
        "signal_class": signal_class,
        "checks": checks,
        "ela_heatmap_url": ela_url,
        "disclaimer": DISCLAIMER_TEXT
    }
