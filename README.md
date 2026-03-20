# DATA236 Lab 1 - Restaurant Discovery App

This repository contains the Lab 1 project with a simplified frontend structure for beginner-friendly collaboration.

## Team Split

- Partner A (Nikhil): backend (database, FastAPI endpoints, auth, reviews, favorites/history, owner dashboard, AI endpoint, Swagger)
- Partner B (Jim): frontend (routes, auth UI, profile, explore, details, forms, favorites/history, report screenshots)

## Current Repo Structure

- `frontend/` - React + Vite application
  - frontend docs: `frontend/README.md`

## Frontend Status

Completed:

- Core UI flows for auth, profile, explore, details, forms, favorites/history
- Responsive navigation and route protection
- Axios client and auth integration points

Deferred:

- Chatbot UI section

## Quick Start

```bash
# backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3000
```

```bash
# frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Import Yelp Business Dataset (Real Data)

This project includes a loader script for Yelp Open Dataset business records:

- Script: `scripts/seed_yelp_business.py`
- Input file: `yelp_academic_dataset_business.json` (JSON lines)

Example import (30 CA restaurants):

```bash
cd /Users/jimhe/Documents/sjsu/DATA236/Lab1
source venv/bin/activate
python3 scripts/seed_yelp_business.py \
  --business-json "/Users/jimhe/.cache/kagglehub/datasets/yelp-dataset/yelp-dataset/versions/4/yelp_academic_dataset_business.json" \
  --state CA \
  --limit 30 \
  --truncate
```

Useful flags:

- `--city "San Jose"` to filter one city.
- `--min-review-count 50` to keep stronger businesses.
- `--update-existing` to update duplicate name/address rows instead of skipping.
- `--dry-run` to preview counts without writing to DB.

## Notes

- Frontend auth is wired to the backend API.
- Some non-auth UI flows still use local placeholder data until the matching backend endpoints are finalized.
