# 🏃 RUNBOOK — AI Fraud Alert Dashboard

Step-by-step guide to install the stack, run the app end-to-end, capture
portfolio screenshots, and run SonarQube. Written for **Windows 11 + PowerShell**
(notes for macOS/Linux inline).

> Already installed on this machine: **Python 3.13**, **Git**.
> Still needed: **Node.js**, **PostgreSQL**, **Ollama** (or Docker for the first two services).

---

## 0. Install prerequisites

### Node.js (required for the React frontend)
- Download the LTS installer from <https://nodejs.org> (v18+), or:
  ```powershell
  winget install OpenJS.NodeJS.LTS
  ```
- Verify: `node --version` and `npm --version`.

### Ollama + llama3 (required for AI explanations)
- Download from <https://ollama.com/download>, or:
  ```powershell
  winget install Ollama.Ollama
  ```
- Pull the model (one-time, ~4.7 GB):
  ```powershell
  ollama pull llama3
  ```
- Ollama serves on `http://localhost:11434` automatically.

### PostgreSQL — pick ONE option

**Option A — Docker (easiest; also runs Ollama).** Requires Docker Desktop.
```powershell
# from the project root
docker compose up -d
docker compose exec ollama ollama pull llama3   # if using the dockerized Ollama
```
This starts Postgres on `localhost:5432` (db `fraud_dashboard`, user/pass `fraud`/`fraud`).

**Option B — Native PostgreSQL.**
```powershell
winget install PostgreSQL.PostgreSQL.16
```
Then create the database and user:
```sql
-- in psql as the postgres superuser
CREATE DATABASE fraud_dashboard;
CREATE USER fraud WITH PASSWORD 'fraud';
GRANT ALL PRIVILEGES ON DATABASE fraud_dashboard TO fraud;
ALTER DATABASE fraud_dashboard OWNER TO fraud;
```

---

## 1. Backend (Django REST API)

```powershell
cd backend

# The virtualenv already exists (.venv). If not: python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt          # already installed; safe to re-run

# Configure environment
Copy-Item .env.example .env               # then edit values if needed

# Database + demo data
python manage.py migrate
python manage.py seed_demo                # creates analyst/analyst123 + sample batch

# Run
python manage.py runserver
```

API is now at **http://localhost:8000/api/**. Quick checks:
- `http://localhost:8000/api/health/` → `{ "status": "ok", "database": true, "ollama": true/false }`
- `http://localhost:8000/admin/` → Django admin (create a superuser with
  `python manage.py createsuperuser` if you want to browse data).

> **Strict stack:** the backend requires Postgres to be reachable to run, and
> Ollama to be running for the "Explain with AI" feature. If Ollama is down,
> everything else works and the explain button returns a clear error.

---

## 2. Frontend (React SPA)

In a **second terminal**:

```powershell
cd frontend
npm install
Copy-Item .env.example .env               # default VITE_API_BASE_URL=/api works with the dev proxy
npm run dev
```

App is now at **http://localhost:5173**. The Vite dev server proxies `/api`
to the Django backend, so no CORS setup is needed during development.

**Log in** with the seeded demo account:

| Username | Password     |
|----------|--------------|
| `analyst`| `analyst123` |

---

## 3. Feature walkthrough (and screenshot checklist)

Capture these for your README / portfolio (save into `docs/screenshots/`):

1. **Login page** — `/login` → `docs/screenshots/login.png`
2. **Dashboard** — `/` → KPIs + risk donut + fraud trend + top rules
   → `docs/screenshots/dashboard.png`
3. **Transactions** — `/transactions` → filter by risk level, search
   → `docs/screenshots/transactions.png`
4. **Alert queue** — `/alerts` → filter by status
   → `docs/screenshots/alerts.png`
5. **Alert detail (the money shot)** — click any alert → shows the fired rules
   with weights, then click **“Explain with AI”** to generate the Llama-3
   summary → `docs/screenshots/alert-detail-ai.png`
6. **Upload** — `/upload` → drop `backend/data/sample_transactions.csv`, see the
   import + flagged summary → `docs/screenshots/upload.png`

Then reference them in `README.md` (replace the “coming soon” placeholders).

**Windows screenshot tip:** `Win + Shift + S` for a region snip, or `Win + PrtScn`
for a full-screen capture saved to `Pictures/Screenshots`.

---

## 4. Tests & coverage

### Backend (pytest)
A test DB is created in PostgreSQL automatically, so Postgres must be running.
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
coverage run -m pytest
coverage xml          # produces backend/coverage.xml for SonarQube
coverage report       # console summary
```
> Tests live under each app's `tests/` package (e.g. `apps/fraud/tests/`).

### Frontend (vitest)
```powershell
cd frontend
npm test              # runs vitest with v8 coverage → frontend/coverage/lcov.info
```

---

## 5. SonarQube

### Start a local SonarQube server (Docker)
```powershell
docker run -d --name sonarqube -p 9000:9000 sonarqube:lts-community
```
Open <http://localhost:9000> (default login `admin` / `admin`, then set a new
password). Create a project with key **`ai-fraud-alert-dashboard`** and generate
an analysis **token**.

### Install the scanner
```powershell
winget install SonarSource.SonarScanner
```

### Run the analysis (from the project root)
First generate coverage reports (see §4), then:
```powershell
sonar-scanner -D"sonar.host.url=http://localhost:9000" -D"sonar.token=YOUR_TOKEN"
```
`sonar-project.properties` already defines the project key, sources, test paths,
coverage report paths, and exclusions (migrations, node_modules, dist). Results
appear in the SonarQube dashboard at <http://localhost:9000>.

---

## 6. Troubleshooting

| Symptom | Fix |
|--------|------|
| `connection to server at "127.0.0.1", port 5432 failed` | Postgres isn't running. Start Docker (`docker compose up -d`) or the Postgres service. |
| `Explain with AI` returns 502 | Ollama isn't running or `llama3` isn't pulled. Run `ollama pull llama3` and ensure `ollama serve` is up. |
| Frontend 401s / login loops | Token expired and refresh failed; log in again. Check `VITE_API_BASE_URL` and that the backend is on :8000. |
| CORS errors | Use the Vite dev proxy (default), or set `CORS_ALLOWED_ORIGINS` in `backend/.env` to your frontend origin. |
| `seed_demo` says user exists | It's idempotent for the user; use `python manage.py seed_demo --reset` to wipe and re-import transaction data. |

---

## 7. One-glance startup (after everything is installed)

```powershell
# Terminal 1 — infra (if using Docker)
docker compose up -d

# Terminal 2 — backend
cd backend; .\.venv\Scripts\Activate.ps1; python manage.py runserver

# Terminal 3 — frontend
cd frontend; npm run dev
```
Open <http://localhost:5173> → log in as `analyst` / `analyst123`. Done. 🎉
