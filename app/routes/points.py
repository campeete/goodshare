from flask import Blueprint, jsonify
points_bp = Blueprint('points', __name__)

@points_bp.route('/points', methods=['GET'])
def get_points():
    return jsonify({"status": "ok", "data": []})
