# SentinelML — Self-Healing MLOps Platform

SentinelML is an end-to-end MLOps control plane that trains, tracks, deploys, monitors, and **automatically recovers** a fraud-detection model through its full lifecycle:

> **Detect → Diagnose → Retrain → Evaluate → Promote → Deploy → Monitor → Rollback**

It's a portfolio project demonstrating production-oriented ML engineering: experiment tracking (MLflow), a champion/challenger model registry, drift detection (PSI + KS test), composite health scoring, an autonomous self-healing engine, automated rollback, SHAP-based explainability, and a fully live (WebSocket-driven) dashboard.

See [`SYSTEM_REQUIREMENTS.md`](./SYSTEM_REQUIREMENTS.md) for the full specification this project implements.

---

## Quick start (Docker — recommended)

```bash
git clone <this-repo>
cd sentinelml
cp .env.example .env
docker compose up --build
```

Then open:

| Service | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |
| MLflow UI | http://localhost:5000 |

The dashboard opens on the **Overview** page — it will be empty until you complete the demo scenario below.

---

## Demo scenario (2 minutes)

This is the fastest way to see everything work end-to-end.

1. **Datasets** → upload `ml/datasets/samples/transactions.csv` (target column: `fraud`).
2. Click **Train models** on that dataset, select all four algorithms, and start training.
3. Go to **Models** → find the model with the best F1 → click **Deploy**.
4. Go to **Monitoring** → click **Simulate Data Drift**.
   - Watch the **Recovery** page: a workflow appears and walks through Detected → Diagnosing → Retraining → Evaluating → Promoted/Rejected in real time.
5. Back on **Monitoring**, click **Simulate Error Spike** or **Simulate Model Degradation**.
   - If the deployed model's health drops below the configured threshold, SentinelML **automatically rolls back** to the previous champion — watch the **Alert Center** and **Audit Log**.

Everything above is also exercised automatically by `backend/tests/test_self_healing.py` and `test_rollback.py`.

---

## Local development (without Docker)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env            # or export the variables in .env.example manually
uvicorn app.main:app --reload --port 8000
```

By default the backend uses a local SQLite database (`backend/sentinelml.db`) and a local-file MLflow tracking store (`./mlruns`) — no Postgres or MLflow server required for local dev.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Visit http://localhost:5173.

### Generate the sample dataset yourself

A sample dataset is already checked in at `ml/datasets/samples/transactions.csv`, but you can regenerate or resize it:

```bash
python3 scripts/generate_sample_dataset.py --rows 20000 --out ml/datasets/samples/transactions.csv
```

### Run the test suite

```bash
cd backend
pytest -v
```

30 tests covering data validation, drift math, promotion rules, health scoring, and full integration flows (train → deploy → predict, self-healing, rollback).

---

## Architecture

```
                    ┌──────────────────────┐
                    │      Web Frontend    │   React + TypeScript + Tailwind
                    │   (light-theme UI)    │   Real-time via WebSocket
                    └──────────┬───────────┘
                               │  REST + WS  (/api/v1, /api/v1/ws/events)
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI API     │   Control plane
                    └──────────┬───────────┘
             ┌─────────────────┼──────────────────┐
             ▼                 ▼                  ▼
       Training Engine    Monitoring Engine   Deployment
       (sklearn/XGBoost)  (drift/health/perf)  (joblib model serving)
             │                 │
             ▼                 ▼
          MLflow          Self-Healing Engine ── Rollback
             │             (detect→retrain→promote)
             ▼
        PostgreSQL / SQLite (metadata)
```

**Backend:** FastAPI, SQLAlchemy, scikit-learn, XGBoost, MLflow, SHAP, SciPy.
**Frontend:** React, TypeScript, Vite, Tailwind CSS, Recharts.
**Storage:** PostgreSQL (Docker) or SQLite (local dev) for metadata; MLflow's local file store for experiment artifacts.

Full directory layout is documented in `SYSTEM_REQUIREMENTS.md` §48.

---

## What "self-healing" means here

The Self-Healing Engine (`backend/app/self_healing/engine.py`) is triggered either by the background monitoring loop (real drift/performance conditions, checked every `MONITORING_INTERVAL_SECONDS`) or by the dashboard's failure-simulation buttons. It:

1. Records a `RecoveryWorkflow` and logs each step (visible live on the **Recovery** page).
2. Trains a challenger model on the current dataset.
3. Evaluates the challenger against the champion using the configurable promotion rule (`PROMOTION_MIN_IMPROVEMENT`, latency-regression guard).
4. Promotes and deploys the challenger if it passes, or rejects it (with a documented reason) if not.

Automated rollback (`backend/app/self_healing/rollback.py`) runs independently: if the deployed model's composite health score drops below `ROLLBACK_MIN_HEALTH_SCORE` or its error rate exceeds `ROLLBACK_MAX_ERROR_RATE`, SentinelML restores the most recently archived (previously healthy) champion — no human involved.

---

## Configuration

Nothing is hard-coded — every threshold lives in `backend/app/core/config.py`, is overridable via environment variables (see `.env.example`), and can additionally be hot-adjusted at runtime from the dashboard's **Settings** page (backed by `GET/PATCH /api/v1/config`).

---

## API

Interactive docs: **http://localhost:8000/docs** (auto-generated OpenAPI/Swagger).

Key endpoints (all under `/api/v1`, plus a top-level `/health`):

```
POST   /datasets/upload
POST   /training/start
GET    /models
POST   /models/{id}/deploy
POST   /models/{id}/rollback
GET    /models/{id}/explainability/global
POST   /models/{id}/explainability/predict
POST   /predict
GET    /monitoring/overview | /drift | /performance
GET    /alerts
GET    /audit-log
GET    /recovery
POST   /simulation/drift | /degradation | /latency | /errors
GET    /config          PATCH  /config
WS     /ws/events
```

---

## Notes on scope

This is a portfolio-scale system, per its own design philosophy (`SYSTEM_REQUIREMENTS.md` §3):

- MLflow runs with a **local file store** — no separate tracking server database required to run the demo, though `docker-compose.yml` includes an `mlflow` service (with a UI) for a fuller demonstration.
- Explainability uses SHAP's `TreeExplainer` for tree-based models and closed-form linear contributions for `LogisticRegression`; the RBF-kernel SVM falls back to a documented approximation rather than an expensive `KernelExplainer`.
- Background jobs use FastAPI's async event loop directly rather than Celery/Redis, per the "prefer the simplest reliable solution" guidance in §36.
- Authentication is not implemented (optional per §38/§52) — do not expose this deployment on the open internet without adding it first.

---

## License

Portfolio / demonstration project. No license restrictions implied — adapt freely.
