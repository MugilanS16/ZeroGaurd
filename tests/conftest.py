"""
Pytest configuration and shared test fixtures for ZeroGuard AI test suite.
"""
import sys
import os
import pytest

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database import db
from database.models import User, OTPChallenge, Guardian, NotificationLog, ActivityLog


@pytest.fixture(scope='session')
def app():
    """Creates a test application configured with in-memory database and console provider."""
    test_app = create_app('testing')
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'MESSAGING_PROVIDER': 'console',
        'OTP_SECRET_KEY': 'test-otp-hmac-sha256-secret-2026',
        'OTP_RESEND_COOLDOWN_SECONDS': 30,
        'OTP_EXPIRY_SECONDS': 300,
        'OTP_MAX_ATTEMPTS': 5,
        'OTP_MAX_HOURLY_SENDS': 5
    })
    return test_app


@pytest.fixture(scope='function')
def db_session(app):
    """Provides a clean database session per test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app, db_session):
    """Flask test client."""
    return app.test_client()
