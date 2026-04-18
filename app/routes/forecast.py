from flask import Blueprint, jsonify

forecast_bp = Blueprint('forecast', __name__)

WARD_FORECASTS = {
    "ward7": {
        "ward": "Ward 7",
        "nvi_score": 0.81,
        "signals": {
            "noaa_alert": True,
            "snap_cycle_day": 4,
            "unemployment_delta": 0.6,
            "school_break": False
        },
        "forecast": [
            {"day": 1, "risk": 0.42}, {"day": 2, "risk": 0.48},
            {"day": 3, "risk": 0.55}, {"day": 4, "risk": 0.61},
            {"day": 5, "risk": 0.67}, {"day": 6, "risk": 0.72},
            {"day": 7, "risk": 0.78}, {"day": 8, "risk": 0.83},
            {"day": 9, "risk": 0.87}, {"day": 10, "risk": 0.85},
            {"day": 11, "risk": 0.80}, {"day": 12, "risk": 0.74},
            {"day": 13, "risk": 0.68}, {"day": 14, "risk": 0.61}
        ],
        "peak_day": 9,
        "peak_risk": 0.87,
        "brief": "Ward 7 faces elevated demand risk peaking around day 9. NVI score of 0.81 indicates high concentration of elderly and low-income households. Recommend pre-positioning protein and shelf-stable supplies by day 6. Prioritize diabetic-friendly inventory given demographic profile."
    },
    "ward8": {
        "ward": "Ward 8",
        "nvi_score": 0.86,
        "signals": {
            "noaa_alert": True,
            "snap_cycle_day": 4,
            "unemployment_delta": 0.8,
            "school_break": False
        },
        "forecast": [
            {"day": 1, "risk": 0.51}, {"day": 2, "risk": 0.58},
            {"day": 3, "risk": 0.64}, {"day": 4, "risk": 0.70},
            {"day": 5, "risk": 0.75}, {"day": 6, "risk": 0.80},
            {"day": 7, "risk": 0.85}, {"day": 8, "risk": 0.89},
            {"day": 9, "risk": 0.92}, {"day": 10, "risk": 0.90},
            {"day": 11, "risk": 0.86}, {"day": 12, "risk": 0.79},
            {"day": 13, "risk": 0.71}, {"day": 14, "risk": 0.64}
        ],
        "peak_day": 9,
        "peak_risk": 0.92,
        "brief": "Ward 8 is the highest-risk zone. NVI 0.86 — highest in DC. Unemployment delta and SNAP cycle timing compound the storm signal. Activate Martha's Table and Congress Heights Mutual Aid immediately. Infant formula and diabetic supplies are critical gaps based on demographic data."
    }
}

@forecast_bp.route('/forecast/<ward>', methods=['GET'])
def get_forecast(ward):
    data = WARD_FORECASTS.get(ward.lower())
    if not data:
        return jsonify({"error": f"No forecast for {ward}"}), 404
    return jsonify({"status": "ok", **data})
