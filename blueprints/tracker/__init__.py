from flask import Blueprint

tracker_bp = Blueprint('tracker', __name__)

from . import routes  # noqa
