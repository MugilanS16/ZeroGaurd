import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Add workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from ai.evidence_relevance_checker import check_evidence_relevance, extract_ocr_text_from_image

TEST_DIR = Path("scratch_relevance_test_images")
TEST_DIR.mkdir(parents=True, exist_ok=True)

def create_text_image(filename: str, text: str, bg_color=(255, 255, 255), text_color=(0, 0, 0)):
    img = Image.new("RGB", (700, 350), color=bg_color)
    draw = ImageDraw.Draw(img)
    lines = text.split("\n")
    y = 30
    for line in lines:
        draw.text((30, y), line, fill=text_color)
        y += 40
    path = TEST_DIR / filename
    img.save(path)
    return str(path)

def create_plain_image(filename: str):
    img = Image.new("RGB", (700, 350), color=(120, 160, 200))
    path = TEST_DIR / filename
    img.save(path)
    return str(path)

# 1. Generate test images
img_unrelated = create_text_image(
    "unrelated_webpage.png",
    "Fresh Strawberry Jam Recipe and Cooking Guide\nIngredients: Sugar, Strawberries, Lemon Juice\nServing Size: 2 Tablespoons\nNutrition: 50 Calories per serving"
)

img_upi = create_text_image(
    "upi_receipt.png",
    "GPay Payment Successful\nPaid to Merchant Cyber Store\nUPI Ref No: 428192019281\nAmount Transferred: Rs 5,000.00"
)

img_photo = create_plain_image("plain_photo.png")

print("="*80)
print("RUNNING RELEVANCE CHECKER REAL-CASE VERIFICATION")
print("="*80)

# TEST CASE A: Unrelated Evidence (Should be BLOCKED / status='unverified')
print("\n" + "="*80)
print("TEST CASE A: UPI Fraud Description + Unrelated Recipe Screenshot")
print("="*80)
desc_a = "I was duped into transferring money through a Google Pay UPI QR code scam."
crime_a = "UPI Fraud"
ocr_a = extract_ocr_text_from_image(img_unrelated)
res_a = check_evidence_relevance(desc_a, crime_type=crime_a, evidence_image_paths=[img_unrelated])

print(f"Complaint Description: \"{desc_a}\"")
print(f"Offense Type: {crime_a}")
print(f"Evidence Image: {img_unrelated}")
print(f"\n[RAW OCR TEXT EXTRACTED ({len(ocr_a)} chars)]:\n{ocr_a}")
print(f"\n[RELEVANCE EVALUATION RESULT]:")
print(f"  Status: {res_a['status']} (Expected: 'unverified' -> BLOCKED at Step 3)")
print(f"  Matched Terms: {res_a['matched_terms']}")
print(f"  Message: {res_a['message']}")
assert res_a['status'] == 'unverified', f"Test A Failed: Expected 'unverified', got {res_a['status']}"
print("-> TEST CASE A PASSED (Correctly Flagged as Unverified & Blocked)")

# TEST CASE B: Relevant Evidence (Should PASS / status='verified')
print("\n" + "="*80)
print("TEST CASE B: UPI Fraud Description + Authentic GPay / UPI Receipt")
print("="*80)
desc_b = "I was duped into transferring money through a Google Pay UPI QR code scam."
crime_b = "UPI Fraud"
ocr_b = extract_ocr_text_from_image(img_upi)
res_b = check_evidence_relevance(desc_b, crime_type=crime_b, evidence_image_paths=[img_upi])

print(f"Complaint Description: \"{desc_b}\"")
print(f"Offense Type: {crime_b}")
print(f"Evidence Image: {img_upi}")
print(f"\n[RAW OCR TEXT EXTRACTED ({len(ocr_b)} chars)]:\n{ocr_b}")
print(f"\n[RELEVANCE EVALUATION RESULT]:")
print(f"  Status: {res_b['status']} (Expected: 'verified' -> ALLOWED to Step 4/PDF)")
print(f"  Matched Terms: {res_b['matched_terms']}")
print(f"  Message: {res_b['message']}")
assert res_b['status'] == 'verified', f"Test B Failed: Expected 'verified', got {res_b['status']}"
print("-> TEST CASE B PASSED (Correctly Verified & Permitted)")

# TEST CASE C: Plain Photo / Non-textual Evidence (Should PASS / status='inconclusive')
print("\n" + "="*80)
print("TEST CASE C: Harassment Description + Plain Photo Proof (No Text)")
print("="*80)
desc_c = "Someone is stalking and harassing me online and posting abusive comments."
crime_c = "Cyber Bullying"
ocr_c = extract_ocr_text_from_image(img_photo)
res_c = check_evidence_relevance(desc_c, crime_type=crime_c, evidence_image_paths=[img_photo])

print(f"Complaint Description: \"{desc_c}\"")
print(f"Offense Type: {crime_c}")
print(f"Evidence Image: {img_photo}")
print(f"\n[RAW OCR TEXT EXTRACTED ({len(ocr_c)} chars)]:\n{repr(ocr_c)}")
print(f"\n[RELEVANCE EVALUATION RESULT]:")
print(f"  Status: {res_c['status']} (Expected: 'inconclusive' -> NOT blocked)")
print(f"  Matched Terms: {res_c['matched_terms']}")
print(f"  Message: {res_c['message']}")
assert res_c['status'] == 'inconclusive', f"Test C Failed: Expected 'inconclusive', got {res_c['status']}"
print("-> TEST CASE C PASSED (Correctly Inconclusive & Not Blocked)")

print("\n" + "="*80)
print("ALL TESTS PASSED 100%!")
print("="*80)
