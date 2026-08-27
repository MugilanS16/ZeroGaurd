import os
import json
from datetime import datetime, timedelta
from app import create_app
from database import db
from database.models import User, Complaint, AdminNote, LoginHistory

def seed_database():
    app = create_app('development')
    with app.app_context():
        db.create_all()
        
        print("[*] Seeding ZeroGuard AI Database...")
        
        # 1. Seed Citizen User
        citizen = User.query.filter_by(email='citizen@zeroguard.ai').first()
        if not citizen:
            citizen = User(
                fullname='Rahul Sharma',
                email='citizen@zeroguard.ai',
                phone='+91 98765 43210',
                role='citizen',
                created_at=datetime.utcnow() - timedelta(days=15),
                last_login=datetime.utcnow() - timedelta(hours=2)
            )
            citizen.set_password('Citizen@123')
            db.session.add(citizen)
            print("  [+] Created citizen demo account: citizen@zeroguard.ai / Citizen@123")
        else:
            citizen.fullname = 'Rahul Sharma'
            citizen.role = 'citizen'
            citizen.set_password('Citizen@123')
            
        # 2. Seed Cyber-Cell Admin User
        admin = User.query.filter_by(email='admin@cybercell.gov.in').first()
        if not admin:
            admin = User(
                fullname='Inspector V. K. Menon (Cyber Crime Cell)',
                email='admin@cybercell.gov.in',
                phone='+91 11 2345 6789',
                role='admin',
                created_at=datetime.utcnow() - timedelta(days=60),
                last_login=datetime.utcnow() - timedelta(minutes=15)
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            print("  [+] Created admin demo account: admin@cybercell.gov.in / Admin@123")
        else:
            admin.fullname = 'Inspector V. K. Menon (Cyber Crime Cell)'
            admin.role = 'admin'
            admin.set_password('Admin@123')

        db.session.commit()
        
        # 3. Seed Login History Records
        if LoginHistory.query.count() == 0:
            hist1 = LoginHistory(
                user_id=citizen.id,
                email_attempted=citizen.email,
                ip_address='192.168.1.45',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0',
                status='SUCCESS',
                timestamp=datetime.utcnow() - timedelta(hours=2)
            )
            hist2 = LoginHistory(
                user_id=admin.id,
                email_attempted=admin.email,
                ip_address='10.0.0.12',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/123.0',
                status='SUCCESS',
                timestamp=datetime.utcnow() - timedelta(minutes=15)
            )
            db.session.add_all([hist1, hist2])
            db.session.commit()
            print("  [+] Seeded initial login audit records.")

        # 4. Seed Sample Complaints if none exist
        if Complaint.query.count() == 0:
            c1 = Complaint(
                user_id=citizen.id,
                reference_number='CC-2026-10492',
                crime_type='UPI Fraud',
                risk_level='High',
                risk_score=78,
                language='en',
                original_description='Someone called saying they were Paytm support and asked me to scan QR to receive cashback of Rs 4000. When I entered UPI PIN Rs 35,000 was debited from SBI account.',
                description='The victim was targeted by a fraudulent caller posing as official Paytm customer support claiming to credit a cashback amount of INR 4,000. Under social engineering deceit, the complainant was induced to scan a fraudulent QR code, leading to an unauthorized debit of INR 35,000 to an unknown UPI VPA from their State Bank of India account.',
                answers={
                    'transaction_id': 'UPI/20260221/987654321',
                    'amount_lost': 'INR 35,000',
                    'suspect_vpa_phone': 'paytm-refund-help@ybl / 9876500000',
                    'bank_reported': 'Yes, informed SBI toll-free immediately'
                },
                guidance=[
                    'Immediately called National Cybercrime Helpline 1930 within golden hour',
                    'Submitted formal dispute request with SBI Fraud Monitoring Cell',
                    'Changed UPI PIN on all linked banking applications'
                ],
                evidence_meta=[
                    {'name': 'sms_alert_debit.png', 'category': 'Screenshot', 'size': '245 KB'},
                    {'name': 'bank_mini_statement.pdf', 'category': 'Bank Statement', 'size': '512 KB'}
                ],
                pdf_filename='CC-2026-10492.pdf',
                status='In Review',
                created_at=datetime.utcnow() - timedelta(days=2, hours=4)
            )
            
            c2 = Complaint(
                user_id=citizen.id,
                reference_number='CC-2026-10493',
                crime_type='Sextortion',
                risk_level='Critical',
                risk_score=95,
                language='en',
                original_description='Received video call on WhatsApp from unknown girl. Morphing face in compromising video and blackmailing to send Rs 50,000 or will send to contact list and family members.',
                description='The complainant was subjected to an orchestrated sextortion scheme initiated via an unsolicited WhatsApp video call. The perpetrators recorded and manipulated video footage to produce fabricated compromising media, and are actively extorting INR 50,000 with imminent threats of dissemination to personal and professional contacts.',
                answers={
                    'suspect_contact': '+91 78901 23456 (WhatsApp)',
                    'money_demanded': 'INR 50,000',
                    'amount_paid': 'INR 0 (Refused so far)',
                    'platform': 'WhatsApp and Instagram'
                },
                guidance=[
                    'Preserve all chat screenshots, suspect phone numbers, and payment QR handles',
                    'Do not transfer money or engage further with the extortionist',
                    'Adjust privacy settings across all social media accounts immediately'
                ],
                evidence_meta=[
                    {'name': 'whatsapp_blackmail_chat.png', 'category': 'Screenshot', 'size': '680 KB'}
                ],
                pdf_filename='CC-2026-10493.pdf',
                status='Pending',
                created_at=datetime.utcnow() - timedelta(hours=6)
            )

            c3 = Complaint(
                user_id=citizen.id,
                reference_number='CC-2026-10488',
                crime_type='Job Scam',
                risk_level='Medium',
                risk_score=52,
                language='en',
                original_description='Offered part-time Telegram task job rating YouTube videos for 3000/day. Made initial deposit of 500 got 800 back. Then asked to invest 20000 for VIP task and blocked.',
                description='Victim lured into a Telegram task scam involving YouTube video likes and ratings with promised daily payouts. After a low-value initial payout trap, victim was induced into depositing INR 20,000 for VIP tier tasks, after which communication was terminated.',
                answers={
                    'telegram_group': '@GlobalMediaTasks_VIP',
                    'amount_lost': 'INR 20,000',
                    'transaction_details': 'IMPS to Private Bank A/c 9876001234'
                },
                guidance=[
                    'Exported Telegram chat log and suspect user IDs',
                    'Reported recipient account number to recipient bank nodal officer'
                ],
                evidence_meta=[
                    {'name': 'telegram_deposit_receipt.png', 'category': 'Screenshot', 'size': '380 KB'}
                ],
                pdf_filename='CC-2026-10488.pdf',
                status='Resolved',
                created_at=datetime.utcnow() - timedelta(days=5)
            )
            
            c4 = Complaint(
                user_id=None, # Anonymous report
                reference_number='CC-2026-10501',
                crime_type='Phishing',
                risk_level='High',
                risk_score=82,
                language='en',
                original_description='Received SMS claiming HDFC netbanking blocked due to PAN update needed. Clicked link hdfc-kyc-pan-update.online and entered user ID, password, and OTP.',
                description='Complainant fell victim to an SMS phishing (smishing) credential harvesting scheme impersonating HDFC Bank. Following a fraudulent SMS regarding urgent PAN/KYC verification, credentials and OTP were submitted on malicious clone website hdfc-kyc-pan-update.online.',
                answers={
                    'fake_website_url': 'http://hdfc-kyc-pan-update.online',
                    'sender_header': 'AD-HDFCBK',
                    'netbanking_blocked': 'Yes, user contacted bank branch'
                },
                guidance=[
                    'Immediately called HDFC Bank helpline to freeze Netbanking and Cards',
                    'Reported fake phishing URL to Google Safe Browsing and CERT-In'
                ],
                evidence_meta=[
                    {'name': 'smishing_message.png', 'category': 'Screenshot', 'size': '190 KB'}
                ],
                pdf_filename='CC-2026-10501.pdf',
                status='Pending',
                created_at=datetime.utcnow() - timedelta(hours=18)
            )

            db.session.add_all([c1, c2, c3, c4])
            db.session.commit()
            
            # Add Admin Notes for complaint 1 and 3
            note1 = AdminNote(
                complaint_id=c1.id,
                admin_id=admin.id,
                note='Case assigned to SI Sharma (Financial Crimes Cell). Bank nodal officer notified for lien mark on suspect beneficiary account.',
                previous_status='Pending',
                new_status='In Review',
                created_at=datetime.utcnow() - timedelta(days=1, hours=2)
            )
            note2 = AdminNote(
                complaint_id=c3.id,
                admin_id=admin.id,
                note='Suspect beneficiary account frozen via 1930 portal integration. Refund of INR 18,500 processed by nodal bank. Case marked resolved.',
                previous_status='In Review',
                new_status='Resolved',
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add_all([note1, note2])
            db.session.commit()
            print("  [+] Seeded 4 diverse test complaints and admin audit notes.")
            
        print("[SUCCESS] ZeroGuard AI Database seeding completed successfully!\n")

if __name__ == '__main__':
    import sys
    print("=" * 60)
    print("WARNING: This script will populate the database with DEMO/DUMMY data.")
    print("=" * 60)
    confirm = input("Are you sure you want to seed demo accounts and complaints? (yes/no): ").strip().lower()
    if confirm in ('y', 'yes'):
        seed_database()
    else:
        print("[!] Seeding canceled by user. Database unchanged.")
        sys.exit(0)

