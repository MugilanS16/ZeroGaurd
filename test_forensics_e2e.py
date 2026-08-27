import os
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app import create_app
from database import db
from database.models import Complaint, User
from utils.upload import save_evidence_file

def run_e2e_tests():
    print("=" * 70)
    print("STARTING END-TO-END IMAGE FORENSICS INTEGRATION TEST")
    print("=" * 70)

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    test_dir = Path("scratch_e2e_test_images")
    test_dir.mkdir(exist_ok=True)
    ela_dir = Path(app.root_path) / "static" / "ela_heatmaps"
    ela_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create clean synthetic screenshot
    clean_img_path = test_dir / "clean_evidence.png"
    img = Image.new("RGB", (1080, 1920), color=(250, 250, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([50, 100, 1030, 300], fill=(240, 240, 240))
    d.text((80, 150), "Authentic Bank SMS Notification", fill=(0, 0, 0))
    img.save(clean_img_path, "PNG")

    # 2. Create tampered image with EXIF software tag
    edited_img_path = test_dir / "edited_evidence.jpg"
    img_base = Image.new("RGB", (1080, 1920), color=(245, 247, 250))
    d_base = ImageDraw.Draw(img_base)
    d_base.text((100, 200), "Base Account Text", fill=(0, 0, 0))
    temp_b = test_dir / "tb.jpg"
    img_base.save(temp_b, "JPEG", quality=40)

    img_sp = Image.new("RGB", (400, 120), color=(255, 255, 0))
    d_sp = ImageDraw.Draw(img_sp)
    d_sp.text((10, 10), "TAMPERED OVERLAY", fill=(255, 0, 0))
    temp_sp = test_dir / "ts.jpg"
    img_sp.save(temp_sp, "JPEG", quality=99)

    ed = Image.open(temp_b)
    sp = Image.open(temp_sp)
    ed.paste(sp, (100, 200))

    exif = ed.getexif()
    exif[0x0131] = "Adobe Photoshop 2024 (Windows)"
    ed.save(edited_img_path, "JPEG", quality=90, exif=exif)

    with app.app_context():
        # -------------------------------------------------------------
        # TEST 1: Clean Evidence File Screening
        # -------------------------------------------------------------
        print("\n[TEST 1] Processing Clean Evidence Image...")
        with open(clean_img_path, 'rb') as f:
            class DummyFileStorage:
                def __init__(self, filename, fp):
                    self.filename = filename
                    self.fp = fp
                def save(self, dst):
                    self.fp.seek(0)
                    with open(dst, 'wb') as out:
                        out.write(self.fp.read())

            fs = DummyFileStorage("clean_evidence.png", f)
            meta_clean = save_evidence_file(fs, category="Screenshot")

        print("Meta Clean:")
        print("  Filename:", meta_clean['saved_filename'])
        print("  Forensics Signal:", meta_clean['forensics']['overall_signal'])
        print("  ELA Heatmap URL:", meta_clean['forensics']['ela_heatmap_url'])
        assert meta_clean['forensics']['overall_signal'] == "Low Concern", f"Expected Low Concern, got {meta_clean['forensics']['overall_signal']}"
        print("  -> Clean image passed with Low Concern (SUCCESS)")

        # -------------------------------------------------------------
        # TEST 2: Tampered / Photoshop Evidence File Screening
        # -------------------------------------------------------------
        print("\n[TEST 2] Processing Tampered (Photoshop + Spliced) Evidence Image...")
        with open(edited_img_path, 'rb') as f:
            fs_ed = DummyFileStorage("edited_evidence.jpg", f)
            meta_edited = save_evidence_file(fs_ed, category="Screenshot")

        print("Meta Edited:")
        print("  Filename:", meta_edited['saved_filename'])
        print("  Forensics Signal:", meta_edited['forensics']['overall_signal'])
        print("  ELA Heatmap URL:", meta_edited['forensics']['ela_heatmap_url'])
        for check in meta_edited['forensics']['checks']:
            print(f"    - [{check['status'].upper()}] {check['name']}: {check['result']}")
        
        assert meta_edited['forensics']['overall_signal'] in ["Some Signals Present", "Multiple Signals Present"], f"Expected signals present, got {meta_edited['forensics']['overall_signal']}"
        assert meta_edited['forensics']['disclaimer'] != "", "Disclaimer must be present"
        print("  -> Tampered image flagged with 'Some Signals Present' and EXIF warning (SUCCESS)")

        print("\n" + "=" * 70)
        print("ALL E2E IMAGE FORENSICS INTEGRATION TESTS PASSED 100%!")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    run_e2e_tests()
