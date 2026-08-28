import os
import re
from pathlib import Path
from PIL import Image
import pytesseract
from dotenv import load_dotenv

from ai.amount_extractor import get_tesseract_cmd
from ai.classifier import KEYWORD_RULES

load_dotenv()

# Standard stop words to ignore during token overlap extraction
COMMON_STOP_WORDS = {
    'the', 'and', 'this', 'that', 'with', 'from', 'have', 'been', 'were', 'will', 
    'would', 'could', 'should', 'they', 'them', 'their', 'what', 'when', 'where', 
    'which', 'who', 'whom', 'whose', 'why', 'how', 'all', 'any', 'both', 'each', 
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
    'own', 'same', 'so', 'than', 'too', 'very', 'can', 'just', 'should', 'now',
    'about', 'above', 'after', 'again', 'against', 'before', 'being', 'below', 
    'between', 'into', 'through', 'during', 'under', 'over', 'while', 'here', 'there'
}

COMMON_PLATFORMS_AND_ENTITIES = [
    # UPI / Payment Apps & Wallets
    'upi', 'gpay', 'google pay', 'phonepe', 'paytm', 'bhim', 'cred', 'amazon pay', 
    'mobikwik', 'freecharge', 'bharatpe', 'razorpay', 'cashfree',
    # Banks
    'sbi', 'hdfc', 'icici', 'axis', 'pnb', 'bob', 'canara', 'kotak', 'indusind', 
    'yes bank', 'union bank', 'idbi', 'rbi', 'bank',
    # Social Media & Messaging
    'instagram', 'facebook', 'whatsapp', 'telegram', 'twitter', 'snapchat', 
    'linkedin', 'youtube', 'meta', 'gmail', 'yahoo', 'outlook', 'skype',
    # E-commerce & classifieds
    'olx', 'quikr', 'amazon', 'flipkart', 'meesho', 'swiggy', 'zomato',
    # Remote support apps
    'anydesk', 'teamviewer', 'rustdesk', 'quicksupport'
]

def extract_ocr_text_from_image(image_path: str) -> str:
    """Runs pytesseract on an image path and returns clean extracted text."""
    if not os.path.exists(image_path):
        return ""
    try:
        pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"[RELEVANCE OCR ERROR] Failed reading image {image_path}: {e}")
        return ""

from datetime import datetime

def extract_complaint_signals(description_text: str, crime_type: str = None, answers_dict: dict = None) -> set:
    """
    Extracts high-signal domain phrases, entities, and category keywords from the complaint.
    Avoids generic English filler words that cause false positives on random web pages.
    """
    signals = set()
    combined_text = f"{description_text or ''} {' '.join(str(v) for v in (answers_dict or {}).values())}".lower()
    
    # 1. Add Category-Specific Keywords and Strong Phrases from KEYWORD_RULES
    if crime_type and crime_type in KEYWORD_RULES:
        rules = KEYWORD_RULES[crime_type]
        for phrase in rules.get('strong_phrases', []):
            if phrase in combined_text or len(phrase.split()) <= 2:
                signals.add(phrase.lower())
        for kw in rules.get('keywords', []):
            # Only add domain-specific keywords (length >= 4 and not generic filler)
            if len(kw) >= 4 and kw not in {'bank', 'site', 'page', 'info', 'link', 'call', 'user', 'help'}:
                signals.add(kw.lower())

    # 2. Extract platforms, payment apps, remote desktop tools, and entity names mentioned in text
    for entity in COMMON_PLATFORMS_AND_ENTITIES:
        if re.search(r'\b' + re.escape(entity) + r'\b', combined_text):
            signals.add(entity)

    # 3. Extract concrete identifiers: phone numbers, UPI IDs, emails, and handles
    for phone in re.findall(r'\b[6-9]\d{9}\b', combined_text):
        signals.add(phone)
    for vpa in re.findall(r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b', combined_text):
        signals.add(vpa)
    for handle in re.findall(r'@[a-zA-Z0-9._]{3,30}\b', combined_text):
        signals.add(handle)

    # 4. Extract meaningful 2-word domain phrases directly present in description
    words = re.findall(r'\b[a-z]{3,}\b', combined_text)
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        if w1 not in COMMON_STOP_WORDS and w2 not in COMMON_STOP_WORDS:
            bigram = f"{w1} {w2}"
            if len(bigram) >= 8:
                signals.add(bigram)

    return signals

def check_evidence_relevance(
    description_text: str, 
    crime_type: str = 'General Cybercrime', 
    evidence_image_paths: list = None, 
    answers_dict: dict = None
) -> dict:
    """
    Checks whether uploaded evidence screenshot content (extracted via OCR)
    shares semantic relevance and consistent entity/crime signals with the complaint.
    """
    # Mandatory debug print with timestamp as the very first line
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] RELEVANCE CHECK CALLED")
    print(f"[RELEVANCE CHECK] Crime Type: {crime_type}")
    print(f"[RELEVANCE CHECK] Description: \"{description_text}\"")
    print(f"[RELEVANCE CHECK] Evidence Images: {evidence_image_paths}")

    if not evidence_image_paths:
        return {
            "status": "inconclusive",
            "ocr_text_length": 0,
            "matched_terms": [],
            "message": "No image evidence attached."
        }

    # 1. Extract combined OCR text from all evidence images
    combined_ocr_text = ""
    for path in evidence_image_paths:
        if path:
            text = extract_ocr_text_from_image(str(path))
            if text:
                combined_ocr_text += " " + text

    combined_ocr_text = combined_ocr_text.strip()
    ocr_text_lower = combined_ocr_text.lower()
    ocr_length = len(combined_ocr_text)

    print(f"[RELEVANCE CHECK] Total OCR Text Extracted ({ocr_length} chars):\n---START OCR---\n{combined_ocr_text}\n---END OCR---")

    # 2. Check if OCR text is negligible / non-textual evidence (< 15 chars)
    if ocr_length < 15:
        print(f"[RELEVANCE CHECK] Inconclusive OCR text ({ocr_length} < 15 chars). Skipping relevance flag.")
        return {
            "status": "inconclusive",
            "ocr_text_length": ocr_length,
            "matched_terms": [],
            "message": "➖ Evidence Relevance Not Applicable (No Text Detected)"
        }

    # 3. Extract complaint signals
    complaint_signals = extract_complaint_signals(description_text, crime_type, answers_dict)
    print(f"[RELEVANCE CHECK] Extracted Domain Signals ({len(complaint_signals)} terms): {sorted(list(complaint_signals))[:15]}...")

    # 4. Check for overlapping signals in OCR text
    matched_terms = []
    for signal in sorted(complaint_signals, key=lambda s: len(s), reverse=True):
        # Match phrase or word with boundary
        if len(signal.split()) > 1:
            if signal in ocr_text_lower:
                matched_terms.append(signal)
        else:
            if re.search(r'\b' + re.escape(signal) + r'\b', ocr_text_lower):
                matched_terms.append(signal)

    # De-duplicate matches while preserving order
    unique_matched = []
    for term in matched_terms:
        if term not in unique_matched:
            unique_matched.append(term)

    print(f"[RELEVANCE CHECK] Matched Terms in OCR Text: {unique_matched}")

    # 5. Formulate Result
    if unique_matched:
        result = {
            "status": "verified",
            "ocr_text_length": ocr_length,
            "matched_terms": unique_matched,
            "message": f"✅ Evidence Content Verified — Relevant to Complaint (Found: {', '.join(unique_matched[:4])})."
        }
    else:
        result = {
            "status": "unverified",
            "ocr_text_length": ocr_length,
            "matched_terms": [],
            "message": f"⚠️ This evidence doesn't appear related to your complaint (classified as {crime_type}). The uploaded file's content doesn't match your description. Please upload relevant evidence or replace this file."
        }

    print(f"[RELEVANCE CHECK] Final Status: {result['status']}")
    return result

