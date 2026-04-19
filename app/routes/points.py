import json
from flask import Blueprint, jsonify, send_from_directory

points_bp = Blueprint('points', __name__)

@points_bp.route('/points', methods=['GET'])
def get_points():
    with open('data/seed/food_points.json') as f:
        data = json.load(f)

    return jsonify({
        "status": "ok",
        "data": data
    })

@points_bp.route('/map')
def serve_map():
    return send_from_directory('static', 'map.html')

from flask import send_from_directory
import os

@points_bp.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '../../static'), 'index.html')
