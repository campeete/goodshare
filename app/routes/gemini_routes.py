from flask import Blueprint, jsonify, request
from app.services.gemini_service import generate_coordinator_brief, parse_food_point_description

gemini_bp = Blueprint('gemini', __name__)

WARD_DATA = {
    "ward7": {"peak_risk": 0.87, "peak_day": 9, "nvi": 0.81, "signals": {"noaa_alert": True, "snap_cycle_day": 4, "unemployment_delta": 0.6}},
    "ward8": {"peak_risk": 0.92, "peak_day": 9, "nvi": 0.86, "signals": {"noaa_alert": True, "snap_cycle_day": 4, "unemployment_delta": 0.8}}
}

@gemini_bp.route('/gemini/brief/<ward>', methods=['GET'])
def coordinator_brief(ward):
    data = WARD_DATA.get(ward.lower())
    if not data:
        return jsonify({"error": f"No data for {ward}"}), 404
    
    brief = generate_coordinator_brief(
        ward=ward.upper(),
        forecast=data,
        nvi=data['nvi']
    )
    return jsonify({
        "ward": ward,
        "nvi": data['nvi'],
        "peak_risk": data['peak_risk'],
        "brief": brief
    })

@gemini_bp.route('/gemini/parse', methods=['POST'])
def parse_point():
    body = request.get_json()
    if not body or 'text' not in body:
        return jsonify({"error": "send JSON with 'text' field"}), 400
    
    result = parse_food_point_description(body['text'])
    return jsonify(result)
