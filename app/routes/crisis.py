from flask import Blueprint, jsonify
crisis_bp = Blueprint('crisis', __name__)

@crisis_bp.route('/crisis/status', methods=['GET'])
def crisis_status():
    return jsonify({"crisis_mode": False})
