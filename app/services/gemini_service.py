import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

def _get_client():
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    return genai.Client(api_key=key)

def generate_coordinator_brief(ward, forecast, nvi):
    prompt = f"""Ward: {ward}
Nutritional Vulnerability Index (0-1, higher = more vulnerable): {nvi}
Forecast peak risk: {forecast['peak_risk']} on day {forecast['peak_day']}
Active signals: NOAA alert={forecast['signals']['noaa_alert']}, SNAP cycle day={forecast['signals']['snap_cycle_day']}, unemployment delta={forecast['signals']['unemployment_delta']}

Write a 3-sentence action brief for a coordinator.
Sentence 1: summarize the risk level and timeline.
Sentence 2: specific actions to take in the next 48 hours.
Sentence 3: which populations to prioritize and why.
Keep it direct and actionable, no filler."""
    client = _get_client()
    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return response.text

def parse_food_point_description(raw_text: str) -> dict:
    prompt = f"""Convert this informal food access description into structured JSON.
Raw text: "{raw_text}"

Return ONLY valid JSON with exactly these keys:
name, type (one of: community_fridge/pantry/mutual_aid/church/food_bank),
address, hours, food_types (list), dietary_flags (list), notes

No explanation, no markdown, just the JSON object."""
    client = _get_client()
    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
