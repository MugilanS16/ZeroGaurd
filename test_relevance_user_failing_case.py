import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Add workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import create_app
from ai.evidence_relevance_checker import check_evidence_relevance, extract_ocr_text_from_image

TEST_DIR = Path("scratch_relevance_user_case")
TEST_DIR.mkdir(parents=True, exist_ok=True)

def create_text_image(filename: str, text: str):
    img = Image.new("RGB", (750, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    lines = text.split("\n")
    y = 30
    for line in lines:
        draw.text((30, y), line, fill=(0, 0, 0))
        y += 40
    path = TEST_DIR / filename
    img.save(path)
    return str(path)

# 1. Unrelated Evidence: Tesseract OCR Installation Wiki Screenshot
tesseract_wiki_img = create_text_image(
    "tesseract_ocr_wiki.png",
    "GitHub Wiki: Tesseract OCR Installation Instructions\nBuilding from Source with CMake and MSVC\ngit clone https://github.com/tesseract-ocr/tesseract.git\nvcpkg install tesseract:x64-windows\nConfigure environmental PATH variable"
)

# 2. Authentic Relevant Evidence: Fake Customer Care / AnyDesk / Swiggy Call Screenshot
fake_care_img = create_text_image(
    "fake_customer_care_proof.png",
    "Incoming Call: +91 9876543210\nIdentified as: Food Delivery Customer Care\nAgent: Please install AnyDesk remote access tool\nBank Debit Alert: Rs 15,000 debited from account"
)

desc = "I searched for my food delivery app's customer care number on Google and called a number that appeared in the search results. The person asked for remote access to my phone to 'resolve' my issue, and later I found money missing from my bank account."
crime_type = "Fake Customer Care Scam"

print("="*80)
print("TESTING USER'S EXACT FAILING SCENARIO")
print("="*80)
print(f"Complaint Description:\n  \"{desc}\"\n")
print(f"Classified Offense: {crime_type}\n")

# TEST 1: Tesseract Wiki Screenshot (MUST BE UNVERIFIED & BLOCKED)
print("-" * 80)
print("SCENARIO 1: Uploading Tesseract OCR GitHub Wiki Screenshot (Completely Unrelated)")
print("-" * 80)

res_wiki = check_evidence_relevance(desc, crime_type=crime_type, evidence_image_paths=[tesseract_wiki_img])

print(f"\nResult Status: {res_wiki['status']}")
print(f"Matched Terms: {res_wiki['matched_terms']}")
print(f"User-Facing Message:\n  {res_wiki['message']}")

assert res_wiki['status'] == 'unverified', f"FAILED: Expected status 'unverified', got '{res_wiki['status']}'"
print("\n-> SCENARIO 1 PASSED: Tesseract Wiki is 100% UNVERIFIED and BLOCKED!")

# TEST 2: Relevant Fake Customer Care / AnyDesk Screenshot (MUST BE VERIFIED & ALLOWED)
print("\n" + "-" * 80)
print("SCENARIO 2: Uploading Authentic Fake Support & AnyDesk Screenshot (Relevant)")
print("-" * 80)

res_care = check_evidence_relevance(desc, crime_type=crime_type, evidence_image_paths=[fake_care_img])

print(f"\nResult Status: {res_care['status']}")
print(f"Matched Terms: {res_care['matched_terms']}")
print(f"User-Facing Message:\n  {res_care['message']}")

assert res_care['status'] == 'verified', f"FAILED: Expected status 'verified', got '{res_care['status']}'"
print("\n-> SCENARIO 2 PASSED: Fake Customer Care Evidence is 100% VERIFIED and ALLOWED!")

print("\n" + "="*80)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*80)
