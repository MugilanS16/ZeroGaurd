import os
import sys
import re

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.classifier import classify_incident, KEYWORD_RULES, CATEGORIES
from ai.questions import generate_questions

print("=====================================================================")
print("DEBUG DIAGNOSTIC RUN")
print("=====================================================================")

api_key = os.environ.get('GEMINI_API_KEY', '').strip()
print(f"1. GEMINI_API_KEY status: {'SET (Length: ' + str(len(api_key)) + ')' if api_key else 'NOT SET (Empty - Rule-Based Engine will be used)'}")
print(f"2. Total categories in spec: {len(CATEGORIES)}")
print(f"   Categories: {CATEGORIES}")

test_cases = [
    (
        "Test 1: Phishing / Fake Bank Link (User Exact Failing Case)",
        "I received a message claiming to be from a bank and asking me to verify my account by clicking a link. After clicking the link, I was asked to enter personal and banking information. I later realized that the message was suspicious and may have been an attempt to steal my information."
    ),
    (
        "Test 2: Harassment / Fake Profile / Cyber Bullying",
        "Someone created a fake profile using my photos on Instagram and has been sending threatening messages to my friends and family, demanding money to take it down. I have not lost any money but I am extremely worried about my privacy and safety."
    ),
    (
        "Test 3: Job Scam / WFH Tasks",
        "I applied for a work-from-home job on Telegram where they promised daily returns for liking YouTube videos and completing prepaid merchant tasks."
    )
]

for title, desc in test_cases:
    print("\n" + "="*75)
    print(f"RUNNING: {title}")
    print("="*75)
    result = classify_incident(desc)
    print(f"\nFinal Classification Output:\n  Crime Type: {result.get('crime_type')}\n  Confidence: {result.get('confidence')}\n  Risk Level: {result.get('risk_level')}\n  Risk Score: {result.get('risk_score')}\n  Source: {result.get('source')}\n  Summary: {result.get('summary')}")
    
    questions = generate_questions(result.get('crime_type'), desc)
    print(f"\nStep 2 Dynamic Questions Generated ({len(questions)} questions):")
    for q in questions:
        print(f"  - [{q.get('id')}] {q.get('question')}")

