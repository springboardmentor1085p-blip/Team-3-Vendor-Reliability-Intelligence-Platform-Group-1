-- =====================================================================
-- MIGRATION: Complete users table alignment with SQLAlchemy User model
-- Vendor Reliability Intelligence Platform
-- =====================================================================
--
-- Purpose:
--   Safely complete the partially applied users-table alignment without
--   recreating the database, dropping tables, or modifying older migrations.
--
-- Aligns public.users with app/models/users.py:
--   username    VARCHAR(50)  NOT NULL UNIQUE, indexed
--   full_name   VARCHAR(150) NOT NULL
--   email       VARCHAR(255) NOT NULL UNIQUE, indexed
--   role_id     SMALLINT     NOT NULL FK roles(role_id), indexed
--   is_active   BOOLEAN      NOT NULL DEFAULT TRUE, indexed
--
-- Safe to rerun:
--   Uses IF NOT EXISTS where PostgreSQL supports it, and guarded DO blocks
--   for constraints.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1. Ensure username exists, is populated, and is constrained/indexed.
-- ---------------------------------------------------------------------

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS username VARCHAR(50);

UPDATE users
SET username = LEFT(SPLIT_PART(email, '@', 1), 42) || '_' || LEFT(user_id::TEXT, 7)
WHERE username IS NULL;

ALTER TABLE users
    ALTER COLUMN username SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.users'::regclass
          AND conname = 'uq_users_username'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT uq_users_username UNIQUE (username);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_users_username
    ON users(username);

-- ---------------------------------------------------------------------
-- 2. Ensure is_active exists and mirrors the legacy status column.
-- ---------------------------------------------------------------------

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN;

UPDATE users
SET is_active = COALESCE(is_active, status::TEXT = 'active');

ALTER TABLE users
    ALTER COLUMN is_active SET DEFAULT TRUE;

ALTER TABLE users
    ALTER COLUMN is_active SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_users_is_active
    ON users(is_active);

-- ---------------------------------------------------------------------
-- 3. Widen columns to match the ORM model.
-- ---------------------------------------------------------------------

ALTER TABLE users
    ALTER COLUMN full_name TYPE VARCHAR(150);

ALTER TABLE users
    ALTER COLUMN email TYPE VARCHAR(255);

CREATE INDEX IF NOT EXISTS ix_users_email
    ON users(email);

-- ---------------------------------------------------------------------
-- 4. Ensure role_id has the expected supporting index.
-- ---------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_users_role_id
    ON users(role_id);

COMMIT;
