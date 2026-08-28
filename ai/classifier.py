import os
import re
import json
from ai.redact import redact_pii
from ai.prompts import CLASSIFY_PROMPT, ENHANCE_PROMPT
from ai.risk_scorer import calculate_risk_score

CATEGORIES = [
    'Phishing',
    'UPI Fraud',
    'Banking Fraud',
    'Card Fraud',
    'Identity Theft',
    'Social Media Hacking',
    'Email Hacking',
    'Online Shopping Fraud',
    'Job Scam',
    'Investment Scam',
    'Lottery/Prize Scam',
    'Cyber Bullying',
    'Sextortion',
    'Malware/Ransomware',
    'Fake Customer Care Scam',
    'Other'
]

# Comprehensive keyword-based fallback rules for all 15 categories + neutral fallback
KEYWORD_RULES = {
    'Phishing': {
        'strong_phrases': [
            'clicking a link', 'clicked a link', 'click a link', 'clicking the link', 
            'clicked the link', 'click the link', 'suspicious link', 'fake link', 
            'malicious link', 'fraudulent link', 'link in sms', 'link in message', 
            'link sent', 'received a link', 'message claiming to be', 'claiming to be from a bank', 
            'claiming to be from', 'verify my account', 'verify your account', 'account verification', 
            'enter personal and banking', 'banking information', 'personal information', 
            'steal my information', 'stolen information', 'suspicious message', 'fake website', 
            'fake webpage', 'login page', 'login page clone', 'credential harvest', 
            'entered password on link', 'entered netbanking credentials', 'fake login page', 
            'kyc update', 'pan update', 'aadhaar update', 'sim block alert', 
            'account suspended', 'account will be suspended', 'account blocked', 
            'update kyc', 'verify kyc', 'enter password', 'enter otp'
        ],
        'keywords': [
            'phishing', 'smishing', 'vishing', 'link', 'links', 'url', 'urls', 
            'hyperlink', 'website', 'portal', 'spoofed', 'imposter', 'credentials', 
            'credential', 'harvesting', 'suspicious'
        ]
    },
    'Banking Fraud': {
        'strong_phrases': [
            'bank fraud', 'banking fraud', 'netbanking', 'net banking', 'internet banking', 
            'mobile banking', 'unauthorized transfer', 'unauthorized debit', 'unauthorized transaction', 
            'bank account hacked', 'account hacked', 'account compromised', 'fixed deposit broken', 
            'fd broken', 'balance debited', 'account emptied', 'money deducted from bank', 
            'bank manager fraud', 'branch manager', 'bank statement', 'dispute transaction', 
            'unauthorized withdrawal', 'bank transfer', 'claiming to be a bank'
        ],
        'keywords': [
            'bank', 'banks', 'banking', 'neft', 'rtgs', 'imps', 'cibil', 'beneficiary', 
            'passbook', 'overdraft', 'savings'
        ]
    },
    'UPI Fraud': {
        'strong_phrases': [
            'qr code', 'scan qr', 'scanned qr', 'scanning qr', 'collect request', 
            'upi pin', 'entered upi pin', 'pin entered', 'debited via upi', 
            'money sent on upi', 'upi transaction', 'cashback scam', 'olx qr scam', 
            'sent money to receive money', 'upi transfer', 'upi payment'
        ],
        'keywords': [
            'upi', 'gpay', 'google pay', 'phonepe', 'paytm', 'bhim', 'vpa', 'cred'
        ]
    },
    'Card Fraud': {
        'strong_phrases': [
            'credit card', 'debit card', 'card skimmed', 'card cloned', 'atm fraud', 
            'atm skimming', 'unauthorized swipe', 'international transaction on card', 
            'card blocked', 'card details stolen', 'card number', 'cvv entered', 
            'card charge', 'card unauthorized'
        ],
        'keywords': [
            'cvv', 'card', 'cards', 'pos machine', 'cardholder', 'mastercard', 'visa', 'rupay', 'amex'
        ]
    },
    'Job Scam': {
        'strong_phrases': [
            'work from home', 'work-from-home', 'wfh job', 'part time job', 'part-time job', 
            'telegram task', 'youtube like', 'liking youtube', 'liking videos', 'rating videos', 
            'prepaid task', 'prepaid merchant tasks', 'hotel review task', 'google review task', 
            'salary deposit', 'vip task', 'freelance scam', 'daily returns', 'daily income', 
            'earn per task', 'data entry job', 'typing job', 'job offer', 'recruiter scam'
        ],
        'keywords': [
            'job', 'jobs', 'salary', 'recruiter', 'wfh', 'freelance', 'commission'
        ]
    },
    'Cyber Bullying': {
        'strong_phrases': [
            'fake profile', 'fake account', 'abusive comments', 'abusive messages', 
            'threatening messages', 'using my photos', 'stolen photos', 'morphed photos', 
            'character assassination', 'online harassment', 'cyber bullying', 'privacy and safety', 
            'threatening to harm', 'hate speech', 'online stalking', 'trolling online', 
            'leaked photos', 'defamatory remarks', 'take it down', 'demanding money to take'
        ],
        'keywords': [
            'harassment', 'harass', 'harassed', 'harassing', 'stalking', 'stalker', 'stalked', 
            'bullying', 'bullied', 'bully', 'trolling', 'trolled', 'troll', 'doxxing', 'doxxed', 
            'defamation', 'defamatory', 'defame', 'slander', 'threat', 'threats', 'threatening', 
            'threatened', 'abusive', 'abuse', 'impersonation', 'impersonating', 'impersonated', 
            'impersonate', 'morphed', 'photos'
        ]
    },
    'Social Media Hacking': {
        'strong_phrases': [
            'instagram hacked', 'facebook hacked', 'whatsapp hacked', 'twitter hacked', 
            'snapchat hacked', 'telegram hacked', 'account takeover', 'account stolen', 
            'hacked my account', 'lost access to account', 'compromised account', 
            'reset link sent to hacker', 'hacker changed password', 'hacker changed email', 
            'social media hacked'
        ],
        'keywords': [
            'instagram', 'facebook', 'whatsapp', 'snapchat', 'telegram', 'twitter', 
            'tiktok', 'social media', 'hacked profile', 'hijacked account'
        ]
    },
    'Sextortion': {
        'strong_phrases': [
            'video call scam', 'leaked video', 'private video', 'intimate video', 
            'intimate photos', 'morphed video', 'morphed photo', 'threatening to make viral', 
            'threatening to leak', 'send to family', 'nude video', 'nude call', 
            'demanding money to delete video'
        ],
        'keywords': [
            'sextortion', 'nude', 'nudes', 'naked', 'nudity', 'blackmail', 'blackmailed', 
            'blackmailing', 'extort', 'extortion', 'extorting', 'webcam blackmail'
        ]
    },
    'Identity Theft': {
        'strong_phrases': [
            'identity theft', 'identity fraud', 'fake loan in my name', 'loan taken in my name', 
            'aadhaar misuse', 'pan misuse', 'pan card misused', 'aadhaar card misused', 
            'sim swap', 'duplicate sim', 'cibil score dropped', 'fake cibil enquiry', 
            'forged documents', 'loan without my knowledge'
        ],
        'keywords': [
            'identity', 'aadhaar', 'pan', 'passport', 'forged', 'impersonated'
        ]
    },
    'Investment Scam': {
        'strong_phrases': [
            'guaranteed returns', 'stock market tips', 'trading app', 'fake trading platform', 
            'forex trading', 'funds locked', 'withdrawal blocked', 'ipo allotment scam', 
            'high returns', 'deposit more to withdraw', 'crypto investment', 'bitcoin investment', 
            'binary options', 'double money', 'crypto trading'
        ],
        'keywords': [
            'crypto', 'cryptocurrency', 'bitcoin', 'usdt', 'forex', 'investment', 
            'invest', 'invested', 'trading', 'broker', 'ponzi', 'shares tip', 'profit share'
        ]
    },
    'Lottery/Prize Scam': {
        'strong_phrases': [
            'won prize', 'prize scam', 'lucky draw', 'kbc lottery', 'won 25 lakh', 
            'car prize', 'customs clearance fee', 'foreign parcel', 'gift package held', 
            'claim lottery', 'congratulations you won', 'lottery winner'
        ],
        'keywords': [
            'lottery', 'jackpot', 'prize', 'reward', 'contest'
        ]
    },
    'Fake Customer Care Scam': {
        'strong_phrases': [
            'customer care', 'fake customer care', 'fake helpline', 'googled helpline', 
            'toll free number scam', 'fake support', 'screen sharing app', 'remote access', 
            'asked to install app'
        ],
        'keywords': [
            'anydesk', 'teamviewer', 'rustdesk', 'quicksupport', 'helpline', 'tollfree', 'support'
        ]
    },
    'Malware/Ransomware': {
        'strong_phrases': [
            'ransom note', 'files encrypted', 'files locked', '.locked', '.crypt', 
            'demanding bitcoin to decrypt', 'device locked', 'encrypted all files', 
            'computer locked'
        ],
        'keywords': [
            'ransomware', 'malware', 'virus', 'trojan', 'spyware', 'keylogger', 
            'payload', 'decrypt', 'encrypted'
        ]
    },
    'Email Hacking': {
        'strong_phrases': [
            'email hacked', 'gmail hacked', 'yahoo hacked', 'outlook hacked', 
            'email compromised', 'business email compromise', 'forwarding rule set', 
            'unauthorized email access', 'email account takeover'
        ],
        'keywords': [
            'bec', 'ceo fraud', 'mailbox', 'email', 'outlook', 'gmail'
        ]
    },
    'Online Shopping Fraud': {
        'strong_phrases': [
            'online shopping', 'shopping fraud', 'fake courier', 'fake website shopping', 
            'ordered product never arrived', 'item not delivered', 'counterfeit product', 
            'fake return refund', 'fake tracking id', 'customs fee for order', 'e-commerce scam'
        ],
        'keywords': [
            'olx', 'quikr', 'seller', 'courier', 'parcel', 'delivery'
        ]
    }
}

def classify_by_rules(text: str) -> dict:
    """Fallback rule-based classifier matching keywords and patterns across 15 cyber categories."""
    text_lower = text.lower()
    # Normalize hyphens and multiple spaces for phrase matching
    text_normalized = re.sub(r'[\-_/]', ' ', text_lower)
    
    scores = {cat: 0 for cat in CATEGORIES if cat != 'Other'}
    matched_details = {cat: [] for cat in CATEGORIES if cat != 'Other'}
    
    for cat, rules in KEYWORD_RULES.items():
        # 1. Match strong multi-word key phrases (weight = 3 points)
        for phrase in rules.get('strong_phrases', []):
            phrase_clean = phrase.lower()
            if phrase_clean in text_lower or phrase_clean in text_normalized:
                scores[cat] += 3
                matched_details[cat].append(f"phrase:'{phrase}'(+3)")
                
        # 2. Match single keyword tokens with word boundary (weight = 1 or 2 points)
        for kw in rules.get('keywords', []):
            kw_clean = kw.lower()
            pattern = r'\b' + re.escape(kw_clean) + r'\b'
            if re.search(pattern, text_lower) or re.search(pattern, text_normalized):
                scores[cat] += 2 if len(kw_clean) > 5 else 1
                matched_details[cat].append(f"kw:'{kw}'")
                
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_cat, max_score = sorted_scores[0]
    
    print("\n[CLASSIFIER DEBUG - RULE-BASED ENGINE EVALUATION]")
    print(f"Raw Text: {text}")
    print("Keyword Match Scores Breakdown:")
    for cat, score in sorted_scores:
        if score > 0:
            print(f"  - {cat:24}: Score = {score} | Matches: {', '.join(matched_details[cat])}")
        else:
            print(f"  - {cat:24}: Score = 0")
            
    if max_score == 0:
        best_cat = 'Other'
        confidence = 0.40
        print(f"Decision: Inconclusive keyword match (Score=0). Defaulting neutrally to '{best_cat}' (Confidence={confidence}).")
    else:
        confidence = min(0.95, 0.60 + (max_score * 0.05))
        print(f"Decision: Highest keyword match score -> '{best_cat}' (Score={max_score}, Confidence={round(confidence, 2)}).")

    risk_info = calculate_risk_score(best_cat, text)
    
    return {
        'crime_type': best_cat,
        'confidence': round(confidence, 2),
        'risk_level': risk_info['level'],
        'risk_score': risk_info['score'],
        'summary': f"Incident classified as {best_cat} with an evaluated {risk_info['level']} risk level.",
        'source': 'Rule-Based Engine'
    }

def classify_incident(raw_description: str) -> dict:
    """Classifies incident using Gemini API if configured, otherwise rule-based fallback."""
    clean_text = redact_pii(raw_description)
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    print("\n" + "="*70)
    print("[CLASSIFIER INVOCATION]")
    print(f"Raw Description: \"{raw_description}\"")
    print(f"GEMINI_API_KEY Configured: {'YES' if api_key else 'NO (Empty in environment)'}")
    print(f"Engine Selected: {'Gemini AI Model (gemini-1.5-flash)' if api_key else 'Rule-Based Scoring Engine'}")

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"{CLASSIFY_PROMPT}\n\n{clean_text}"
            response = model.generate_content(prompt)
            
            # Extract JSON block
            resp_text = response.text.strip()
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0].strip()
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1].split('```')[0].strip()
                
            data = json.loads(resp_text)
            crime_type = data.get('crime_type', 'Other')
            if crime_type not in CATEGORIES:
                crime_type = 'Other'
                
            risk_info = calculate_risk_score(crime_type, clean_text)
            
            print(f"[GEMINI CLASSIFICATION SUCCESS] Crime Type: {crime_type}, Confidence: {data.get('confidence', 0.90)}")
            return {
                'crime_type': crime_type,
                'confidence': float(data.get('confidence', 0.90)),
                'risk_level': risk_info['level'],
                'risk_score': risk_info['score'],
                'summary': data.get('summary', f'Classified incident as {crime_type}.'),
                'source': 'Gemini AI'
            }
        except Exception as e:
            print(f"[GEMINI CLASSIFICATION EXCEPTION] {str(e)} -> Falling back to Rule-Based Engine.")
            pass

    return classify_by_rules(clean_text)

def enhance_description(raw_description: str, language: str = 'en') -> dict:
    """Polishes informal/regional descriptions into formal structured legal drafts."""
    clean_text = redact_pii(raw_description)
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"{ENHANCE_PROMPT}\n\nSelected Language Context: {language}\n\n{clean_text}"
            response = model.generate_content(prompt)
            
            resp_text = response.text.strip()
            if '```json' in resp_text:
                resp_text = resp_text.split('```json')[1].split('```')[0].strip()
            elif '```' in resp_text:
                resp_text = resp_text.split('```')[1].split('```')[0].strip()
                
            data = json.loads(resp_text)
            return {
                'formal_description': data.get('formal_description', clean_text),
                'key_facts': data.get('key_facts', []),
                'source': 'Gemini AI'
            }
        except Exception:
            pass

    # Rule-based structured enhancer fallback
    classification = classify_by_rules(clean_text)
    structured_draft = (
        f"COMPLAINT REGARDING INCIDENT OF {classification['crime_type'].upper()}:\n\n"
        f"1. INCIDENT NARRATIVE: The complainant reports a cyber offense wherein the perpetrator "
        f"orchestrated deceptive practices resulting in unauthorized compromise.\n\n"
        f"2. COMPLAINANT STATEMENT: \"{clean_text}\"\n\n"
        f"3. PRELIMINARY TRIAGE: Evaluated as {classification['crime_type']} ({classification['risk_level']} Risk). "
        f"Immediate legal and investigative assistance requested under the IT Act 2000."
    )
    
    return {
        'formal_description': structured_draft,
        'key_facts': [
            f"Crime Type: {classification['crime_type']}",
            f"Evaluated Risk Level: {classification['risk_level']}",
            "Preliminary citizen statement recorded and scrubbed of private credentials."
        ],
        'source': 'Rule-Based Synthesizer'
    }

