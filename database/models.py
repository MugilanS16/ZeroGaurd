from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    """User account model for citizens and cyber-cell administrators."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='citizen', nullable=False) # 'citizen' or 'admin'
    is_verified = db.Column(db.Boolean, default=False, nullable=False)  # Email verification flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    complaints = db.relationship('Complaint', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    login_records = db.relationship('LoginHistory', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    admin_notes = db.relationship('AdminNote', back_populates='admin', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def to_dict(self):
        return {
            'id': self.id,
            'fullname': self.fullname,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Complaint(db.Model):
    """Cybercrime complaint record with automated risk scoring and metadata."""
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    reference_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    crime_type = db.Column(db.String(80), nullable=False, index=True)
    risk_level = db.Column(db.String(20), default='Medium', nullable=False, index=True) # Low, Medium, High, Critical
    risk_score = db.Column(db.Integer, default=50, nullable=False) # 0 - 100
    language = db.Column(db.String(10), default='en', nullable=False) # en, hi, ta, te
    
    # Descriptions & text
    description = db.Column(db.Text, nullable=False) # AI polished / formal complaint text
    original_description = db.Column(db.Text, nullable=True) # Raw citizen input
    
    # JSON structured columns stored as Text
    answers_json = db.Column(db.Text, default='{}', nullable=False)
    guidance_json = db.Column(db.Text, default='[]', nullable=False)
    evidence_meta_json = db.Column(db.Text, default='[]', nullable=False)

    # Anti-Fraud Amount Verification fields
    claimed_amount = db.Column(db.Float, nullable=True)
    amount_verification_status = db.Column(db.String(30), default='N/A', nullable=False, index=True) # Verified, Mismatch, Manual Review Needed, N/A
    amount_verification_details_json = db.Column(db.Text, default='{}', nullable=False)
    
    pdf_filename = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(30), default='Pending', nullable=False, index=True) # Pending, In Review, Resolved
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='complaints')
    admin_notes = db.relationship('AdminNote', back_populates='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='AdminNote.created_at.desc()')
    
    @property
    def answers(self):
        try:
            return json.loads(self.answers_json) if self.answers_json else {}
        except Exception:
            return {}
            
    @answers.setter
    def answers(self, value):
        self.answers_json = json.dumps(value or {}, ensure_ascii=False)

    @property
    def guidance(self):
        try:
            return json.loads(self.guidance_json) if self.guidance_json else []
        except Exception:
            return []
            
    @guidance.setter
    def guidance(self, value):
        self.guidance_json = json.dumps(value or [], ensure_ascii=False)

    @property
    def evidence_meta(self):
        try:
            return json.loads(self.evidence_meta_json) if self.evidence_meta_json else []
        except Exception:
            return []
            
    @evidence_meta.setter
    def evidence_meta(self, value):
        self.evidence_meta_json = json.dumps(value or [], ensure_ascii=False)
            
    @property
    def amount_verification_details(self):
        try:
            return json.loads(self.amount_verification_details_json) if self.amount_verification_details_json else {}
        except Exception:
            return {}

    @amount_verification_details.setter
    def amount_verification_details(self, value):
        self.amount_verification_details_json = json.dumps(value or {}, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else 'Guest / Anonymous',
            'user_name': self.user.fullname if self.user else 'Anonymous Citizen',
            'reference_number': self.reference_number,
            'crime_type': self.crime_type,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'language': self.language,
            'description': self.description,
            'original_description': self.original_description,
            'answers': self.answers,
            'guidance': self.guidance,
            'evidence_meta': self.evidence_meta,
            'claimed_amount': self.claimed_amount,
            'amount_verification_status': self.amount_verification_status,
            'amount_verification_details': self.amount_verification_details,
            'pdf_filename': self.pdf_filename,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Complaint {self.reference_number} ({self.crime_type} - {self.status})>'


class AdminNote(db.Model):
    """Audit log and internal case notes added by Cyber-Cell personnel."""
    __tablename__ = 'admin_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    previous_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    complaint = db.relationship('Complaint', back_populates='admin_notes')
    admin = db.relationship('User', back_populates='admin_notes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'admin_id': self.admin_id,
            'admin_name': self.admin.fullname if self.admin else 'System Officer',
            'note': self.note,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<AdminNote {self.id} for Complaint {self.complaint_id}>'


class LoginHistory(db.Model):
    """Security audit log recording all citizen and admin login activity."""
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    email_attempted = db.Column(db.String(120), nullable=True)
    ip_address = db.Column(db.String(50), default='127.0.0.1')
    user_agent = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='SUCCESS') # SUCCESS, FAILED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', back_populates='login_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_attempted': self.email_attempted,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }

    def __repr__(self):
        return f'<LoginHistory {self.email_attempted} - {self.status} at {self.timestamp}>'


class OTPVerification(db.Model):
    """Database model for storing hashed one-time verification codes."""
    __tablename__ = 'otp_verifications'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_hash = db.Column(db.String(256), nullable=False)
    purpose = db.Column(db.String(20), default='registration', nullable=False) # 'registration' or 'login'
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def set_otp(self, otp_code):
        self.otp_hash = generate_password_hash(otp_code)

    def check_otp(self, otp_code):
        return check_password_hash(self.otp_hash, otp_code)

    def __repr__(self):
        return f'<OTPVerification {self.email} ({self.purpose}) - Used: {self.is_used}>'


class EmergencyContact(db.Model):
    """Emergency trusted contact model linked to a user account."""
    __tablename__ = 'emergency_contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    contact_name = db.Column(db.String(120), nullable=False)
    relationship = db.Column(db.String(50), nullable=False) # Parent, Guardian, Spouse, Sibling, Other Family Member, Close Friend
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('emergency_contact', uselist=False, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'contact_name': self.contact_name,
            'relationship': self.relationship,
            'email': self.email,
            'phone': self.phone,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<EmergencyContact {self.contact_name} ({self.relationship}) for User {self.user_id}>'


class ActivityLog(db.Model):
    """Audit log recording user actions such as emergency contact updates."""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), default='127.0.0.1')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('activity_logs', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }

    def __repr__(self):
        return f'<ActivityLog {self.action} for User {self.user_id} at {self.timestamp}>'


