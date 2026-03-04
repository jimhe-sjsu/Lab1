# DATA236 Lab 1 - Restaurant Discovery App

This repository contains my Lab 1 project for DATA236. The goal is to build a Yelp-style restaurant platform with core user flows for authentication, discovery, reviews, activity tracking, and recommendation/chat interaction.

## Project Scope

The assignment focuses on these product tasks:

- React routes + layout + responsive navbar
- Axios client + auth handling
- Signup/login pages
- Profile/preferences editor page
- Explore/search page with filters + cards
- Restaurant details page + reviews list
- Add restaurant form + write review form
- Favorites + history tabs
- Chat widget UI + clickable restaurant cards
- Screenshot-ready UI flows for report submission

## Repository Structure

- `frontend/` - React + Vite frontend application for Lab 1
  - detailed app docs: [`frontend/README.md`](./frontend/README.md)

## Current Status

- Frontend scaffold is implemented and runnable.
- UI flows are available with mock data and mock auth for demo/report screenshots.
- Axios/API structure is in place for backend integration.

## Quick Start

From this root directory:

```bash
cd frontend
npm install
npm run dev
```

Build and lint:

```bash
npm run build
npm run lint
```

## Notes

- This repo is currently local and can be pushed later when ready.
- For real backend integration, configure `frontend/.env` using `frontend/.env.example` and wire endpoints for auth, users, restaurants, reviews, favorites, and history.
