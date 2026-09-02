# BhoomiSetu

> Land acquisition & compensation management platform for Indian infrastructure projects.

## Monorepo Structure

```
BHOOMI-SETU/
├── frontend/    – React + TypeScript + Vite SPA
├── backend/     – FastAPI Python service
├── ml/          – ML model artefacts
├── data/        – GeoJSON boundaries, synthetic & training data
└── docs/        – Product & technical documentation
```

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
```

Frontend → http://localhost:5173  
Backend  → http://localhost:8000  
API docs → http://localhost:8000/docs
