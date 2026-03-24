# Lab 1 Report Template

## 1. Introduction
This project implements a Yelp-style restaurant discovery and review system using React for the frontend and FastAPI with MySQL for the backend. The platform supports two personas: reviewer users and restaurant owners. The system allows restaurant discovery, review management, favorites, owner management features, and an AI assistant for restaurant recommendation.

## 2. System Design
### Frontend
- React + Vite
- React Router for navigation
- Axios for API calls
- Responsive UI for desktop and mobile

### Backend
- FastAPI for REST APIs
- SQLAlchemy ORM
- JWT authentication
- Swagger documentation

### Database
- MySQL database storing users, restaurants, reviews, favorites, and preferences

### Key Tables
- Users
- User Preferences
- Restaurants
- Reviews
- Favorites

## 3. AI Implementation
The AI assistant endpoint is `/ai-assistant/chat`.

The assistant works by:
1. Loading the current user's saved preferences from the database.
2. Parsing the natural-language message for cuisine, budget, dietary needs, ambiance, location, and occasion.
3. Filtering the restaurant database.
4. Ranking results using ratings, review count, matching preferences, and optional live context.
5. Returning structured recommendations with reasoning.

Optional live context is supported with Tavily if an API key is configured.

## 4. Implemented Features
### Reviewer Features
- Signup/Login
- Profile management
- Preferences management
- Search restaurants
- View restaurant details
- Add restaurant
- Add/edit/delete review
- Favorites
- History
- AI assistant chatbot

### Owner Features
- Owner signup/login
- Owner profile
- Claim restaurant
- Edit restaurant profile
- View reviews
- Owner dashboard with analytics, rating distribution, and recent reviews

## 5. Results
Insert screenshots here:

### Home Page with AI Assistant
[Insert screenshot]

### Explore/Search Page
[Insert screenshot]

### Restaurant Details Page
[Insert screenshot]

### Profile and Preferences Page
[Insert screenshot]

### Review Submission / Review Management
[Insert screenshot]

### Favorites / History Page
[Insert screenshot]

### Owner Profile Page
[Insert screenshot]

### Owner Dashboard
[Insert screenshot]

### Swagger API Testing
[Insert screenshot]

## 6. Challenges and Fixes
- Migrated from SQLite config to MySQL for assignment compliance.
- Fixed profile serialization so owner restaurant location is returned correctly.
- Added search radius to user preferences.
- Improved owner dashboard to include recent reviews and rating distribution.
- Fixed Explore page so filters from the Home page are carried correctly.
- Added clear chat support for AI assistant UI.

## 7. Conclusion
The project successfully delivers a Yelp-style prototype with reviewer features, owner features, REST APIs, and an AI recommendation component. The system demonstrates full-stack integration across React, FastAPI, MySQL, and AI-assisted restaurant discovery.
