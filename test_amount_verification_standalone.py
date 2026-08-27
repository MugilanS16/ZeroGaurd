import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from ai.amount_extractor import extract_amount_from_text, extract_amount_from_image
from ai.evidence_validator import verify_amount_match

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_tests():
    print("=" * 70)
    print("STARTING AMOUNT VERIFICATION & OCR FORENSICS STANDALONE TEST")
    print("=" * 70)

    test_dir = Path("scratch_amount_test_images")
    test_dir.mkdir(exist_ok=True)

    # 1. Generate image with ₹5,000 text
    img_5000_path = test_dir / "receipt_5000.png"
    img1 = Image.new("RGB", (800, 600), color=(255, 255, 255))
    d1 = ImageDraw.Draw(img1)
    d1.text((50, 50), "GPay Payment Successful", fill=(0, 0, 0))
    d1.text((50, 120), "Paid to Merchant: Cyber Store", fill=(0, 0, 0))
    d1.text((50, 200), "Amount Transferred: Rs. 5,000.00", fill=(0, 128, 0))
    d1.text((50, 280), "UPI Ref No: 428192019281", fill=(100, 100, 100))
    img1.save(img_5000_path, "PNG")

    # 2. Generate image with ₹500 text
    img_500_path = test_dir / "receipt_500.png"
    img2 = Image.new("RGB", (800, 600), color=(255, 255, 255))
    d2 = ImageDraw.Draw(img2)
    d2.text((50, 50), "GPay Payment Successful", fill=(0, 0, 0))
    d2.text((50, 120), "Paid to Merchant: Cyber Store", fill=(0, 0, 0))
    d2.text((50, 200), "Amount Transferred: Rs. 500.00", fill=(0, 128, 0))
    d2.text((50, 280), "UPI Ref No: 428192019282", fill=(100, 100, 100))
    img2.save(img_500_path, "PNG")

    # -------------------------------------------------------------
    # TEST CASE 1: Matches (Claimed ₹5000, Evidence ₹5000)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 1: Matches (Claimed ₹5000, Evidence ₹5000) ---")
    desc1 = "I lost ₹5000 in a UPI scam after clicking a phishing link."
    res1 = verify_amount_match(desc1, [str(img_5000_path)])
    print(f"Status: {res1['status']}")
    print(f"Claimed Amounts: {res1['claimed_amounts']}")
    print(f"Found in Evidence OCR: {res1['found_in_evidence']}")
    print(f"Message: {res1['message']}")
    assert res1['status'] == 'verified', f"Expected verified, got {res1['status']}"
    print("  -> TEST CASE 1 PASSED (VERIFIED)")

    # -------------------------------------------------------------
    # TEST CASE 2: Mismatch (Claimed ₹50000, Evidence ₹500)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 2: Mismatch (Claimed ₹50000, Evidence ₹500) ---")
    desc2 = "I lost ₹50000 in an online investment fraud."
    res2 = verify_amount_match(desc2, [str(img_500_path)])
    print(f"Status: {res2['status']}")
    print(f"Claimed Amounts: {res2['claimed_amounts']}")
    print(f"Found in Evidence OCR: {res2['found_in_evidence']}")
    print(f"Message: {res2['message']}")
    assert res2['status'] == 'mismatch', f"Expected mismatch, got {res2['status']}"
    print("  -> TEST CASE 2 PASSED (MISMATCH DETECTED & BLOCKED)")

    # -------------------------------------------------------------
    # TEST CASE 3: Not Applicable (No Amount Mentioned)
    # -------------------------------------------------------------
    print("\n--- TEST CASE 3: Not Applicable (No Financial Amount Mentioned) ---")
    desc3 = "Someone hacked into my Instagram account and is sending spam messages to my contacts."
    res3 = verify_amount_match(desc3, [str(img_5000_path)])
    print(f"Status: {res3['status']}")
    print(f"Message: {res3['message']}")
    assert res3['status'] == 'not_applicable', f"Expected not_applicable, got {res3['status']}"
    print("  -> TEST CASE 3 PASSED (SKIPPED SILENTLY)")

    print("\n" + "=" * 70)
    print("ALL STANDALONE AMOUNT VERIFICATION TESTS PASSED 100%!")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    run_tests()
