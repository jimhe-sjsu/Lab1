# Lab 1 Completion Guide

This guide tells you exactly what to finish, in the right order, so your project is submission-ready.

## 1. Switch fully to MySQL

Why:
- The assignment requires **MySQL**, not SQLite.

Do this:
1. Install MySQL locally.
2. Create a database named `lab1_yelp`.
3. Copy `.env.example` to `.env`.
4. Update `DATABASE_URL`.
5. Run the backend and verify the app creates tables.

Example:
```env
DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/lab1_yelp
```

## 2. Start the backend and verify Swagger

```bash
uvicorn app.main:app --reload --port 8000
```

Open:
- `http://localhost:8000/docs`

Test these routes in Swagger:
- signup
- login
- get/update profile
- get/update preferences
- list/search restaurants
- create/update restaurant
- create/update/delete review
- favorites
- owner dashboard
- ai assistant chat

## 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open:
- `http://localhost:5173`

## 4. Test every required flow

### Reviewer flow
- Sign up as reviewer
- Log in
- Update profile
- Save preferences, including search radius
- Search restaurants
- Open restaurant details
- Add review
- Edit review
- Delete review
- Add favorite
- Open history/favorites
- Use AI assistant

### Owner flow
- Sign up as owner
- Update owner profile
- Post a restaurant
- Confirm owner is automatically linked
- Claim an existing restaurant
- Open owner dashboard
- Confirm analytics and recent reviews appear

## 5. Take screenshots for the report

Capture these screens:
- Home page with chatbot
- Explore page with filters
- Restaurant details page
- Reviewer profile and preferences
- Review submission page
- Favorites/history page
- Owner profile
- Owner dashboard
- Swagger docs with tested endpoints

## 6. Complete the report

Use this structure:

### Introduction
Explain the purpose of the Yelp prototype and the two personas.

### System Design
Describe:
- React frontend
- FastAPI backend
- MySQL database
- JWT authentication
- AI assistant service

### AI Implementation
Explain:
- how user preferences are loaded
- how natural language is parsed
- how restaurants are filtered and ranked
- how Tavily is optionally used for live context

### Results
Insert screenshots and describe:
- successful auth
- restaurant search
- reviews
- favorites/history
- owner dashboard
- AI assistant examples
- Swagger tests

## 7. Clean the final ZIP before submitting

Remove these folders/files:
- `venv/`
- `frontend/node_modules/`
- `__pycache__/`
- `.git/`
- `.env`
- `test.db`
- `.DS_Store`
- `__MACOSX/`

Keep:
- `app/`
- `frontend/`
- `scripts/`
- `requirements.txt`
- `README.md`
- report/screenshots/Postman collection if required

## 8. Important files already updated in this fixed source

### Backend
- `app/database.py`
- `app/core/security.py`
- `app/main.py`
- `app/models/user.py`
- `app/routes/users.py`
- `app/routes/restaurants.py`
- `app/routes/reviews.py`
- `app/services/ai_service.py`
- `.env.example`

### Frontend
- `frontend/src/pages/Explore.jsx`
- `frontend/src/pages/Profile.jsx`
- `frontend/src/pages/Home.jsx`
- `frontend/src/pages/AddRestaurant.jsx`
- `frontend/src/pages/OwnerProfile.jsx`
- `frontend/src/pages/OwnerDashboard.jsx`

## 9. Remaining optional improvements

These are optional, not blockers:
- real file upload storage instead of image URLs
- Postman collection export
- extra charts on owner dashboard
- stronger LLM integration if your instructor expects a true model-backed chatbot

## 10. Final demo checklist

Before submission or demo, confirm:
- backend runs on port 8000
- frontend runs on port 5173
- MySQL connection works
- reviewer and owner accounts both work
- AI assistant returns recommendations
- Swagger loads without server errors
- README instructions match the actual app behavior
