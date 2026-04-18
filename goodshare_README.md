# GoodShare — Food Crisis Early Warning System

> GWU Hackathon 2026 · Track 2: GW Global Food Institute
> Problem Statement 3: "Feeding Communities When It Matters Most"

## The Problem

When conflict broke out in Sudan in 2023, the WFP took 3 weeks to establish food aid access. FEWS NET data showed deteriorating food security around Khartoum 45 days before the conflict began. The signals existed. The translation layer did not. GoodShare is that translation layer.

## What It Does

- Maps 15 real DC food access points (community fridges, pantries, mutual aid networks)
- Identifies crisis zones Ward 7 and Ward 8 based on NOAA alerts and SNAP cycle timing
- Generates a 14-day demand forecast with a Nutritional Vulnerability Index (NVI)
- AI coordinator brief via Gemini 2.0 Flash — 3 sentences, actionable, ward-specific

## Quick Start

git clone https://github.com/campeete/goodshare.git
cd goodshare
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "GEMINI_API_KEY=your_key_here" > .env
python3 run.py

Open http://127.0.0.1:8080

## API Endpoints

GET  /api/points               All 15 DC food access points
GET  /api/crisis/status        Active crisis state and trigger
GET  /api/crisis/points        Food points filtered to high-risk wards
GET  /api/forecast/<ward>      14-day risk curve and NVI (ward7 or ward8)
GET  /api/gemini/brief/<ward>  AI coordinator brief
POST /api/gemini/parse         Parse informal food point description to JSON

## Tech Stack

Backend:  Python 3.9, Flask, Flask-CORS
AI:       Google Gemini 2.0 Flash via google-genai v1.47.0
Frontend: Leaflet.js, Chart.js, HTML/CSS/JS (single file, no build step)
Env:      python-dotenv

## Project Structure

goodshare/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── goodshare_points.py
│   │   ├── goodshare_crisis.py
│   │   ├── goodshare_forecast.py
│   │   └── goodshare_gemini.py
│   └── services/
│       └── goodshare_gemini_service.py
├── data/seed/food_points.json
├── static/goodshare_dashboard.html
├── run.py
├── requirements.txt
├── goodshare_README.md
└── goodshare_DEVLOG.md

## NVI Formula

NVI = 0.35 * elderly_population_share
    + 0.30 * children_in_poverty_share
    + 0.20 * chronic_condition_households
    + 0.15 * food_desert_proximity

Ward 8: 0.86 (highest in DC)
Ward 7: 0.81

## Team

Cameron P.      Backend, Gemini integration, dashboard UI
Alex            Frontend React/Leaflet map
Ash             NVI formula, FEWS NET/ACLED/CHIRPS data architecture
Chaeyeon Nicky  Devpost, pitch script, demo video

## SDG Alignment

SDG 2 Zero Hunger
SDG 13 Climate Action
SDG 17 Partnerships for the Goals

## Future Data Integration

FEWS NET API:     https://fdw.fews.net/api/ipcphase/?format=json
WFP DataBridges:  https://databridges.vam.wfp.org
ACLED:            Armed conflict events overlay
CHIRPS:           Rainfall data back to 1981
Census API:       Real NVI demographic data per ward

## File Naming Convention

All files in this project are prefixed with goodshare_ to prevent
conflicts when multiple projects are open at once. Apply this pattern
to every new project going forward.

## License

MIT
