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
cd frontend
npm install
npm run dev
```

## Notes

- Frontend currently supports mock auth/data mode for fast UI iteration.
- Switch to real backend by setting `VITE_USE_MOCK_AUTH=false` and wiring the API endpoints.
