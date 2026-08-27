import os
import sys
from app import create_app
from database import db
from database.models import User, OTPVerification
from utils.otp import create_and_send_otp

def run_tests():
    print("=" * 70)
    print("STARTING END-TO-END OTP SYSTEM VERIFICATION TEST")
    print("=" * 70)

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        # Clean up any existing test user
        test_email = 'otptest.user@example.com'
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        OTPVerification.query.filter_by(email=test_email).delete()
        db.session.commit()

        client = app.test_client()

        # -------------------------------------------------------------
        # TEST 1: Register User (Unverified + OTP Created)
        # -------------------------------------------------------------
        print("\n[TEST 1] Registering new test user...")
        from unittest.mock import patch
        
        with patch('utils.otp.generate_otp', return_value='654321'):
            resp = client.post('/auth/register', data={
                'fullname': 'OTP Test User',
                'email': test_email,
                'phone': '9876543210',
                'password': 'Password123!',
                'confirm_password': 'Password123!',
                'terms': 'y'
            }, follow_redirects=True)

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert b'Verify Email Address' in resp.data or b'verify-otp' in resp.data, "Registration did not redirect to verify-otp page"

        user = User.query.filter_by(email=test_email).first()
        assert user is not None, "User record was not created"
        assert user.is_verified is False, "User must start with is_verified = False"
        print("  -> User registered with is_verified = False (SUCCESS)")

        # Verify hashed OTP record
        otp_rec = OTPVerification.query.filter_by(email=test_email, is_used=False).first()
        assert otp_rec is not None, "OTPVerification record was not created"
        assert otp_rec.otp_hash != '', "OTP hash must not be empty"
        assert '654321' not in otp_rec.otp_hash, "OTP must NOT be stored in plaintext"
        assert otp_rec.check_otp('654321'), "OTP hash validation failed"
        print(f"  -> OTP record created and hashed securely: {otp_rec.otp_hash[:30]}... (SUCCESS)")

        # -------------------------------------------------------------
        # TEST 2: Unverified Login Attempt Blocked
        # -------------------------------------------------------------
        print("\n[TEST 2] Testing unverified login attempt...")
        # Logout current session
        client.get('/auth/logout')
        
        with patch('utils.otp.generate_otp', return_value='654321'):
            login_resp = client.post('/auth/login', data={
                'email': test_email,
                'password': 'Password123!'
            }, follow_redirects=True)

        assert b'email has not been verified yet' in login_resp.data or b'Verify Email Address' in login_resp.data, "Unverified user login was not blocked"
        print("  -> Unverified login correctly blocked & redirected to OTP verification (SUCCESS)")

        latest_otp_rec = OTPVerification.query.filter_by(email=test_email, is_used=False).order_by(OTPVerification.created_at.desc()).first()

        # -------------------------------------------------------------
        # TEST 3: Invalid OTP Code
        # -------------------------------------------------------------
        print("\n[TEST 3] Testing incorrect OTP submission...")
        wrong_resp = client.post('/auth/verify-otp', data={'otp': '000000'}, follow_redirects=True)
        assert b'Invalid OTP code' in wrong_resp.data, "Incorrect OTP was not rejected"
        
        user = User.query.filter_by(email=test_email).first()
        assert user.is_verified is False, "User remained unverified on invalid OTP"
        print("  -> Incorrect OTP code '000000' rejected with clear error (SUCCESS)")

        # -------------------------------------------------------------
        # TEST 4: Valid OTP Verification
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing correct OTP submission ('654321')...")
        valid_resp = client.post('/auth/verify-otp', data={'otp': '654321'}, follow_redirects=True)
        assert b'verified successfully' in valid_resp.data.lower() or b'dashboard' in valid_resp.data.lower(), "Valid OTP submission failed"

        user = User.query.filter_by(email=test_email).first()
        assert user.is_verified is True, "User is_verified was not set to True"
        
        latest_otp_rec = OTPVerification.query.get(latest_otp_rec.id)
        assert latest_otp_rec.is_used is True, "OTP is_used was not set to True"
        print("  -> Correct OTP accepted: user.is_verified = True, otp.is_used = True (SUCCESS)")

        # -------------------------------------------------------------
        # TEST 5: OTP Re-use Blocked
        # -------------------------------------------------------------
        print("\n[TEST 5] Testing OTP single-use protection...")
        reuse_resp = client.post('/auth/verify-otp', data={'otp': '654321'}, follow_redirects=True)
        assert b'No active verification code found' in reuse_resp.data or b'already verified' in reuse_resp.data or b'No email pending verification' in reuse_resp.data, "Reusing OTP was not blocked"
        print("  -> Reusing previously verified OTP blocked (SUCCESS)")

        print("\n" + "=" * 70)
        print("ALL OTP SYSTEM VERIFICATION TESTS PASSED SUCCESSFULLY! 100% VERIFIED")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    run_tests()
