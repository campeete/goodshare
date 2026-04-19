"""
goodshare_gemini_service.py
---------------------------
Gemini AI service layer for CrisisFeed.
All prompts, all AI calls, all parsing logic in one place.
"""

import os
import json
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from app.goodshare_logger import get_logger, log_external_api

load_dotenv()
logger = get_logger(__name__)


def _get_client():
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise ValueError("GEMINI_API_KEY not set in .env")
    return genai.Client(api_key=key)


def _call_gemini(prompt: str, context: str = '') -> str:
    try:
        client = _get_client()
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        log_external_api('Gemini', 'generate_content', True, context)
        return response.text
    except genai_errors.ClientError as e:
        error_str = str(e)
        if '401' in error_str or 'API_KEY_INVALID' in error_str:
            log_external_api('Gemini', 'generate_content', False, 'Invalid key')
            raise PermissionError("Gemini API key invalid")
        if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
            log_external_api('Gemini', 'generate_content', False, 'Quota exhausted')
            raise ResourceWarning("Gemini quota exhausted. Get fresh key from aistudio.google.com")
        log_external_api('Gemini', 'generate_content', False, str(e))
        raise RuntimeError(f"Gemini error: {e}")
    except Exception as e:
        log_external_api('Gemini', 'generate_content', False, str(type(e).__name__))
        raise RuntimeError(f"Gemini service error: {e}")


def _call_gemini_json(prompt: str, context: str = '') -> dict:
    raw = _call_gemini(prompt, context)
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Gemini invalid JSON for {context}: {text[:300]}")
        raise ValueError(f"Model returned invalid JSON: {e}")


def generate_coordinator_brief(ward: str, forecast: dict, nvi: float) -> str:
    prompt = f"""You are a humanitarian coordinator briefing tool.
Ward: {ward}
NVI: {nvi}
Peak risk: {forecast['peak_risk']} on day {forecast['peak_day']}
Signals: NOAA={forecast['signals']['noaa_alert']}, SNAP day={forecast['signals']['snap_cycle_day']}, unemployment delta={forecast['signals']['unemployment_delta']}
Write exactly 3 sentences for a field coordinator.
Sentence 1: Risk level and when it peaks.
Sentence 2: Specific actions in next 48 hours.
Sentence 3: Which populations to prioritize and why.
Direct. No filler."""
    return _call_gemini(prompt, context=f"ward brief {ward}")


def generate_country_brief(country: dict) -> str:
    m = country['who_malnutrition']
    d = country['who_diabetes']
    prompt = f"""You are a humanitarian coordinator briefing tool.
Country: {country['name']}
NVI: {country.get('nvi_score')}
Wasting: {m['wasting_rate']}%  Severe wasting: {m['severe_wasting_rate']}%
Stunting: {m['stunting_rate']}%  Diabetes 18+: {d['prevalence_18plus_crude']}%
Write exactly 3 sentences for a humanitarian field coordinator.
Sentence 1: Vulnerability level and most urgent indicator with actual numbers.
Sentence 2: Pre-positioning actions for next 48 hours.
Sentence 3: Which population groups to prioritize and what food support they need.
Direct. Use actual numbers. No filler."""
    return _call_gemini(prompt, context=f"country brief {country['name']}")


def parse_food_point_description(raw_text: str) -> dict:
    prompt = f"""Convert this food access point description to JSON.
Text: "{raw_text}"
Return ONLY valid JSON with keys: name, type (community_fridge/pantry/mutual_aid/church/food_bank),
address, hours, food_types (list), dietary_flags (list), notes
No markdown. Only JSON."""
    raw = _call_gemini(prompt, context="parse food point")
    text = raw.strip().lstrip('```json').lstrip('```').rstrip('```').strip()
    return json.loads(text)


def ingest_country_data(raw_text: str) -> dict:
    """Parse unstructured humanitarian report text into structured country data."""
    prompt = f"""You are a humanitarian data extraction tool.
Extract food security data from this text and return ONLY valid JSON.
Text: "{raw_text}"
Return:
{{
  "name": "country name",
  "code": "ISO-3 uppercase or null",
  "who_malnutrition": {{
    "wasting_rate": number or null,
    "severe_wasting_rate": number or null,
    "stunting_rate": number or null,
    "survey_year": number or null,
    "source": "string or null"
  }},
  "who_diabetes": {{
    "prevalence_18plus_crude": number or null,
    "year": number or null,
    "source": "string or null"
  }},
  "ipc_phase": number or null,
  "notes": "any other relevant data"
}}
All percentages as plain numbers. Null if not in text. No markdown. Only JSON."""
    return _call_gemini_json(prompt, context="country ingestion")


def generate_crisis_alert(country: dict, signals: dict) -> str:
    """2-sentence urgent crisis alert for coordinator broadcast."""
    prompt = f"""You are a humanitarian crisis alert system.
Country: {country["name"]}
NVI: {country.get("nvi_score")}
Child wasting: {country["who_malnutrition"]["wasting_rate"]}%
Diabetes 18+: {country["who_diabetes"]["prevalence_18plus_crude"]}%
IPC Phase: {signals.get("ipc_phase", "unknown")}
Write exactly 2 sentences for humanitarian coordinators.
Sentence 1: Urgency and which population is most at risk with specific numbers.
Sentence 2: Single most critical action needed in next 24 hours.
Direct. Cite actual numbers. No filler."""
    return _call_gemini(prompt, context=f"crisis alert {country['name']}")


def compare_countries(country_a: dict, country_b: dict) -> str:
    """Resource allocation comparison of two countries."""
    prompt = f"""You are a humanitarian resource allocation advisor.
Country A: {country_a["name"]} — NVI {country_a.get("nvi_score")}, Wasting {country_a["who_malnutrition"]["wasting_rate"]}%, Severe {country_a["who_malnutrition"]["severe_wasting_rate"]}%, Diabetes {country_a["who_diabetes"]["prevalence_18plus_crude"]}%
Country B: {country_b["name"]} — NVI {country_b.get("nvi_score")}, Wasting {country_b["who_malnutrition"]["wasting_rate"]}%, Severe {country_b["who_malnutrition"]["severe_wasting_rate"]}%, Diabetes {country_b["who_diabetes"]["prevalence_18plus_crude"]}%
Write exactly 3 sentences.
Sentence 1: Which needs immediate intervention and why, with specific numbers.
Sentence 2: What type of food support each needs differently.
Sentence 3: How to split resources if you can only fund one operation."""
    return _call_gemini(prompt, context=f"compare {country_a['name']} vs {country_b['name']}")


def generate_supply_recommendation(country: dict, available_stock: list) -> str:
    """Logistics pre-positioning recommendation based on country nutrition profile."""
    stock_str = ", ".join(available_stock) if available_stock else "standard emergency rations"
    prompt = f"""You are a humanitarian logistics advisor.
Country: {country["name"]}
NVI: {country.get("nvi_score")}
Child wasting: {country["who_malnutrition"]["wasting_rate"]}%
Severe wasting: {country["who_malnutrition"]["severe_wasting_rate"]}%
Stunting: {country["who_malnutrition"]["stunting_rate"]}%
Diabetes 18+: {country["who_diabetes"]["prevalence_18plus_crude"]}%
Available stock: {stock_str}
Write exactly 3 sentences.
Sentence 1: Which food types to prioritize and why based on the nutrition data.
Sentence 2: Specific allocation proportions (therapeutic vs supplementary vs general).
Sentence 3: Which population subgroups need specialized support and what type.
Specific. Reference actual percentages."""
    return _call_gemini(prompt, context=f"supply rec {country['name']}")


def generate_situation_report(country: dict) -> str:
    """WFP/OCHA-style professional situation report."""
    m = country["who_malnutrition"]
    d = country["who_diabetes"]
    prompt = f"""You are a WFP situation report writer.
Generate a professional humanitarian situation report for {country["name"]}.
Data:
- NVI: {country.get("nvi_score")} (Nutritional Vulnerability Index 0-1)
- Child wasting (GAM): {m["wasting_rate"]}% (WHO crisis threshold: 15%)
- Severe wasting (SAM): {m["severe_wasting_rate"]}%
- Stunting: {m["stunting_rate"]}%
- Diabetes 18+: {d["prevalence_18plus_crude"]}%
- Survey year: {m["survey_year"]}
- Source: {m["source"]}
Write with these sections:
SITUATION OVERVIEW (2 sentences)
VULNERABILITY PROFILE (3 bullet points with numbers)
PRIORITY POPULATIONS (2 sentences on who is most at risk)
RECOMMENDED ACTIONS (3 bullet points, specific and actionable)
NEXT ASSESSMENT (1 sentence on data gaps and next steps)
Professional humanitarian language. Precise and data-driven."""
    return _call_gemini(prompt, context=f"sitrep {country['name']}")
