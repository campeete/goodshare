import os, json
from dotenv import load_dotenv
from google import genai

load_dotenv()

def _client():
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    return genai.Client(api_key=key)

def generate_coordinator_brief(ward, forecast, nvi):
    prompt = f"""Ward: {ward}
NVI: {nvi}
Peak risk: {forecast['peak_risk']} on day {forecast['peak_day']}
Signals: NOAA={forecast['signals']['noaa_alert']}, SNAP day={forecast['signals']['snap_cycle_day']}, unemployment delta={forecast['signals']['unemployment_delta']}

Write a 3-sentence coordinator brief.
Sentence 1: risk level and timeline.
Sentence 2: actions in next 48 hours.
Sentence 3: populations to prioritize and why.
Direct and actionable only."""
    r = _client().models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return r.text

def parse_food_point_description(raw_text):
    prompt = f"""Convert to JSON: "{raw_text}"
Keys: name, type (community_fridge/pantry/mutual_aid/church/food_bank), address, hours, food_types (list), dietary_flags (list), notes
Return ONLY valid JSON, no markdown."""
    r = _client().models.generate_content(model='gemini-2.0-flash', contents=prompt)
    text = r.text.strip().lstrip('```json').lstrip('```').rstrip('```').strip()
    return json.loads(text)

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
        logger.error(f"Gemini returned invalid JSON for {context}: {text[:300]}")
        raise ValueError(f"Model returned invalid JSON: {e}")


def ingest_country_data(raw_text: str) -> dict:
    prompt = f"""You are a humanitarian data extraction tool.
Extract food security and nutrition data from this text and return ONLY valid JSON.
Text: "{raw_text}"
Return a JSON object with exactly these keys:
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
  "conflict_events": number or null,
  "notes": "any other relevant data"
}}
All percentages as numbers. Null if not mentioned. No markdown. Only JSON."""
    return _call_gemini_json(prompt, context="country data ingestion")


def generate_crisis_alert(country: dict, signals: dict) -> str:
    prompt = f"""You are a humanitarian crisis alert system.
Country: {country["name"]}
NVI Score: {country.get("nvi_score")}
Wasting rate: {country["who_malnutrition"]["wasting_rate"]}%
Diabetes prevalence: {country["who_diabetes"]["prevalence_18plus_crude"]}%
IPC Phase: {signals.get("ipc_phase", "unknown")}
Write a 2-sentence crisis alert for humanitarian coordinators.
Sentence 1: Urgency level and which population is most at risk with specific numbers.
Sentence 2: The single most critical action needed in the next 24 hours.
Direct. Use actual numbers. No filler."""
    return _call_gemini(prompt, context=f"crisis alert for {country['name']}")


def compare_countries(country_a: dict, country_b: dict) -> str:
    prompt = f"""You are a humanitarian resource allocation advisor.
Country A: {country_a["name"]} — NVI {country_a.get("nvi_score")}, Wasting {country_a["who_malnutrition"]["wasting_rate"]}%, Severe wasting {country_a["who_malnutrition"]["severe_wasting_rate"]}%, Diabetes {country_a["who_diabetes"]["prevalence_18plus_crude"]}%
Country B: {country_b["name"]} — NVI {country_b.get("nvi_score")}, Wasting {country_b["who_malnutrition"]["wasting_rate"]}%, Severe wasting {country_b["who_malnutrition"]["severe_wasting_rate"]}%, Diabetes {country_b["who_diabetes"]["prevalence_18plus_crude"]}%
Write 3 sentences:
Sentence 1: Which country needs immediate intervention and why with specific numbers.
Sentence 2: What type of food support each needs differently.
Sentence 3: How to split resources if you can only fund one operation."""
    return _call_gemini(prompt, context=f"compare {country_a['name']} vs {country_b['name']}")
