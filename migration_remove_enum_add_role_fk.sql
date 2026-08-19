-- =====================================================================
-- MIGRATION: Remove Enum role column, Add role_id FK to users table
-- Vendor Reliability Intelligence Platform
-- =====================================================================
--
-- PREREQUISITES:
--   1. The 'roles' table must already exist (from the original schema).
--   2. Run seed_roles.sql first to ensure roles are populated.
--
-- This migration:
--   1. Adds a nullable role_id column
--   2. Populates role_id from the existing enum 'role' column
--   3. Makes role_id NOT NULL
--   4. Adds the foreign key constraint
--   5. Creates an index on role_id
--   6. Drops the old enum 'role' column
--   7. Drops the old user_role_enum type (if it exists)
--
-- NOTE: This is a DESTRUCTIVE migration. Back up your data first.
-- =====================================================================

BEGIN;

-- Step 1: Add role_id column (nullable initially for data migration)
ALTER TABLE users
    ADD COLUMN role_id SMALLINT;

-- Step 2: Populate role_id from the existing enum column
-- Maps enum values to the corresponding role_id in the roles table.
-- If the users table has an enum 'role' column with values like
-- 'ADMIN', 'PROCUREMENT_MANAGER', 'VENDOR', 'AUDITOR', this maps them.
UPDATE users u
SET role_id = r.role_id
FROM roles r
WHERE UPPER(r.role_name) = u.role::TEXT;

-- Step 3: Set NOT NULL constraint (fails if any user has no matching role)
ALTER TABLE users
    ALTER COLUMN role_id SET NOT NULL;

-- Step 4: Add foreign key constraint
ALTER TABLE users
    ADD CONSTRAINT fk_users_role_id
    FOREIGN KEY (role_id) REFERENCES roles(role_id);

-- Step 5: Create index for performance
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);

-- Step 6: Drop the old enum-based role column
ALTER TABLE users
    DROP COLUMN role;

-- Step 7: Drop the old enum type (safe — only if it exists and is unused)
DROP TYPE IF EXISTS user_role_enum;

COMMIT;
