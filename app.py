import os
from pathlib import Path
from flask import Flask, session, g
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

from config import config_by_name
from database import db
from database.models import User

from extensions import csrf, mail

def create_app(config_name=None):
    """Application factory for ZeroGuard AI."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        
    app = Flask(__name__)
    app_config = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(app_config)
    
    # Ensure directories exist
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_dir = Path(app.root_path) / 'static' / 'generated_pdfs'
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    # Exclude specific API endpoints from CSRF if needed (e.g. public quick check API)
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.report import report_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.admin import admin_bp
    from blueprints.chatbot import chatbot_bp
    from blueprints.tracker import tracker_bp
    from blueprints.awareness import awareness_bp
    from blueprints.fraud_checker import fraud_checker_bp
    
    # Exempt public JSON scan endpoint
    csrf.exempt(fraud_checker_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(tracker_bp)
    app.register_blueprint(awareness_bp)
    app.register_blueprint(fraud_checker_bp)

    # Top-level URL routing aliases for citizen convenience
    from flask import redirect, url_for, request

    @app.route('/login')
    def login_alias():
        return redirect(url_for('auth.login', **request.args))

    @app.route('/register')
    def register_alias():
        return redirect(url_for('auth.register', **request.args))

    @app.route('/dashboard')
    def dashboard_alias():
        return redirect(url_for('dashboard.index', **request.args))

    @app.route('/my-complaints')
    def my_complaints_alias():
        return redirect(url_for('dashboard.index', **request.args))

    @app.route('/track-status')
    def track_status_alias():
        return redirect(url_for('tracker.track', **request.args))
    
    from utils.constants import EMERGENCY_HELPLINES

    # Context processor for templates
    @app.context_processor
    def inject_global_vars():
        current_user = None
        user_id = session.get('user_id')
        if user_id:
            current_user = User.query.get(user_id)
        return {
            'current_user': current_user,
            'is_logged_in': bool(user_id),
            'is_admin': bool(current_user and current_user.is_admin),
            'app_title': 'ZeroGuard AI: Simplifying Cybercrime Reporting with Instant AI Assistance',
            'emergency_helplines': EMERGENCY_HELPLINES
        }

        
    # Custom template filters
    @app.template_filter('datetime')
    def format_datetime(value, format='%d %b %Y, %I:%M %p'):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except Exception:
                return value
        return value.strftime(format)
        
    @app.template_filter('risk_badge')
    def risk_badge_class(risk_level):
        risk = (risk_level or '').lower()
        if risk == 'critical':
            return 'badge-critical'
        elif risk == 'high':
            return 'badge-high'
        elif risk == 'medium':
            return 'badge-medium'
        return 'badge-low'

    @app.template_filter('status_badge')
    def status_badge_class(status):
        st = (status or '').lower()
        if st == 'resolved':
            return 'badge-success'
        elif st in ('in review', 'in_review'):
            return 'badge-warning'
        return 'badge-pending'
        
    with app.app_context():
        db.create_all()
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
