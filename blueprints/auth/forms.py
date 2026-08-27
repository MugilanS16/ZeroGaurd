import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from database.models import User

class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email Address', validators=[
        DataRequired(message='Please enter your email address.'),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password.')
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    """Citizen registration form."""
    fullname = StringField('Full Name', validators=[
        DataRequired(message='Please enter your full name as per official ID.'),
        Length(min=3, max=100, message='Name must be between 3 and 100 characters.')
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message='Please enter a valid email address.'),
        Email(message='Please enter a valid email address.')
    ])
    phone = StringField('Mobile Number', validators=[
        DataRequired(message='Please enter your 10-digit mobile number.'),
        Regexp(r'^\+?[0-9\s\-]{10,15}$', message='Please enter a valid phone number (e.g., +91 9876543210).')
    ])
    password = PasswordField('Create Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])

    # Emergency Trusted Contact Fields (Required at Signup)
    trusted_contact_name = StringField('Trusted Contact Name', validators=[
        DataRequired(message='Please enter your emergency contact\'s full name.'),
        Length(min=3, max=100, message='Contact name must be between 3 and 100 characters.')
    ])
    trusted_contact_relationship = SelectField('Relationship', choices=[
        ('', 'Select Relationship...'),
        ('Parent', 'Parent'),
        ('Guardian', 'Guardian'),
        ('Spouse', 'Spouse'),
        ('Sibling', 'Sibling'),
        ('Other Family Member', 'Other Family Member'),
        ('Close Friend', 'Close Friend')
    ], validators=[
        DataRequired(message='Please select a valid relationship option.')
    ])
    trusted_contact_email = StringField('Trusted Contact Email', validators=[
        DataRequired(message='Please enter your emergency contact\'s email address.'),
        Email(message='Please enter a valid email address.')
    ])
    trusted_contact_phone = StringField('Trusted Contact Mobile', validators=[
        DataRequired(message='Please enter a valid 10-digit mobile number for your emergency contact.'),
        Regexp(r'^\+?[0-9\s\-]{10,15}$', message='Please enter a valid phone number.')
    ])

    terms = BooleanField('I agree to the Terms of Service and Privacy Policy', validators=[
        DataRequired(message='You must agree to continue.')
    ])
    submit = SubmitField('Continue to OTP Verification')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data.lower().strip()).first()
        if user and user.is_verified:
            raise ValidationError('An account with this email already exists. Please sign in.')

    def validate_trusted_contact_email(self, field):
        if self.email.data and field.data.lower().strip() == self.email.data.lower().strip():
            raise ValidationError('Emergency contact email cannot be identical to your own account email.')

    def validate_trusted_contact_phone(self, field):
        user_phone_digits = re.sub(r'\D', '', self.phone.data or '')
        contact_phone_digits = re.sub(r'\D', '', field.data or '')
        if len(contact_phone_digits) == 12 and contact_phone_digits.startswith('91'):
            contact_phone_digits = contact_phone_digits[2:]

        if len(contact_phone_digits) != 10 or not contact_phone_digits[0] in '6789':
            raise ValidationError('Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.')

        if user_phone_digits and len(user_phone_digits) >= 10 and contact_phone_digits == user_phone_digits[-10:]:
            raise ValidationError('Emergency contact phone number cannot be identical to your own mobile number.')



class OTPForm(FlaskForm):
    """6-digit OTP verification form."""
    otp = StringField('Verification Code (OTP)', validators=[
        DataRequired(message='Please enter the 6-digit OTP.'),
        Length(min=6, max=6, message='OTP must be exactly 6 digits.'),
        Regexp(r'^\d{6}$', message='OTP must contain only numbers.')
    ])
    submit = SubmitField('Verify & Complete Registration')


class ChangePasswordForm(FlaskForm):
    """Password change form."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Please enter your current password.')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='Please enter a new password.'),
        Length(min=6, message='New password must be at least 6 characters.')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password.'),
        EqualTo('new_password', message='New passwords must match.')
    ])
    submit = SubmitField('Update Password')
