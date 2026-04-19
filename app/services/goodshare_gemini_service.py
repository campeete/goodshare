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
