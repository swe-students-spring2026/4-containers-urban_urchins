[![lint-free](https://github.com/swe-students-spring2026/4-containers-urban_urchins/actions/workflows/lint.yml/badge.svg)](https://github.com/swe-students-spring2026/4-containers-urban_urchins/actions/workflows/lint.yml)
[![ML Client Tests](https://github.com/swe-students-spring2026/4-containers-urban_urchins/actions/workflows/ml_client.yml/badge.svg)](https://github.com/swe-students-spring2026/4-containers-urban_urchins/actions/workflows/ml_client.yml)
[![Web App Tests](https://github.com/swe-students-spring2026/4-containers-urban_urchins/actions/workflows/webapp.yml/badge.svg)](https://github.com/swe-students-spring2026/4-containers-urban_urchins/actions/workflows/webapp.yml)

# Emotion Detection Dashboard

This repo is a containerized, multi-service system with three parts:

1. A **machine learning client** that analyzes uploaded face images with DeepFace and predicts the dominant emotion.
2. A **Flask web app** where users upload images and browse recent analysis results.
3. A **MongoDB database** that stores image metadata and emotion predictions.

The web app sends each uploaded image to the ML client, then saves the result in MongoDB so users can review recent history from a dashboard.

## Team

- [Sheldon Xie](https://github.com/FilthyS)
- [Harrison Wong](https://github.com/harrisonmangitwong)
- [Antonio Jackson](https://github.com/antoniojacksnn)
- [Sarah Randhawa](https://github.com/sarahrandhawa)
- [Bryce Lin](https://github.com/blin03)

## Repository Layout

```text
.
|-- docker-compose.yml
|-- .env.example
|-- machine-learning-client/
|   |-- app.py
|   |-- Dockerfile
|   `-- tests/
`-- web-app/
    |-- app.py
    |-- db.py
    |-- Dockerfile
    |-- templates/
    `-- tests/
```

## Prerequisites

Install the following tools:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) or Docker Engine + Compose (Linux)

This project is intended to be run with Docker containers.

## Environment Variables

This repository includes [.env.example](.env.example).

Create a local copy of `.env` at the repository root:

```bash
# macOS / Linux
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

Then ensure `.env` contains at least:

```env
MONGO_URI=mongodb://mongodb:27017
ML_CLIENT_URL=http://ml-client:5000
FLASK_PORT=5000
```

These values are used by the Docker workflow below, where services communicate over a shared Docker network.

Optional variables can be set as needed:

- `MONGO_DBNAME` (default: `emotion_detector`)
- `SECRET_KEY` (default: `dev-secret-key`)
- `ML_CLIENT_URL` (default: `http://ml-client:5000`)
- `FLASK_PORT` (default: `5000`)

## Setup

### 1) Create a shared Docker network

From the repository root:

```bash
docker network create urban-net
```

If the network already exists, Docker will return an error that can be ignored.

### 2) Start MongoDB

```bash
docker run --rm --name mongodb --network urban-net -p 27017:27017 mongo
```

Keep this terminal open.

### 3) Build images

```bash
docker build -t ml-client ./machine-learning-client
docker build -t web-app ./web-app
```

### 4) Start ML client (new terminal)

```bash
docker run --rm --name ml-client --network urban-net ml-client
```

Keep this terminal open.

### 5) Start web app (new terminal)

```bash
docker run --rm --name web-app \
	--network urban-net \
	--env-file .env \
	-p 8000:5000 \
	web-app
```

Notes:

- Open http://localhost:8000 in your browser.

## Starter Data Import

No starter dataset is required for the system to run, but you can seed sample records for demo/testing.

1. Start MongoDB:

```bash
docker compose up -d mongodb
```

2. Insert sample records:

```bash
docker exec -i mongodb mongosh emotion_detector --eval '
db.images.insertMany([
	{
		filename: "sample-happy.jpg",
		dominant_emotion: "happy",
		uploaded_at: new Date()
	},
	{
		filename: "sample-neutral.jpg",
		dominant_emotion: "neutral",
		uploaded_at: new Date()
	}
]);
'
```

## Running Tests

From each subsystem directory:

### ML client

```bash
cd machine-learning-client
pipenv install --dev
pipenv run pytest --cov=. tests/*
```

### Web app

```bash
cd web-app
pipenv install --dev
pipenv run pytest --cov=. tests/*
```
