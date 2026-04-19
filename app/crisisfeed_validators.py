import re
from app.crisisfeed_logger import get_logger

logger = get_logger(__name__)

VALID_COUNTRY_CODES = {'HTI', 'SDN', 'ETH', 'MLI', 'NER', 'SOM'}
VALID_WARDS = {'ward1','ward2','ward3','ward4','ward5','ward6','ward7','ward8'}
MAX_GEMINI_INPUT = 500
COUNTRY_CODE_PATTERN = re.compile(r'^[A-Za-z]{3}$')

def validate_country_code(code):
    if not code:
        return False, "Country code required"
    if not COUNTRY_CODE_PATTERN.match(code):
        return False, f"Country code must be 3 letters"
    if code.upper() not in VALID_COUNTRY_CODES:
        return False, f"Country '{code.upper()}' not in dataset. Supported: {', '.join(sorted(VALID_COUNTRY_CODES))}"
    return True, ''

def validate_ward(ward):
    if not ward:
        return False, "Ward required"
    if ward.lower() not in VALID_WARDS:
        return False, f"Ward '{ward}' not valid"
    return True, ''

def validate_gemini_input(text):
    if not text:
        return False, "Text field required"
    if not isinstance(text, str):
        return False, "Text must be a string"
    if len(text) > MAX_GEMINI_INPUT:
        return False, f"Text exceeds {MAX_GEMINI_INPUT} chars (got {len(text)})"
    for pattern in ['ignore previous instructions','ignore all instructions','system prompt','you are now']:
        if pattern in text.lower():
            logger.warning(f"Prompt injection attempt: '{pattern}'")
            return False, "Input contains invalid content"
    return True, ''

def validate_json_body(body, required_fields):
    if body is None:
        return False, "Request body must be valid JSON"
    for field in required_fields:
        if field not in body:
            return False, f"Missing required field: '{field}'"
    return True, ''
