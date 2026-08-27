from flask import Blueprint

awareness_bp = Blueprint('awareness', __name__)

from . import routes  # noqa
