import os
from ai.classifier import classify_crime

text = "My Instagram account was hacked yesterday and someone changed my email address."

print("--- Testing CyberCrimeAI Classification ---")
result = classify_crime(text)

print(f"Detected Crime Type: {result['crime_type']}")
print(f"Classification Method: {result['method']}")
print(f"Redacted Text: {result['redacted_text']}")

api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key or api_key.lower() in ("your_gemini_api_key_here", "your-api-key", ""):
    print("\nNote: GEMINI_API_KEY is not set in .env. Falling back to Rule-Based Classification.")
    print("To enable Google Gemini AI, paste your API key in the .env file.")
else:
    print("\nGoogle Gemini API key is configured!")