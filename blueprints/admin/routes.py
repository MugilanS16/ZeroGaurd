from datetime import datetime, timedelta, timezone
from collections import Counter
from flask import render_template, request, redirect, url_for, flash, jsonify, session, abort
from blueprints.admin import admin_bp
from blueprints.auth.routes import admin_required
from database import db
from database.models import User, Complaint, AdminNote
from utils.mailer import send_status_update_notification

@admin_bp.route('/')
@admin_required
def dashboard():
    """Cyber-Cell incident intelligence dashboard with KPI metrics and complaints table."""
    current_admin = User.query.get(session['user_id'])
    
    # Filter parameters
    status_filter = request.args.get('status', '').strip()
    risk_filter = request.args.get('risk', '').strip()
    crime_filter = request.args.get('crime_type', '').strip()
    search_query = request.args.get('q', '').strip()

    query = Complaint.query

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if risk_filter:
        query = query.filter(Complaint.risk_level == risk_filter)
    if crime_filter:
        query = query.filter(Complaint.crime_type == crime_filter)
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Complaint.reference_number.ilike(search_pattern)) |
            (Complaint.description.ilike(search_pattern)) |
            (Complaint.crime_type.ilike(search_pattern))
        )

    # Priority Sorting: Critical/High Risk first, then newest
    complaints = query.order_by(Complaint.risk_score.desc(), Complaint.created_at.desc()).all()

    # KPI Metrics across ALL complaints
    all_complaints = Complaint.query.all()
    total_count = len(all_complaints)
    critical_count = sum(1 for c in all_complaints if c.risk_level in ['Critical', 'High'])
    pending_count = sum(1 for c in all_complaints if c.status == 'Pending')
    in_review_count = sum(1 for c in all_complaints if c.status in ['In Review', 'In_Review'])
    resolved_count = sum(1 for c in all_complaints if c.status == 'Resolved')

    # Categories list for filter dropdown
    all_categories = sorted(list(set(c.crime_type for c in all_complaints if c.crime_type)))

    # Aggregations for Chart.js
    category_counts = Counter(c.crime_type for c in all_complaints)
    status_counts = Counter(c.status for c in all_complaints)
    risk_counts = Counter(c.risk_level for c in all_complaints)

    # 7-day trend
    today = datetime.now().date()
    date_labels = [(today - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]
    date_counts = {lbl: 0 for lbl in date_labels}

    for c in all_complaints:
        if c.created_at:
            lbl = c.created_at.strftime('%d %b')
            if lbl in date_counts:
                date_counts[lbl] += 1

    chart_data = {
        'categories': {
            'labels': list(category_counts.keys()),
            'data': list(category_counts.values())
        },
        'statuses': {
            'labels': ['Pending', 'In Review', 'Resolved'],
            'data': [status_counts.get('Pending', 0), status_counts.get('In Review', 0) + status_counts.get('In_Review', 0), status_counts.get('Resolved', 0)]
        },
        'risks': {
            'labels': ['Critical', 'High', 'Medium', 'Low'],
            'data': [risk_counts.get('Critical', 0), risk_counts.get('High', 0), risk_counts.get('Medium', 0), risk_counts.get('Low', 0)]
        },
        'trends': {
            'labels': date_labels,
            'data': [date_counts[lbl] for lbl in date_labels]
        }
    }

    return render_template(
        'admin/dashboard.html',
        complaints=complaints,
        total_count=total_count,
        critical_count=critical_count,
        pending_count=pending_count,
        in_review_count=in_review_count,
        resolved_count=resolved_count,
        all_categories=all_categories,
        status_filter=status_filter,
        risk_filter=risk_filter,
        crime_filter=crime_filter,
        search_query=search_query,
        chart_data=chart_data,
        current_admin=current_admin
    )

@admin_bp.route('/complaint/<int:complaint_id>')
@admin_required
def complaint_detail(complaint_id):
    """Detailed view for investigating, auditing, and acting upon a complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    notes = complaint.admin_notes.all()
    return render_template('admin/complaint_detail.html', complaint=complaint, notes=notes)

@admin_bp.route('/complaint/<int:complaint_id>/update-status', methods=['POST'])
@admin_required
def update_complaint_status(complaint_id):
    """Updates complaint status, logs case note, and notifies citizen."""
    complaint = Complaint.query.get_or_404(complaint_id)
    admin_user = User.query.get(session['user_id'])
    
    new_status = request.form.get('status', complaint.status).strip()
    note_text = request.form.get('note', '').strip()
    notify_citizen = request.form.get('notify_citizen', 'false') == 'true'

    if not note_text:
        flash('Please provide an internal case note or investigation log reason.', 'warning')
        return redirect(url_for('admin.complaint_detail', complaint_id=complaint.id))

    prev_status = complaint.status
    complaint.status = new_status
    complaint.updated_at = datetime.now(timezone.utc)

    # Create admin note audit record
    admin_note = AdminNote(
        complaint_id=complaint.id,
        admin_id=admin_user.id,
        note=note_text,
        previous_status=prev_status,
        new_status=new_status,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(admin_note)
    db.session.commit()

    # Dispatch email update if requested or status changed
    recipient_email = complaint.user.email if complaint.user else None
    if recipient_email and notify_citizen:
        send_status_update_notification(
            recipient_email=recipient_email,
            user_name=complaint.user.fullname if complaint.user else 'Citizen',
            ref_number=complaint.reference_number,
            new_status=new_status,
            prev_status=prev_status,
            officer_note=note_text
        )
        flash(f'Status updated to "{new_status}" and citizen was notified via email.', 'success')
    else:
        flash(f'Case status updated to "{new_status}" successfully.', 'success')

    return redirect(url_for('admin.complaint_detail', complaint_id=complaint.id))

@admin_bp.route('/api/analytics')
@admin_required
def api_analytics():
    """Returns real-time analytics JSON for AJAX charts."""
    complaints = Complaint.query.all()
    category_counts = Counter(c.crime_type for c in complaints)
    status_counts = Counter(c.status for c in complaints)
    risk_counts = Counter(c.risk_level for c in complaints)

    return jsonify({
        'total': len(complaints),
        'categories': category_counts,
        'statuses': status_counts,
        'risks': risk_counts
    })
