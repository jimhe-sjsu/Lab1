# DATA236 Lab 1 - Frontend (Beginner-Friendly Structure)

This frontend is intentionally simplified for easy collaboration and step-by-step development.

## Current Scope

Implemented now:

- React routes + shared layout + responsive navbar
- Axios client + auth handling
- Signup/login pages
- Profile/preferences editor page
- Explore/search page + filters + cards
- Restaurant details page + reviews list
- Add restaurant form + write review form
- Favorites + history tabs

Deferred for later:

- Chat widget UI + clickable chat suggestion cards

## Simple `src` Structure

```text
src/
  main.jsx
  App.jsx
  index.css
  api.js
  auth.js
  mockData.js
  pages/
    Home.jsx
    Login.jsx
    Signup.jsx
    Profile.jsx
    Explore.jsx
    RestaurantDetails.jsx
    AddRestaurant.jsx
    WriteReview.jsx
    FavoritesHistory.jsx
```

## Run

```bash
npm install
npm run dev
```

## Build + Lint

```bash
npm run lint
npm run build
```

## Environment Variables

- `VITE_API_BASE_URL` (leave blank in local development to use the Vite proxy to `http://localhost:3000`)
