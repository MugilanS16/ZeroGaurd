import os
import re
from pathlib import Path
from PIL import Image
import pytesseract
from dotenv import load_dotenv

# Load environment variables for TESSERACT_CMD
load_dotenv()

def get_tesseract_cmd() -> str:
    cmd = os.environ.get('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    if os.path.exists(cmd):
        return cmd
    return 'tesseract'

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()

def parse_numeric_val(raw_num_str: str, multiplier_str: str = '') -> float:
    """Parses raw numeric strings with multipliers (e.g., '50,000', '50k', '1.5 lakh') into floats."""
    clean_num = raw_num_str.replace(',', '').strip()
    try:
        val = float(clean_num)
    except ValueError:
        return 0.0

    mult = (multiplier_str or '').lower().strip()
    if mult == 'k':
        val *= 1000.0
    elif mult in ('lakh', 'lakhs', 'lac', 'lacs'):
        val *= 100000.0
    elif mult in ('crore', 'crores', 'cr'):
        val *= 10000000.0

    return val

def extract_amount_from_text(text: str) -> list[float]:
    """
    Extracts monetary amounts from complaint description or OCR text.
    Handles INR, Rs, ₹, USD, 50k, 1.5 lakh, and action-context patterns.
    """
    if not text:
        return []

    found_amounts = set()
    years_to_ignore = {2023.0, 2024.0, 2025.0, 2026.0, 2027.0}

    # 1. Explicit Currency Symbols & Codes: ₹5000, Rs. 5,000, INR 50000, $500
    p1 = re.compile(
        r'(?:[₹$€]|rs\.?|inr)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lacs?|crores?|cr)?\b',
        re.IGNORECASE
    )
    for match in p1.finditer(text):
        num_str, mult = match.group(1), match.group(2)
        val = parse_numeric_val(num_str, mult)
        if val > 0:
            found_amounts.add(val)

    # 2. Number + Multiplier / Units: 50k, 1.5 lakh, 5000 rupees
    p2 = re.compile(
        r'\b([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]+)?)\s*(k|lakhs?|lacs?|crores?|cr|rupees?)\b',
        re.IGNORECASE
    )
    for match in p2.finditer(text):
        num_str, mult = match.group(1), match.group(2)
        val = parse_numeric_val(num_str, mult if mult != 'rupees' else '')
        if val > 0:
            found_amounts.add(val)

    # 3. Action Context: "lost 5000", "scammed of 25000", "debited 500.00"
    p3 = re.compile(
        r'\b(?:lost|scammed|paid|transferred|debited|stolen|cheated|fraud|received|sent|amount|total|sum|fee)\s+(?:of\s+)?(?:[₹$€]|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]+)?)\b',
        re.IGNORECASE
    )
    for match in p3.finditer(text):
        num_str = match.group(1)
        val = parse_numeric_val(num_str)
        if val > 0:
            found_amounts.add(val)

    # 4. Plain numeric amounts >= 100 e.g. "yes,42000", "42000", "Rs 42,000"
    p4 = re.compile(r'(?<!\d)([1-9][0-9]{0,2}(?:,[0-9]{3})+|[1-9][0-9]{2,7})(?:\.[0-9]{1,2})?(?!\d)')
    for match in p4.finditer(text):
        val = parse_numeric_val(match.group(1))
        if val >= 100.0 and val not in years_to_ignore:
            found_amounts.add(val)

    # Filter out year numbers unless explicit currency symbol was attached
    result = []
    for amt in sorted(list(found_amounts)):
        if amt in years_to_ignore:
            # Only include if text explicitly has currency tag e.g. "₹2026"
            if re.search(r'(?:[₹$€]|rs\.?|inr)\s*' + str(int(amt)), text, re.IGNORECASE):
                result.append(amt)
        elif amt >= 10.0: # Filter out tiny noise numbers < 10
            result.append(amt)

    return result

def extract_structured_amount(answers_dict: dict) -> list[float]:
    """
    Directly extracts financial loss amounts from structured questionnaire form fields
    (e.g., answers['financial_loss'] = "yes,42000" or answers['amount'] = "50000").
    """
    if not isinstance(answers_dict, dict):
        return []

    found = set()
    fin_keys = {
        'financial_loss', 'amount', 'demanded_amount', 'amount_paid',
        'unauthorized_transfers', 'total_deposited', 'total_invested',
        'disputed_amount', 'order_details', 'processing_fee_paid',
        'ransom_demand', 'financial_loss_amount', 'loss_amount'
    }

    # Match numbers with or without thousand separator commas
    num_pattern = re.compile(r'\b[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?\b|\b[0-9]{3,8}(?:\.[0-9]{1,2})?\b')

    for k, v in answers_dict.items():
        if not v:
            continue
        v_str = str(v).strip()
        key_lower = str(k).lower()

        if key_lower in fin_keys or 'loss' in key_lower or 'amount' in key_lower or 'paid' in key_lower:
            print(f"[DEBUG extract_structured_amount] Key='{k}', Value='{v_str}'")
            matches = num_pattern.findall(v_str)
            print(f"[DEBUG extract_structured_amount] Regex matches in '{v_str}': {matches}")
            for m in matches:
                try:
                    val = float(m.replace(',', ''))
                    if val >= 100.0 and val not in {2023.0, 2024.0, 2025.0, 2026.0, 2027.0}:
                        found.add(val)
                except ValueError:
                    pass

    res = sorted(list(found))
    print(f"[DEBUG extract_structured_amount] Extracted structured amounts: {res}")
    return res

def extract_claimed_amounts(raw_description: str = '', formal_description: str = '', answers_dict: dict = None) -> list[float]:
    """
    Combined amount extraction: First checks structured questionnaire fields, then runs regex on free text.
    Structured fields take priority.
    """
    print(f"[DEBUG extract_claimed_amounts] answers_dict={answers_dict}")
    structured = extract_structured_amount(answers_dict or {})
    if structured:
        print(f"[DEBUG extract_claimed_amounts] Returning structured: {structured}")
        return structured

    # Fallback to free-text regex extraction
    text_combined = f"{raw_description or ''} {formal_description or ''} {' '.join(str(v) for v in (answers_dict or {}).values())}"
    res = extract_amount_from_text(text_combined)
    print(f"[DEBUG extract_claimed_amounts] Fallback text extraction: {res}")
    return res

def extract_amount_from_image(image_path: str) -> list[float]:
    """
    Runs Tesseract OCR on an uploaded evidence image and extracts monetary amounts.
    """
    if not os.path.exists(image_path):
        print(f"[DEBUG extract_amount_from_image] Image path does not exist: {image_path}")
        return []

    try:
        t_cmd = get_tesseract_cmd()
        pytesseract.pytesseract.tesseract_cmd = t_cmd

        img = Image.open(image_path)
        # Preprocess: convert to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        ocr_text = pytesseract.image_to_string(img)
        print(f"[DEBUG extract_amount_from_image] FULL RAW OCR TEXT FOR {image_path}:\n---START OCR---\n{ocr_text}\n---END OCR---")
        
        # 1. Run structured amount extraction on OCR text
        amounts = set(extract_amount_from_text(ocr_text))

        # 2. Extract plain numbers > 100 visible in OCR text (to catch numbers like 5000.00 in bank receipts)
        p_plain = re.compile(r'\b([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]{3,7})\b')
        for match in p_plain.finditer(ocr_text):
            val = parse_numeric_val(match.group(1))
            if val >= 100.0 and val not in {2023.0, 2024.0, 2025.0, 2026.0, 2027.0}:
                amounts.add(val)

        res = sorted(list(amounts))
        print(f"[DEBUG extract_amount_from_image] Extracted amounts from OCR: {res}")
        return res

    except Exception as e:
        print(f"[OCR AMOUNT EXTRACTION ERROR] {e}")
        return []

