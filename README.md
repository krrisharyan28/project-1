# 🛡️ AI Fraud Alert Dashboard

A full-stack fintech analyst tool that ingests transaction CSVs, scores each
transaction for fraud risk with a transparent **rule engine**, explains the
riskiest ones in plain English using **Llama-3 (via Ollama)**, and lets analysts
**confirm or dismiss** alerts from a clean React dashboard with live analytics.

> **Portfolio project — not intended for production banking systems.**

---

## ✨ Features

- 📤 **CSV upload** — drop in a batch of transactions; they're parsed, validated and scored on import.
- ⚙️ **Rule-based fraud engine** — transparent, deterministic 0–100 risk score from explainable rules (high amount, odd hour, velocity, country mismatch, high-risk category, …).
- 🤖 **AI explanations** — Llama-3 turns the fired rules into a plain-English summary and recommended next action, on demand.
- 🗂️ **Alert workflow** — analysts confirm fraud or dismiss false positives, with notes and an audit trail.
- 📊 **Analytics dashboard** — KPIs and Recharts visualizations (risk distribution, fraud over time, top rules, top countries).
- 🔐 **JWT auth** — register / login with access + refresh tokens and silent refresh.

---

## 🧱 Tech Stack

| Layer     | Technology                                                    |
|-----------|---------------------------------------------------------------|
| Frontend  | React (Vite), React Router, Axios, Tailwind CSS, Recharts     |
| Backend   | Python, Django, Django REST Framework, SimpleJWT              |
| Database  | PostgreSQL                                                    |
| AI        | Ollama running the `llama3` model                            |
| Quality   | SonarQube, pytest, ruff                                       |

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full design, data model, API
surface and fraud rules.

---

## 📁 Project Structure

```
ai-fraud-alert-dashboard/
├── ARCHITECTURE.md          # full architecture & plan
├── docker-compose.yml       # Postgres + Ollama for local dev
├── sonar-project.properties # SonarQube config
├── backend/                 # Django REST API (apps: accounts, transactions, fraud, ai, core)
└── frontend/                # React (Vite) SPA
```

---

## 🚀 Getting Started

> For a detailed, copy-paste walkthrough (installing Node/Postgres/Ollama,
> running everything, capturing screenshots, and SonarQube), see
> **[RUNBOOK.md](./RUNBOOK.md)**.

### Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 15+ (or use the provided `docker-compose.yml`)
- [Ollama](https://ollama.com) with the `llama3` model pulled

### 1. Infrastructure (Postgres + Ollama)

```bash
docker compose up -d
docker compose exec ollama ollama pull llama3   # first run only
```

### 2. Backend

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # then edit values
python manage.py migrate
python manage.py seed_demo      # demo analyst + sample transactions
python manage.py runserver
```

API runs at `http://localhost:8000/api/`.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App runs at `http://localhost:5173`.

---

## 🔑 Demo Login

After running `seed_demo`:

| Username | Password    |
|----------|-------------|
| `analyst`| `analyst123`|

---

## 🧪 Quality

```bash
# Backend tests + coverage
cd backend && coverage run -m pytest && coverage xml

# Frontend tests + coverage
cd frontend && npm test

# SonarQube
sonar-scanner
```

---

## 🖥️ Screens

| Screen | What it shows |
|--------|---------------|
| **Dashboard** | KPI cards + risk-distribution donut, fraud-over-time line, and top-rules bar charts |
| **Transactions** | Paginated, searchable, risk-filterable table of all transactions |
| **Alert queue** | Flagged transactions sorted by risk score, filterable by status |
| **Alert detail** | Transaction facts, the transparent rule breakdown with weights, the on-demand Llama-3 explanation, and confirm/dismiss workflow |
| **Upload** | CSV upload with an import + flagged summary |

> To add image captures, run the app (`http://localhost:5173`), snip each screen,
> and drop the PNGs into `docs/screenshots/`.

---

## ⚠️ Disclaimer

This is a learning/portfolio project. It is **not** PCI-compliant, uses no real
cardholder data, and must not be used for real fraud decisioning.
