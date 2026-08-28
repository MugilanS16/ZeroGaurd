from flask import Blueprint

fraud_checker_bp = Blueprint('fraud_checker', __name__)

from . import routes  # noqa
