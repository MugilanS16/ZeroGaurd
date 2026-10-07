import os
import sys
from datetime import datetime, timezone
from app import create_app
from database import db
from database.models import User, EmergencyContact, Guardian, OTPVerification, ActivityLog, OTPChallenge

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_full_registration_flow():
    print("=" * 80)
    print("TESTING FULL REGISTRATION FLOW WITH EMERGENCY TRUSTED CONTACT & OTP")
    print("=" * 80)

    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['MAIL_SUPPRESS_SEND'] = True
    app.config['MESSAGING_PROVIDER'] = 'console'

    client = app.test_client()

    new_user_email = "new_citizen_2026@example.com"
    trusted_contact_email = "vaishnav2291@gmail.com" # real recipient email

    with app.app_context():
        # Clean up existing test records if present
        user = User.query.filter_by(email=new_user_email).first()
        if user:
            EmergencyContact.query.filter_by(user_id=user.id).delete()
            ActivityLog.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
        
        OTPVerification.query.filter_by(email=new_user_email).delete()
        db.session.commit()

        # -------------------------------------------------------------------
        # STEP 1: SUBMIT REGISTRATION FORM (USER + TRUSTED CONTACT)
        # -------------------------------------------------------------------
        print("\n[STEP 1] Submitting Registration Form with Emergency Trusted Contact...")
        reg_payload = {
            'fullname': 'Siddharth Rao',
            'email': new_user_email,
            'phone': '9876500111',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'trusted_contact_name': 'Kavita Rao',
            'trusted_contact_relationship': 'Spouse',
            'trusted_contact_email': trusted_contact_email,
            'trusted_contact_phone': '9812345678',
            'terms': 'y'
        }

        from unittest.mock import patch, MagicMock
        with patch('smtplib.SMTP') as mock_smtp_cls:
            smtp_inst = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = smtp_inst

            resp1 = client.post('/auth/register', data=reg_payload, follow_redirects=True)
            print(f"  Response Code: {resp1.status_code}")
            assert resp1.status_code == 200

            # Check DB after registration: User created (unverified), EmergencyContact & Guardian created
            unverified_user = User.query.filter_by(email=new_user_email).first()
            assert unverified_user is not None
            assert unverified_user.is_verified == False

            contact = EmergencyContact.query.filter_by(user_id=unverified_user.id).first()
            assert contact is not None
            assert contact.contact_name == 'Kavita Rao'
            assert contact.email == trusted_contact_email

            guardian = Guardian.query.filter_by(user_id=unverified_user.id).first()
            assert guardian is not None
            assert guardian.verified == False

            print("  --> Form submission accepted. User created (Unverified). EmergencyContact & Guardian created with confirmation request!")

            # -------------------------------------------------------------------
            # STEP 2: RETRIEVE OTP CHALLENGE & SUBMIT 2FA VERIFICATION
            # -------------------------------------------------------------------
            print("\n[STEP 2] Fetching OTP and Verifying Account...")
            from database.models import OTPChallenge
            from backend.services.otp_service import hash_otp

            challenge = OTPChallenge.query.filter_by(user_id=unverified_user.id, purpose='registration').order_by(OTPChallenge.created_at.desc()).first()
            assert challenge is not None
            challenge.expires_at = datetime.utcnow().replace(year=2030)
            challenge.otp_hash = hash_otp('123456')
            db.session.commit()

            with client.session_transaction() as sess:
                sess['2fa_challenge_id'] = challenge.id
                sess['2fa_user_id'] = unverified_user.id

            resp2 = client.post('/auth/verify-2fa', data={'otp': '123456'}, follow_redirects=True)
            print(f"  2FA Verification Response Code: {resp2.status_code}")
            assert resp2.status_code == 200

        # -------------------------------------------------------------------
        # STEP 3: CONFIRM USER & EMERGENCY CONTACT IN DATABASE
        # -------------------------------------------------------------------
        print("\n[STEP 3] Verifying Final Database Records...")
        verified_user = User.query.filter_by(email=new_user_email).first()
        assert verified_user.is_verified == True

        final_contact = EmergencyContact.query.filter_by(user_id=verified_user.id).first()
        assert final_contact is not None
        assert final_contact.contact_name == 'Kavita Rao'
        assert final_contact.relationship == 'Spouse'
        assert final_contact.email == trusted_contact_email
        assert final_contact.phone == '+91 9812345678'

        activity = ActivityLog.query.filter_by(user_id=verified_user.id, action='ADD_EMERGENCY_CONTACT').first()
        assert activity is not None

        print("  --> SUCCESS: User is Verified!")
        print(f"      User ID      : {verified_user.id} ({verified_user.fullname})")
        print(f"      Contact Name : {final_contact.contact_name}")
        print(f"      Relationship : {final_contact.relationship}")
        print(f"      Email        : {final_contact.email}")
        print(f"      Phone        : {final_contact.phone}")
        print(f"      Activity Log : {activity.action} - {activity.details}")

        print("\n" + "=" * 80)
        print("REGISTRATION WITH EMERGENCY TRUSTED CONTACT END-TO-END TEST PASSED 100%!")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    test_full_registration_flow()
