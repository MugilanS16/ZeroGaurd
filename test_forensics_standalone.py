import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ai.image_forensics import analyze_image_authenticity

def run_standalone_test():
    print("=" * 70)
    print("TESTING IMAGE FORENSICS MODULE STANDALONE")
    print("=" * 70)

    test_dir = Path("scratch_test_images")
    test_dir.mkdir(exist_ok=True)
    ela_out_dir = Path("static/ela_heatmaps")
    ela_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create a clean synthetic screenshot (1080x1920)
    clean_path = test_dir / "clean_screenshot.png"
    img = Image.new("RGB", (1080, 1920), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 100, 1030, 400], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    draw.text((80, 150), "Bank Transaction Receipt", fill=(30, 41, 59))
    draw.text((80, 220), "Amount: INR 25,000.00", fill=(16, 185, 129))
    draw.text((80, 280), "Status: SUCCESS", fill=(37, 99, 235))
    img.save(clean_path, "PNG")

    print("\n--- TEST 1: Analyzing Clean Unedited Image ---")
    res_clean = analyze_image_authenticity(str(clean_path), output_dir=str(ela_out_dir))
    print(f"Overall Signal: {res_clean['overall_signal']} ({res_clean['signal_class']})")
    print(f"ELA Heatmap URL: {res_clean['ela_heatmap_url']}")
    print("Checks:")
    for c in res_clean['checks']:
        print(f"  - [{c['status'].upper()}] {c['name']}: {c['result']} --> {c['note']}")

    # 2. Create an edited/tampered image (simulating software edit and composite splicing)
    edited_path = test_dir / "edited_screenshot.jpg"
    img_base = Image.new("RGB", (1080, 1920), color=(245, 247, 250))
    draw_base = ImageDraw.Draw(img_base)
    draw_base.text((100, 200), "Original Text", fill=(0, 0, 0))
    temp_base = test_dir / "temp_base.jpg"
    img_base.save(temp_base, "JPEG", quality=50) # Low quality base

    # Paste high-quality splice
    img_splice = Image.new("RGB", (300, 100), color=(255, 255, 0))
    draw_sp = ImageDraw.Draw(img_splice)
    draw_sp.text((10, 10), "SPLICED FAKE", fill=(255, 0, 0))
    temp_splice = test_dir / "temp_splice.jpg"
    img_splice.save(temp_splice, "JPEG", quality=98) # High quality splice

    edited_img = Image.open(temp_base)
    splice_patch = Image.open(temp_splice)
    edited_img.paste(splice_patch, (100, 200))
    
    # Save with EXIF software tag
    exif = edited_img.getexif()
    exif[0x0131] = "Adobe Photoshop 2024 (Windows)"
    edited_img.save(edited_path, "JPEG", quality=90, exif=exif)

    print("\n--- TEST 2: Analyzing Tampered / Edited Image (Photoshop EXIF + Splicing) ---")
    res_edited = analyze_image_authenticity(str(edited_path), output_dir=str(ela_out_dir))
    print(f"Overall Signal: {res_edited['overall_signal']} ({res_edited['signal_class']})")
    print(f"ELA Heatmap URL: {res_edited['ela_heatmap_url']}")
    print("Checks:")
    for c in res_edited['checks']:
        print(f"  - [{c['status'].upper()}] {c['name']}: {c['result']} --> {c['note']}")

    print("\nDisclaimer:", res_edited['disclaimer'])
    print("\n=" * 70)
    print("STANDALONE TEST COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    run_standalone_test()
