import os
import sys
from datetime import datetime, timezone
from app import create_app
from database import db
from database.models import User, EmergencyContact, OTPVerification, ActivityLog

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_full_registration_flow():
    print("=" * 80)
    print("TESTING FULL REGISTRATION FLOW WITH EMERGENCY TRUSTED CONTACT & OTP")
    print("=" * 80)

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

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

        resp1 = client.post('/auth/register', data=reg_payload, follow_redirects=True)
        print(f"  Response Code: {resp1.status_code}")
        assert resp1.status_code == 200

        # Check DB before OTP verification: User exists but unverified, EmergencyContact does NOT exist yet
        unverified_user = User.query.filter_by(email=new_user_email).first()
        assert unverified_user is not None
        assert unverified_user.is_verified == False

        pre_contact = EmergencyContact.query.filter_by(user_id=unverified_user.id).first()
        assert pre_contact is None, "EmergencyContact must NOT be created before OTP verification!"

        print("  --> Form submission accepted. User created (Unverified). EmergencyContact NOT orphaned before OTP!")

        # -------------------------------------------------------------------
        # STEP 2: RETRIEVE OTP & SUBMIT OTP VERIFICATION
        # -------------------------------------------------------------------
        print("\n[STEP 2] Fetching OTP and Verifying Account...")
        otp_rec = OTPVerification.query.filter_by(email=new_user_email, purpose='registration', is_used=False).order_by(OTPVerification.created_at.desc()).first()
        assert otp_rec is not None

        # In testing/dev setup, test with actual generated OTP logic or inspect OTP
        # We can test OTP check directly or simulate OTP entry
        # Let's inspect the OTP code generated for this user
        # Note: set_otp hashes the code, so let's verify using client.post with the known demo OTP or set a known hash
        otp_rec.expires_at = datetime.utcnow().replace(year=2030) # Ensure not expired
        
        # Override OTP hash to known code '123456' for verification test
        otp_rec.set_otp('123456')
        db.session.commit()

        resp2 = client.post('/auth/verify-otp', data={'otp': '123456'}, follow_redirects=True)
        print(f"  OTP Verification Response Code: {resp2.status_code}")
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
