import sys
import getpass
from app import create_app
from database import db
from database.models import User

def create_admin():
    """CLI utility to create a verified administrative account."""
    app = create_app('development')
    with app.app_context():
        print("=" * 60)
        print("ZeroGuard AI — Cyber-Cell Administrator Setup")
        print("=" * 60)
        
        fullname = input("Enter Admin Full Name & Title (e.g. Officer R. K. Varma): ").strip()
        if not fullname:
            print("[!] Error: Full name cannot be empty.")
            return

        email = input("Enter Official Admin Email: ").strip().lower()
        if not email or '@' not in email:
            print("[!] Error: Valid email required.")
            return

        existing = User.query.filter_by(email=email).first()
        if existing:
            if existing.is_admin:
                print(f"[*] Account with email '{email}' already exists and is an admin.")
                return
            else:
                promote = input(f"[*] User '{email}' exists as citizen. Promote to admin? (y/n): ").strip().lower()
                if promote in ('y', 'yes'):
                    existing.role = 'admin'
                    db.session.commit()
                    print(f"[SUCCESS] User '{email}' promoted to Admin role.")
                return

        phone = input("Enter Official Mobile Phone (optional): ").strip()
        password = getpass.getpass("Enter Admin Password: ").strip()
        if len(password) < 6:
            print("[!] Error: Password must be at least 6 characters.")
            return

        admin_user = User(
            fullname=fullname,
            email=email,
            phone=phone or None,
            role='admin'
        )
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()

        print("\n" + "=" * 60)
        print(f"[SUCCESS] Admin account created successfully for: {email}")
        print("You can now log in at /login with these credentials.")
        print("=" * 60 + "\n")

if __name__ == '__main__':
    create_admin()
