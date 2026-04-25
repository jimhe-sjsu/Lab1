# DATA 236 Lab 2 – Yelp Microservices Prototype

This repository upgrades the Lab 1 Yelp-style prototype into the Lab 2 architecture required by the assignment:

- 4 backend services: `user-service`, `owner-service`, `restaurant-service`, `review-service`
- 1 frontend container served by Nginx
- MongoDB for operational data
- Kafka for asynchronous review create/update/delete flows
- Redux Toolkit in the React frontend
- Docker Compose for local orchestration
- Kubernetes manifests for local clusters and AWS EKS deployment

The original Lab 1 FastAPI + MySQL code is still present under `app/` so the migration script can copy existing relational data into MongoDB.

## Architecture

### Service split

- `services/user_service/app.py`
  - reviewer signup/login/logout
  - profile and dining preferences
  - favorites/history
  - uploads
  - AI assistant
- `services/owner_service/app.py`
  - owner signup/login/logout
  - owner profile
  - restaurant claim flow
  - owner dashboard
- `services/restaurant_service/app.py`
  - restaurant CRUD
  - search/list/detail APIs
- `services/review_service/app.py`
  - review listing
  - async review create/update/delete producer endpoints
  - review job status API
- `services/review_service/worker.py`
  - Kafka consumer that processes review events and writes to MongoDB

### Shared backend package

`backend_shared/` contains shared configuration, MongoDB helpers, JWT/session handling, serializers, AI helpers, ID counters, Kafka utilities, activity logging, and review job helpers.

### Frontend

The React app now uses Redux Toolkit slices for:

- `auth`
- `restaurants`
- `reviews`
- `favourites`

The frontend talks to the split services through these prefixes:

- `/api/user/*`
- `/api/owner/*`
- `/api/restaurant/*`
- `/api/review/*`

In Docker and Kubernetes, the frontend Nginx container reverse-proxies those paths to the appropriate services.

## Data model

MongoDB collections used by the Lab 2 runtime:

- `users`
- `preferences`
- `sessions`
- `restaurants`
- `reviews`
- `favorites`
- `activity_logs`
- `review_jobs`
- `counters`

The `sessions` collection uses a TTL index on `expires_at`.

## Kafka flow

Kafka is used for asynchronous review mutations.

Topics:

- `review.created`
- `review.updated`
- `review.deleted`
- `booking.status`

Flow:

1. Frontend submits a review mutation to `review-service`.
2. `review-service` creates a job record in `review_jobs` and returns `202 Accepted`.
3. `review-service` publishes an event to Kafka.
4. `review-worker` consumes the event and applies the MongoDB write.
5. `review-worker` publishes completion or failure to `booking.status`.
6. `review-service` consumes `booking.status` and updates the stored job status.
7. Frontend polls `GET /review-jobs/{job_id}` until the job completes.

## Repository layout

```text
Lab1/
├── app/                         # Original Lab 1 FastAPI + SQLAlchemy code retained for migration
├── backend_shared/              # Shared Lab 2 backend package
├── deploy/
│   └── k8s/                     # Kubernetes manifests
├── frontend/
│   ├── nginx/
│   └── src/
│       └── store/               # Redux Toolkit store and slices
├── jmeter/                      # JMeter load-test plan
├── scripts/
│   └── migrate_mysql_to_mongo.py
├── services/                    # Lab 2 FastAPI service entrypoints and review worker
├── uploads/
├── Dockerfile.user-service
├── Dockerfile.owner-service
├── Dockerfile.restaurant-service
├── Dockerfile.review-service
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Environment configuration

Copy the root `.env.example` to `.env` for Python services:

```bash
cp .env.example .env
```

Important variables:

- `DATABASE_URL` for the Lab 1 MySQL source database
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `JWT_SECRET_KEY`
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_TOPIC_REVIEW_CREATED`
- `KAFKA_TOPIC_REVIEW_UPDATED`
- `KAFKA_TOPIC_REVIEW_DELETED`
- `KAFKA_TOPIC_REVIEW_STATUS`
- `REVIEW_STATUS_CONSUMER_ENABLED`
- `CORS_ORIGINS`

Copy `frontend/.env.example` to `frontend/.env` if you want to override the default frontend proxy paths during local Vite development.

## Local development

### 1. Install Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Start MongoDB and Kafka locally

You can use the Docker Compose services below or your own local services.

### 4. Migrate Lab 1 MySQL data to MongoDB

Make sure MySQL is running and `DATABASE_URL` points at your Lab 1 database.

```bash
python3 scripts/migrate_mysql_to_mongo.py --drop-existing
```

### 5. Run the backend services

Open separate terminals or use a process manager:

```bash
uvicorn services.user_service.app:app --reload --port 8001
uvicorn services.owner_service.app:app --reload --port 8002
uvicorn services.restaurant_service.app:app --reload --port 8003
uvicorn services.review_service.app:app --reload --port 8004
python3 -m services.review_service.worker
```

### 6. Run the frontend

```bash
cd frontend
npm run dev
```

Local URLs:

- Frontend: `http://localhost:5173`
- User service: `http://localhost:8001/docs`
- Owner service: `http://localhost:8002/docs`
- Restaurant service: `http://localhost:8003/docs`
- Review service: `http://localhost:8004/docs`

## Docker Compose

The repository includes a full local stack:

- `frontend`
- `user-service`
- `owner-service`
- `restaurant-service`
- `review-service`
- `review-worker`
- `mongodb`
- `kafka`

Run:

```bash
docker compose up --build
```

Docker Compose URLs:

- Frontend: `http://localhost:8080`
- User service: `http://localhost:8001/docs`
- Owner service: `http://localhost:8002/docs`
- Restaurant service: `http://localhost:8003/docs`
- Review service: `http://localhost:8004/docs`
- MongoDB: `mongodb://localhost:27017`

The frontend container reverse-proxies service requests so the browser only needs the frontend origin.

## Kubernetes

All Kubernetes manifests are under `deploy/k8s/`.

Resources included:

- namespace
- ConfigMap
- Secret
- MongoDB Deployment + Service
- Kafka Deployment + Service
- `user-service` Deployment + Service
- `owner-service` Deployment + Service
- `restaurant-service` Deployment + Service
- `review-service` Deployment + Service
- `review-worker` Deployment
- `frontend` Deployment + LoadBalancer Service

### Apply locally

```bash
kubectl apply -k deploy/k8s
```

For local clusters without a cloud load balancer:

```bash
kubectl port-forward svc/frontend 8080:80 -n lab2-yelp
```

### Image names

The manifests reference these image tags:

- `lab2-yelp/frontend:latest`
- `lab2-yelp/user-service:latest`
- `lab2-yelp/owner-service:latest`
- `lab2-yelp/restaurant-service:latest`
- `lab2-yelp/review-service:latest`

Update the image names or retag them before deploying to EKS/ECR.

## AWS EKS deployment flow

One workable submission flow:

1. Build and tag the 5 scored images locally.
2. Push them to Amazon ECR.
3. Update the Kubernetes manifests to use your ECR image URIs.
4. Create or connect to an EKS cluster.
5. Apply `deploy/k8s/`.
6. Verify pods and services are running.
7. Capture screenshots of:
   - running services/pods
   - frontend exposed from AWS
   - Redux DevTools state
   - JMeter graphs/results

Useful commands:

```bash
kubectl get pods -n lab2-yelp
kubectl get svc -n lab2-yelp
kubectl logs deployment/review-worker -n lab2-yelp
```

## Frontend state management

Redux Toolkit lives in `frontend/src/store/`.

Slices:

- `authSlice.js`
- `restaurantsSlice.js`
- `reviewsSlice.js`
- `favouritesSlice.js`

Use Redux DevTools to capture the required screenshots for `Auth`, `Restaurant`, `Review`, and `Favourites`.

## JMeter

The base load-test plan is stored at:

- `jmeter/lab2-yelp-load-test.jmx`

It covers:

- login
- restaurant search
- review submission

The plan is parameterized so you can run the required concurrency levels:

- 100 users
- 200 users
- 300 users
- 400 users
- 500 users

Recommended workflow:

1. Open the `.jmx` file in JMeter.
2. Set `THREADS`, `RAMP_UP`, and user credentials.
3. Run the plan against your Docker Compose or EKS deployment.
4. Export result CSV files and response-time graphs for the report.

### Scale MongoDB for load tests

Use the Mongo scale seed script when you need larger local data for JMeter:

```bash
python3 scripts/seed_mongo_scale_data.py --users 10000 --restaurants 10000 --reviews 10000
```

For a Kubernetes-local MongoDB deployment, port-forward MongoDB first:

```bash
kubectl port-forward svc/mongodb 27018:27017 -n lab2-yelp
MONGODB_URL=mongodb://localhost:27018 MONGODB_DATABASE=lab2_yelp \
  python3 scripts/seed_mongo_scale_data.py --users 10000 --restaurants 10000 --reviews 10000 --drop-existing
```

## Validation checklist

- `python3 -m compileall backend_shared services`
- `cd frontend && npm run build`
- `docker compose config`
- `kubectl kustomize deploy/k8s >/tmp/lab2-k8s-rendered.yaml`

## Notes

- The fifth Dockerfile is the frontend container, not Kafka.
- Kafka is deployed as infrastructure in Docker Compose and Kubernetes.
- The original Lab 1 `app/` package is intentionally retained for data migration and reference.
- `venv`, `.venv`, and `__pycache__` remain ignored by `.gitignore`.
