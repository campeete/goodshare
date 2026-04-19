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


@gemini_bp.route('/gemini/ingest', methods=['POST'])
def ingest_country():
    """
    POST /api/gemini/ingest
    AI-powered ingestion of raw humanitarian report text into structured country data.
    Paste any WHO survey, UNICEF bulletin, or news article — Gemini extracts the data.
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
        logger.info(f"Country data ingested: {extracted.get('name', 'unknown')}")
        return success_response({
            "extracted":    extracted,
            "ready_to_add": extracted.get('name') is not None,
            "message":      "Data extracted. Review then add to goodshare_global_data.json.",
            "next_step":    "POST to /api/admin/countries to add to live dataset"
        })
    except PermissionError as e:
        return service_unavailable(f"Gemini: {e}")
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
    Generate a 2-sentence urgent crisis alert for coordinator broadcast.
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
        logger.info(f"Crisis alert generated for {country_code.upper()}")
        return success_response({"country": country_data['name'], "code": country_code.upper(), "alert": alert, "nvi": nvi})
    except PermissionError as e:
        return service_unavailable(f"Gemini: {e}")
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except Exception as e:
        logger.error(f"Alert error: {e}", exc_info=True)
        return internal_error()


@gemini_bp.route('/gemini/compare', methods=['POST'])
def compare_countries():
    """
    POST /api/gemini/compare
    AI-powered comparative analysis of two countries for resource allocation.
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
        from app.services.goodshare_gemini_service import compare_countries as compare
        analysis = compare({**data_a, 'nvi_score': nvi_a}, {**data_b, 'nvi_score': nvi_b})
        logger.info(f"Comparison: {code_a} vs {code_b}")
        return success_response({"country_a": data_a['name'], "country_b": data_b['name'], "analysis": analysis, "nvi_a": nvi_a, "nvi_b": nvi_b})
    except PermissionError as e:
        return service_unavailable(f"Gemini: {e}")
    except ResourceWarning as e:
        return service_unavailable(str(e))
    except Exception as e:
        logger.error(f"Compare error: {e}", exc_info=True)
        return internal_error()
