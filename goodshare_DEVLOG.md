# GoodShare — Developer Log
## GWU Hackathon 2026 | Cameron P. | Backend Lead | April 18, 2026

---

## ~14:00 ET — Project Conception

Team aligned on Track 2, Problem Statement 3.
Project name went: NutriTrack → GoodShare → AidNet → GoodShare.
Ash proposed the Sudan 45-day-warning framing.

LESSON: Settle on a name before touching the filesystem. Renaming folders mid-build caused ~45 minutes of debugging.

---

## ~14:30 ET — Flask Structure Built

Created app/ with blueprints for points, crisis, forecast, gemini.
Chose google-genai over deprecated google-generativeai.

LESSON: Check if a library is deprecated before building on it. The old package used gRPC; the new one uses REST and has cleaner error handling.

---

## ~15:00 ET — Seed Data Created

food_points.json: 15 real DC food access locations with coordinates, dietary flags, ward assignments.
dietary_flags (halal, kosher, diabetic_friendly, infant_formula) directly power the AI brief.

---

## ~15:30 ET — All API Endpoints Confirmed Working

Tested via curl:
- /api/points → 200
- /api/crisis/status → 200
- /api/crisis/points → 200
- /api/forecast/ward7 → 200
- /api/forecast/ward8 → 200

Full backend operational before touching the frontend.

---

## ~16:00 ET — Gemini Integration — First Attempt

ERROR: ValueError: Missing key inputs argument
ROOT CAUSE: .env file had raw key without variable name prefix.
File contained: AIzaSy...
Should have been: GEMINI_API_KEY=AIzaSy...

FIX: echo "GEMINI_API_KEY=value" > .env
LESSON: Always use echo for single-line .env writes. Never heredoc. Always verify with cat .env before starting the server.

---

## ~16:30 ET — Gemini Quota Exhausted

ERROR: 429 RESOURCE_EXHAUSTED, limit: 0
ROOT CAUSE: Free tier daily quota exhausted from failed test calls. All keys in the same Google project share the same quota pool — using a different key from the same project doesn't help.

FIX: Get a key from a different Google account (different project = fresh quota).
LESSON: Before any hackathon, have a backup Gemini key from a different Google account. The free tier resets at midnight Pacific.

---

## ~16:45 ET — Package Mismatch

ERROR: 400 API_KEY_INVALID when using google.generativeai (old package)
ROOT CAUSE: gemini_service.py still imported google.generativeai after it was uninstalled.
FIX: Updated all imports to use google.genai and client.models.generate_content().

---

## ~17:00 ET — Ash's Data Architecture Drop

Ash proposed FEWS NET + ACLED + CHIRPS + WFP VAM architecture.
The Sudan/45-day framing replaced the original DC tropical storm hook.

LESSON: Let the data scientist drive the pitch narrative when they have better domain framing. The Sudan anchor is a stronger opening than a weather alert.

---

## ~17:30 ET — Fresh Gemini Key from ADSilberman

Key from different Google account = fresh quota. The code was always correct.
LESSON: When you get 429 with limit: 0, don't debug the code — get a new key from a different project.

---

## ~18:00 ET — Frontend Dashboard Built

goodshare_dashboard.html: Leaflet map, Chart.js risk curve, NVI bars, Gemini brief button.
Used const API = 'http://127.0.0.1:8080' as base URL constant — port changes are one edit.
Added catch() fallback for when Gemini quota is exhausted — shows hardcoded brief instead of crashing.

---

## ~18:15 ET — Folder Rename Chaos

WHAT HAPPENED: mv ~/Documents/aidnet ~/Documents/goodshare
EXPECTED: aidnet renamed to goodshare
ACTUAL: aidnet folder moved INSIDE goodshare (goodshare/aidnet/)

ROOT CAUSE: On macOS, mv source dest when dest already exists MOVES source INTO dest, not over it. For a rename to work, the destination must not exist.

CASCADING EFFECTS:
- venv path broke (source venv/bin/activate failed)
- app/ routes/ all paths broke
- Had to rebuild venv from scratch
- Had to manually re-create all route files

FIX: mv ~/Documents/goodshare/aidnet/* ~/Documents/goodshare/ to move files up one level.

LESSON: Check whether destination directory exists before mv. Use: mv source dest only when dest does not exist.

---

## ~18:30 ET — Git Re-initialization + venv Commit

PROBLEM 1: .git folder lost during folder move. Had to git init + git remote add + git fetch.
PROBLEM 2: git add . before creating .gitignore committed entire venv/ — 1799 files, ~40MB.

FIX:
git rm -r --cached venv/
echo "venv/" > .gitignore
echo ".env" >> .gitignore
git commit -m "chore: remove venv from tracking"
git push origin main --force

LESSON: .gitignore BEFORE the first git add. Always. The three things that always go in .gitignore for Python: venv/, .env, __pycache__/

---

## ~18:45 ET — Dashboard Live

http://127.0.0.1:8080 loads full GoodShare dashboard.
Map loads with 15 pins (7 red crisis, 8 green normal).
14-day risk curve renders.
NVI bars display.
All 5 API endpoints confirmed.

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| google-genai over google-generativeai | Old package deprecated, uses gRPC; new uses REST |
| Port 8080 over 5000 | macOS AirPlay uses 5000 by default |
| Single HTML file frontend | No build step, no node_modules, opens in browser immediately |
| goodshare_ prefix on all route files | Prevents naming conflicts with other projects |
| Hardcoded forecast data | Acceptable for hackathon; real integration uses FEWS NET API |
| Flask factory pattern (create_app) | Standard Flask production pattern, avoids circular imports |

---

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| heredoc> stuck | EOF not on its own line | Type EOF Enter, or use echo |
| ValueError: Missing key inputs | .env missing KEY= prefix | echo "KEY=value" > .env |
| 400 API_KEY_INVALID | Bad/expired key | Fresh key from aistudio.google.com |
| 429 RESOURCE_EXHAUSTED limit:0 | Daily quota exhausted (project-level) | Key from different Google account |
| Address already in use Port 5000 | macOS AirPlay Receiver | Change to port 8080 |
| source: no such file venv/bin/activate | venv lost during folder move | python3 -m venv venv |
| Not Found at / | No route for / registered | Add @app.route('/') to __init__.py |
| fatal: not a git repository | .git folder lost | git init + git remote add |
| push rejected non-fast-forward | Diverged histories | git push --force |
| 1799 files committed | venv committed before .gitignore | git rm -r --cached venv/ |

---

## File Naming Convention (Going Forward)

All files in a project should be prefixed with the project name to avoid
conflicts when multiple projects are open at once:

goodshare_README.md
goodshare_DEVLOG.md
goodshare_dashboard.html
goodshare_points.py
goodshare_crisis.py
goodshare_forecast.py
goodshare_gemini.py
goodshare_gemini_service.py

This prevents confusion in editors, terminals, and git diffs when working
on multiple projects simultaneously.

---

## What's Next

- [ ] Wire FEWS NET API for real IPC phase data
- [ ] ACLED conflict event overlay on map
- [ ] MongoDB Atlas for persistent food point storage
- [ ] Province-level malnutrition data (Ash — wasting/severe_wasting columns ready)
- [ ] Census API demographic pull for real NVI
- [ ] Deploy to Railway or Render for live Devpost URL
