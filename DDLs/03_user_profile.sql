-- DDL: User Profile Fields for Onboarding (Phase 3)
-- Uses a single JSONB column for flexible onboarding data.
-- Non-breaking: nullable with default empty object.

    ALTER TABLE users
        ADD COLUMN IF NOT EXISTS name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS additional_data JSONB DEFAULT '{}';

-- GIN index for efficient queries on JSONB fields
CREATE INDEX IF NOT EXISTS idx_users_additional_data ON users USING GIN(additional_data);
