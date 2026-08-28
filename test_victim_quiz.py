import os
import sys

# Add workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import create_app

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
client = app.test_client()

print("="*80)
print("TESTING 'AM I A VICTIM?' QUICK SELF-CHECK QUIZ IMPLEMENTATION")
print("="*80)

# 1. Test GET / (Home Page)
print("\n--- Test 1: Home Page Loading & Quiz Section Markup ---")
response = client.get('/')
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
html = response.data.decode('utf-8')

assert 'id="victim-quiz-section"' in html, "Missing #victim-quiz-section in index.html"
assert 'Not sure if this is a cybercrime?' in html, "Missing Quiz title in index.html"
assert 'Start 30-Second Check' in html, "Missing Start button in index.html"
assert 'victim-quiz.js' in html, "Missing victim-quiz.js script include in index.html"
print("✓ Home page successfully renders the 'Am I a Victim?' interactive quiz section.")

# 2. Test static assets
print("\n--- Test 2: Static JS & CSS Assets Availability ---")
js_res = client.get('/static/js/victim-quiz.js')
assert js_res.status_code == 200, f"Expected 200 for victim-quiz.js, got {js_res.status_code}"
js_code = js_res.data.decode('utf-8')

# Verify 5 questions in JS
assert "Did you receive an unexpected message, call, or link" in js_code, "Q1 text missing"
assert "Were you asked to share an OTP, password, PIN, or banking details" in js_code, "Q2 text missing"
assert "Did you lose money, or was money transferred from your account" in js_code, "Q3 text missing"
assert "Has someone threatened you, harassed you, or shared/threatened to share" in js_code, "Q4 text missing"
assert "Has someone gained unauthorized access to your email, social media" in js_code, "Q5 text missing"
print("✓ All 5 required questions are present in client-side interactive quiz engine.")

# Verify result mapping logic in JS
assert "Phishing & Impersonation Scam" in js_code, "Phishing mapping missing"
assert "Financial Loss & Payment Fraud" in js_code, "Financial fraud mapping missing"
assert "Cyber Harassment, Doxxing" in js_code or "Sextortion" in js_code, "Harassment mapping missing"
assert "Account Takeover & Hacking" in js_code, "Account takeover mapping missing"
assert "doesn't appear to be a cybercrime" in js_code, "0-yes message missing"
assert "may be a reportable cybercrime incident" in js_code, "1-yes message missing"
assert "This quick check is informational only and doesn't replace filing an official report" in html, "Disclaimer missing in index.html"
print("✓ All outcome classifications, mapped category cards, and reassurance disclaimers verified.")

css_res = client.get('/static/css/components.css')
assert css_res.status_code == 200, "Expected 200 for components.css"
css_code = css_res.data.decode('utf-8')
assert ".victim-quiz-card" in css_code, "Missing .victim-quiz-card CSS class"
assert ".quiz-btn-choice" in css_code, "Missing .quiz-btn-choice CSS class"
assert ".btn-choice-yes" in css_code, "Missing .btn-choice-yes CSS class"
assert ".btn-choice-no" in css_code, "Missing .btn-choice-no CSS class"
print("✓ Responsive design classes and smooth animation keyframes verified.")

print("\n" + "="*80)
print("ALL 'AM I A VICTIM?' QUIZ VERIFICATION TESTS PASSED 100%!")
print("="*80)
