# Database migrations

These are plain PostgreSQL migrations targeting the Supabase PostgreSQL database.

## Apply with the Supabase CLI

If this repository is linked to a Supabase project:

```bash
supabase db push
```

The CLI expects migrations in `supabase/migrations/`. These files live under
`backend/migrations/` because the backend owns its persistence layer. Either:

- run them directly with `psql`, or
- copy/symlink them into `supabase/migrations/` if you adopt the Supabase CLI.

## Apply with psql

Use the direct database connection string from Supabase (Project Settings →
Database → Connection string → URI). Prefer the session pooler for migrations.

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/001_initial_schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/002_rls_policies.sql
```

Both files run inside a transaction and are intended to be applied once.

## What is created

| Object | Purpose |
| --- | --- |
| `customers` | Customer master data, optional auth-user link |
| `accounts` | Accounts owned by customers |
| `transactions` | Immutable transaction stream + optional ground-truth label |
| `alerts` | Rule/ML evidence, 0–100 risk score, triage status |
| `cases` | Investigation wrapper around an alert |
| `case_evidence` | Evidence snapshots linked to a case/transaction |
| `kb_documents`, `kb_chunks` | RAG source documents and 1536-dim embeddings |

Indexes cover transaction search, account/device/IP pivots, alert triage, case
workload, JSONB rule hits, and HNSW cosine search for embeddings.

## Roles and RLS

`002_rls_policies.sql` enables and forces RLS on every table. It expects Supabase
JWTs with a role in `app_metadata.role` (preferred) or `user_metadata.role`.

- **admin** — full read/write.
- **investigator** — read operational data, triage alerts, create/update cases
  and evidence.
- **authenticated non-staff** — customers can read their own customer/account
  records, nothing else.

Set roles through the Supabase Admin API or by updating `auth.users.raw_app_meta_data`.
Do not store the service-role key in the frontend or commit it to the repo.

## Notes

- Migration 002 calls `auth.jwt()`, so it is Supabase-specific. A vanilla
  PostgreSQL instance will fail at this step.
- The API connects through a trusted database role, so RLS is a second line of
  defense for direct Supabase client access. The FastAPI layer still enforces
  authentication and authorization on every business endpoint.
- pgvector's HNSW index is used for `vector_cosine_ops`; OpenAI
  `text-embedding-3-small` returns 1536 dimensions.
