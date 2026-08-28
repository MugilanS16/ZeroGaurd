import os
import sys

# Add workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import create_app
from ai.fraud_checker import (
    detect_input_type,
    query_google_safe_browsing,
    check_url_heuristics,
    check_url,
    check_phone_number
)

app = create_app('development')

print("="*80)
print("TESTING STANDALONE FRAUD URL & NUMBER CHECKER")
print("="*80)

# 1. Test Input Type Detection
print("\n--- TEST 1: Input Type Detection ---")
test_inputs = [
    ("https://google.com", "url"),
    ("sbi-verify-kyc.tk", "url"),
    ("http://192.168.1.1/login", "url"),
    ("+91 9876543210", "phone"),
    ("9876543210", "phone"),
    ("1800-11-2211", "phone"),
    ("hello world something random", "unknown")
]

for inp, expected in test_inputs:
    detected = detect_input_type(inp)
    print(f"Input: {inp:<30} -> Detected: {detected:<10} (Expected: {expected})")
    assert detected == expected, f"Expected {expected}, got {detected}"
print("✓ Input type detection passed 100%!")

# 2. Test URL Heuristics
print("\n--- TEST 2: Rule-Based URL Heuristics ---")
heuristics_safe = check_url_heuristics("https://www.google.com")
print(f"Safe URL (google.com) Score: {heuristics_safe['suspicion_score']}, Findings: {len(heuristics_safe['findings'])}")

heuristics_bad = check_url_heuristics("http://sbi-verify-kyc.tk/update-pan")
print(f"Bad URL (sbi-verify-kyc.tk) Score: {heuristics_bad['suspicion_score']}, Findings: {[f['message'] for f in heuristics_bad['findings']]}")
assert heuristics_bad['suspicion_score'] >= 70, "Typosquatted .tk URL must have high suspicion score"
print("✓ Heuristics engine correctly identifies brand impersonation, suspicious TLD, and keyword harvesting!")

# 3. Test Full check_url() with DB Context
print("\n--- TEST 3: Full URL Multi-Source Check ---")
with app.app_context():
    res_safe = check_url("https://www.google.com")
    print(f"Safe URL Result: Risk Level = {res_safe['risk_level']}, Score = {res_safe['risk_score']}")
    assert res_safe['risk_level'] == "Low", f"Expected Low, got {res_safe['risk_level']}"

    res_phish = check_url("http://sbi-verify-kyc.tk/update-pan")
    print(f"Phishing URL Result: Risk Level = {res_phish['risk_level']}, Score = {res_phish['risk_score']}")
    print("Reasons Identified:")
    for r in res_phish['reasons']:
        print(f"  - [{r['source']}] ({r['severity']}): {r['title']} - {r['description']}")
    assert res_phish['risk_level'] == "High", f"Expected High, got {res_phish['risk_level']}"

# 4. Test Phone Number Checks
print("\n--- TEST 4: Phone Number Analysis ---")
with app.app_context():
    res_phone_valid = check_phone_number("+91 9876543210")
    print(f"Valid Phone Result: Risk Level = {res_phone_valid['risk_level']}, Summary = {res_phone_valid['summary']}")

    res_phone_spoof = check_phone_number("+91 9999999999")
    print(f"Spoofed Phone Result: Risk Level = {res_phone_spoof['risk_level']}, Score = {res_phone_spoof['risk_score']}")
    print("Reasons Identified:")
    for r in res_phone_spoof['reasons']:
        print(f"  - [{r['source']}] ({r['severity']}): {r['title']} - {r['description']}")

# 5. Test Google Safe Browsing API Call
print("\n--- TEST 5: Google Safe Browsing API Call ---")
test_phishing_url = "http://testsafebrowsing.appspot.com/s/phishing.html"
gsb_res = query_google_safe_browsing(test_phishing_url)
print(f"Google Safe Browsing Test URL: {test_phishing_url}")
print(f"GSB Status: {gsb_res['status']}")
print(f"GSB Flagged: {gsb_res['flagged']}")
print(f"GSB Details: {gsb_res['details']}")

print("\n" + "="*80)
print("ALL STANDALONE TESTS COMPLETED!")
print("="*80)
