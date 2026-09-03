-- =============================================================================
-- Repair — Initial Database Schema
-- Migration: 001_initial_schema.sql
--
-- Apply in Supabase SQL editor or via `supabase db push` (Supabase CLI).
--
-- Table creation order respects foreign key dependencies:
--   domains → concepts → artifacts
--   auth.users → users → mastery, attempts
-- =============================================================================

-- Enable UUID generation (available by default in Supabase/Postgres 13+)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- =============================================================================
-- 1. domains
--    Lookup table for the 5 learning domains.
--    Seeded below — add new domains without a migration by INSERT.
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.domains (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT         NOT NULL UNIQUE,   -- slug: "code", "physics", …
    display_name TEXT        NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.domains            IS 'Learning domains supported by Repair (code, physics, story, business_model, chemistry).';
COMMENT ON COLUMN public.domains.name       IS 'Slug used in the backend domain registry — must match DomainHandler.domain_slug.';


-- =============================================================================
-- 2. users
--    Public profile table that mirrors auth.users.
--    Created automatically when a user signs up via a DB trigger (see below).
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id          UUID         PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT         NOT NULL,
    display_name TEXT,
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.users IS 'Public user profile — mirrors auth.users and is safe to expose via RLS.';


-- =============================================================================
-- 3. concepts
--    Individual skills / concepts within a domain.
--    e.g. domain=code, tag="recursion-base-case"
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.concepts (
    id           UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id    UUID  NOT NULL REFERENCES public.domains(id) ON DELETE CASCADE,
    tag          TEXT  NOT NULL,                -- machine-readable slug
    display_name TEXT  NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (domain_id, tag)
);

COMMENT ON TABLE  public.concepts            IS 'Individual learnable concepts within a domain.';
COMMENT ON COLUMN public.concepts.tag        IS 'Slug used in the backend, e.g. "recursion-base-case".';


-- =============================================================================
-- 4. mastery
--    Tracks a user''s mastery score for each concept.
--    Composite PK — one row per (user, concept) pair.
--    Written by MasteryService after each attempt.
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.mastery (
    user_id        UUID   NOT NULL REFERENCES public.users(id)    ON DELETE CASCADE,
    concept_id     UUID   NOT NULL REFERENCES public.concepts(id) ON DELETE CASCADE,
    mastery_score  FLOAT  NOT NULL DEFAULT 0.0 CHECK (mastery_score BETWEEN 0.0 AND 1.0),
    attempts_count INT    NOT NULL DEFAULT 0   CHECK (attempts_count >= 0),
    last_updated   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, concept_id)
);

COMMENT ON TABLE  public.mastery               IS 'User mastery score per concept — updated after every attempt via exponential moving average.';
COMMENT ON COLUMN public.mastery.mastery_score IS 'EMA of (fix_correctness + understanding_score) / 2, clamped to [0, 1].';


-- =============================================================================
-- 5. artifacts
--    A broken artifact presented to users for repair.
--    artifact_payload is domain-specific JSONB (see domain handler docs).
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.artifacts (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id          UUID        NOT NULL REFERENCES public.domains(id)   ON DELETE RESTRICT,
    target_concept_id  UUID        NOT NULL REFERENCES public.concepts(id)  ON DELETE RESTRICT,
    artifact_payload   JSONB       NOT NULL DEFAULT '{}',
    root_cause         TEXT        NOT NULL DEFAULT '',
    expected_behavior  TEXT        NOT NULL DEFAULT '',
    actual_behavior    TEXT        NOT NULL DEFAULT '',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.artifacts                  IS 'Broken artifacts presented to users. Payload shape is domain-specific — see domains/*/handler.py.';
COMMENT ON COLUMN public.artifacts.artifact_payload IS 'Domain-specific payload JSONB. Shape documented in each DomainHandler.';
COMMENT ON COLUMN public.artifacts.root_cause       IS 'Internal note describing WHY the artifact is broken (used by hint generation).';

CREATE INDEX IF NOT EXISTS artifacts_domain_idx   ON public.artifacts (domain_id);
CREATE INDEX IF NOT EXISTS artifacts_concept_idx  ON public.artifacts (target_concept_id);


-- =============================================================================
-- 6. attempts
--    A user''s attempt at fixing an artifact.
--    fix_correctness and understanding_score are set by DomainHandler.validate_fix().
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.attempts (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id           UUID        NOT NULL REFERENCES public.artifacts(id) ON DELETE CASCADE,
    user_id               UUID        NOT NULL REFERENCES public.users(id)     ON DELETE CASCADE,
    submitted_fix         JSONB       NOT NULL DEFAULT '{}',
    submitted_explanation TEXT        NOT NULL DEFAULT '',
    fix_correctness       FLOAT       CHECK (fix_correctness    BETWEEN 0.0 AND 1.0),
    understanding_score   FLOAT       CHECK (understanding_score BETWEEN 0.0 AND 1.0),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE  public.attempts                      IS 'Each row is one user attempt at repairing an artifact.';
COMMENT ON COLUMN public.attempts.fix_correctness      IS 'Score [0,1] assigned by DomainHandler.validate_fix().';
COMMENT ON COLUMN public.attempts.understanding_score  IS 'Explanation quality score [0,1] assigned by DomainHandler.validate_fix().';

CREATE INDEX IF NOT EXISTS attempts_artifact_idx ON public.attempts (artifact_id);
CREATE INDEX IF NOT EXISTS attempts_user_idx     ON public.attempts (user_id);


-- =============================================================================
-- Trigger: auto-create users row on signup
-- =============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, email, display_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data ->> 'full_name',
        NEW.raw_user_meta_data ->> 'avatar_url'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- =============================================================================
-- Row-Level Security (RLS) — stubs
-- All tables have RLS enabled; policies are permissive placeholders until
-- production access patterns are finalised.
-- =============================================================================

ALTER TABLE public.users     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.domains   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.concepts  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mastery   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attempts  ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile.
CREATE POLICY "users_select_own" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users_update_own" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Domains and concepts are publicly readable (reference data).
CREATE POLICY "domains_public_read"  ON public.domains  FOR SELECT USING (true);
CREATE POLICY "concepts_public_read" ON public.concepts FOR SELECT USING (true);

-- Artifacts are publicly readable.
CREATE POLICY "artifacts_public_read" ON public.artifacts FOR SELECT USING (true);

-- Mastery: users can read/write their own rows.
CREATE POLICY "mastery_select_own" ON public.mastery
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "mastery_upsert_own" ON public.mastery
    FOR ALL USING (auth.uid() = user_id);

-- Attempts: users can read/insert their own rows.
CREATE POLICY "attempts_select_own" ON public.attempts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "attempts_insert_own" ON public.attempts
    FOR INSERT WITH CHECK (auth.uid() = user_id);


-- =============================================================================
-- Seed data — 5 domains
-- =============================================================================
INSERT INTO public.domains (name, display_name) VALUES
    ('code',           'Code'),
    ('physics',        'Physics'),
    ('story',          'Story'),
    ('business_model', 'Business Model'),
    ('chemistry',      'Chemistry')
ON CONFLICT (name) DO NOTHING;
