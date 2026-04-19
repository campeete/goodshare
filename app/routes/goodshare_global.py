from flask import Blueprint, jsonify
import json, os

global_bp = Blueprint('global', __name__)

def load_global():
    path = os.path.join(os.path.dirname(__file__), '../../data/seed/goodshare_global_data.json')
    with open(path) as f:
        return json.load(f)

def calculate_nvi(country):
    """
    Nutritional Vulnerability Index — calculated from real WHO data only.
    Inputs are normalized against maximum plausible values for each metric.
    All source data: WHO MGRS malnutrition surveys + WHO Diabetes Database 2022.

    Formula:
        NVI = 0.35 * wasting_norm
            + 0.30 * stunting_norm
            + 0.20 * diabetes_norm
            + 0.15 * severe_wasting_norm

    Normalization denominators (max plausible values):
        wasting:         20% = crisis threshold per WHO
        stunting:        60% = extreme upper bound
        diabetes:        30% = extreme upper bound for 18+ crude
        severe_wasting:  10% = emergency threshold per WHO
    """
    m = country['who_malnutrition']
    d = country['who_diabetes']

    wasting_norm        = min(m['wasting_rate'] / 20.0, 1.0)
    stunting_norm       = min(m['stunting_rate'] / 60.0, 1.0)
    diabetes_norm       = min(d['prevalence_18plus_crude'] / 30.0, 1.0)
    severe_wasting_norm = min(m['severe_wasting_rate'] / 10.0, 1.0)

    nvi = (0.35 * wasting_norm +
           0.30 * stunting_norm +
           0.20 * diabetes_norm +
           0.15 * severe_wasting_norm)

    return round(nvi, 4)

def build_country_response(c):
    """Build the full API response for one country."""
    nvi = calculate_nvi(c)
    return {
        "name":    c['name'],
        "code":    c['code'],
        "lat":     c['lat'],
        "lng":     c['lng'],
        "nvi_score": nvi,
        "nvi_formula": {
            "wasting_weight":        0.35,
            "stunting_weight":       0.30,
            "diabetes_weight":       0.20,
            "severe_wasting_weight": 0.15,
            "note": "NVI calculated from real WHO data. Higher = more vulnerable."
        },
        "who_malnutrition": c['who_malnutrition'],
        "who_diabetes":     c['who_diabetes'],
        "ipc_phase":        c['ipc_phase_placeholder'],
        "ipc_phase_status": "PLACEHOLDER — " + c['ipc_phase_source'],
        "forecast_status":  "NOT YET WIRED — requires FEWS NET IPC + ACLED + CHIRPS",
        "data_complete":    False,
        "pending": [
            "IPC phase — FEWS NET API",
            "Forecast signals — FEWS NET + ACLED + CHIRPS",
            "Population at risk — FEWS NET population data"
        ]
    }

@global_bp.route('/global/countries', methods=['GET'])
def get_countries():
    data = load_global()
    return jsonify([build_country_response(c) for c in data['countries']])

@global_bp.route('/global/forecast/<country_code>', methods=['GET'])
def get_country_forecast(country_code):
    data = load_global()
    country = next(
        (c for c in data['countries'] if c['code'].lower() == country_code.lower()),
        None
    )
    if not country:
        return jsonify({"error": f"No data for {country_code}"}), 404
    return jsonify({"status": "ok", **build_country_response(country)})

@global_bp.route('/global/summary', methods=['GET'])
def get_summary():
    data = load_global()
    countries = data['countries']
    built = [build_country_response(c) for c in countries]
    highest = max(built, key=lambda c: c['nvi_score'])
    return jsonify({
        "total_countries_monitored": len(built),
        "data_complete":             False,
        "pending_signals":           ["FEWS NET IPC", "ACLED conflicts", "CHIRPS rainfall"],
        "highest_nvi_country":       highest['name'],
        "highest_nvi_score":         highest['nvi_score'],
        "countries": [{
            "name":      c['name'],
            "code":      c['code'],
            "nvi_score": c['nvi_score'],
            "ipc_phase": c['ipc_phase'],
            "lat":       c['lat'],
            "lng":       c['lng']
        } for c in built]
    })
