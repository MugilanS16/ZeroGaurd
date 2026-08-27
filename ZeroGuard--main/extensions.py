"""
Flask Extensions Initialization for ZeroGuard AI
Prevents circular imports by instantiating shared extension objects here.
Extensions are bound to the Flask application in create_app() or app setup.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
