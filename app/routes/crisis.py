from flask import Blueprint, jsonify, request

crisis_bp = Blueprint('crisis', __name__)

# Simulated crisis state — in prod this would come from NOAA/FEMA webhook
CRISIS_STATE = {
    "active": True,
    "level": "HIGH",
    "trigger": "Tropical Storm Warning — NOAA Alert DC Metro",
    "high_risk_wards": ["Ward 7", "Ward 8"],
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
    """Return only food points in high-risk wards during crisis"""
    import json, os
    with open('data/seed/food_points.json') as f:
        all_points = json.load(f)
    
    high_risk = CRISIS_STATE["high_risk_wards"]
    filtered = [p for p in all_points if p.get("ward") in high_risk]
    
    return jsonify({
        "status": "crisis",
        "affected_wards": high_risk,
        "active_points": filtered,
        "count": len(filtered)
    })
