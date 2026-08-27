import os
import re
import json
from flask import render_template, request, jsonify, session, current_app
from blueprints.chatbot import chatbot_bp
from ai.redact import redact_pii
from ai.classifier import classify_by_rules
from ai.prompts import CHATBOT_SYSTEM_PROMPT

# Detailed rule-based knowledge fallback responses
TOPIC_KNOWLEDGE_FALLBACK = [
    {
        'patterns': [r'\b1930\b', r'helpline', r'golden hour', r'emergency number'],
        'response': """<strong>National Cybercrime Emergency Helpline 1930:</strong><br/>
• <strong>What it does:</strong> Connects citizens directly to the Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS).<br/>
• <strong>The Golden Hour (First 2-3 Hours):</strong> If you report unauthorized financial fraud within 2-3 hours of occurrence, nodal officers can immediately flag and freeze the stolen funds before the fraudster withdraws them at an ATM or transfers to mule accounts.<br/>
• <strong>What to have ready:</strong> Your bank account number, debit card last 4 digits, suspect UPI ID/account, and transaction SMS with UTR reference number.""",
        'suggestions': ['How to report UPI fraud?', 'What is RBI Zero Liability policy?', 'File a complaint now']
    },
    {
        'patterns': [r'upi', r'gpay', r'phonepe', r'paytm', r'qr code', r'cashback'],
        'response': """<strong>Immediate Steps for UPI & QR Code Fraud:</strong><br/>
1. <strong>Do NOT enter PIN for receiving money:</strong> UPI PIN is ONLY required to send/transfer money, NEVER to receive cashback or refunds.<br/>
2. <strong>Call 1930 Immediately:</strong> Report the 12-digit UTR/RRN number.<br/>
3. <strong>Raise Dispute in App:</strong> Open GPay/PhonePe/Paytm &rarr; Transaction History &rarr; "Have an issue with this transaction" &rarr; Raise fraud dispute.<br/>
4. <strong>Change UPI PIN:</strong> Reset your UPI PIN across all bank accounts immediately to prevent unauthorized collect requests.""",
        'suggestions': ['What is 1930 helpline?', 'How do I attach evidence?', 'File an official report']
    },
    {
        'patterns': [r'sextort', r'nude', r'video call', r'blackmail', r'morph', r'intimate'],
        'response': """<strong>Urgent Guidance for Sextortion & Blackmail:</strong><br/>
1. <strong>DO NOT SEND MONEY:</strong> Paying extortionists will NEVER make them delete the video; it only invites higher extortion demands.<br/>
2. <strong>Do NOT delete chats immediately:</strong> Take uncropped screenshots of threatening chats, the fraudster's phone number, UPI QR, and profile handles.<br/>
3. <strong>Lock your Social Profiles:</strong> Make your Instagram, Facebook, and LinkedIn private. Restrict direct messages.<br/>
4. <strong>Use StopNCII.org:</strong> StopNCII generates a non-reversible cryptographic hash of intimate media to block upload across Facebook, Instagram, TikTok, and OnlyFans.<br/>
5. <strong>Legal Protection:</strong> This is an offense under Section 67A (IT Act) & Section 384 (IPC/BNS Extortion). File a complaint through our 5-Step Wizard.""",
        'suggestions': ['File Sextortion Complaint', 'What evidence is needed?', 'Talk to an officer']
    },
    {
        'patterns': [r'rbi', r'zero liability', r'bank dispute', r'refund from bank', r'time limit'],
        'response': """<strong>RBI Zero Liability Policy (Circular DBR.No.Leg.BC.78/09.07.005/2017-18):</strong><br/>
• <strong>Within 3 Working Days:</strong> If unauthorized transaction occurs due to third-party breach and you notify your bank within 3 working days, you have <strong>ZERO customer liability</strong>.<br/>
• <strong>Between 4 to 7 Working Days:</strong> Customer liability is capped at maximum Rs 10,000 (for savings accounts) or Rs 25,000 (for credit cards with limit > Rs 5 lakh).<br/>
• <strong>After 7 Days:</strong> As per bank's board-approved policy.<br/>
<em>Always obtain a formal dispute acknowledgment ticket from your bank branch!</em>""",
        'suggestions': ['How to file bank fraud complaint', 'Explain Step 3', 'Helpline 1930']
    },
    {
        'patterns': [r'step 1', r'step 2', r'step 3', r'step 4', r'step 5', r'how to file', r'wizard'],
        'response': """<strong>ZeroGuard AI 5-Step Complaint Filing Process:</strong><br/>
• <strong>Step 1 (Incident Narrative):</strong> Type your incident in English, Hindi, Tamil, or Telugu. Our AI provides live risk triage and polishes your text.<br/>
• <strong>Step 2 (Follow-up Questions):</strong> Answer dynamic crime-specific questions (UTR, suspect handles, amounts).<br/>
• <strong>Step 3 (Safety Guidance & Evidence):</strong> Review immediate containment checklist and attach optional screenshots.<br/>
• <strong>Step 4 (Preview):</strong> Review the PII-scrubbed complaint summary.<br/>
• <strong>Step 5 (Submission & PDF):</strong> Generates an official ReportLab PDF complaint with reference code (<code>CC-YYYY-NNNNN</code>). Evidence files are auto-purged from the server for privacy.""",
        'suggestions': ['Start Filing Complaint', 'Track My Complaint', 'Check Crime Categories']
    },
    {
        'patterns': [r'anydesk', r'teamviewer', r'rustdesk', r'quicksupport', r'customer care scam'],
        'response': """<strong>Fake Customer Care & Remote App Alert:</strong><br/>
1. <strong>Disconnect Internet & Uninstall:</strong> Disconnect Wi-Fi/mobile data and uninstall AnyDesk / TeamViewer / RustDesk immediately.<br/>
2. <strong>Check Banking:</strong> Fraudsters use screen sharing to view your OTPs and netbanking passwords. Call your bank immediately to block netbanking.<br/>
3. <strong>Official Helplines:</strong> Real customer care teams never ask you to download remote access apps to process refunds!""",
        'suggestions': ['Freeze Bank Account', 'Call 1930 Helpline', 'File Complaint']
    },
    {
        'patterns': [r'telegram', r'job scam', r'part time job', r'youtube like', r'rating task'],
        'response': """<strong>Part-Time Job / Telegram Task Scam:</strong><br/>
• <strong>Modus Operandi:</strong> Fraudsters offer Rs 150-500 for liking YouTube videos or writing Google reviews. They pay small initial amounts to build trust, then demand Rs 10,000+ for "prepaid VIP tasks" and lock withdrawals.<br/>
• <strong>Action:</strong> Stop making any deposits. Export Telegram chat logs and suspect UPI handles, and register a complaint to help Cyber-Cells freeze the beneficiary accounts.""",
        'suggestions': ['File Job Scam Complaint', 'Call 1930', 'What is 1930 helpline?']
    }
]

DEFAULT_FALLBACK_RESPONSE = """I am here to assist you with cybercrime reporting, safety protocols, and evidence preparation. 

Here are some key things I can help you with:
• <strong>Immediate Emergency:</strong> Dial <strong>1930</strong> for financial cyber fraud or <strong>112</strong> for general emergency.
• <strong>File an Official Complaint:</strong> Use our 5-Step AI-assisted wizard to generate a police-ready PDF report.
• <strong>Ask Questions:</strong> Ask about bank dispute time limits, UPI fraud recovery, sextortion guidance, or how to unblock compromised accounts.""",

DEFAULT_SUGGESTIONS = [
    'How do I report UPI fraud?',
    'What should I do for Sextortion blackmail?',
    'What is the 1930 helpline?',
    'How to file an official complaint?'
]

@chatbot_bp.route('/chatbot')
def chatbot_page():
    """Renders the full-page AI cyber assistant interface."""
    return render_template('chatbot/chatbot.html')

@chatbot_bp.route('/api/chat', methods=['POST'])
def api_chat():
    """Handles multi-turn conversational AI queries."""
    data = request.get_json() or {}
    user_msg = data.get('message', '').strip()
    history = data.get('history', []) # list of {role: 'user'|'model', text: str}

    if not user_msg:
        return jsonify({'error': 'Empty message'}), 400

    clean_msg = redact_pii(user_msg)
    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    # Try Gemini Multi-Turn Generation
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Format history (keep last 8 turns)
            recent_history = history[-8:]
            formatted_history = "\n".join([f"{h.get('role', 'user').title()}: {h.get('text', '')}" for h in recent_history])
            
            system_context = CHATBOT_SYSTEM_PROMPT.format(history=formatted_history if formatted_history else 'New conversation started.')
            full_prompt = f"{system_context}\n\nUser: {clean_msg}\nAI Assistant:"
            
            response = model.generate_content(full_prompt)
            reply_text = response.text.strip()
            
            # Quick classification
            rule_eval = classify_by_rules(clean_msg)
            
            return jsonify({
                'response': reply_text.replace('\n', '<br/>'),
                'crime_type': rule_eval['crime_type'],
                'risk_level': rule_eval['risk_level'],
                'suggestions': [
                    f"How to report {rule_eval['crime_type']}?",
                    "What evidence should I save?",
                    "File a formal complaint now"
                ],
                'source': 'Gemini AI'
            })
        except Exception as e:
            current_app.logger.warning(f"Chatbot Gemini API fallback: {e}")

    # Fallback to topic knowledge engine
    msg_lower = clean_msg.lower()
    for topic in TOPIC_KNOWLEDGE_FALLBACK:
        for pattern in topic['patterns']:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                rule_eval = classify_by_rules(clean_msg)
                return jsonify({
                    'response': topic['response'],
                    'crime_type': rule_eval['crime_type'],
                    'risk_level': rule_eval['risk_level'],
                    'suggestions': topic.get('suggestions', DEFAULT_SUGGESTIONS),
                    'source': 'Rule-Based Knowledge Hub'
                })

    rule_eval = classify_by_rules(clean_msg)
    return jsonify({
        'response': f"Regarding your query about <strong>{rule_eval['crime_type']}</strong>:<br/><br/>"
                    f"1. Preserve all electronic records, transaction IDs, and communication screenshots without tampering.<br/>"
                    f"2. If financial loss occurred within the last 2-3 hours, dial <strong>1930</strong> immediately.<br/>"
                    f"3. You can compile an official complaint letter via our 5-Step Guided Wizard.",
        'crime_type': rule_eval['crime_type'],
        'risk_level': rule_eval['risk_level'],
        'suggestions': DEFAULT_SUGGESTIONS,
        'source': 'Rule-Based Knowledge Hub'
    })
