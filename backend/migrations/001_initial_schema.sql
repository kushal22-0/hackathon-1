-- =============================================================================
-- FraudNet AI — Phase 1 schema
-- Target: Supabase PostgreSQL (PostgreSQL 15+)
--
-- Apply in order with the Supabase CLI or SQL editor:
--   psql "$DATABASE_URL" -f backend/migrations/001_initial_schema.sql
--   psql "$DATABASE_URL" -f backend/migrations/002_rls_policies.sql
--
-- Note: migration 002 defines policies that call Supabase's auth.jwt() helper.
-- It is intended for Supabase, not a vanilla PostgreSQL instance.
-- =============================================================================

begin;

-- -----------------------------------------------------------------------------
-- Extensions
-- -----------------------------------------------------------------------------
create extension if not exists pgcrypto;   -- gen_random_uuid()
create extension if not exists vector;     -- pgvector: embeddings + HNSW index

-- -----------------------------------------------------------------------------
-- Shared updated_at trigger
-- -----------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- -----------------------------------------------------------------------------
-- customers
-- -----------------------------------------------------------------------------
create table public.customers (
    id              uuid primary key default gen_random_uuid(),
    auth_user_id    uuid unique,
    external_id     text not null unique,
    full_name       text not null,
    email           text,
    phone           text,
    country         text not null default 'US',
    risk_level      text not null default 'low'
                    check (risk_level in ('low', 'medium', 'high', 'critical')),
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

comment on table public.customers is
    'Customer master data. auth_user_id optionally links a Supabase Auth user.';

create index customers_risk_level_idx on public.customers (risk_level);
create index customers_email_lower_idx on public.customers (lower(email));

create trigger customers_set_updated_at
before update on public.customers
for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- accounts
-- -----------------------------------------------------------------------------
create table public.accounts (
    id              uuid primary key default gen_random_uuid(),
    customer_id     uuid not null references public.customers (id) on delete cascade,
    account_number  text not null unique,
    account_type    text not null default 'checking'
                    check (account_type in ('checking', 'savings', 'credit', 'business', 'wallet')),
    currency        char(3) not null default 'USD',
    status          text not null default 'active'
                    check (status in ('active', 'dormant', 'frozen', 'closed')),
    balance         numeric(18, 2) not null default 0,
    opened_at       date not null default current_date,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

comment on table public.accounts is
    'Bank accounts owned by customers. Transactions reference account UUIDs.';

create index accounts_customer_id_idx on public.accounts (customer_id);
create index accounts_status_idx on public.accounts (status);
create index accounts_currency_idx on public.accounts (currency);

create trigger accounts_set_updated_at
before update on public.accounts
for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- transactions
-- -----------------------------------------------------------------------------
create table public.transactions (
    id              uuid primary key default gen_random_uuid(),
    from_account    uuid not null references public.accounts (id) on delete restrict,
    to_account      uuid not null references public.accounts (id) on delete restrict,
    amount          numeric(18, 2) not null check (amount > 0),
    currency        char(3) not null default 'USD',
    "timestamp"     timestamptz not null,
    device_id       text,
    ip_address      text,
    channel         text not null default 'api'
                    check (channel in ('mobile', 'web', 'atm', 'branch', 'api', 'wire', 'upi')),
    label           smallint check (label in (0, 1)),
    created_at      timestamptz not null default now()
);

comment on table public.transactions is
    'Immutable transaction event stream. label is nullable ground truth for demo evaluation only.';

create index transactions_timestamp_idx on public.transactions ("timestamp" desc);
create index transactions_from_account_idx on public.transactions (from_account, "timestamp" desc);
create index transactions_to_account_idx on public.transactions (to_account, "timestamp" desc);
create index transactions_amount_idx on public.transactions (amount);
create index transactions_channel_idx on public.transactions (channel);
create index transactions_device_id_idx on public.transactions (device_id) where device_id is not null;
create index transactions_ip_address_idx on public.transactions (ip_address) where ip_address is not null;
create index transactions_fraud_label_idx on public.transactions (label) where label = 1;

-- -----------------------------------------------------------------------------
-- alerts
-- -----------------------------------------------------------------------------
create table public.alerts (
    id              uuid primary key default gen_random_uuid(),
    transaction_id  uuid not null references public.transactions (id) on delete cascade,
    risk_score      numeric(5, 2) not null check (risk_score between 0 and 100),
    rule_hits       jsonb not null default '[]'::jsonb,
    ml_score        numeric(5, 2) not null default 0 check (ml_score between 0 and 100),
    explanation     text not null,
    evidence        jsonb not null default '{}'::jsonb,
    status          text not null default 'open'
                    check (status in ('open', 'triaged', 'dismissed', 'escalated')),
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

comment on table public.alerts is
    'Detection output. rule_hits and evidence preserve a point-in-time audit trail.';

create index alerts_transaction_id_idx on public.alerts (transaction_id);
create index alerts_status_idx on public.alerts (status);
create index alerts_risk_score_idx on public.alerts (risk_score desc);
create index alerts_created_at_idx on public.alerts (created_at desc);
create index alerts_rule_hits_gin_idx on public.alerts using gin (rule_hits);

-- One active alert per transaction; dismissed alerts can be superseded later.
create unique index alerts_one_active_per_transaction_idx
    on public.alerts (transaction_id)
    where status in ('open', 'triaged', 'escalated');

create trigger alerts_set_updated_at
before update on public.alerts
for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- cases
-- -----------------------------------------------------------------------------
create table public.cases (
    id              uuid primary key default gen_random_uuid(),
    alert_id        uuid not null unique references public.alerts (id) on delete cascade,
    title           text not null,
    assignee        uuid,
    status          text not null default 'open'
                    check (status in ('open', 'investigating', 'pending_review', 'closed')),
    outcome         text check (outcome in ('fraud', 'legitimate', 'inconclusive')),
    notes           text,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    closed_at       timestamptz
);

comment on table public.cases is
    'Investigator workflow around an alert. assignee is a Supabase Auth user UUID.';

create index cases_assignee_idx on public.cases (assignee);
create index cases_status_idx on public.cases (status);
create index cases_outcome_idx on public.cases (outcome);
create index cases_created_at_idx on public.cases (created_at desc);

create trigger cases_set_updated_at
before update on public.cases
for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- case_evidence
-- -----------------------------------------------------------------------------
create table public.case_evidence (
    id              uuid primary key default gen_random_uuid(),
    case_id         uuid not null references public.cases (id) on delete cascade,
    transaction_id  uuid references public.transactions (id) on delete set null,
    evidence_type   text not null,
    description     text not null,
    payload         jsonb not null default '{}'::jsonb,
    created_by      uuid,
    created_at      timestamptz not null default now()
);

comment on table public.case_evidence is
    'Immutable-ish evidence log for a case. Attach snapshots and supporting IDs here.';

create index case_evidence_case_id_idx on public.case_evidence (case_id, created_at desc);
create index case_evidence_transaction_id_idx on public.case_evidence (transaction_id);
create index case_evidence_payload_gin_idx on public.case_evidence using gin (payload);

-- -----------------------------------------------------------------------------
-- knowledge base: documents, chunks, pgvector embeddings
-- -----------------------------------------------------------------------------
create table public.kb_documents (
    id              uuid primary key default gen_random_uuid(),
    title           text not null,
    source          text not null,
    content         text not null,
    metadata        jsonb not null default '{}'::jsonb,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

comment on table public.kb_documents is
    'Source documents for the future RAG/Copilot phase.';

create index kb_documents_source_idx on public.kb_documents (source);
create index kb_documents_metadata_gin_idx on public.kb_documents using gin (metadata);

create trigger kb_documents_set_updated_at
before update on public.kb_documents
for each row execute function public.set_updated_at();

create table public.kb_chunks (
    id              uuid primary key default gen_random_uuid(),
    document_id     uuid not null references public.kb_documents (id) on delete cascade,
    chunk_index     integer not null check (chunk_index >= 0),
    content         text not null,
    metadata        jsonb not null default '{}'::jsonb,
    embedding       vector(1536),
    created_at      timestamptz not null default now(),
    unique (document_id, chunk_index)
);

comment on table public.kb_chunks is
    'Chunked knowledge-base content with optional 1536-dim OpenAI embeddings.';

create index kb_chunks_document_id_idx on public.kb_chunks (document_id, chunk_index);
create index kb_chunks_metadata_gin_idx on public.kb_chunks using gin (metadata);

-- HNSW gives better recall/latency than IVFFlat for a small, growing corpus.
-- Cosine distance matches OpenAI text-embedding-3-small normalization.
create index kb_chunks_embedding_hnsw_idx
    on public.kb_chunks
    using hnsw (embedding vector_cosine_ops)
    with (m = 16, ef_construction = 64);

commit;
