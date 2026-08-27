from flask import render_template, session, redirect, url_for, request
from blueprints.dashboard import dashboard_bp
from blueprints.auth.routes import login_required
from database.models import User, Complaint

@dashboard_bp.route('/')
@login_required
def index():
    """Citizen dashboard displaying complaint history, status summaries, and PDF downloads."""
    user = User.query.get(session['user_id'])
    
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))

    # Citizen's complaints
    status_filter = request.args.get('status', '').strip()
    
    query = Complaint.query.filter_by(user_id=user.id)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
        
    complaints = query.order_by(Complaint.created_at.desc()).all()

    # Metric counts
    all_user_complaints = Complaint.query.filter_by(user_id=user.id).all()
    total_count = len(all_user_complaints)
    pending_count = sum(1 for c in all_user_complaints if c.status == 'Pending')
    in_review_count = sum(1 for c in all_user_complaints if c.status in ['In Review', 'In_Review'])
    resolved_count = sum(1 for c in all_user_complaints if c.status == 'Resolved')

    return render_template(
        'dashboard/index.html',
        user=user,
        complaints=complaints,
        total_count=total_count,
        pending_count=pending_count,
        in_review_count=in_review_count,
        resolved_count=resolved_count,
        status_filter=status_filter
    )
