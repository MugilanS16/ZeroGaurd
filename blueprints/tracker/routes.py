from flask import render_template, request, flash, redirect, url_for
from blueprints.tracker import tracker_bp
from database.models import Complaint, AdminNote, User

@tracker_bp.route('/track', methods=['GET', 'POST'])
def track():
    """Public complaint tracker accessible without authentication."""
    complaint = None
    latest_note = None
    step_index = 1
    
    # Check GET query params (e.g. from success page or email link) or POST form
    ref_number = request.values.get('ref', '').strip()
    email = request.values.get('email', '').lower().strip()

    if ref_number:
        c = Complaint.query.filter(Complaint.reference_number.ilike(ref_number)).first()
        
        if not c:
            flash(f'No complaint found with reference number "{ref_number}". Please check the code format (e.g. CC-2026-XXXXX).', 'danger')
        else:
            # If email was supplied, verify matching
            complaint_email = (c.user.email if c.user else '').lower()
            
            # Allow viewing if email matches OR if user is logged in as owner OR for quick demo lookup
            if email and complaint_email and email != complaint_email:
                flash('The provided email does not match the registered email for this complaint.', 'danger')
            else:
                complaint = c
                latest_note = c.admin_notes.first() # most recent admin note
                
                # Compute timeline step index (1: Submitted, 2: In Review, 3: Resolved)
                status_lower = c.status.lower()
                if status_lower == 'resolved':
                    step_index = 3
                elif status_lower in ('in review', 'in_review'):
                    step_index = 2
                else:
                    step_index = 1

    return render_template(
        'tracker.html',
        complaint=complaint,
        latest_note=latest_note,
        step_index=step_index,
        ref_number=ref_number,
        email=email
    )
