from flask import Blueprint, jsonify
import json, os

crisis_bp = Blueprint('crisis', __name__)

CRISIS_STATE = {
    "active": True,
    "level": "HIGH",
    "high_risk_wards": ["Ward 7", "Ward 8"],
    "trigger": "Tropical Storm Warning — NOAA Alert DC Metro",
    "issued_at": "2025-04-18T14:00:00Z",
    "recommended_actions": [
        "Pre-position protein and shelf-stable supplies in Ward 7 and Ward 8",
        "Activate Deanwood Mutual Aid Network and Congress Heights Mutual Aid",
        "Prioritize diabetic-friendly and infant formula inventory"
    ]
}

@crisis_bp.route('/crisis/status', methods=['GET'])
def crisis_status():
    return jsonify(CRISIS_STATE)

@crisis_bp.route('/crisis/points', methods=['GET'])
def crisis_points():
    path = os.path.join(os.path.dirname(__file__), '../../data/seed/food_points.json')
    with open(path) as f:
        all_points = json.load(f)
    filtered = [p for p in all_points if p.get('ward') in CRISIS_STATE['high_risk_wards']]
    return jsonify({"status": "crisis", "affected_wards": CRISIS_STATE['high_risk_wards'], "active_points": filtered, "count": len(filtered)})
