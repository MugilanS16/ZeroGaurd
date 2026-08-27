from flask import render_template
from blueprints.awareness import awareness_bp

@awareness_bp.route('/awareness')
def awareness():
    """Cyber security awareness portal with interactive scam detection quiz."""
    return render_template('awareness.html')

@awareness_bp.route('/emergency')
def emergency():
    """Emergency helpline directory and state nodal cyber contacts."""
    return render_template('emergency.html')
