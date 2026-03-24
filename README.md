# DATA236 Lab 1 - Yelp Prototype

A Yelp-style restaurant discovery and review platform built with **FastAPI + MySQL + React + Vite**.

## What is included

- Reviewer signup, login, profile, preferences, favorites, history, restaurant posting, and review CRUD
- Restaurant owner signup, claim restaurant, owner profile, restaurant editing, and owner analytics dashboard
- AI assistant endpoint and chatbot UI for personalized restaurant recommendations
- Swagger API docs at `/docs`

## Tech stack

- Backend: FastAPI, SQLAlchemy, JWT auth, Passlib, PyMySQL
- Frontend: React, React Router, Axios, Vite
- Database: MySQL
- AI helper layer: LangChain-style prompt parsing + optional Tavily live context

## Project structure

- `app/` - FastAPI backend
- `frontend/` - React frontend
- `scripts/seed_yelp_business.py` - optional Yelp business import
- `.env.example` - backend environment template
- `LAB1_COMPLETION_GUIDE.md` - step-by-step final submission guide

## Backend setup

1. Create a MySQL database named `lab1_yelp`.
2. Copy `.env.example` to `.env`.
3. Update `DATABASE_URL` with your MySQL username and password.
4. Create a virtual environment and install dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on `http://localhost:5173` and proxies backend routes to `http://localhost:8000`.

## Environment variables

Backend `.env` values:

```env
DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/lab1_yelp
SECRET_KEY=change-this-to-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
TAVILY_API_KEY=
```

## Core API routes

### Auth
- `POST /auth/signup`
- `POST /auth/login`

### User
- `GET /users/me`
- `PUT /users/me`
- `GET /users/me/preferences`
- `PUT /users/me/preferences`
- `GET /users/me/history`

### Restaurants
- `POST /restaurants/`
- `GET /restaurants/`
- `GET /restaurants/search`
- `GET /restaurants/{restaurant_id}`
- `PUT /restaurants/{restaurant_id}`
- `DELETE /restaurants/{restaurant_id}`
- `POST /restaurants/{restaurant_id}/claim`
- `GET /restaurants/{restaurant_id}/dashboard`

### Reviews and favorites
- `POST /reviews/`
- `GET /reviews/restaurant/{restaurant_id}`
- `PUT /reviews/{review_id}`
- `DELETE /reviews/{review_id}`
- `POST /favorites/{restaurant_id}`
- `GET /favorites/`
- `DELETE /favorites/{restaurant_id}`

### AI assistant
- `POST /ai-assistant/chat`

## Optional Yelp dataset import

If you have the Yelp Open Dataset business JSON, you can import restaurants:

```bash
python3 scripts/seed_yelp_business.py \
  --business-json /path/to/yelp_academic_dataset_business.json \
  --state CA \
  --limit 30 \
  --truncate
```

## Final submission cleanup

Do **not** submit:

- `venv/`
- `frontend/node_modules/`
- `__pycache__/`
- `.git/`
- `.env`
- local database files like `test.db`

Submit:

- source code
- `requirements.txt`
- `README.md`
- screenshots/report
- Swagger screenshots or Postman collection

## Documentation checklist

Before submission, capture screenshots for:

- Home page with AI assistant
- Explore/search page
- Restaurant details page
- Reviewer profile and preferences
- Write/edit review flow
- Owner profile
- Owner dashboard
- Swagger docs and tested endpoints

## Notes

- Reviewer preferences now include **search radius**.
- Owners are automatically linked to restaurants they create.
- Owner analytics now include **recent reviews**, **rating distribution**, and **public sentiment**.
- The AI assistant now considers cuisine, budget, locations, dietary needs, ambiance, and sort preference.
