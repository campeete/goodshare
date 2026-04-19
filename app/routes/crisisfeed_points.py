from flask import Blueprint, jsonify, send_from_directory
import json, os

points_bp = Blueprint('points', __name__)

@points_bp.route('/')
def index():
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static'))
    return send_from_directory(static_dir, 'crisisfeed_dashboard.html')

@points_bp.route('/points', methods=['GET'])
def get_points():
    path = os.path.join(os.path.dirname(__file__), '../../data/seed/food_points.json')
    with open(path) as f:
        return jsonify(json.load(f))
