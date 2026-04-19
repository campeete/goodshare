# CrisisFeed — Food Crisis Early Warning System

> GWU Hackathon 2026 · Track 2: GW Global Food Institute
> Problem Statement 3: "Feeding Communities When It Matters Most"

## The Problem

When conflict broke out in Sudan in 2023, the WFP took 3 weeks to establish food aid access. FEWS NET data showed deteriorating food security around Khartoum 45 days before the conflict began. The signals existed. The translation layer did not. CrisisFeed is that translation layer.

## What It Does

- Maps 15 real DC food access points (community fridges, pantries, mutual aid networks)
- Identifies crisis zones Ward 7 and Ward 8 based on NOAA alerts and SNAP cycle timing
- Generates a 14-day demand forecast with a Nutritional Vulnerability Index (NVI)
- AI coordinator brief via Gemini 2.0 Flash — 3 sentences, actionable, ward-specific
- Global dashboard covering 6 high-priority countries with real WHO data and NVI scores

## Quick Start

\`\`\`bash
git clone https://github.com/campeete/crisisfeed.git
cd crisisfeed
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "GEMINI_API_KEY=your_key_here" > .env
python3 run.py
\`\`\`

Open http://127.0.0.1:8080

## API Endpoints

| Endpoint | Description |
|---|---|
| GET /api/points | All 15 DC food access points |
| GET /api/crisis/status | Active crisis state and trigger |
| GET /api/crisis/points | Food points filtered to high-risk wards |
| GET /api/forecast/\<ward\> | 14-day risk curve and NVI (ward7 or ward8) |
| GET /api/global/countries | All 6 global countries with NVI scores |
| GET /api/gemini/brief/\<id\> | AI coordinator brief (ward or country) |
| GET /api/gemini/alert/\<code\> | 2-sentence crisis alert |
| GET /api/gemini/report/\<code\> | WFP-style situation report |
| POST /api/gemini/compare | Resource allocation advisor |
| POST /api/gemini/supply/\<code\> | Logistics pre-positioning recommendation |
| POST /api/gemini/parse | Parse informal food point description to JSON |

## Tech Stack

- **Backend:** Python 3.9, Flask, Flask-CORS
- **AI:** Google Gemini 2.0 Flash via google-genai v1.47.0
- **Frontend:** Leaflet.js, Chart.js, HTML/CSS/JS (single file, no build step)
- **Env:** python-dotenv

## Project Structure

\`\`\`
crisisfeed/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── crisisfeed_points.py
│   │   ├── crisisfeed_crisis.py
│   │   ├── crisisfeed_forecast.py
│   │   ├── crisisfeed_global.py
│   │   └── crisisfeed_gemini.py
│   └── services/
│       └── crisisfeed_gemini_service.py
├── data/seed/
│   ├── food_points.json
│   ├── crisisfeed_global_data.json
│   └── crisisfeed_ipc_predicted_vs_actual.csv
├── static/crisisfeed_dashboard.html
├── run.py
├── requirements.txt
└── LICENSE.md
\`\`\`

## NVI Formula

\`\`\`
NVI = 0.35 * wasting_norm
    + 0.30 * stunting_norm
    + 0.20 * diabetes_norm
    + 0.15 * severe_wasting_norm
\`\`\`

Ward 8: 0.86 (highest in DC) | Ward 7: 0.81

## Global Coverage

| Country | Code | IPC Phase |
|---|---|---|
| Haiti | HTI | 4 — Emergency |
| Sudan | SDN | 5 — Catastrophe |
| Ethiopia | ETH | 3 — Crisis |
| Mali | MLI | 3 — Crisis |
| Niger | NER | 3 — Crisis |
| Somalia | SOM | 4 — Emergency |

## Team

| Name | Role |
|---|---|
| Cameron P. | Backend, Gemini integration, dashboard UI |
| Alex | Data architecture, IPC/ACLED datasets, frontend |
| Ash | NVI formula, FEWS NET/ACLED/CHIRPS data architecture |
| Chaeyeon Nicky | Devpost, pitch script, demo video |

## SDG Alignment

- SDG 2 Zero Hunger
- SDG 13 Climate Action
- SDG 17 Partnerships for the Goals

## Data Sources

- [FEWS NET](https://fdw.fews.net/api/ipcphase/?format=json) — IPC food security phase classifications
- [ACLED](https://acleddata.com) — Armed conflict event data
- [WHO Malnutrition Database](https://www.who.int/nutgrowthdb) — Wasting, stunting, severe wasting
- [WHO Diabetes Database](https://www.who.int/data/gho) — Diabetes prevalence 18+
- [NOAA](https://www.weather.gov) — Weather alerts
- [WFP DataBridges](https://databridges.vam.wfp.org) — Future integration

## License

[MIT](LICENSE.md) — Copyright (c) 2026 LoopHackers
