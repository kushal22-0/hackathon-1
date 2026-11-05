# FraudNet AI

> **Detect. Investigate. Explain.**

FraudNet AI is a full-stack fraud analytics workspace: ingest transaction data, detect
suspicious activity with configurable rules plus an IsolationForest model, investigate
fund flows, and explain every alert in language a human can act on.

This repository is being delivered in phases. **Phase 1** establishes the data model,
transaction pipeline, detection engine, investigation services, authentication, and
architecture. Graph exploration, cases UI, analytics, Copilot, and MCP tools are deferred
to later phases.

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
├── frontend/              # React + TypeScript + Vite + Tailwind + shadcn/ui
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

## Phase 1 status

- [x] Monorepo scaffold and local developer workflow
- [ ] Supabase migrations, pgvector, RLS policies, and indexes
- [ ] Synthetic demo data with injected fraud patterns and ground truth
- [ ] CSV ingestion and paginated transaction search
- [ ] Detection engine: rules + IsolationForest + weighted risk score
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
