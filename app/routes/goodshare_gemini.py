from flask import Blueprint, jsonify, request
from app.services.goodshare_gemini_service import generate_coordinator_brief, parse_food_point_description
from app.routes.goodshare_forecast import WARD_FORECASTS

gemini_bp = Blueprint('gemini', __name__)

@gemini_bp.route('/gemini/brief/<ward>', methods=['GET'])
def coordinator_brief(ward):
    data = WARD_FORECASTS.get(ward.lower())
    if not data:
        return jsonify({"error": f"No data for {ward}"}), 404
    brief = generate_coordinator_brief(ward.upper(), data, data['nvi_score'])
    return jsonify({"ward": ward, "nvi": data['nvi_score'], "peak_risk": data['peak_risk'], "brief": brief})

@gemini_bp.route('/gemini/parse', methods=['POST'])
def parse_point():
    body = request.get_json()
    if not body or 'text' not in body:
        return jsonify({"error": "send JSON with 'text' field"}), 400
    return jsonify(parse_food_point_description(body['text']))
