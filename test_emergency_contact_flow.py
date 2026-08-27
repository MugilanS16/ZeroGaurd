import os
import sys
from datetime import datetime, timezone
from app import create_app
from database import db
from database.models import User, EmergencyContact, ActivityLog

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_emergency_contact_feature():
    print("=" * 80)
    print("TESTING EMERGENCY TRUSTED CONTACT FEATURE (ADD, EDIT, REMOVE & EMAIL)")
    print("=" * 80)

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    client = app.test_client()

    with app.app_context():
        # Ensure test user exists
        test_email = "citizen_test_user@example.com"
        user = User.query.filter_by(email=test_email).first()
        if not user:
            user = User(
                fullname="Anand Verma",
                email=test_email,
                phone="+91 9999911111",
                role="citizen",
                is_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            user.set_password("Password123!")
            db.session.add(user)
            db.session.commit()

        # Clean up previous emergency contacts for test user
        EmergencyContact.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # Log in test user
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['role'] = user.role
            sess['user_name'] = user.fullname

        # -------------------------------------------------------------------
        # PART 1: ADD TRUSTED CONTACT & TRIGGER EMAIL
        # -------------------------------------------------------------------
        print("\n[PART 1] Adding Emergency Trusted Contact...")
        trusted_email = "vaishnav2291@gmail.com" # real email address
        resp1 = client.post('/auth/emergency-contact/save', data={
            'contact_name': 'Ramesh Verma',
            'relationship': 'Parent',
            'email': trusted_email,
            'phone': '9876543210'
        }, follow_redirects=True)

        print(f"  Response Code: {resp1.status_code}")
        contact = EmergencyContact.query.filter_by(user_id=user.id).first()
        assert contact is not None
        assert contact.contact_name == "Ramesh Verma"
        assert contact.relationship == "Parent"
        assert contact.email == trusted_email
        assert contact.phone == "+91 9876543210"

        act1 = ActivityLog.query.filter_by(user_id=user.id, action='ADD_EMERGENCY_CONTACT').first()
        assert act1 is not None

        print("  --> ADD CONTACT SUCCESSFUL!")
        print(f"      Contact Name : {contact.contact_name}")
        print(f"      Relationship : {contact.relationship}")
        print(f"      Email        : {contact.email}")
        print(f"      Phone        : {contact.phone}")
        print(f"      Activity Log : {act1.action} - {act1.details}")

        # -------------------------------------------------------------------
        # PART 2: UPDATE TRUSTED CONTACT & TRIGGER UPDATE EMAIL
        # -------------------------------------------------------------------
        print("\n[PART 2] Updating Emergency Trusted Contact...")
        resp2 = client.post('/auth/emergency-contact/save', data={
            'contact_name': 'Ramesh Verma (Senior)',
            'relationship': 'Guardian',
            'email': trusted_email,
            'phone': '9876543210'
        }, follow_redirects=True)

        contact_updated = EmergencyContact.query.filter_by(user_id=user.id).first()
        assert contact_updated.contact_name == "Ramesh Verma (Senior)"
        assert contact_updated.relationship == "Guardian"

        act2 = ActivityLog.query.filter_by(user_id=user.id, action='EDIT_EMERGENCY_CONTACT').first()
        assert act2 is not None

        print("  --> EDIT CONTACT SUCCESSFUL!")
        print(f"      Updated Name : {contact_updated.contact_name}")
        print(f"      Relationship : {contact_updated.relationship}")
        print(f"      Activity Log : {act2.action} - {act2.details}")

        # -------------------------------------------------------------------
        # PART 3: REMOVE TRUSTED CONTACT & TRIGGER REMOVAL EMAIL
        # -------------------------------------------------------------------
        print("\n[PART 3] Removing Emergency Trusted Contact...")
        resp3 = client.post('/auth/emergency-contact/delete', follow_redirects=True)


        contact_deleted = EmergencyContact.query.filter_by(user_id=user.id).first()
        assert contact_deleted is None

        act3 = ActivityLog.query.filter_by(user_id=user.id, action='REMOVE_EMERGENCY_CONTACT').first()
        assert act3 is not None

        print("  --> REMOVE CONTACT SUCCESSFUL!")
        print(f"      Contact in DB : {contact_deleted}")
        print(f"      Activity Log   : {act3.action} - {act3.details}")

        print("\n" + "=" * 80)
        print("ALL EMERGENCY TRUSTED CONTACT TESTS PASSED 100%!")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    test_emergency_contact_feature()
