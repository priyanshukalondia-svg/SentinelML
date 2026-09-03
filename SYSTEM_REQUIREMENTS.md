# SentinelML — System Requirements Document

**Project:** SentinelML
**Version:** 2.0 (Enhanced)
**Document Type:** System Requirements Specification
**Purpose:** Portfolio / Demonstration Project
**Status:** Development Specification

> **Revision note (v2.0):** This revision preserves all original v1.0 requirements and adds: a mandatory, detailed visual design system (light theme, professional dashboard polish), real-time updates, API versioning/docs, environment/secrets specification, model artifact storage strategy, rate limiting, accessibility baseline, and expanded testing scope. Nothing from v1.0 was removed.

---

# 1. Project Overview

## 1.1 Project Name

**SentinelML — Self-Healing Machine Learning Platform**

## 1.2 Vision

SentinelML is an end-to-end MLOps platform designed to demonstrate how machine learning systems can be trained, tracked, deployed, monitored, evaluated, and automatically recovered from model or data degradation.

The defining capability of SentinelML is its **self-healing ML lifecycle**:

> Detect → Diagnose → Retrain → Evaluate → Promote → Deploy → Monitor → Rollback

The platform should demonstrate production-oriented ML engineering practices rather than focusing solely on model accuracy — **and it should look and feel like a real, professionally designed product**, not a developer-only debug UI. The dashboard is the first thing a recruiter or hiring manager sees; it must carry its own weight visually.

---

# 2. Primary Objectives

SentinelML must demonstrate the following capabilities:

1. Automated ML model training.
2. Experiment tracking.
3. Model versioning and registry management.
4. Model deployment through an API.
5. Production prediction serving.
6. Data quality monitoring.
7. Data drift detection.
8. Model performance monitoring.
9. Champion–challenger evaluation.
10. Automated retraining.
11. Automated model promotion.
12. Automated rollback.
13. Model lineage.
14. Audit logging.
15. Production-like monitoring.
16. Failure simulation.
17. Explainable predictions.
18. **A polished, visually excellent monitoring dashboard with a light theme as the primary/default experience.**

The platform should feel like a **small real-world MLOps control plane**, not a collection of unrelated ML scripts.

---

# 3. Portfolio Philosophy

SentinelML is primarily a **portfolio and learning project**, not a commercial SaaS product.

Therefore:

* Prioritize technical depth over scalability.
* Prioritize demonstrability over enterprise complexity.
* Prefer simple architectures that can run locally.
* Avoid unnecessary cloud infrastructure.
* Avoid Kubernetes unless there is a compelling reason.
* Avoid unnecessary microservices.
* Avoid implementing features solely for buzzwords.
* Every major feature should be demonstrable through the UI or API.
* The entire system should be runnable on a developer laptop using Docker Compose.
* **Visual polish is not optional.** A technically excellent backend paired with a mediocre-looking dashboard will undersell the project. Budget real effort into the frontend design system (see Section 44).

The final project should be understandable — and visually impressive — to a recruiter or ML/MLOps engineer reviewing the GitHub repository or a live demo/screen recording.

---

# 4. Target User

The primary user is:

> A developer/ML engineer interacting with SentinelML through its web dashboard.

The user should be able to:

* Upload or select a dataset.
* Configure a training run.
* Start model training.
* Compare experiments.
* Register models.
* Deploy a model.
* Generate predictions.
* Monitor production health.
* Inspect drift.
* Simulate failures.
* Observe automatic recovery.
* Inspect model versions and lineage.

A secondary "audience" is anyone reviewing the project asynchronously (via README screenshots, a demo video, or a live-hosted instance) — the dashboard must communicate the system's sophistication within seconds of viewing.

---

# 5. Core System Workflow

The primary workflow is:

```text
Dataset
   ↓
Data Validation
   ↓
Feature Processing
   ↓
Model Training
   ↓
Experiment Tracking
   ↓
Model Evaluation
   ↓
Model Registry
   ↓
Champion / Challenger
   ↓
Deployment
   ↓
Prediction Serving
   ↓
Monitoring
   ↓
Drift / Performance Detection
   ↓
Retraining Trigger
   ↓
Challenger Training
   ↓
Evaluation
   ↓
Promotion / Rejection
   ↓
Deployment
   ↓
Continuous Monitoring
   ↓
Rollback if unhealthy
```

---

# 6. System Architecture

The system should use a modular architecture.

Recommended high-level architecture:

```text
                    ┌──────────────────────┐
                    │      Web Frontend    │
                    │   Monitoring UI      │
                    │  (Light theme, React)│
                    └──────────┬───────────┘
                               │  REST + WebSocket/SSE
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI API     │
                    │   Backend / Control   │
                    │        Plane          │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
       Training Engine    Monitoring Engine   Deployment
             │                 │                  │
             ▼                 ▼                  ▼
          MLflow          Drift Detection    Model Server
             │                 │
             ▼                 ▼
        Model Registry    Alert Engine
             │
             ▼
        PostgreSQL / Metadata
```

The exact implementation may differ if the AI development agent identifies a simpler and better architecture.

---

# 7. Recommended Technology Stack

## Backend

* Python
* FastAPI
* Pydantic
* Uvicorn

## Machine Learning

* scikit-learn
* XGBoost or LightGBM where appropriate
* pandas
* NumPy
* SciPy

## Experiment Tracking

* MLflow

## Model Registry

* MLflow Model Registry

## Monitoring

Possible technologies:

* Evidently
* SciPy statistical tests
* Custom monitoring logic

The implementation should prefer simple transparent statistical methods where practical.

## Explainability

* SHAP

## Database

* PostgreSQL

SQLite may be used for development if it significantly simplifies the setup, but PostgreSQL is preferred for the final Dockerized environment.

## Frontend

Recommended:

* React
* TypeScript
* Tailwind CSS
* Recharts or another lightweight charting library
* A component/animation library such as Framer Motion for subtle, purposeful transitions (see Section 44)

The agent may choose an equivalent modern frontend stack if it provides a clear advantage, **provided it is capable of producing a genuinely polished, custom-styled light-theme UI** (i.e., not left looking like unstyled default component-library output).

## Real-Time Communication

* WebSockets (FastAPI native support) or Server-Sent Events for live monitoring/alert updates

## Infrastructure

* Docker
* Docker Compose

## Testing

* pytest
* HTTP/API testing
* frontend component tests where appropriate
* basic end-to-end test for the demo scenario (Playwright or similar) — see Section 42

---

# 8. Functional Requirements

---

## FR-001 — Dataset Management

The system must allow datasets to be loaded into SentinelML.

Supported initial format:

* CSV

The platform should validate:

* File format
* Number of rows
* Number of columns
* Column names
* Data types
* Missing values
* Duplicate rows
* Target column
* **Maximum file size (see Section 38 — Security Requirements)**

The UI should display a dataset summary.

Example:

```text
Dataset
────────────────────────

Name: transactions.csv

Rows:        71,204
Columns:     27
Missing:      1.8%
Duplicates:   0.3%

Target:
fraud

Class distribution:

Normal      91%
Fraud        9%
```

Uploaded datasets should be stored under a dedicated, non-web-exposed directory (e.g. `data/raw/{dataset_id}/{version}/`), never served directly as static files.

---

# 9. Data Quality Validation

SentinelML must perform basic data quality checks before training.

Checks should include:

### Missing values

Identify:

* Missing columns
* Missing cells
* Percentage missing per feature

### Duplicates

Identify duplicate rows.

### Data types

Detect unexpected data types.

### Categorical consistency

Detect unexpected categories.

### Numerical validation

Detect:

* Negative values where invalid
* Infinite values
* Extreme outliers

### Schema changes

Compare the current dataset against the previous dataset version.

The validation result must be:

```text
HEALTHY
WARNING
FAILED
```

Training should be blocked when critical validation checks fail.

---

# 10. Dataset Versioning

Each dataset state should receive a version.

Example:

```text
Dataset: fraud_transactions

v1.0
v1.1
v1.2
```

Every model training run must record the dataset version used.

Dataset metadata should include:

* Dataset ID
* Version
* File name
* Row count
* Feature count
* Target column
* Schema
* Creation timestamp
* Data quality statistics

---

# 11. Automated Model Training

The training engine must support multiple algorithms.

Initial classification models:

* Logistic Regression
* Random Forest
* XGBoost
* Support Vector Machine

The system should allow the user to select:

```text
Train all models
```

or:

```text
Train selected models
```

Each training run should automatically:

1. Load dataset.
2. Validate dataset.
3. Split data.
4. Preprocess features.
5. Train model.
6. Evaluate model.
7. Log parameters.
8. Log metrics.
9. Log artifacts.
10. Register candidate model where appropriate.

Each training run must have a configurable **timeout**, and if training fails or times out, the run must be marked `FAILED` with a captured error reason (not left in an ambiguous "stuck" state) so the UI can surface it clearly.

---

# 12. Model Evaluation

For classification models, calculate at minimum:

* Accuracy
* Precision
* Recall
* F1 Score
* ROC-AUC
* Confusion Matrix

Where appropriate, also calculate:

* PR-AUC
* Inference latency
* Model size
* Training duration

The evaluation metric used for automatic promotion must be configurable.

Default:

```text
F1 Score
```

---

# 13. Experiment Tracking

All training experiments must be tracked using MLflow.

Each experiment must store:

### Parameters

Examples:

```text
model_type
learning_rate
max_depth
n_estimators
train_test_split
random_state
```

### Metrics

Examples:

```text
accuracy
precision
recall
f1
roc_auc
training_time
inference_latency
```

### Artifacts

Examples:

* Model
* Confusion matrix
* Feature importance
* Evaluation report
* Dataset metadata

Each experiment should have a unique run ID.

---

# 14. Experiment Comparison

The frontend must provide an experiment comparison interface.

Example:

```text
MODEL              F1       AUC      LATENCY

XGBoost            0.91     0.95     84ms
Random Forest      0.88     0.93     91ms
SVM                0.86     0.91     120ms
Logistic           0.81     0.87     42ms
```

Users should be able to select multiple experiments and compare:

* Metrics
* Parameters
* Dataset version
* Training duration
* Model type

---

# 15. Model Registry

MLflow Model Registry must be used to manage model versions.

Model states should conceptually support:

```text
Candidate
Champion
Archived
Rejected
```

Every model version must store:

* Model ID
* Version
* MLflow run ID
* Dataset version
* Training timestamp
* Evaluation metrics
* Git commit if available
* Deployment status

---

# 16. Champion Model

At any given time, a model can be designated as the production **Champion**.

Example:

```text
fraud-detector

Champion:
v1.4

F1:
0.913

Status:
PRODUCTION
```

Only one model should be considered the active production champion for a given model/application.

---

# 17. Challenger Model

Newly trained models can become Challengers.

Example:

```text
Champion
v1.4
F1 = 0.913

        VS

Challenger
v1.5
F1 = 0.932
```

The system must evaluate the challenger against the champion before automatic promotion.

---

# 18. Champion–Challenger Evaluation

Promotion rules must be configurable.

Example configuration:

```yaml
promotion:
  metric: f1
  minimum_improvement: 0.02
  maximum_latency_increase_percent: 10
```

A challenger should only be promoted when:

```text
challenger_metric >= champion_metric + minimum_improvement
```

and all configured safety conditions pass.

If the challenger does not satisfy the rules:

```text
REJECTED
```

---

# 19. Model Deployment

SentinelML must expose the currently active model through FastAPI.

Minimum endpoint:

```http
POST /api/v1/predict
```

The prediction endpoint must:

1. Validate input.
2. Load active model.
3. Generate prediction.
4. Record prediction metadata.
5. Return prediction and confidence where supported.

Example response:

```json
{
  "prediction": 1,
  "probability": 0.93,
  "model_version": "1.4"
}
```

---

# 20. Prediction Logging

Prediction requests should be logged for monitoring.

Metadata may include:

* Timestamp
* Model version
* Input feature values where appropriate
* Prediction
* Probability
* Request latency
* Error status

Sensitive data should not be logged unnecessarily.

---

# 21. Data Drift Detection

SentinelML must detect changes in production input data compared with a reference/training dataset.

Initial supported techniques:

* Population Stability Index (PSI)
* Kolmogorov–Smirnov test

The implementation may use Evidently if it provides a cleaner implementation.

For each feature:

```text
Feature              Drift Score      Status

age                   0.04             NORMAL
income                0.31             HIGH
amount                0.18             WARNING
account_age           0.06             NORMAL
```

---

# 22. Drift Thresholds

Thresholds must be configurable.

Example:

```yaml
drift:
  warning: 0.10
  critical: 0.25
```

The exact statistical interpretation should be documented according to the selected drift method.

---

# 23. Model Performance Monitoring

SentinelML must monitor model performance where ground-truth labels become available.

Track:

* Accuracy
* Precision
* Recall
* F1
* ROC-AUC

The system should compare current performance with the champion's baseline.

Example:

```text
Baseline F1:
0.91

Current F1:
0.77

Performance degradation:
15.4%
```

---

# 24. Model Health Monitoring

Every deployed model should receive an overall health status.

Possible states:

```text
HEALTHY
WARNING
CRITICAL
```

The health evaluation can consider:

* Data drift
* Model performance
* Prediction errors
* API latency
* Error rate
* Data quality

Example:

```text
MODEL HEALTH

91 / 100

Performance     94
Data Quality    89
Drift           86
Latency         97
Errors          95
```

The health score should be transparent and documented. Health checks should run on a configurable interval (default: every 60 seconds, per Section 37) and the timestamp of the last check must be visible in the UI (Section 39).

---

# 25. Automated Retraining

When configurable critical conditions occur, SentinelML should be capable of triggering retraining.

Possible triggers:

```text
Critical data drift
OR
Model performance degradation
OR
Data quality degradation
```

Workflow:

```text
Problem detected
      ↓
Check retraining policy
      ↓
Start training
      ↓
Generate Challenger
      ↓
Evaluate Challenger
```

Retraining must not automatically replace the champion unless promotion rules are satisfied. A cooldown period (configurable) should prevent retraining from being triggered repeatedly in rapid succession by the same condition.

---

# 26. Self-Healing Engine

The Self-Healing Engine is the central component of SentinelML.

It must coordinate:

```text
Detection
   ↓
Diagnosis
   ↓
Retraining
   ↓
Evaluation
   ↓
Promotion
   ↓
Deployment
```

The engine must maintain a clear state for each recovery workflow.

Example:

```text
RECOVERY #104

Status:
RETRAINING

Trigger:
Critical feature drift

Champion:
v1.4

Challenger:
v1.5

Progress:
Training → Evaluation
```

---

# 27. Automated Rollback

If a newly deployed model becomes unhealthy, SentinelML must be capable of rolling back to the previous healthy champion.

Rollback triggers may include:

* Severe performance degradation
* Excessive prediction errors
* High latency
* High API error rate
* Failed health checks

Rollback workflow:

```text
v1.5 deployed
      ↓
Health monitoring
      ↓
Failure detected
      ↓
Rollback policy triggered
      ↓
v1.4 restored
      ↓
Health check
      ↓
Rollback completed
```

Every rollback must be recorded in the audit log.

---

# 28. Failure Simulation

SentinelML must provide a controlled failure simulation system.

This is primarily for demonstration purposes.

The UI should provide actions such as:

```text
Simulate Data Drift
Simulate Model Degradation
Simulate Latency Spike
Simulate Error Spike
```

Example:

```text
[ SIMULATE DRIFT ]

        ↓

Drift detected

        ↓

Retraining triggered

        ↓

Challenger trained

        ↓

Challenger evaluated

        ↓

Model promoted

        ↓

Production updated
```

The simulation must be isolated from real production data, and simulation endpoints must be clearly non-destructive and disabled/guarded outside of demo mode if the project is ever deployed publicly (see Section 38a).

---

# 29. Model Explainability

SentinelML should provide explainability for supported models using SHAP.

For an individual prediction:

```text
Prediction:
FRAUD

Confidence:
93%

Top Features:

transaction_amount      ██████████
transaction_frequency   ███████
account_age             █████
location_change         ███
```

The UI should provide both:

* Global feature importance
* Individual prediction explanation

---

# 30. Model Lineage

Every deployed model must have traceable lineage.

Example:

```text
Model v1.4
│
├── Dataset v1.2
│
├── Training Run #104
│
├── Code Commit 82fa21
│
├── Features: 27
│
├── F1: 0.913
│
└── Deployment
       └── Production
```

The system should make this information accessible through the dashboard.

---

# 31. Audit Logging

All major system events must be recorded.

Examples:

```text
MODEL_TRAINED
MODEL_REGISTERED
MODEL_PROMOTED
MODEL_DEPLOYED
MODEL_REJECTED
DRIFT_DETECTED
RETRAINING_TRIGGERED
ROLLBACK_TRIGGERED
ROLLBACK_COMPLETED
DATA_VALIDATION_FAILED
```

Each audit event should include:

* Timestamp
* Event type
* Model version
* Dataset version where applicable
* Description
* Status

---

# 32. Alert Center

The frontend must contain an alert center.

Example:

```text
CRITICAL
Model performance degraded
2 minutes ago

WARNING
Income feature drift detected
12 minutes ago

RESOLVED
Automatic rollback completed
18 minutes ago
```

Alerts should have states:

```text
OPEN
ACKNOWLEDGED
RESOLVED
```

New alerts should appear in the UI in near real time (see Section 44a — Real-Time Updates) rather than requiring a manual refresh.

---

# 33. Dashboard Requirements

The dashboard should be the primary interface.

## Dashboard overview

Display:

```text
Active Model
Model Health
Current F1
Current AUC
Drift Status
API Latency
Prediction Volume
Open Alerts
Latest Deployment
```

This overview must be glanceable — a viewer should understand overall system health within 3–5 seconds of landing on the page, aided by clear visual hierarchy, color-coded status, and well-chosen chart types (see Section 44).

---

# 34. Required Frontend Pages

## 34.1 Overview

High-level system health.

## 34.2 Models

Display:

* Model versions
* Champion
* Challengers
* Status
* Metrics
* Deployment state

## 34.3 Experiments

Display MLflow experiments and comparison.

## 34.4 Datasets

Display:

* Dataset versions
* Schema
* Quality
* Drift

## 34.5 Monitoring

Display:

* Drift
* Performance
* Latency
* Error rate
* Prediction distribution

## 34.6 Alerts

Display system alerts and recovery events.

## 34.7 Model Details

Display:

* Metrics
* Parameters
* Lineage
* SHAP
* Deployment history

## 34.8 Recovery / Self-Healing

Display active and previous recovery workflows.

## 34.9 Settings

Allow configurable:

* Drift thresholds
* Promotion thresholds
* Rollback thresholds
* Monitoring intervals

---

# 35. API Requirements

FastAPI should expose a clean, **versioned** REST API under an `/api/v1/` prefix.

Suggested endpoints:

```text
GET    /health

GET    /api/v1/models
GET    /api/v1/models/{model_id}
POST   /api/v1/models/{model_id}/deploy
POST   /api/v1/models/{model_id}/rollback

POST   /api/v1/predict

GET    /api/v1/experiments
GET    /api/v1/experiments/{run_id}

POST   /api/v1/training/start
GET    /api/v1/training/{run_id}

GET    /api/v1/datasets
GET    /api/v1/datasets/{dataset_id}

GET    /api/v1/monitoring/overview
GET    /api/v1/monitoring/drift
GET    /api/v1/monitoring/performance

GET    /api/v1/alerts

GET    /api/v1/audit-log

POST   /api/v1/simulation/drift
POST   /api/v1/simulation/degradation
POST   /api/v1/simulation/latency

WS     /api/v1/ws/events        # real-time push: alerts, health, recovery state
```

The `/health` endpoint remains unversioned/top-level as is conventional for infra health checks.

The agent may reorganize endpoints according to REST best practices. Auto-generated OpenAPI/Swagger documentation (FastAPI provides this by default at `/docs`) must remain enabled and should be linked from the README.

---

# 36. Background Processing

Training and monitoring operations should not block the main API.

Long-running jobs should run asynchronously.

Potential implementation:

* Celery + Redis
* FastAPI background tasks for simpler operations
* Another lightweight job system

For the portfolio version, prefer the simplest reliable solution.

The architecture should remain extensible to a proper task queue later.

---

# 37. Configuration

System behavior must be configurable.

Example:

```yaml
monitoring:
  interval_seconds: 60

drift:
  warning_threshold: 0.10
  critical_threshold: 0.25

promotion:
  metric: f1
  minimum_improvement: 0.02

rollback:
  max_error_rate: 0.05
  minimum_health_score: 70

training:
  timeout_seconds: 900
  retraining_cooldown_seconds: 300
```

Do not hard-code thresholds throughout the application.

---

# 38. Security Requirements

The project is not intended to be a production SaaS system, but basic security practices must be followed.

Requirements:

* Validate API inputs.
* Validate uploaded files.
* Limit uploaded file size (recommended default: 50 MB for portfolio scope).
* Avoid arbitrary code execution through uploaded datasets (e.g., never `eval`/deserialize untrusted pickle-like content from user uploads; parse CSVs defensively).
* Do not expose secrets in source code.
* Use environment variables for credentials.
* Do not log sensitive information unnecessarily.
* Restrict dangerous simulation endpoints appropriately.
* Apply basic CORS configuration (explicit allowed origins, not wildcard, once a real frontend origin is known).

Authentication may be implemented if time permits but is not a core requirement.

## 38a. Rate Limiting & Abuse Prevention

Even for a local/portfolio deployment:

* The `/predict` endpoint and simulation endpoints should have basic rate limiting (e.g., via `slowapi` or a simple in-memory token bucket) to prevent runaway loops (including accidental ones from the frontend) from overwhelming training or monitoring jobs.
* If the project is ever exposed publicly (e.g., a hosted demo), simulation endpoints and `/training/start` should be gated behind a "demo mode" flag or lightweight auth to prevent strangers from triggering resource-intensive jobs.

---

# 39. Observability

SentinelML itself should be observable.

The system should expose:

```text
API health
Service health
Training status
Monitoring status
Active model
Last successful training
Last drift check
Last recovery event
```

A simple `/health` endpoint is required, and it should return structured JSON (status, per-dependency checks such as database/MLflow connectivity, uptime) rather than a bare 200 OK.

---

# 40. Docker Requirements

The entire project should be runnable using Docker Compose.

Potential services:

```text
frontend
backend
mlflow
postgres
redis (if required)
```

Example command:

```bash
docker compose up --build
```

The project should not require manual installation of MLflow/PostgreSQL if Docker is being used.

---

# 41. Local Development

The project must support local development without Docker where practical.

Required documentation:

```text
1. Clone repository
2. Create virtual environment
3. Install dependencies
4. Configure environment variables
5. Start backend
6. Start frontend
7. Start MLflow
```

## 41a. Environment & Secrets Management

`.env.example` should document (at minimum):

```env
# Database
DATABASE_URL=postgresql://sentinel:sentinel@localhost:5432/sentinelml

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_ARTIFACT_ROOT=./mlruns

# Backend
BACKEND_PORT=8000
CORS_ALLOWED_ORIGINS=http://localhost:5173
SECRET_KEY=change-me

# Redis (if used for background jobs)
REDIS_URL=redis://localhost:6379/0

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1/ws/events

# Misc
DEMO_MODE=true
MAX_UPLOAD_SIZE_MB=50
```

No real secrets should ever be committed; `.env` must be git-ignored.

---

# 42. Testing Requirements

The project must contain automated tests.

## Unit tests

Test:

* Data validation
* Drift calculation
* Promotion logic
* Rollback logic
* Health score
* Dataset versioning

## Integration tests

Test:

```text
Training
→ MLflow
→ Registry
→ Deployment
→ Prediction
```

## Self-healing test

At minimum:

```text
Simulated drift
→ Retraining
→ Challenger
→ Evaluation
→ Promotion / rejection
```

## Rollback test

```text
Deploy v2
→ Simulate failure
→ Rollback
→ v1 active
```

## Load/basic performance test

A lightweight load test (e.g., using `locust` or a simple concurrent script) hitting `/predict` to confirm the API remains responsive under a modest number of concurrent requests.

## End-to-end demo test

A scripted end-to-end test (Playwright, Cypress, or similar) that walks through the core demo scenario (Section 50) via the actual UI, to catch regressions in the flow that matters most for demonstrations.

---

# 43. Error Handling

The backend must return meaningful, consistently structured errors.

Example:

```json
{
  "error": "DATA_VALIDATION_FAILED",
  "message": "Target column contains 12% missing values.",
  "timestamp": "..."
}
```

Avoid exposing raw stack traces to frontend users.

Detailed errors should remain available in server logs. The frontend should render these errors as clear, human-readable toasts/banners rather than raw JSON — error states are part of the visual design and deserve the same polish as success states (see Section 44).

---

# 44. UI/UX & Visual Design System *(expanded — read carefully)*

The interface must feel like a **modern, premium SaaS product** — comparable in polish to tools like Linear, Vercel's dashboard, or Datadog's lighter views — not a default Bootstrap/Material admin template and not a raw component-library scaffold.

## 44.1 Theme — Light Theme Is Mandatory

* **The dashboard's primary and default theme must be a clean, professional light theme.** This is a hard requirement, not a stylistic suggestion.
* Dark mode may be added as an optional secondary toggle *if time permits*, but the project must never ship, demo, or default to a look that reads as an unfinished dark-mode-only dev tool.
* Light theme palette guidance:
  * Base background: near-white (e.g. `#FAFAFA`–`#FFFFFF`), not stark pure white everywhere — use subtle off-white/neutral-gray surfaces to create depth between cards and background.
  * Primary text: dark neutral gray/near-black (e.g. `#111827`–`#1F2937`), not pure black.
  * Secondary/muted text: mid-gray (e.g. `#6B7280`).
  * Borders/dividers: very light gray (e.g. `#E5E7EB`), used sparingly — prefer subtle shadows and whitespace over heavy borders.
  * One confident accent/brand color (e.g. an indigo, blue, or teal) used consistently for primary actions, active states, and key data highlights.
  * Semantic status colors, consistent everywhere: green (healthy), amber (warning), red (critical), blue/gray (neutral/info), applied consistently across badges, charts, and alerts.

## 44.2 Typography & Spacing

* Use a single well-chosen sans-serif type family (e.g. Inter, Geist, or system UI stack) with a clear type scale (distinct sizes/weights for page titles, section headers, card labels, body text, and numeric/metric displays).
* Numeric metrics (F1, AUC, health scores, latency) should be visually emphasized — larger, tabular-figure font weight — since they are the core "story" of the dashboard.
* Generous, consistent spacing/padding using a defined scale (e.g. 4/8px grid). Avoid cramped card layouts.

## 44.3 Layout & Information Density

* Strong visual hierarchy: the most important status (overall system health, active model, open critical alerts) must be immediately visible without scrolling on the Overview page.
* Use a persistent sidebar or top navigation with clear active-state styling.
* Cards/panels should have subtle elevation (soft shadow or 1px border + light background differentiation), rounded corners, and consistent internal padding.
* Prioritize information density without clutter — group related metrics, use whitespace to separate unrelated sections rather than heavy dividers.
* Responsive layout: usable down to a reasonable tablet width; a full mobile-first redesign is not required.

## 44.4 Charts & Data Visualization

* Charts (Recharts or equivalent) must be restyled to match the design system — no default library styling left as-is (default blue/green line charts on a plain white background read as unfinished).
* Use appropriate chart types deliberately: line charts for metric trends over time, bar charts for per-feature drift comparison, gauge/radial or large numeric callouts for health scores, sparklines where a full chart would be too heavy.
* Tooltips, axis labels, and legends must be styled consistently with the rest of the UI (correct font, muted gridlines, accent colors matching semantic status where relevant).

## 44.5 Component Polish

* Buttons, badges, inputs, tables, and modals must have deliberate hover/active/disabled states — not raw default browser or unstyled component-library states.
* Status badges (HEALTHY / WARNING / CRITICAL / TRAINING / DEPLOYED / CHAMPION / CHALLENGER / REJECTED / ARCHIVED — see Section 45) must use consistent color + icon pairing throughout every page they appear on.
* Loading states: use skeleton loaders (not blank screens or generic spinners) for data-heavy pages like Experiments, Models, and Monitoring.
* Empty states (e.g., no datasets uploaded yet, no alerts) should have simple, friendly illustrations or icon + short copy — not a bare blank page.
* Use subtle, purposeful motion (e.g., 150–250ms transitions on state changes, a gentle pulse/highlight when a metric updates live) — avoid gratuitous or distracting animation.

## 44.6 The "Demo Moment"

Because the failure-simulation → self-healing → recovery flow (Section 50) is the centerpiece of this project, its visual presentation deserves particular attention: the recovery workflow view (Section 34.8) should visually communicate progress through Detection → Diagnosis → Retraining → Evaluation → Promotion → Deployment as a clear, animated step/progress indicator, so a viewer can watch the system heal itself in real time and immediately understand what's happening.

---

# 44a. Real-Time Updates

Polling is acceptable as a fallback, but the following should update **live** without a manual page refresh, via WebSocket or Server-Sent Events:

* Alert Center (new alerts appear immediately)
* Model health score / status badges on the Overview and Models pages
* Active Recovery workflow progress (Section 34.8)
* Prediction volume / latency counters during a live demo

This is what makes the "Simulate Drift → watch it self-heal" demo moment actually land — a page that requires manual refreshing during a live demo undercuts the story significantly.

---

# 44b. Accessibility Baseline

Not an enterprise-grade WCAG audit, but as a baseline:

* Sufficient color contrast for text and status badges (avoid low-contrast light-gray-on-white text).
* All interactive elements reachable and operable via keyboard.
* Status conveyed by color must also be conveyed by an icon or label (not color alone), since color-only status indicators are also an accessibility issue.

---

# 45. Model Status Colors / States

Use consistent semantic states.

```text
HEALTHY
WARNING
CRITICAL
TRAINING
DEPLOYED
CHALLENGER
CHAMPION
REJECTED
ARCHIVED
```

Exact color/icon pairing is left to the frontend implementation but must be applied **consistently across every page** per Section 44.5.

---

# 46. Performance Requirements

This is a local portfolio system, so enterprise-scale throughput is not required.

However:

* API responses should normally be under 1 second excluding model inference.
* Prediction latency should be recorded.
* Long training jobs must not block API requests.
* Monitoring operations should run asynchronously where appropriate.
* The dashboard should remain responsive during training.
* Real-time UI updates (Section 44a) should not visibly degrade page interactivity even during an active retraining/recovery workflow.

---

# 47. Reproducibility

Training runs should be reproducible.

Record:

* Random seed
* Dataset version
* Model parameters
* Feature preprocessing configuration
* Python/package environment where practical
* Git commit hash where available

A model should be traceable back to the exact training configuration that produced it.

---

# 47a. Model Artifact & Storage Strategy

* Trained models should be serialized via a standard, well-supported format (`joblib` for scikit-learn/XGBoost is recommended for simplicity and reproducibility in this project's scope; ONNX may be considered as a stretch goal if cross-framework portability becomes relevant).
* MLflow's artifact store should be used as the source of truth for model binaries and associated artifacts (confusion matrix images, evaluation reports); avoid duplicating model files outside MLflow's managed storage.
* Local filesystem artifact storage (`./mlruns` or a mounted Docker volume) is sufficient for this project's scope — cloud object storage (S3, GCS) is explicitly out of scope unless pursued as a stretch goal.

---

# 48. Project Structure

Recommended structure:

```text
sentinelml/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── monitoring/
│   │   ├── training/
│   │   ├── registry/
│   │   ├── deployment/
│   │   └── main.py
│   │
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── styles/          # design tokens: colors, typography, spacing
│   │   └── types/
│   │
│   └── tests/
│
├── ml/
│   ├── datasets/
│   ├── preprocessing/
│   ├── training/
│   ├── evaluation/
│   └── models/
│
├── monitoring/
│   ├── drift/
│   ├── performance/
│   └── health/
│
├── configs/
│
├── docker/
│
├── scripts/
│
├── docs/
│
├── docker-compose.yml
├── .env.example
├── README.md
└── SYSTEM_REQUIREMENTS.md
```

The AI development agent may alter this structure if it improves maintainability.

---

# 49. Non-Functional Requirements

## Maintainability

Code must be modular and separated by responsibility.

## Readability

Avoid unnecessarily clever implementations.

## Documentation

Every major component must have documentation.

## Reproducibility

Another developer should be able to run the project using the README.

## Extensibility

The architecture should allow:

* Additional ML algorithms
* Additional monitoring techniques
* Additional deployment targets
* Additional datasets

without rewriting the entire application.

## Visual Quality

The dashboard must maintain the light-theme design system (Section 44) consistently across every page — no page should be left "temporarily unstyled."

---

# 50. Demo Scenario

The final project must provide a complete demonstration scenario.

Recommended scenario:

### Step 1

Train initial models.

```text
Logistic Regression
Random Forest
XGBoost
SVM
```

### Step 2

Select the best model.

```text
XGBoost
F1 = 0.91
```

### Step 3

Register it.

```text
fraud-detector:v1.0
```

### Step 4

Deploy it.

```text
Production
```

### Step 5

Generate predictions.

### Step 6

Show monitoring dashboard.

```text
HEALTHY
```

### Step 7

Click:

```text
SIMULATE DRIFT
```

### Step 8

SentinelML detects drift.

```text
CRITICAL DRIFT DETECTED
```

### Step 9

Self-healing engine triggers retraining.

```text
RETRAINING...
```

### Step 10

New challenger is evaluated.

```text
Champion F1:   0.91
Challenger F1: 0.94
```

### Step 11

Challenger is promoted.

```text
v1.1 → PRODUCTION
```

### Step 12

Simulate model degradation.

### Step 13

SentinelML detects failure.

### Step 14

Automatic rollback occurs.

```text
v1.1 → ROLLBACK
v1.0 → RESTORED
```

This scenario should be possible to demonstrate entirely through the UI, with every state transition visible live (Section 44a) and clearly styled (Section 44).

---

# 51. Acceptance Criteria

SentinelML will be considered complete when:

### Training

* [ ] Multiple ML models can be trained.
* [ ] Training metrics are recorded.
* [ ] MLflow tracks experiments.
* [ ] Training timeout/failure states are handled gracefully.

### Registry

* [ ] Models are versioned.
* [ ] Champion and challenger states exist.
* [ ] Model lineage is available.

### Deployment

* [ ] A registered model can be deployed.
* [ ] `/api/v1/predict` serves the active model.
* [ ] Prediction latency is recorded.

### Monitoring

* [ ] Data quality is monitored.
* [ ] Data drift is detected.
* [ ] Model performance is monitored.
* [ ] API health is monitored.

### Self-Healing

* [ ] Drift can trigger retraining.
* [ ] Challenger models are evaluated.
* [ ] Promotion rules are enforced.
* [ ] Healthy challengers can become champions.
* [ ] Failed models can be rolled back.

### UI

* [ ] Dashboard exists and defaults to a polished light theme.
* [ ] Model page exists.
* [ ] Experiment page exists.
* [ ] Dataset page exists.
* [ ] Monitoring page exists.
* [ ] Alert page exists.
* [ ] Recovery page exists, with a clear step-by-step visual of the healing workflow.
* [ ] Alerts and recovery status update in real time without manual refresh.
* [ ] Status colors/badges are used consistently across all pages.
* [ ] Loading and empty states are designed, not left blank/default.

### Testing

* [ ] Unit tests exist.
* [ ] Integration tests exist.
* [ ] Self-healing workflow is tested.
* [ ] Rollback workflow is tested.
* [ ] A basic load test exists for `/predict`.
* [ ] An end-to-end test covers the core demo scenario.

### Infrastructure

* [ ] Docker Compose works.
* [ ] README contains setup instructions and screenshots/GIF of the dashboard.
* [ ] `.env.example` exists and is complete.
* [ ] No secrets are committed.
* [ ] API docs (`/docs`) are accessible.

---

# 52. Stretch Features

These are explicitly optional.

The development agent may implement them only if they provide meaningful value.

Potential features:

* JWT authentication
* Role-based access control
* Email alerts
* Slack notifications
* Scheduled retraining
* Model A/B testing
* Canary deployments
* Batch prediction
* Feature importance tracking
* GPU training support
* Cloud deployment
* Kubernetes deployment
* Prometheus/Grafana integration
* GitHub Actions CI/CD
* Optional dark mode toggle (light theme remains default and primary)
* ONNX model export for cross-framework portability

These must **not** delay completion of the core system.

---

# 53. Features That Should NOT Be Prioritized

Do not spend significant development time on:

* Complex billing
* Payment systems
* Multi-tenant SaaS architecture
* Enterprise SSO
* Kubernetes unless required
* Complex distributed computing
* Advanced cloud infrastructure
* Mobile applications
* Excessive authentication features

SentinelML is a **portfolio demonstration of ML engineering and MLOps**, not a commercial SaaS platform.

---

# 54. AI Development Agent Authority

The AI development agent is authorized to:

* Improve implementation details.
* Refactor code.
* Select appropriate libraries.
* Add small supporting components.
* Improve UI/UX (within the light-theme design system mandated in Section 44).
* Add useful validation.
* Add useful tests.
* Improve error handling.
* Improve architecture when necessary.

However, the agent must not:

* Remove core requirements.
* Replace MLflow without strong justification.
* Remove monitoring.
* Remove champion–challenger logic.
* Remove automated rollback.
* Remove self-healing behavior.
* Introduce unnecessary enterprise infrastructure.
* Add dependencies without evaluating their necessity.
* **Ship or default to an unstyled, default-component-library, or dark-only dashboard.**

When uncertain, the agent should favor:

> **Simple + demonstrable + maintainable + visually polished (light theme)**

over:

> **Complex + enterprise-like + difficult to run + visually unfinished.**

---

# 55. Definition of "Self-Healing"

For this project, "self-healing" specifically means:

> SentinelML can automatically detect predefined ML system failures, initiate an appropriate recovery workflow, train/evaluate a replacement model when required, safely promote it when predefined conditions are satisfied, and restore the previous healthy model when a deployment becomes unhealthy.

Self-healing must therefore be **observable and demonstrable** — both functionally and visually (Section 44.6).

It must not simply be a marketing label.

---

# 56. Definition of Done

The project is complete when a developer can run:

```bash
docker compose up --build
```

and access SentinelML through a polished, light-themed dashboard.

They should be able to:

```text
1. Load dataset
2. Validate dataset
3. Train models
4. View experiments
5. Compare models
6. Register model
7. Deploy champion
8. Generate predictions
9. Monitor production
10. Simulate drift
11. Trigger self-healing
12. Train challenger
13. Promote challenger
14. Simulate model failure
15. Automatically rollback
16. Inspect complete audit history
```

The entire workflow should be visible through the dashboard, updating live, in a UI that looks like a real, shippable product.

---

# 57. Final Project Identity

SentinelML should ultimately communicate the following engineering story:

```text
"I didn't just train an ML model.

I built a system that manages an ML model
through its entire lifecycle.

It knows when data changes.

It knows when model performance degrades.

It can train a challenger.

It can evaluate whether the challenger is actually better.

It can promote the challenger.

And if the new model fails,

it can automatically roll back
to the previous healthy version.

And it looks like a product I could ship."
```

That is the core identity of SentinelML.

---

# 58. Resume-Level Description

Final resume description:

> **Built SentinelML, an end-to-end self-healing MLOps platform for automated model training, experiment tracking, deployment and monitoring. Implemented data drift detection, champion–challenger evaluation, model registry, automated retraining and rollback using MLflow, FastAPI, Docker and monitoring infrastructure.**

Alternative stronger version:

> **Engineered SentinelML, a self-healing MLOps platform that detects data/model degradation, automatically retrains and evaluates challenger models, promotes validated versions and rolls back unhealthy deployments using MLflow, FastAPI and Docker.**

---

# 59. Success Metric

The project should not be judged primarily by model accuracy.

The primary success metric is:

> **Can SentinelML demonstrate a complete, automated ML lifecycle from training to failure detection and recovery — in a polished, professional, real-time dashboard?**

If the answer is yes, the project has achieved its primary objective.
