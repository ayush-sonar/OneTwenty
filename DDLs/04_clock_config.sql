-- DDL: Clock Configuration (Phase 4)
-- Stores hardware configuration and assignment for OneTwenty Clocks.

CREATE TABLE IF NOT EXISTS clock_configs (
    id SERIAL PRIMARY KEY,
    clock_id VARCHAR(100) UNIQUE NOT NULL, -- Alphanumeric unique identifier
    wifi_name VARCHAR(255),
    wifi_password VARCHAR(255),
    user_subdomain_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup by clock_id
CREATE INDEX IF NOT EXISTS idx_clock_configs_clock_id ON clock_configs(clock_id);

-- Optional: Link to tenants table if we want to enforce relationship
-- ALTER TABLE clock_configs ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES tenants(id) ON DELETE SET NULL;
