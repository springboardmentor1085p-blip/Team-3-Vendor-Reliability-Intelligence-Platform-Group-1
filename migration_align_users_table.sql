-- =====================================================================
-- MIGRATION: Align PostgreSQL 'users' table with SQLAlchemy User model
-- Vendor Reliability Intelligence Platform
-- =====================================================================
--
-- PROBLEM: The PostgreSQL schema (vendor_reliability_platform_schema.sql)
-- was created independently from the SQLAlchemy model. The model expects
-- columns that don't exist in PostgreSQL, and PostgreSQL has columns
-- the model doesn't use.
--
-- SCHEMA MISMATCH ANALYSIS:
--
-- ┌──────────────────┬─────────────────────────────┬──────────────────────────────┐
-- │ Column           │ PostgreSQL (actual)          │ SQLAlchemy Model (expected)  │
-- ├──────────────────┼─────────────────────────────┼──────────────────────────────┤
-- │ user_id          │ UUID PK ✅                   │ UUID PK ✅                   │
-- │ username         │ ❌ MISSING                   │ VARCHAR(50) NOT NULL UNIQUE  │
-- │ full_name        │ VARCHAR(120) ⚠️              │ VARCHAR(150) — length diff   │
-- │ email            │ VARCHAR(150) ⚠️              │ VARCHAR(255) — length diff   │
-- │ password_hash    │ VARCHAR(255) ✅              │ VARCHAR(255) ✅              │
-- │ role_id          │ SMALLINT NOT NULL FK ✅      │ SMALLINT NOT NULL FK ✅      │
-- │ is_active        │ ❌ MISSING                   │ BOOLEAN NOT NULL DEFAULT T   │
-- │ status           │ user_status_enum ⚠️ EXTRA   │ ❌ Not in model              │
-- │ phone            │ VARCHAR(20) ⚠️ EXTRA        │ ❌ Not in model              │
-- │ is_email_verified│ BOOLEAN ⚠️ EXTRA            │ ❌ Not in model              │
-- │ last_login_at    │ TIMESTAMPTZ ⚠️ EXTRA        │ ❌ Not in model              │
-- │ created_at       │ TIMESTAMPTZ ✅              │ TIMESTAMPTZ ✅              │
-- │ updated_at       │ TIMESTAMPTZ ✅              │ TIMESTAMPTZ ✅              │
-- └──────────────────┴─────────────────────────────┴──────────────────────────────┘
--
-- INDEXES:
-- ┌─────────────────────────┬──────────────┬──────────────┐
-- │ Index                   │ PostgreSQL   │ Model        │
-- ├─────────────────────────┼──────────────┼──────────────┤
-- │ idx_users_role (role_id)│ ✅ exists    │ ✅ expected  │
-- │ ix_users_username       │ ❌ missing   │ ✅ expected  │
-- │ ix_users_email          │ ❌ missing   │ ✅ expected  │
-- │ ix_users_is_active      │ ❌ missing   │ ✅ expected  │
-- │ idx_users_status        │ ✅ exists    │ ❌ not needed│
-- └─────────────────────────┴──────────────┴──────────────┘
--
-- CONSTRAINTS:
-- ┌─────────────────────────────┬──────────────┬──────────────┐
-- │ Constraint                  │ PostgreSQL   │ Model        │
-- ├─────────────────────────────┼──────────────┼──────────────┤
-- │ PK on user_id               │ ✅           │ ✅           │
-- │ FK role_id → roles.role_id  │ ✅           │ ✅           │
-- │ UNIQUE on username          │ ❌ missing   │ ✅ expected  │
-- │ UNIQUE on email             │ ✅           │ ✅           │
-- └─────────────────────────────┴──────────────┴──────────────┘
--
-- ROLES TABLE: ✅ Matches perfectly — no changes needed.
--
-- =====================================================================

BEGIN;

-- -----------------------------------------------------------------
-- FIX 1: Add missing 'username' column
-- -----------------------------------------------------------------
-- The SQLAlchemy model defines: username VARCHAR(50) NOT NULL UNIQUE
-- PostgreSQL has no such column. This is the cause of the crash:
--   asyncpg.exceptions.UndefinedColumnError: column users.username does not exist
--
-- Strategy for existing rows:
--   Add as nullable → populate from email prefix → set NOT NULL → add UNIQUE + index
-- -----------------------------------------------------------------

ALTER TABLE users
    ADD COLUMN username VARCHAR(50);

-- Populate username for any existing rows using email prefix (before @)
-- Append user_id fragment to guarantee uniqueness
UPDATE users
SET username = LEFT(SPLIT_PART(email, '@', 1), 42) || '_' || LEFT(user_id::TEXT, 7)
WHERE username IS NULL;

-- Now enforce NOT NULL
ALTER TABLE users
    ALTER COLUMN username SET NOT NULL;

-- Add UNIQUE constraint
ALTER TABLE users
    ADD CONSTRAINT uq_users_username UNIQUE (username);

-- Add index (model specifies index=True)
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);


-- -----------------------------------------------------------------
-- FIX 2: Add missing 'is_active' column
-- -----------------------------------------------------------------
-- The SQLAlchemy model defines: is_active BOOLEAN NOT NULL DEFAULT TRUE
-- PostgreSQL has 'status' (user_status_enum) instead.
-- We derive is_active from status: 'active' → TRUE, everything else → FALSE
-- -----------------------------------------------------------------

ALTER TABLE users
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Populate from existing status column for any existing rows
UPDATE users
SET is_active = (status::TEXT = 'active');


-- -----------------------------------------------------------------
-- FIX 3: Widen 'full_name' column from VARCHAR(120) to VARCHAR(150)
-- -----------------------------------------------------------------
-- PostgreSQL: VARCHAR(120)
-- Model:      String(150)
-- This is a safe operation — only increases max length, no data loss.
-- -----------------------------------------------------------------

ALTER TABLE users
    ALTER COLUMN full_name TYPE VARCHAR(150);


-- -----------------------------------------------------------------
-- FIX 4: Widen 'email' column from VARCHAR(150) to VARCHAR(255)
-- -----------------------------------------------------------------
-- PostgreSQL: VARCHAR(150)
-- Model:      String(255)
-- Safe operation — only increases max length.
-- -----------------------------------------------------------------

ALTER TABLE users
    ALTER COLUMN email TYPE VARCHAR(255);


-- -----------------------------------------------------------------
-- FIX 5: Add missing index on 'email'
-- -----------------------------------------------------------------
-- The model specifies index=True on email.
-- PostgreSQL only has UNIQUE constraint but no explicit index.
-- (Note: UNIQUE constraints implicitly create indexes in PostgreSQL,
-- but we add an explicit one to match the model's intent.)
-- -----------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);


-- -----------------------------------------------------------------
-- FIX 6: Add missing index on 'is_active'
-- -----------------------------------------------------------------
-- The model specifies index=True on is_active.
-- -----------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_users_is_active ON users(is_active);


COMMIT;
