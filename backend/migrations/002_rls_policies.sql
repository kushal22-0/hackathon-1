-- =============================================================================
-- FraudNet AI — Phase 1 Row-Level Security
-- Target: Supabase PostgreSQL. Apply after 001_initial_schema.sql.
--
-- Roles live in the Supabase JWT:
--   app_metadata.role (preferred) or user_metadata.role
--   allowed: 'admin' | 'investigator'
--
-- The FastAPI backend itself performs JWT verification and connects with a
-- trusted database role. These policies defend direct Supabase client access
-- (anon/authenticated keys), not the backend service connection.
-- =============================================================================

begin;

-- -----------------------------------------------------------------------------
-- Role helpers
-- -----------------------------------------------------------------------------
create or replace function public.current_app_role()
returns text
language sql
stable
security invoker
set search_path = public
as $$
    select coalesce(
        nullif(auth.jwt() -> 'app_metadata' ->> 'role', ''),
        nullif(auth.jwt() -> 'user_metadata' ->> 'role', ''),
        'investigator'
    );
$$;

comment on function public.current_app_role() is
    'Reads the application role from the Supabase JWT, defaulting to investigator.';

create or replace function public.is_staff()
returns boolean
language sql
stable
security invoker
set search_path = public
as $$
    select public.current_app_role() in ('admin', 'investigator');
$$;

create or replace function public.is_admin()
returns boolean
language sql
stable
security invoker
set search_path = public
as $$
    select public.current_app_role() = 'admin';
$$;

-- -----------------------------------------------------------------------------
-- Enable RLS
-- -----------------------------------------------------------------------------
alter table public.customers      enable row level security;
alter table public.accounts       enable row level security;
alter table public.transactions   enable row level security;
alter table public.alerts         enable row level security;
alter table public.cases          enable row level security;
alter table public.case_evidence  enable row level security;
alter table public.kb_documents   enable row level security;
alter table public.kb_chunks      enable row level security;

-- -----------------------------------------------------------------------------
-- customers
-- -----------------------------------------------------------------------------
create policy "staff read customers"
    on public.customers for select
    to authenticated
    using (public.is_staff());

create policy "customers read own record"
    on public.customers for select
    to authenticated
    using (auth_user_id = (select auth.uid()));

create policy "admins manage customers"
    on public.customers for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- -----------------------------------------------------------------------------
-- accounts
-- -----------------------------------------------------------------------------
create policy "staff read accounts"
    on public.accounts for select
    to authenticated
    using (public.is_staff());

create policy "customers read own accounts"
    on public.accounts for select
    to authenticated
    using (
        customer_id in (
            select id from public.customers where auth_user_id = (select auth.uid())
        )
    );

create policy "admins manage accounts"
    on public.accounts for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- -----------------------------------------------------------------------------
-- transactions (staff read; admins write. Ingest is normally backend-only.)
-- -----------------------------------------------------------------------------
create policy "staff read transactions"
    on public.transactions for select
    to authenticated
    using (public.is_staff());

create policy "admins manage transactions"
    on public.transactions for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- -----------------------------------------------------------------------------
-- alerts (investigators can triage; admins can manage everything)
-- -----------------------------------------------------------------------------
create policy "staff read alerts"
    on public.alerts for select
    to authenticated
    using (public.is_staff());

create policy "staff update alerts"
    on public.alerts for update
    to authenticated
    using (public.is_staff())
    with check (public.is_staff());

create policy "admins manage alerts"
    on public.alerts for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- -----------------------------------------------------------------------------
-- cases
-- -----------------------------------------------------------------------------
create policy "staff read cases"
    on public.cases for select
    to authenticated
    using (public.is_staff());

create policy "staff create cases"
    on public.cases for insert
    to authenticated
    with check (public.is_staff());

create policy "staff update cases"
    on public.cases for update
    to authenticated
    using (public.is_staff())
    with check (public.is_staff());

create policy "admins delete cases"
    on public.cases for delete
    to authenticated
    using (public.is_admin());

create policy "admins manage cases"
    on public.cases for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- -----------------------------------------------------------------------------
-- case_evidence
-- -----------------------------------------------------------------------------
create policy "staff read case evidence"
    on public.case_evidence for select
    to authenticated
    using (public.is_staff());

create policy "staff add case evidence"
    on public.case_evidence for insert
    to authenticated
    with check (public.is_staff());

create policy "admins manage case evidence"
    on public.case_evidence for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

-- -----------------------------------------------------------------------------
-- knowledge base (staff read; admins manage)
-- -----------------------------------------------------------------------------
create policy "staff read kb documents"
    on public.kb_documents for select
    to authenticated
    using (public.is_staff());

create policy "admins manage kb documents"
    on public.kb_documents for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

create policy "staff read kb chunks"
    on public.kb_chunks for select
    to authenticated
    using (public.is_staff());

create policy "admins manage kb chunks"
    on public.kb_chunks for all
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());

commit;
