from datetime import datetime
import json
import hashlib
from typing import Optional, List
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime, ForeignKey, Enum
from database import db

class User(db.Model):
    """User account model for citizens and cyber-cell administrators with SMS/WhatsApp 2FA."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fullname: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)  # Normalized E.164
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_otp_channel: Mapped[str] = mapped_column(String(20), default='sms', nullable=False) # 'sms' or 'whatsapp'
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default='citizen', nullable=False) # 'citizen' or 'admin'
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Verification flag
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    complaints = relationship('Complaint', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    login_records = relationship('LoginHistory', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    admin_notes = relationship('AdminNote', back_populates='admin', lazy='dynamic')
    guardians = relationship('Guardian', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    otp_challenges = relationship('OTPChallenge', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def e164_phone(self):
        return self.phone_number or self.phone
    
    def to_dict(self):
        return {
            'id': self.id,
            'fullname': self.fullname,
            'name': self.fullname,
            'email': self.email,
            'phone': self.phone,
            'phone_number': self.phone_number or self.phone,
            'phone_verified': self.phone_verified,
            'preferred_otp_channel': self.preferred_otp_channel,
            'role': self.role,
            'is_verified': self.is_verified,
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

    # Evidence Semantic Content Relevance fields
    evidence_relevance_status = db.Column(db.String(40), default='N/A', nullable=False, index=True) # Relevant, No Relevant Signal Found, Manual Review Needed, N/A
    evidence_relevance_details_json = db.Column(db.Text, default='{}', nullable=False)
    
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

    @property
    def evidence_relevance_details(self):
        try:
            return json.loads(self.evidence_relevance_details_json) if self.evidence_relevance_details_json else {}
        except Exception:
            return {}

    @evidence_relevance_details.setter
    def evidence_relevance_details(self, value):
        self.evidence_relevance_details_json = json.dumps(value or {}, ensure_ascii=False)

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
            'evidence_relevance_status': self.evidence_relevance_status,
            'evidence_relevance_details': self.evidence_relevance_details,
            'pdf_filename': self.pdf_filename,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def get_timeline_stages(self):
        """Returns structured status timeline stages, active stage description, and transition timestamps."""
        status_lower = (self.status or '').lower()
        
        # Determine current stage index (1: Submitted, 2: Pending Review, 3: In Investigation, 4: Resolved)
        if status_lower == 'resolved':
            current_stage = 4
        elif status_lower in ('in review', 'in_review', 'investigating'):
            current_stage = 3
        elif status_lower in ('pending', 'pending review'):
            current_stage = 2
        else:
            current_stage = 1

        # Extract timestamps from AdminNote status transitions
        stage_dates = {
            1: self.created_at,
            2: None,
            3: None,
            4: None
        }

        try:
            notes = self.admin_notes.all() if hasattr(self.admin_notes, 'all') else list(self.admin_notes)
            for note in notes:
                new_st = (note.new_status or '').lower()
                if new_st in ('pending', 'pending review') and not stage_dates[2]:
                    stage_dates[2] = note.created_at
                elif new_st in ('in review', 'in_review', 'investigating') and not stage_dates[3]:
                    stage_dates[3] = note.created_at
                elif new_st == 'resolved' and not stage_dates[4]:
                    stage_dates[4] = note.created_at
        except Exception:
            pass

        # Fallback dates for active/completed stages if specific transition note is absent
        if current_stage >= 2 and not stage_dates[2]:
            stage_dates[2] = self.created_at
        if current_stage >= 3 and not stage_dates[3]:
            stage_dates[3] = self.updated_at
        if current_stage >= 4 and not stage_dates[4]:
            stage_dates[4] = self.updated_at

        # Reassuring descriptions per stage
        descriptions = {
            1: f"Your complaint has been received and assigned reference number {self.reference_number}.",
            2: "Your complaint is in queue for review by our cyber-cell team.",
            3: "An investigator is actively reviewing your case and evidence.",
            4: "Your case has been resolved. Check your dashboard for details or contact 1930 for further assistance."
        }

        stages = [
            {
                'index': 1,
                'title': 'Submitted',
                'date': stage_dates[1],
                'is_completed': current_stage >= 1,
                'is_active': current_stage == 1
            },
            {
                'index': 2,
                'title': 'Pending Review',
                'date': stage_dates[2] if current_stage >= 2 else None,
                'is_completed': current_stage > 2,
                'is_active': current_stage == 2
            },
            {
                'index': 3,
                'title': 'In Investigation',
                'date': stage_dates[3] if current_stage >= 3 else None,
                'is_completed': current_stage > 3,
                'is_active': current_stage == 3
            },
            {
                'index': 4,
                'title': 'Resolved',
                'date': stage_dates[4] if current_stage >= 4 else None,
                'is_completed': current_stage == 4,
                'is_active': current_stage == 4
            }
        ]

        if current_stage == 4:
            for s in stages:
                s['is_completed'] = True
                s['is_active'] = (s['index'] == 4)

        if current_stage == 4:
            progress_percent = 100
        elif current_stage == 3:
            progress_percent = 66
        elif current_stage == 2:
            progress_percent = 33
        else:
            progress_percent = 0

        return {
            'current_stage': current_stage,
            'current_description': descriptions.get(current_stage, ''),
            'stages': stages,
            'progress_percent': progress_percent
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
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    email_attempted: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone_attempted: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    login_method: Mapped[str] = mapped_column(String(30), default='password', nullable=False) # 'password', 'sms_otp', 'whatsapp_otp', 'sso'
    ip_address: Mapped[str] = mapped_column(String(50), default='127.0.0.1')
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='SUCCESS') # SUCCESS, FAILED
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship('User', back_populates='login_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_attempted': self.email_attempted,
            'phone_attempted': self.phone_attempted,
            'login_method': self.login_method,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'success': self.success,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }

    def __repr__(self):
        return f'<LoginHistory {self.email_attempted or self.phone_attempted} - {self.status} at {self.timestamp}>'


class OTPChallenge(db.Model):
    """SQLAlchemy 2.0 Model for SMS & WhatsApp OTP Challenges with HMAC-SHA256."""
    __tablename__ = 'otp_challenges'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # E.164
    channel: Mapped[str] = mapped_column(String(20), default='sms', nullable=False)     # 'sms' or 'whatsapp'
    purpose: Mapped[str] = mapped_column(String(30), default='2fa_login', nullable=False) # '2fa_login', 'registration', 'guardian_verify'
    otp_hash: Mapped[str] = mapped_column(String(256), nullable=False)                  # HMAC-SHA256
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), default='127.0.0.1', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship('User', back_populates='otp_challenges')

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    @property
    def is_locked(self) -> bool:
        return self.attempts >= 5

    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number[:4] + '******' + self.phone_number[-4:] if len(self.phone_number) >= 8 else '***',
            'channel': self.channel,
            'purpose': self.purpose,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None,
            'is_expired': self.is_expired,
            'is_consumed': self.is_consumed,
            'attempts': self.attempts,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<OTPChallenge {self.id} for {self.phone_number} via {self.channel}>'


class Guardian(db.Model):
    """Emergency Guardian Model for trusted Email, SMS & WhatsApp notifications."""
    __tablename__ = 'guardians'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), default='Guardian', nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True) # E.164
    preferred_channel: Mapped[str] = mapped_column(String(20), default='email', nullable=False) # 'email', 'sms', or 'whatsapp'
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship('User', back_populates='guardians')

    def to_dict(self):
        from backend.services.otp_service import mask_email, mask_phone_number
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'relationship': self.relationship_type,
            'email': self.email,
            'masked_email': mask_email(self.email) if self.email else None,
            'phone_number': self.phone_number,
            'masked_phone': mask_phone_number(self.phone_number) if self.phone_number else '***',
            'preferred_channel': self.preferred_channel,
            'consent_given': self.consent_given,
            'consent_at': self.consent_at.strftime('%Y-%m-%d %H:%M:%S') if self.consent_at else None,
            'verified': self.verified,
            'opted_out': self.opted_out,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Guardian {self.name} ({self.preferred_channel}) for User {self.user_id} - Verified: {self.verified}>'


class NotificationLog(db.Model):
    """Audit and delivery status log for all outbound SMS, WhatsApp, and email messages."""
    __tablename__ = 'notification_log'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_type: Mapped[str] = mapped_column(String(30), nullable=False) # 'user' or 'guardian'
    recipient_ref: Mapped[str] = mapped_column(String(120), nullable=False)  # Masked phone/email or reference
    channel: Mapped[str] = mapped_column(String(20), nullable=False)        # 'sms', 'whatsapp', 'email'
    template: Mapped[str] = mapped_column(String(100), nullable=False)      # Template ID or name
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default='queued', nullable=False) # 'queued', 'sent', 'delivered', 'failed'
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'recipient_type': self.recipient_type,
            'recipient_ref': self.recipient_ref,
            'channel': self.channel,
            'template': self.template,
            'provider_message_id': self.provider_message_id,
            'status': self.status,
            'error': self.error,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<NotificationLog {self.id} ({self.channel}) -> {self.recipient_ref} - {self.status}>'


class OTPVerification(db.Model):
    """Database model for storing legacy hashed one-time verification codes (preserved for backwards compatibility)."""
    __tablename__ = 'otp_verifications'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_hash = db.Column(db.String(256), nullable=False)
    purpose = db.Column(db.String(20), default='registration', nullable=False)
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
    """Emergency trusted contact model linked to a user account (legacy contact model)."""
    __tablename__ = 'emergency_contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    contact_name = db.Column(db.String(120), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
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
    """Audit log recording user actions and security events with tamper-evident SHA-256 hash ledger."""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    action_type = db.Column(db.String(100), nullable=True) # Alias for test compatibility
    description = db.Column(db.Text, nullable=True)        # Alias for test compatibility
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), default='127.0.0.1')
    prev_hash = db.Column(db.String(64), nullable=True)
    record_hash = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('activity_logs', lazy='dynamic', cascade='all, delete-orphan'))

    def compute_hash(self, previous_hash='0' * 64):
        """Generates SHA-256 cryptographic chaining hash for immutable audit ledger."""
        raw = f"{self.user_id}:{self.action or self.action_type}:{self.details or self.description}:{self.ip_address}:{self.timestamp.isoformat() if self.timestamp else ''}:{previous_hash}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'action_type': self.action_type or self.action,
            'description': self.description or self.details,
            'details': self.details,
            'ip_address': self.ip_address,
            'record_hash': self.record_hash,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }

    def __repr__(self):
        return f'<ActivityLog {self.action or self.action_type} for User {self.user_id} at {self.timestamp}>'
