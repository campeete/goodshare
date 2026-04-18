from flask import Blueprint, jsonify

forecast_bp = Blueprint('forecast', __name__)

WARD_FORECASTS = {
    "ward7": {
        "ward": "Ward 7", "nvi_score": 0.81, "peak_day": 9, "peak_risk": 0.87,
        "signals": {"noaa_alert": True, "snap_cycle_day": 4, "unemployment_delta": 0.6, "school_break": False},
        "forecast": [{"day": i+1, "risk": r} for i, r in enumerate([0.42,0.48,0.55,0.61,0.67,0.72,0.78,0.83,0.87,0.85,0.80,0.74,0.68,0.61])],
        "brief": "Ward 7 faces elevated demand risk peaking around day 9."
    },
    "ward8": {
        "ward": "Ward 8", "nvi_score": 0.86, "peak_day": 9, "peak_risk": 0.92,
        "signals": {"noaa_alert": True, "snap_cycle_day": 4, "unemployment_delta": 0.8, "school_break": False},
        "forecast": [{"day": i+1, "risk": r} for i, r in enumerate([0.51,0.58,0.64,0.70,0.75,0.80,0.85,0.89,0.92,0.90,0.86,0.79,0.71,0.64])],
        "brief": "Ward 8 is the highest-risk zone. NVI 0.86 — highest in DC."
    }
}

@forecast_bp.route('/forecast/<ward>', methods=['GET'])
def get_forecast(ward):
    data = WARD_FORECASTS.get(ward.lower())
    if not data:
        return jsonify({"error": f"No forecast for {ward}"}), 404
    return jsonify({"status": "ok", **data})
