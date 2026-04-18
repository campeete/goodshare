from flask import Blueprint, jsonify
forecast_bp = Blueprint('forecast', __name__)

@forecast_bp.route('/forecast/<ward>', methods=['GET'])
def get_forecast(ward):
    return jsonify({"status": "ok", "ward": ward, "forecast": []})
