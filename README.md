# NexGuard AI

> **Detect. Investigate. Explain.**  
> Intelligent Financial Fraud Detection and Investigation Network.

NexGuard AI is a hackathon prototype for exploring suspicious financial activity using transaction ingestion, explainable rule-based detection, an Isolation Forest anomaly model, risk scoring, alerts and an investigation-focused dashboard.

> **Demo integrity:** The included financial dataset and dashboard examples are synthetic. A risk alert is a signal for human review, not proof of fraud. Supabase, OpenAI RAG and remote MCP integrations are optional/future integrations unless explicitly configured and tested.

## Data integrity and test fixtures

The dashboard and directory views now display API-backed values or an explicit empty state; they do not invent customer, account, alert, case, network, or model-performance records. The CSVs under `test/fixtures/` are synthetic fixtures for testing only. They are not live financial data.

For a PostgreSQL-backed test run, configure `REPOSITORY_BACKEND=postgres` and `DATABASE_URL`, then seed only the fixture customer/account master data from `backend/`:

```powershell
python -m scripts.seed_demo_data --data-dir ..\\test\\fixtures --skip-transactions
```

Then upload `test/fixtures/transactions_review_signals.csv` from Transaction Monitoring and run detection. The default in-memory backend has no account-master records, so it will reject fixture transactions until account master data is loaded. For real deployments, use authorized source data and secure PostgreSQL configuration.

## Quick start (Windows)

Requirements: Node.js 20+, Python 3.11 recommended.

```powershell
# Clone this branch
git clone -b nexguard-submission https://github.com/ramachari-upsare/hackathon.git
cd hackathon

# Allow npm scripts in this PowerShell session if Windows blocks npm.ps1
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Install frontend/workspace dependencies
npm install

# Create and activate the backend environment
py -3.11 -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements-dev.txt

# Optional environment files (defaults run in local demo mode)
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env

# Start frontend and API together
npm run dev
```

Open:
- Frontend: http://localhost:5173
- FastAPI: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Local demo sign-in: use any email and password when Supabase is not configured. This is a demo-only local session, not production authentication.

## Technology

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| UI | Tailwind CSS, shadcn/ui primitives, Lucide React |
| Charts | Recharts |
| Network visualization dependency | Cytoscape.js |
| Backend | Python, FastAPI, Pydantic |
| Persistence | In-memory demo repository by default; PostgreSQL/Supabase adapter and migrations included |
| Detection | Configurable fraud rules + scikit-learn Isolation Forest |
| Graph analysis | NetworkX dependency and graph module foundation |
| AI / retrieval | OpenAI + pgvector/RAG are planned integration points |
| MCP | Python MCP SDK integration is planned; do not claim a remote server is connected |
| Tests | pytest, FastAPI TestClient |

## Current working backend workflow

1. Check service health at `GET /health`.
2. Upload a UTF-8 CSV to `POST /api/v1/transactions/ingest`.
3. Search and paginate transactions with `GET /api/v1/transactions`.
4. Run a detection scan with `POST /api/v1/detection/scan`.
5. Review prioritized alerts with `GET /api/v1/alerts` and alert details with `GET /api/v1/alerts/{id}`.

CSV fields include `from_account`, `to_account`, `amount`, `currency`, `timestamp`; optional fields include `id`, `device_id`, `ip_address`, `channel`, and `label`. See `data/sample_transactions.csv`.

## Detection design

- Large transfers, rapid succession and high transaction frequency are evaluated by configurable rules.
- The Isolation Forest model evaluates transaction-behavior features when enough training data is available.
- Rule and model scores are combined into a 0–100 risk score.
- Risk categories and alert thresholds are configurable in `backend/app/core/config.py`.
- When the model has insufficient training data, the API reports that status; rule-based signals remain available.

## Project modules mapped to the Phase 1 plan

- **E01:** application structure, local demo session, role-aware shell, database configuration/migrations.
- **E02:** customer/account UI routes and account-risk service foundation.
- **E03:** CSV transaction ingestion, validation, duplicate checks and transaction search API.
- **E04:** fraud rules, Isolation Forest, risk scoring and alert generation.
- **E05:** network/fund-flow workspace UI and graph dependency foundation; full backend graph workflow remains in progress.
- **E06–E07:** investigation/evidence workspace navigation; persistent case/evidence workflow remains in progress.
- **E08–E09:** detection explanations/model evaluation foundation and command-center analytics UI.
- **E10–E11:** Copilot/MCP navigation and integration design; live RAG and remote MCP are not enabled in this demo.
- **E12–E13:** security hardening, integration tests and deployment remain follow-up work.

## Commands

```powershell
npm run dev             # frontend + backend
npm run build           # frontend TypeScript check + production build
npm run test:backend    # pytest backend suite
npm run generate:demo   # regenerate synthetic CSV data
```

## Submission demo path

1. Open the command-center dashboard and explain the synthetic-data label.
2. Show transaction CSV ingestion in the API docs.
3. Run the detection scan and inspect the generated alert evidence.
4. Show the transaction/alert workspace and explain the score and triggered rules.
5. Walk through the network, fund-flow, investigation and Copilot concepts, clearly distinguishing implemented demo behavior from planned integrations.

## Security

- Never commit `.env` files, database passwords, API keys or Supabase service-role keys.
- Use synthetic records only in the hackathon demo.
- Do not treat anomaly scores as confirmed fraud decisions.
- Configure Supabase Auth, database permissions, API authorization and audit logging before any real financial data is used.
