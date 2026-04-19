"""
goodshare_gemini.py
-------------------
All Gemini AI endpoints for CrisisFeed.
7 distinct AI capabilities serving humanitarian coordinators.
"""

import json
import os
import datetime
from flask import Blueprint, request

from app.goodshare_errors import (
    success_response, not_found, bad_request,
    validation_error, service_unavailable, internal_error
)
from app.goodshare_validators import (
    validate_country_code, validate_ward,
    validate_gemini_input, validate_json_body,
    VALID_COUNTRY_CODES
)
from app.goodshare_logger import get_logger

logger = get_logger(__name__)
gemini_bp = Blueprint('gemini', __name__)

WARD_DATA = {
    "ward7": {
        "nvi_score": 0.81, "peak_risk": 0.87, "peak_day": 9,
        "signals": {"noaa_alert": True, "snap_cycle_day": 4,
                    "unemployment_delta": 0.6, "school_break": False}
    },
    "ward8": {
        "nvi_score": 0.86, "peak_risk": 0.92, "peak_day": 9,
        "signals": {"noaa_alert": True, "snap_cycle_day": 4,
                    "unemployment_delta": 0.8, "school_break": False}
    }
}

_GLOBAL_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../data/seed/goodshare_global_data.json')
)


def _load_country(code: str):
    try:
        with open(_GLOBAL_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return next(
            (c for c in data['countries'] if c['code'].upper() == code.upper()),
            None
        )
    except Exception as e:
        logger.error(f"Failed to load country {code}: {e}")
        return None


@gemini_bp.route('/gemini/brief/<identifier>', methods=['GET'])
def coordinator_brief(identifier: str):
    """Ward or country coordinator brief."""
    identifier_upper = identifier.upper()
    identifier_lower = identifier.lower()
    is_country = identifier_upper in VALID_COUNTRY_CODES
    is_ward = identifier_lower in WARD_DATA

    if not is_country and not is_ward:
        return not_found(f"Identifier '{identifier}'")

    if is_country:
        country = _load_country(identifier_upper)
        if not country:
            return not_found(f"Country data for '{identifier_upper}'")
        from app.routes.goodshare_global import calculate_nvi
        nvi = calculate_nvi(country)
        try:
            from app.services.goodshare_gemini_service import generate_country_brief
            brief = generate_country_brief({**country, 'nvi_score': nvi})
            return success_response({"identifier": identifier_upper, "country": country['name'],
                                     "brief": brief, "brief_type": "country", "nvi_score": nvi})
        except PermissionError as e:
            return service_unavailable(str(e))
        except ResourceWarning as e:
            return service_unavailable(str(e))
        except Exception as e:
            logger.error(f"Brief error: {e}", exc_info=True)
            return internal_error()

    data = WARD_DATA[identifier_lower]
    try:
        from app.services.goodshare_gemini_service import generate_coordinator_brief
        brief = generate_coordinator_brief(identifier_upper, data, data['nvi_score'])
        return success_response({"identifier": identifier_lower, "ward": identifier_upper,
                                 "brief": brief, "brief_type": "ward",
                                 "nvi_score": data['nvi_score'], "peak_risk": data['peak_risk']})
    except PermissionError as e:
        return service_unavailable(str(e))
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except Exception as e:
        logger.error(f"Ward brief error: {e}", exc_info=True)
        return internal_error()


@gemini_bp.route('/gemini/parse', methods=['POST'])
def parse_point():
    """Parse informal food point description into structured JSON."""
    body = request.get_json(silent=True)
    is_valid, error_msg = validate_json_body(body, ['text'])
    if not is_valid:
        return bad_request(error_msg)
    is_valid, error_msg = validate_gemini_input(body['text'])
    if not is_valid:
        return validation_error('text', error_msg)
    try:
        from app.services.goodshare_gemini_service import parse_food_point_description
        result = parse_food_point_description(body['text'])
        return success_response(result)
    except PermissionError as e:
        return service_unavailable(str(e))
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except ValueError as e:
        return internal_error(f"AI response parsing failed: {e}")
    except Exception as e:
        logger.error(f"Parse error: {e}", exc_info=True)
        return internal_error()


@gemini_bp.route('/gemini/ingest', methods=['POST'])
def ingest_country():
    """
    POST /api/gemini/ingest
    AI-powered ingestion — paste any WHO report, UNICEF bulletin, or news article.
    Gemini extracts structured food security data automatically.
    Demo moment: paste unstructured text, get structured JSON back in real time.
    """
    body = request.get_json(silent=True)
    is_valid, error_msg = validate_json_body(body, ['text'])
    if not is_valid:
        return bad_request(error_msg)
    is_valid, error_msg = validate_gemini_input(body['text'])
    if not is_valid:
        return validation_error('text', error_msg)
    try:
        from app.services.goodshare_gemini_service import ingest_country_data
        extracted = ingest_country_data(body['text'])
        logger.info(f"Country ingested: {extracted.get('name', 'unknown')}")
        return success_response({
            "extracted":    extracted,
            "ready_to_add": extracted.get('name') is not None,
            "message":      "Data extracted. Add to goodshare_global_data.json to make live.",
            "next_step":    "Add extracted object to the countries array in seed data"
        })
    except PermissionError as e:
        return service_unavailable(str(e))
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except ValueError as e:
        return internal_error(f"Extraction failed: {e}")
    except Exception as e:
        logger.error(f"Ingest error: {e}", exc_info=True)
        return internal_error()


@gemini_bp.route('/gemini/alert/<country_code>', methods=['GET'])
def crisis_alert(country_code: str):
    """
    GET /api/gemini/alert/<country_code>
    2-sentence urgent crisis alert for coordinator broadcast, SMS, social media.
    """
    is_valid, _ = validate_country_code(country_code)
    if not is_valid:
        return not_found(f"Country '{country_code}'")
    country_data = _load_country(country_code.upper())
    if not country_data:
        return not_found(f"Country data for '{country_code.upper()}'")
    from app.routes.goodshare_global import calculate_nvi
    nvi = calculate_nvi(country_data)
    try:
        from app.services.goodshare_gemini_service import generate_crisis_alert
        alert = generate_crisis_alert(
            {**country_data, 'nvi_score': nvi},
            {"ipc_phase": country_data.get('ipc_phase_placeholder')}
        )
        logger.info(f"Alert: {country_code.upper()}")
        return success_response({"country": country_data['name'],
                                 "code": country_code.upper(), "alert": alert, "nvi": nvi})
    except PermissionError as e:
        return service_unavailable(str(e))
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except Exception as e:
        logger.error(f"Alert error: {e}", exc_info=True)
        return internal_error()


@gemini_bp.route('/gemini/compare', methods=['POST'])
def compare_countries_route():
    """
    POST /api/gemini/compare
    AI resource allocation advisor. Which country needs resources first and why.
    Body: {"country_a": "HTI", "country_b": "SDN"}
    """
    body = request.get_json(silent=True)
    is_valid, error_msg = validate_json_body(body, ['country_a', 'country_b'])
    if not is_valid:
        return bad_request(error_msg)
    code_a, code_b = body['country_a'].upper(), body['country_b'].upper()
    for code in [code_a, code_b]:
        is_valid, _ = validate_country_code(code)
        if not is_valid:
            return not_found(f"Country '{code}'")
    data_a, data_b = _load_country(code_a), _load_country(code_b)
    if not data_a:
        return not_found(f"Country '{code_a}'")
    if not data_b:
        return not_found(f"Country '{code_b}'")
    from app.routes.goodshare_global import calculate_nvi
    nvi_a, nvi_b = calculate_nvi(data_a), calculate_nvi(data_b)
    try:
        from app.services.goodshare_gemini_service import compare_countries
        analysis = compare_countries(
            {**data_a, 'nvi_score': nvi_a},
            {**data_b, 'nvi_score': nvi_b}
        )
        logger.info(f"Compare: {code_a} vs {code_b}")
        return success_response({"country_a": data_a['name'], "country_b": data_b['name'],
                                 "analysis": analysis, "nvi_a": nvi_a, "nvi_b": nvi_b})
    except PermissionError as e:
        return service_unavailable(str(e))
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except Exception as e:
        logger.error(f"Compare error: {e}", exc_info=True)
        return internal_error()


@gemini_bp.route('/gemini/supply/<country_code>', methods=['POST'])
def supply_recommendation(country_code: str):
    """
    POST /api/gemini/supply/<country_code>
    AI logistics advisor. Recommends what food to pre-position based on country profile.
    Body: {"stock": ["RUTF", "ORS", "general rations"]}  (optional, defaults provided)
    """
    is_valid, _ = validate_country_code(country_code)
    if not is_valid:
        return not_found(f"Country '{country_code}'")
    country_data = _load_country(country_code.upper())
    if not country_data:
        return not_found(f"Country data for '{country_code.upper()}'")
    body = request.get_json(silent=True) or {}
    available_stock = body.get('stock', [
        'therapeutic food (RUTF)', 'supplementary food (RUSF)',
        'general food rations', 'oral rehydration salts (ORS)',
        'infant formula', 'diabetic-friendly rations'
    ])
    from app.routes.goodshare_global import calculate_nvi
    nvi = calculate_nvi(country_data)
    try:
        from app.services.goodshare_gemini_service import generate_supply_recommendation
        recommendation = generate_supply_recommendation(
            {**country_data, 'nvi_score': nvi}, available_stock
        )
        logger.info(f"Supply rec: {country_code.upper()}")
        return success_response({"country": country_data['name'], "code": country_code.upper(),
                                 "recommendation": recommendation, "nvi": nvi,
                                 "stock_evaluated": available_stock})
    except PermissionError as e:
        return service_unavailable(str(e))
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except Exception as e:
        logger.error(f"Supply error: {e}", exc_info=True)
        return internal_error()


@gemini_bp.route('/gemini/report/<country_code>', methods=['GET'])
def situation_report(country_code: str):
    """
    GET /api/gemini/report/<country_code>
    WFP/OCHA-style professional situation report.
    Format humanitarian professionals recognize immediately.
    """
    is_valid, _ = validate_country_code(country_code)
    if not is_valid:
        return not_found(f"Country '{country_code}'")
    country_data = _load_country(country_code.upper())
    if not country_data:
        return not_found(f"Country data for '{country_code.upper()}'")
    from app.routes.goodshare_global import calculate_nvi
    nvi = calculate_nvi(country_data)
    try:
        from app.services.goodshare_gemini_service import generate_situation_report
        report = generate_situation_report({**country_data, 'nvi_score': nvi})
        logger.info(f"Report: {country_code.upper()}")
        return success_response({
            "country":      country_data['name'],
            "code":         country_code.upper(),
            "report":       report,
            "nvi":          nvi,
            "format":       "WFP/OCHA situation report style",
            "generated_at": datetime.datetime.utcnow().isoformat() + 'Z'
        })
    except PermissionError as e:
        return service_unavailable(str(e))
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except Exception as e:
        logger.error(f"Report error: {e}", exc_info=True)
        return internal_error()
