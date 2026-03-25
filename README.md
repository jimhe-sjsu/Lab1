# DATA 236 Lab 1 – Yelp Prototype

A full-stack Yelp-style restaurant discovery and review platform built with **FastAPI**, **MySQL**, **React**, and **Vite**. The project supports two primary personas—**reviewers** and **restaurant owners**—and includes an **AI assistant** for personalized restaurant recommendations.

## Project Summary

This lab implements a restaurant discovery platform inspired by Yelp. Users can create accounts, browse restaurants, manage favorites, write reviews, and save dining preferences. Restaurant owners can manage restaurant information, claim listings, and view dashboard analytics. The application also includes an AI chatbot endpoint that uses user preferences and natural-language prompts to recommend restaurants.

## Features

### Reviewer Features
- User signup and login
- JWT-protected authenticated routes
- Profile management
- Dining preferences management for AI recommendations
- Restaurant search and browse experience
- Restaurant detail view
- Create restaurant listing
- Add, edit, and delete personal reviews
- Favorites and activity/history tracking
- AI chatbot on the home/dashboard experience

### Restaurant Owner Features
- Owner signup and login
- Owner profile management
- Post new restaurant listings
- Claim existing restaurants
- Edit restaurant profile details
- View restaurant reviews (read-only)
- Owner dashboard with restaurant analytics

### AI Assistant
- Chat endpoint at `POST /ai-assistant/chat`
- Uses user preferences and natural-language queries
- Supports personalized restaurant recommendations
- Handles refinement/follow-up style conversations
- Can be extended with Tavily live context support

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- MySQL
- PyMySQL
- JWT authentication
- Passlib / bcrypt
- Python dotenv
- LangChain-related packages

### Frontend
- React
- React Router DOM
- Axios
- Vite
- ESLint

## Project Structure

```text
Lab1/
├── app/
│   ├── core/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   ├── database.py
│   └── main.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── pages/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── auth.js
│   │   ├── index.css
│   │   └── main.jsx
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── scripts/
├── uploads/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── seed_data.py
```

## Backend Setup

1. Create a MySQL database named `lab1_yelp`.
2. Create a virtual environment.
3. Install Python dependencies.
4. Copy `.env.example` to `.env` and update database credentials.

### Commands

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Example `.env`

```env
DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/lab1_yelp
SECRET_KEY=change-this-to-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
TAVILY_API_KEY=
```

### Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Backend URLs:
- API root: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Frontend Setup

Open a second terminal and run:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:
- `http://localhost:5173`

The Vite app is configured to communicate with the FastAPI backend on port `8000`.

## Main Frontend Pages

- `/` – Home page
- `/explore` – Restaurant discovery/search page
- `/restaurants/:restaurantId` – Restaurant details page
- `/login` – Login page
- `/signup` – Signup page
- `/profile` – Reviewer profile page
- `/owner/profile` – Owner profile page
- `/restaurants/new` – Add/post restaurant page
- `/restaurants/:restaurantId/review` – Review form
- `/restaurants/:restaurantId/owner-dashboard` – Owner dashboard
- `/my-activity` – Favorites and history page

## Main Backend Routes

### Authentication
- `POST /auth/signup`
- `POST /auth/login`

### Users
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

### Reviews
- `POST /reviews/`
- `GET /reviews/restaurant/{restaurant_id}`
- `PUT /reviews/{review_id}`
- `DELETE /reviews/{review_id}`

### Favorites
- `POST /favorites/{restaurant_id}`
- `GET /favorites/`
- `DELETE /favorites/{restaurant_id}`

### AI Assistant
- `POST /ai-assistant/chat`

## Optional Seed / Dataset Support

This project includes optional scripts for adding sample data.

### Seed sample data

```bash
python seed_data.py
```

### Optional Yelp business import

```bash
python3 scripts/seed_yelp_business.py \
  --business-json /path/to/yelp_academic_dataset_business.json \
  --state CA \
  --limit 30 \
  --truncate
```

## API Documentation

The project supports API testing and documentation through Swagger at `/docs`.

You may also use Postman to validate endpoints during development.

## Submission Checklist

Before submitting, make sure the following are included:
- Source code
- `README.md`
- `requirements.txt`
- Project report
- Screenshots of key pages and API testing
- Swagger screenshots or Postman collection

## Do Not Submit

Remove or exclude the following from your final submission zip:
- `venv/`
- `frontend/node_modules/`
- any `__pycache__/` folders
- `.git/`
- `.env`
- `.DS_Store`
- `__MACOSX`
- merge leftovers such as `.orig` and `.rej` files
- local database files if any

## Recommended Screenshots for Report

Capture screenshots for:
- Home page with AI assistant
- Explore/search page
- Restaurant details page
- Reviewer profile page
- Preferences editor
- Review create/edit flow
- Owner profile page
- Owner dashboard
- Swagger docs with tested endpoints
- Example AI chatbot conversation

## Notes

- Reviewer preferences include search-related choices such as cuisine, price range, location, dietary needs, ambiance, and sort preference.
- The backend serves uploaded files from the `uploads/` directory.
- The application separates concerns using backend route/schema/service layers and frontend page-based routing.

## Author

Prepared for **DATA 236 Lab 1**.
