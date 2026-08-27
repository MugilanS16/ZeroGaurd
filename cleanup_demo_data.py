import os
from pathlib import Path
from app import create_app
from database import db
from database.models import User, Complaint, AdminNote, LoginHistory

DEMO_EMAILS = [
    'citizen@zeroguard.ai',
    'admin@cybercell.gov.in',
    'rahul.google.demo@gmail.com',
    'citizen.digilocker@gov.in',
    'citizen@cybercrime.gov.in',
    'google.user@cybercrime.gov.in',
    'digilocker.user@cybercrime.gov.in',
    'google.user@gmail.com',
    'digilocker.user@gov.in'
]

DEMO_REFS = [
    'CC-2026-10492',
    'CC-2026-10493',
    'CC-2026-10488',
    'CC-2026-10501'
]

def cleanup_database():
    """Deletes all dummy, seed, and demo data from the database."""
    app = create_app('development')
    with app.app_context():
        print("=" * 60)
        print("ZeroGuard AI - Database Cleanup Operation")
        print("=" * 60)

        # 1. Find demo users
        demo_users = User.query.filter(User.email.in_(DEMO_EMAILS)).all()
        demo_user_ids = [u.id for u in demo_users]
        print(f"[*] Found {len(demo_users)} demo user account(s): {[u.email for u in demo_users]}")

        # 2. Find demo complaints
        demo_complaints = Complaint.query.filter(
            (Complaint.user_id.in_(demo_user_ids)) | (Complaint.reference_number.in_(DEMO_REFS))
        ).all()
        demo_complaint_ids = [c.id for c in demo_complaints]
        demo_pdf_names = [c.pdf_filename for c in demo_complaints if c.pdf_filename]
        print(f"[*] Found {len(demo_complaints)} demo complaint(s): {[c.reference_number for c in demo_complaints]}")

        # 3. Delete AdminNotes tied to demo complaints or demo admins
        deleted_notes = 0
        if demo_complaint_ids or demo_user_ids:
            notes_to_del = AdminNote.query.filter(
                (AdminNote.complaint_id.in_(demo_complaint_ids)) | (AdminNote.admin_id.in_(demo_user_ids))
            ).all()
            deleted_notes = len(notes_to_del)
            for note in notes_to_del:
                db.session.delete(note)

        # 4. Delete LoginHistory tied to demo users or demo emails
        logs_to_del = LoginHistory.query.filter(
            (LoginHistory.user_id.in_(demo_user_ids)) | (LoginHistory.email_attempted.in_(DEMO_EMAILS))
        ).all()
        deleted_logs = len(logs_to_del)
        for log in logs_to_del:
            db.session.delete(log)

        # 5. Delete demo complaints
        deleted_complaints = len(demo_complaints)
        for c in demo_complaints:
            db.session.delete(c)

        # 6. Delete demo users
        deleted_users = len(demo_users)
        for u in demo_users:
            db.session.delete(u)

        db.session.commit()

        # 7. Clean up demo PDF files from disk
        pdf_dir = Path(app.root_path) / 'static' / 'generated_pdfs'
        deleted_pdfs = 0
        for pdf_name in demo_pdf_names:
            pdf_file = pdf_dir / pdf_name
            if pdf_file.exists():
                try:
                    pdf_file.unlink()
                    deleted_pdfs += 1
                except Exception as e:
                    print(f"  [!] Could not delete {pdf_file}: {e}")

        # Final Summary
        print("\n" + "-" * 60)
        print("CLEANUP SUMMARY:")
        print(f"  - Users Deleted:        {deleted_users}")
        print(f"  - Complaints Deleted:   {deleted_complaints}")
        print(f"  - Admin Notes Deleted:  {deleted_notes}")
        print(f"  - Login Logs Deleted:   {deleted_logs}")
        print(f"  - Demo PDFs Removed:    {deleted_pdfs}")
        print("-" * 60)

        # Print remaining counts
        print("\nCURRENT LIVE DATABASE ROW COUNTS:")
        print(f"  - users:        {User.query.count()}")
        print(f"  - complaints:   {Complaint.query.count()}")
        print(f"  - admin_notes:  {AdminNote.query.count()}")
        print(f"  - login_history:{LoginHistory.query.count()}")
        print("=" * 60 + "\n")

if __name__ == '__main__':
    cleanup_database()
