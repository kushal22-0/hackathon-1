# FraudNet AI

> **Detect. Investigate. Explain.**

FraudNet AI is a full-stack fraud analytics workspace: ingest transaction data, detect
suspicious activity with configurable rules plus an IsolationForest model, investigate
fund flows, and explain every alert in language a human can act on.

The repository contains the FastAPI fraud-detection foundation and an integrated React dashboard. The dashboard is currently a presentation/demo layer; connect it to the API before describing its sample metrics as live production data. RAG Copilot and remote MCP are planned integrations and must be configured and tested before claiming they are operational.

---

## Monorepo layout

```text
.
├── backend/               # FastAPI, services, repositories, detection, tracing
│   ├── app/
│   │   ├── api/           # HTTP routers and dependencies
│   │   ├── core/          # configuration, database, security
│   │   ├── graph/         # NetworkX fund-flow algorithms
│   │   ├── mcp/           # reserved for Phase 2
│   │   ├── ml/            # IsolationForest feature extraction and model
│   │   ├── models/        # Pydantic schemas and SQLAlchemy tables
│   │   ├── rag/           # reserved for a later Phase
│   │   ├── repositories/  # persistence interfaces and implementations
│   │   └── services/      # all business logic
│   ├── migrations/        # Supabase PostgreSQL / pgvector SQL migrations
│   ├── scripts/           # demo data generation, seeding, knowledge ingestion
│   └── tests/
├── frontend/              # React + TypeScript + Vite + Tailwind; integrated hackathon-ui dashboard
├── data/                  # Generated demo data and knowledge-base source docs
├── docs/                  # architecture and MCP design
└── package.json           # root workspace commands
```

The backend follows a strict dependency direction:

```text
api / (future MCP tools)  ->  services  ->  repositories  ->  database
                                |
                                +-> ml / graph / rag
```

Business rules are never duplicated in routes or tool adapters.

---

## Quick start

### Prerequisites

- Node.js 20+
- Python 3.11
- A Supabase project (PostgreSQL + Auth) for the persistent path

### 1. Install dependencies

```bash
# from the repository root
python -m venv backend/.venv

# Windows PowerShell
backend\.venv\Scripts\Activate.ps1

# macOS / Linux
# source backend/.venv/bin/activate

pip install -r backend/requirements-dev.txt
npm install
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

The default backend configuration uses an in-memory repository so the API can be
exercised immediately. Set `REPOSITORY_BACKEND=postgres` and provide `DATABASE_URL`
to use Supabase.

### 3. Run everything

```bash
npm run dev
```

- Frontend: <http://localhost:5173>
- API: <http://localhost:8000>
- OpenAPI docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

Or run each side separately:

```bash
npm run dev:backend
npm run dev:frontend
```

### 4. Test

```bash
npm test             # backend pytest suite
npm run build        # frontend type-check + production build
```

---

## Demo data

The generated dataset lives in `data/` and includes **5,000 transactions**
(500 fraud) with deterministic IDs and ground-truth labels.

To load it into Supabase after applying the migrations:

```bash
cd backend
python -m scripts.seed_demo_data --database-url "$DATABASE_URL"
```

Use `--skip-transactions` to load only customers and accounts (for example,
before exercising `POST /api/v1/transactions/ingest` with the sample CSV).

The default in-memory backend starts empty. The test suite includes an
end-to-end test that seeds the generated master data and ingests all 5,000
sample transactions through the real endpoint.

---

## Detection engine

Every assessment produces a 0–100 risk score:

```text
risk = 0.60 × rule score + 0.40 × IsolationForest anomaly percentile
```

- **Large transfer** — amount at or above `$10,000`, escalating at 2× and 4×.
- **High frequency** — five outbound transfers from one account in ten minutes.
- **Rapid succession** — three outbound transfers from one account in sixty seconds.

Rule contributions are combined with a noisy-OR, so multiple independent signals
raise confidence without exceeding 100. The IsolationForest is trained on recent
transaction behavior (amount relative to the sender's history, sender/receiver
velocity, unique counterparties, and shared device/IP reuse). Its score is the
percentile of anomaly strength within the training population.

When fewer than 50 transactions exist, the model reports `insufficient_data` and
rules carry the full score, so cold-start deployments still raise large-transfer
and velocity alerts.

An alert is opened at a risk score of 65. Re-scanning a transaction refreshes its
active alert instead of creating a duplicate; dismissed alerts are not reopened.
Each alert keeps the rule hits, weighted scores, transaction snapshot, and a
human-readable explanation as a point-in-time audit trail.

On the deterministic demo corpus, the default configuration detects every
injected large transfer and fan-in consolidation, 75% of rapid-fire rows, and
produces no alerts on legitimate rows. Circular flows, fan-in/fan-out networks,
and mule rings that never trip a value/velocity rule are intentionally left to
the NetworkX fund-flow tracing service.

---

## Phase 1 API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Public liveness/build info |
| `POST` | `/api/v1/transactions/ingest` | All-or-nothing CSV ingestion |
| `GET` | `/api/v1/transactions` | Paginated filters: account, amount, time, channel, label, device, IP |
| `GET` | `/api/v1/transactions/{id}` | Transaction detail |
| `POST` | `/api/v1/detection/scan` | Scan recent transactions or up to 500 explicit IDs |
| `POST` | `/api/v1/detection/transactions/{id}` | Assess one transaction and open/refresh its alert |
| `GET` | `/api/v1/alerts` | Paginated alert filters: status, transaction, risk range |
| `GET` | `/api/v1/alerts/{id}` | Alert detail with rule hits, scores, and evidence |

Errors use one envelope across the API:

```json
{
  "error": {
    "code": "transaction_not_found",
    "message": "Transaction not found",
    "details": {}
  }
}
```

---

## Phase 1 status

- [x] Monorepo scaffold and local developer workflow
- [x] Supabase migrations, pgvector, RLS policies, and indexes
- [x] Synthetic demo data with injected fraud patterns and ground truth
- [x] CSV ingestion and paginated transaction search
- [x] Detection engine: rules + IsolationForest + weighted risk score
- [ ] Account risk profiles
- [ ] NetworkX fund-flow tracing
- [ ] Backend test suite
- [ ] Supabase Auth JWT verification and role enforcement
- [ ] Architecture documentation

Deployment targets: **Vercel** for `frontend/` and **Render** for `backend/`.

---

## Security notes

- Never commit `.env` files or Supabase service-role keys.
- `SUPABASE_SERVICE_ROLE_KEY` is intentionally not part of the Phase 1 runtime:
  the backend connects through `DATABASE_URL` and verifies user JWTs itself.
- Row-Level Security policies protect direct Supabase client access. The API always
  performs its own role checks in addition to database policies.


## Integrated dashboard

The visual dashboard from the companion `hackathon-ui` repository has been consolidated into
`frontend/src/App.tsx` and `frontend/src/App.css` in this main repository. The separate
`hackathon-ui` repository is preserved as a backup/source; the submission's main codebase is
this repository.

**Demo integrity:** dashboard cards and charts currently contain illustrative sample values.
The embedded Copilot is a UI prototype and does not yet perform live RAG retrieval. The MCP
directory is reserved for a future authenticated remote MCP server; do not describe it as
connected until the endpoint and client connection have been tested.

## 90-minute submission focus

1. Run the frontend and backend locally and resolve startup/build errors.
2. Demonstrate transaction ingestion, detection scan, and alert review through the API.
3. Keep dashboard sample values clearly identified as demo data until wired to API responses.
4. Submit this repository as the single source of truth. Do not delete the companion UI repository.
