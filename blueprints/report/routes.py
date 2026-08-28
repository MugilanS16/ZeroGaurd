import os
import random
from pathlib import Path
from datetime import datetime, timezone
from flask import (
    render_template, request, session, redirect, url_for, flash, jsonify, send_file, current_app, abort
)
from blueprints.report import report_bp
from blueprints.auth.routes import login_required
from database import db
from database.models import Complaint, User
from ai.classifier import classify_incident, enhance_description
from ai.questions import generate_questions
from ai.guidance import generate_guidance
from ai.redact import redact_pii
from ai.risk_scorer import calculate_risk_score
from ai.translator import get_translation, SUPPORTED_LANGUAGES
from ai.evidence_validator import verify_amount_match
from utils.upload import save_evidence_file, purge_evidence_files, get_upload_dir
from utils.validator import is_allowed_file, validate_incident_text
from utils.mailer import send_submission_notification
from pdf.report_generator import generate_complaint_pdf

def get_draft():
    """Retrieves or initializes wizard draft in session."""
    if 'report_draft' not in session:
        session['report_draft'] = {
            'language': 'en',
            'raw_description': '',
            'formal_description': '',
            'crime_type': 'Banking Fraud',
            'risk_level': 'Medium',
            'risk_score': 50,
            'answers': {},
            'guidance': [],
            'evidence_meta': []
        }
    return session['report_draft']

@report_bp.route('/')
def home():
    """Home landing page (Public)."""
    return render_template('index.html')

# =====================================================================
# REAL-TIME AI APIS (Debounced / Interactive)
# =====================================================================
@report_bp.route('/api/ai-quick-classify', methods=['POST'])
@login_required
def api_quick_classify():
    """Real-time live classification endpoint called as the user types."""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    
    if len(text) < 12:
        return jsonify({
            'crime_type': 'Pending Input...',
            'confidence': 0.0,
            'risk_level': 'Low',
            'risk_score': 20,
            'summary': 'Please type more details to trigger AI classification.'
        })

    result = classify_incident(text)
    return jsonify(result)

@report_bp.route('/api/ai-enhance-report', methods=['POST'])
@login_required
def api_enhance_report():
    """AI Polish endpoint: structures & formalizes informal / regional text."""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    language = data.get('language', 'en')

    if len(text) < 15:
        return jsonify({'error': 'Please provide a more detailed incident description before polishing.'}), 400

    result = enhance_description(text, language=language)
    return jsonify(result)

# =====================================================================
# 5-STEP GUIDED WIZARD ROUTES
# =====================================================================

@report_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report_step1():
    """Step 1: Incident Description & Language Selection."""
    draft = get_draft()

    if request.method == 'POST':
        language = request.form.get('language', 'en')
        raw_description = request.form.get('raw_description', '').strip()
        formal_description = request.form.get('formal_description', '').strip()

        is_valid, err_msg = validate_incident_text(raw_description)
        if not is_valid:
            flash(err_msg, 'danger')
            return render_template('report/step1_report.html', draft=draft, languages=SUPPORTED_LANGUAGES)

        # Classify incident
        classification = classify_incident(raw_description)

        # Update draft
        draft['language'] = language
        draft['raw_description'] = raw_description
        draft['formal_description'] = formal_description if formal_description else raw_description
        draft['crime_type'] = classification['crime_type']
        draft['risk_level'] = classification['risk_level']
        draft['risk_score'] = classification['risk_score']
        session['report_draft'] = draft
        session.modified = True

        return redirect(url_for('report.report_step2'))

    return render_template('report/step1_report.html', draft=draft, languages=SUPPORTED_LANGUAGES)

@report_bp.route('/report/step2', methods=['GET', 'POST'])
@login_required
def report_step2():
    """Step 2: Dynamic Category-Specific Follow-Up Questions."""
    draft = get_draft()
    if not draft.get('raw_description'):
        flash('Please describe your incident first.', 'warning')
        return redirect(url_for('report.report_step1'))

    crime_type = draft.get('crime_type', 'Banking Fraud')
    questions = generate_questions(crime_type, draft.get('raw_description', ''))

    if request.method == 'POST':
        answers = {}
        # Collect all form fields submitted in request.form
        for key, val in request.form.items():
            if key != 'csrf_token' and val and isinstance(val, str) and val.strip():
                answers[key] = redact_pii(val.strip())

        # Also process specific questions if present
        for q in questions:
            qid = q.get('id', '')
            val = request.form.get(qid, '').strip()
            if val:
                answers[qid] = redact_pii(val)
        
        draft['answers'] = answers
        session['report_draft'] = draft
        session.modified = True
        return redirect(url_for('report.report_step3'))


    return render_template('report/step2_questions.html', draft=draft, questions=questions)

from ai.evidence_validator import verify_amount_match
from ai.evidence_relevance_checker import check_evidence_relevance

@report_bp.route('/report/step3', methods=['GET', 'POST'])
@login_required
def report_step3():
    """Step 3: Immediate Guidance Checklist & Evidence Upload with OCR Amount & Content Relevance Verification."""
    draft = get_draft()
    if not draft.get('raw_description'):
        return redirect(url_for('report.report_step1'))

    crime_type = draft.get('crime_type', 'Banking Fraud')
    guidance_steps = generate_guidance(crime_type, draft.get('raw_description', ''))

    amount_warning = False
    relevance_warning = False
    verification_result = draft.get('amount_verification')
    relevance_result = draft.get('evidence_relevance')

    if request.method == 'POST':
        # Handle uploaded evidence files
        uploaded_files = request.files.getlist('evidence_files')
        categories = request.form.getlist('evidence_categories')

        existing_meta = draft.get('evidence_meta', [])

        for idx, f in enumerate(uploaded_files):
            if f and f.filename and is_allowed_file(f.filename):
                cat = categories[idx] if idx < len(categories) else 'Screenshot'
                saved_meta = save_evidence_file(f, category=cat)
                if saved_meta:
                    existing_meta.append(saved_meta)

        draft['guidance'] = guidance_steps
        draft['evidence_meta'] = existing_meta

        # Run OCR Evidence Amount & Relevance Verifications
        upload_dir = get_upload_dir()
        image_paths = [
            str(upload_dir / item['saved_filename'])
            for item in existing_meta
            if isinstance(item, dict) and item.get('extension') in {'png', 'jpg', 'jpeg', 'webp'}
        ]

        answers = draft.get('answers', {})
        full_claim_text = f"{draft.get('raw_description', '')} {draft.get('formal_description', '')}"

        # 1. Amount Verification Check
        verification_result = verify_amount_match(full_claim_text, image_paths, answers_dict=answers)
        
        # 2. Content & Semantic Relevance Check
        relevance_result = check_evidence_relevance(
            description_text=full_claim_text,
            crime_type=draft.get('crime_type', 'General Cybercrime'),
            evidence_image_paths=image_paths,
            answers_dict=answers
        )

        manual_override = request.form.get('manual_override') == 'true'

        # Process Amount Check Status
        if verification_result['status'] == 'mismatch':
            if manual_override:
                verification_result['status'] = 'manual_review_needed'
                verification_result['message'] = 'Amount mismatch flagged for manual Cyber-Cell review via citizen override.'
            else:
                amount_warning = True

        # Process Relevance Check Status
        if relevance_result['status'] == 'unverified':
            if manual_override:
                relevance_result['status'] = 'manual_review_needed'
                relevance_result['message'] = 'Evidence relevance flagged for manual Cyber-Cell review via citizen override.'
            else:
                relevance_warning = True

        draft['amount_verification'] = verification_result
        draft['evidence_relevance'] = relevance_result
        session['report_draft'] = draft
        session.modified = True

        # If either check is actively failing without override, block and warn on Step 3
        if amount_warning or relevance_warning:
            if amount_warning:
                flash(verification_result['message'], 'danger')
            if relevance_warning:
                flash(relevance_result['message'], 'danger')
            return render_template(
                'report/step3_guidance.html', 
                draft=draft, 
                guidance_steps=guidance_steps, 
                amount_warning=amount_warning, 
                relevance_warning=relevance_warning,
                verification_result=verification_result,
                relevance_result=relevance_result
            )

        return redirect(url_for('report.report_step4'))

    return render_template(
        'report/step3_guidance.html', 
        draft=draft, 
        guidance_steps=guidance_steps, 
        amount_warning=amount_warning, 
        relevance_warning=relevance_warning,
        verification_result=verification_result,
        relevance_result=relevance_result
    )

@report_bp.route('/report/step4', methods=['GET', 'POST'])
@login_required
def report_step4():
    """Step 4: Complaint Review & Verification."""
    draft = get_draft()
    if not draft.get('raw_description'):
        return redirect(url_for('report.report_step1'))

    # Hard backend block: if evidence amount mismatch or unverified evidence is active without override
    if draft.get('amount_verification', {}).get('status') == 'mismatch':
        flash('⚠️ Evidence amount mismatch detected. You must upload valid evidence or use manual review before proceeding.', 'danger')
        return redirect(url_for('report.report_step3'))

    if draft.get('evidence_relevance', {}).get('status') == 'unverified':
        flash('⚠️ Unverified evidence detected. You must upload evidence that relates to your complaint or flag for manual review before proceeding.', 'danger')
        return redirect(url_for('report.report_step3'))

    # Prepare redacted preview
    redacted_preview = redact_pii(draft.get('formal_description') or draft.get('raw_description'))

    return render_template('report/step4_preview.html', draft=draft, redacted_preview=redacted_preview)

@report_bp.route('/report/submit', methods=['POST'])
@login_required
def report_submit():
    """Step 5: Final Submission, PDF generation, Evidence purge, and Notification."""
    draft = get_draft()
    if not draft.get('raw_description'):
        flash('Session expired or empty complaint draft.', 'warning')
        return redirect(url_for('report.report_step1'))

    # Re-evaluate verification_result if missing or N/A
    answers = draft.get('answers', {})
    existing_meta = draft.get('evidence_meta', [])
    upload_dir = get_upload_dir()
    image_paths = [
        str(upload_dir / item['saved_filename'])
        for item in existing_meta
        if isinstance(item, dict) and item.get('extension') in {'png', 'jpg', 'jpeg', 'webp'}
    ]

    amount_verif = draft.get('amount_verification')
    if not amount_verif or amount_verif.get('status') == 'not_applicable':
        amount_verif = verify_amount_match(draft.get('raw_description', ''), image_paths, answers_dict=answers)
        draft['amount_verification'] = amount_verif

    relevance_verif = draft.get('evidence_relevance')
    if not relevance_verif or relevance_verif.get('status') in ('not_applicable', 'inconclusive'):
        relevance_verif = check_evidence_relevance(
            draft.get('raw_description', ''), 
            crime_type=draft.get('crime_type', 'General Cybercrime'), 
            evidence_image_paths=image_paths, 
            answers_dict=answers
        )
        draft['evidence_relevance'] = relevance_verif

    # Hard backend block: reject submission if amount or relevance status is blocked
    if amount_verif.get('status') == 'mismatch':
        flash('⚠️ Submission blocked due to unverified evidence amount mismatch.', 'danger')
        return redirect(url_for('report.report_step3'))

    if relevance_verif.get('status') == 'unverified':
        flash('⚠️ Submission blocked due to unverified unrelated evidence without manual review override.', 'danger')
        return redirect(url_for('report.report_step3'))

    # Generate unique complaint reference: CC-YYYY-NNNNN
    year = datetime.now().year
    rand_num = random.randint(10000, 99999)
    ref_number = f"CC-{year}-{rand_num}"

    # Ensure uniqueness
    while Complaint.query.filter_by(reference_number=ref_number).first():
        rand_num = random.randint(10000, 99999)
        ref_number = f"CC-{year}-{rand_num}"

    # Current user details if logged in
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    # Finalize descriptions
    final_desc = draft.get('formal_description') or draft.get('raw_description')

    # Amount verification status formatting for DB
    claimed_amt = amount_verif.get('claimed_amounts', [None])[0] if amount_verif.get('claimed_amounts') else None
    verif_status_raw = amount_verif.get('status', 'not_applicable')

    if verif_status_raw == 'verified':
        verif_status = 'Verified'
    elif verif_status_raw == 'mismatch':
        verif_status = 'Mismatch'
    elif verif_status_raw == 'manual_review_needed':
        verif_status = 'Manual Review Needed'
    else:
        verif_status = 'N/A'

    # Evidence relevance status formatting for DB
    relevance_status_raw = relevance_verif.get('status', 'inconclusive')
    if relevance_status_raw == 'verified':
        rel_status = 'Verified'
    elif relevance_status_raw == 'unverified':
        rel_status = 'Unverified'
    elif relevance_status_raw == 'manual_review_needed':
        rel_status = 'Manual Review Needed'
    else:
        rel_status = 'Inconclusive'
    
    # Save complaint to database
    complaint = Complaint(
        user_id=user.id if user else None,
        reference_number=ref_number,
        crime_type=draft.get('crime_type', 'Banking Fraud'),
        risk_level=draft.get('risk_level', 'Medium'),
        risk_score=draft.get('risk_score', 50),
        language=draft.get('language', 'en'),
        description=final_desc,
        original_description=draft.get('raw_description'),
        answers=draft.get('answers', {}),
        guidance=draft.get('guidance', []),
        evidence_meta=draft.get('evidence_meta', []),
        claimed_amount=claimed_amt,
        amount_verification_status=verif_status,
        amount_verification_details=amount_verif,
        evidence_relevance_status=rel_status,
        evidence_relevance_details=relevance_verif,
        pdf_filename=f"{ref_number}.pdf",
        status='Pending',
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(complaint)
    db.session.commit()

    # Generate ReportLab PDF
    pdf_dir = Path(current_app.root_path) / 'static' / 'generated_pdfs'
    pdf_path = str(pdf_dir / f"{ref_number}.pdf")
    
    complaint_data = {
        'reference_number': ref_number,
        'crime_type': complaint.crime_type,
        'risk_level': complaint.risk_level,
        'created_at_str': datetime.now().strftime('%d %B %Y, %I:%M %p'),
        'user_name': user.fullname if user else 'Anonymous Citizen',
        'user_email': user.email if user else 'Not Provided',
        'user_phone': user.phone if user else 'Not Provided',
        'description': complaint.description,
        'answers': complaint.answers,
        'guidance': complaint.guidance,
        'evidence_meta': complaint.evidence_meta,
        'claimed_amount': complaint.claimed_amount,
        'amount_verification_status': complaint.amount_verification_status,
        'amount_verification_details': complaint.amount_verification_details
    }
    
    try:
        generate_complaint_pdf(complaint_data, pdf_path)
    except Exception as e:
        current_app.logger.error(f"Error compiling complaint PDF: {e}")

    # Privacy-by-Design: Auto-purge temporary uploaded evidence files from disk
    purged_count = purge_evidence_files(draft.get('evidence_meta', []))
    current_app.logger.info(f"Auto-purged {purged_count} temporary evidence files for {ref_number}")

    # Send confirmation email
    recipient_email = user.email if user else request.form.get('guest_email')
    if recipient_email:
        send_submission_notification(
            recipient_email=recipient_email,
            user_name=user.fullname if user else 'Citizen',
            ref_number=ref_number,
            crime_type=complaint.crime_type,
            risk_level=complaint.risk_level,
            pdf_path=pdf_path
        )

    # Clear draft from session
    session.pop('report_draft', None)

    return render_template('report/step5_success.html', complaint=complaint, ref_number=ref_number)

@report_bp.route('/download-pdf/<reference_number>')
@report_bp.route('/report/download-pdf/<reference_number>')
@login_required
def download_pdf(reference_number):
    """Allows downloading the official complaint PDF."""
    pdf_path = Path(current_app.root_path) / 'static' / 'generated_pdfs' / f"{reference_number}.pdf"
    if not pdf_path.exists():
        # Check if complaint exists in DB and rebuild if necessary
        complaint = Complaint.query.filter_by(reference_number=reference_number).first()
        if not complaint:
            abort(404)
        complaint_data = {
            'reference_number': complaint.reference_number,
            'crime_type': complaint.crime_type,
            'risk_level': complaint.risk_level,
            'created_at_str': complaint.created_at.strftime('%d %B %Y, %I:%M %p') if complaint.created_at else '',
            'user_name': complaint.user.fullname if complaint.user else 'Anonymous Citizen',
            'user_email': complaint.user.email if complaint.user else 'Not Provided',
            'user_phone': complaint.user.phone if complaint.user else 'Not Provided',
            'description': complaint.description,
            'answers': complaint.answers,
            'guidance': complaint.guidance,
            'evidence_meta': complaint.evidence_meta,
            'claimed_amount': complaint.claimed_amount,
            'amount_verification_status': complaint.amount_verification_status,
            'amount_verification_details': complaint.amount_verification_details
        }
        generate_complaint_pdf(complaint_data, str(pdf_path))

    return send_file(pdf_path, as_attachment=True, download_name=f"{reference_number}_Complaint.pdf")

