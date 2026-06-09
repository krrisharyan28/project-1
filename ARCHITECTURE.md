# AI Fraud Alert Dashboard — Architecture & Plan

> A full-stack fintech analyst tool that ingests transaction CSVs, scores each
> transaction for fraud risk with a transparent rule engine, explains the
> riskiest ones in plain English using Llama-3 (Ollama), and lets analysts
> confirm or dismiss alerts from a React dashboard.
>
> **Portfolio project — not for production banking use.**

---

## 1. System Overview

```
                ┌──────────────────────────────────────────────────────────┐
                │                      React (Vite) SPA                      │
                │   Login · Dashboard · Transactions · Alert Detail · Upload │
                │     Axios (JWT interceptor) · Recharts · Tailwind CSS      │
                └───────────────────────────┬──────────────────────────────┘
                                            │  HTTPS / JSON  (Bearer JWT)
                                            ▼
                ┌──────────────────────────────────────────────────────────┐
                │              Django REST Framework API                     │
                │                                                            │
                │   accounts  →  JWT auth (SimpleJWT), analyst profiles      │
                │   transactions → CSV upload, import service, listing       │
                │   fraud     →  rule engine, risk scoring, alert workflow    │
                │   ai        →  Ollama/Llama-3 explanation service           │
                │   core      →  seed command, health, shared services        │
                │                                                            │
                │   common    →  pagination, exception handler, mixins        │
                └───────────────┬───────────────────────────┬───────────────┘
                                │                           │
                                ▼                           ▼
                ┌───────────────────────────┐   ┌──────────────────────────┐
                │      PostgreSQL 15+        │   │   Ollama (llama3 model)   │
                │  users · transactions ·   │   │  local LLM inference at   │
                │  alerts · rule_hits       │   │  http://localhost:11434   │
                └───────────────────────────┘   └──────────────────────────┘
```

**Design principle:** clean, layered architecture. Views stay thin; all business
logic lives in **service modules**. Serializers handle validation and shape.
The fraud engine is deterministic and explainable; the LLM only *describes*
findings, it never decides risk.

---

## 2. Tech Stack

| Layer            | Technology                                             |
|------------------|--------------------------------------------------------|
| Frontend         | React 18 + Vite, React Router, Axios, Tailwind, Recharts |
| Backend          | Python 3.13, Django 5, Django REST Framework            |
| Auth             | djangorestframework-simplejwt (access + refresh)        |
| Database         | PostgreSQL 15+                                           |
| AI               | Ollama running `llama3`                                  |
| Quality          | SonarQube (`sonar-project.properties`), pytest, ruff     |
| Infra (dev)      | docker-compose (Postgres + Ollama), `.env` config        |

---

## 3. Backend Layered Architecture

Each Django app follows the same internal layering:

```
apps/<app>/
├── models.py          # persistence (thin, validation via clean())
├── serializers.py     # request/response shape + field validation
├── services/          # business logic — the heart of each app
│   └── *.py
├── views.py           # thin DRF views/viewsets — orchestrate services
├── urls.py            # routing
├── selectors.py       # (where useful) read queries kept out of views
└── tests/             # unit tests per layer
```

**Request flow (example: upload CSV):**

```
POST /api/transactions/upload/
   → TransactionUploadView (thin)
       → CsvImportService.import_file(file, user)      # parse + validate rows
           → bulk_create Transaction rows
       → FraudEngine.score_batch(transactions)         # rule engine
           → creates Alert + RuleHit rows for flagged txns
   → 201 { imported, flagged, alert_ids }
```

LLM explanation is generated **lazily on demand** (when an analyst opens an
alert), not during import — keeps uploads fast and avoids blocking on the model.

---

## 4. Data Model

```
User (custom: accounts.User)
 ├─ id, username, email, password (hashed)
 ├─ role: 'analyst' | 'admin'
 └─ is_active, date_joined

TransactionBatch                      # one CSV upload
 ├─ id, uploaded_by → User
 ├─ filename, row_count, flagged_count
 └─ created_at

Transaction
 ├─ id (uuid), batch → TransactionBatch
 ├─ external_id            # id from the CSV
 ├─ timestamp, amount, currency
 ├─ merchant, category
 ├─ country, channel       # e.g. 'online' | 'pos' | 'atm'
 ├─ card_last4, customer_id
 ├─ risk_score   (0–100, computed)
 ├─ risk_level   ('low'|'medium'|'high', derived from score)
 └─ created_at

Alert                                 # created when a txn is flagged
 ├─ id, transaction → Transaction (1:1)
 ├─ status: 'open' | 'confirmed_fraud' | 'dismissed'
 ├─ risk_score (snapshot)
 ├─ ai_explanation (text, nullable — filled by Llama-3 on demand)
 ├─ ai_explained_at
 ├─ reviewed_by → User (nullable)
 ├─ reviewed_at, review_note
 └─ created_at

RuleHit                               # which rules fired, for transparency
 ├─ id, alert → Alert (FK)
 ├─ rule_code      # e.g. 'HIGH_AMOUNT'
 ├─ rule_label
 ├─ weight         # points this rule contributed
 └─ detail         # human-readable context, e.g. "$12,400 > $10,000 threshold"
```

`risk_score` is the sum of fired rule weights, capped at 100.
`risk_level`: `>= 70` high, `>= 40` medium, else low. Alerts are created for
`medium` and `high`.

---

## 5. Fraud Detection Engine (rule-based)

Located in `apps/fraud/services/`. Each rule is a small pure function taking a
transaction (+ lightweight customer context) and returning a `RuleResult`
(`fired`, `weight`, `detail`) or `None`. The engine runs all rules, sums
weights, derives the level, and persists `Alert` + `RuleHit` rows.

**Initial rule set (`rules.py`):**

| Code              | Label                          | Trigger                                                  | Weight |
|-------------------|--------------------------------|----------------------------------------------------------|--------|
| `HIGH_AMOUNT`     | Unusually high amount          | amount > configurable threshold (default 10,000)         | 35     |
| `ODD_HOUR`        | Transaction at odd hour        | local hour in 00:00–05:00                                 | 15     |
| `VELOCITY`        | Rapid repeat spending          | > N txns for same customer within M minutes              | 25     |
| `COUNTRY_MISMATCH`| Foreign / unexpected country   | country ∉ customer's usual set                            | 20     |
| `HIGH_RISK_MCC`   | High-risk merchant category    | category in {crypto, gambling, gift_card, wire}          | 20     |
| `ROUND_AMOUNT`    | Suspicious round amount        | amount is a large round number (e.g. exact thousands)    | 10     |
| `NEW_CARD_BURST`  | New card, immediate large spend| first-seen card with amount above smaller threshold      | 15     |

Thresholds live in settings/env so they're tunable without code changes.
The engine is **deterministic and unit-testable** — the portfolio talking point.

---

## 6. AI Explanation Service (Llama-3 via Ollama)

`apps/ai/services/ollama_client.py` — thin HTTP client to Ollama's
`/api/generate` (or `/api/chat`) endpoint, configured by `OLLAMA_BASE_URL` and
`OLLAMA_MODEL=llama3`. Timeouts + clear errors; **no fallback** (strict stack).

`apps/ai/services/explainer.py` — builds a structured prompt from the
transaction fields + fired `RuleHit`s and asks Llama-3 to explain, in plain
analyst-friendly English, *why* the transaction looks suspicious and what to
check next. The result is cached on `Alert.ai_explanation`.

**Prompt shape (summary):** system role = fraud analyst assistant; user content =
transaction facts + list of triggered rules; instruction = concise explanation +
recommended action, no fabricated facts beyond the provided signals.

Endpoint: `POST /api/fraud/alerts/{id}/explain/` → generates (or returns cached)
explanation.

---

## 7. REST API Surface

All under `/api/`. JWT required except auth endpoints. Paginated list responses.

```
# Auth (accounts)
POST   /api/auth/register/           create analyst account
POST   /api/auth/login/              → { access, refresh }
POST   /api/auth/refresh/            → { access }
GET    /api/auth/me/                 current user profile

# Transactions
POST   /api/transactions/upload/     multipart CSV → import + score
GET    /api/transactions/            list (filter: risk_level, country, search; paginated)
GET    /api/transactions/{id}/       detail
GET    /api/transactions/batches/    upload history

# Fraud / Alerts
GET    /api/fraud/alerts/            list alerts (filter: status, risk_level; paginated)
GET    /api/fraud/alerts/{id}/       alert detail incl. rule hits + transaction
POST   /api/fraud/alerts/{id}/explain/   generate/return Llama-3 explanation
PATCH  /api/fraud/alerts/{id}/review/     { status, note } confirm/dismiss

# Analytics (dashboard)
GET    /api/fraud/stats/             KPIs + chart series (counts by level,
                                     fraud over time, top countries, top rules)

# Ops
GET    /api/health/                  liveness (db + ollama reachability)
```

**Conventions:** standardized error envelope via a custom DRF exception handler,
page-number pagination (configurable page size), filtering via query params,
consistent snake_case JSON.

---

## 8. Frontend Architecture

```
src/
├── main.jsx               app bootstrap + router
├── App.jsx                route definitions + protected routes
├── index.css              Tailwind layers + design tokens
├── api/
│   ├── client.js          Axios instance + JWT request/refresh interceptors
│   ├── auth.js            login/register/me/refresh calls
│   ├── transactions.js    upload/list/detail
│   └── fraud.js           alerts/explain/review/stats
├── auth/
│   ├── AuthContext.jsx    token state, login/logout, persistence
│   └── ProtectedRoute.jsx route guard
├── components/
│   ├── ui/                Button, Card, Badge, Table, Spinner, Modal, ...
│   ├── charts/            RiskByLevelChart, FraudTrendChart, TopRulesChart
│   └── layout/            Sidebar, Topbar, AppShell
├── pages/
│   ├── LoginPage.jsx
│   ├── DashboardPage.jsx      KPIs + Recharts analytics
│   ├── TransactionsPage.jsx   paginated table + filters
│   ├── UploadPage.jsx         CSV upload with result summary
│   ├── AlertsPage.jsx         alert queue
│   └── AlertDetailPage.jsx    rule hits + "Explain with AI" + confirm/dismiss
├── hooks/                 usePaginatedQuery, useAuth, ...
└── lib/                   formatters (currency, date), riskLevel helpers
```

Reusable, presentational components; pages compose them. RiskLevel and currency
formatting centralized in `lib/`. A single Axios instance handles auth headers
and silent token refresh on 401.

---

## 9. Repository Layout

```
ai-fraud-alert-dashboard/
├── README.md                  # setup, screenshots, feature tour
├── ARCHITECTURE.md            # this document
├── .gitignore
├── docker-compose.yml         # Postgres + Ollama for local dev
├── sonar-project.properties   # SonarQube config
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── pytest.ini
│   ├── config/                # Django project (settings, urls, wsgi/asgi)
│   ├── common/                # pagination, exceptions, base classes
│   ├── apps/
│   │   ├── accounts/          # custom user + JWT auth
│   │   ├── transactions/      # CSV import + transaction API
│   │   ├── fraud/             # rule engine, alerts, analytics
│   │   ├── ai/                # Ollama/Llama-3 explanation
│   │   └── core/              # health, seed command, shared
│   └── data/sample_transactions.csv
└── frontend/                  # React (Vite) SPA — see §8
```

---

## 10. Code Quality & Tooling

- **SonarQube**: `sonar-project.properties` defines project key, sources
  (`backend`, `frontend/src`), exclusions (migrations, node_modules), and
  coverage report paths.
- **Backend tests**: pytest + pytest-django; unit tests for the rule engine,
  CSV importer, and serializers; API tests for auth + alert workflow.
- **Linting**: ruff (Python). ESLint + Prettier (frontend).
- **Coverage**: `coverage.xml` (backend) and `lcov` (frontend) wired into Sonar.

---

## 11. Security & Config Notes (portfolio scope)

- All secrets via environment variables (`.env`, never committed).
- JWT access/refresh with sensible lifetimes; passwords hashed by Django.
- CORS restricted to the frontend origin.
- CSV import validates and sanitizes every row; bounded file size.
- **Explicitly not production-hardened** — no PCI scope, no real card data.

---

## 12. Implementation Notes

- **Backend:** models + migrations, serializers, a service layer (fraud engine,
  CSV importer, Ollama explainer), thin DRF views, URLs, a seed command, and a
  sample CSV.
- **Frontend:** Axios API layer with JWT refresh, an auth context, layout, pages,
  Recharts visualizations, and reusable components.
- **Quality:** backend `pytest` suite (rule engine, importer, auth, alert
  workflow, analytics) and frontend `vitest` tests, with SonarQube configured.
