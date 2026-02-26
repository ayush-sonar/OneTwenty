-- DDL for Auth System (Phase 2)
-- Using Serial IDs and 10-char Public IDs

DROP TABLE IF EXISTS api_keys;
DROP TABLE IF EXISTS tenant_users;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tenants;

CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    public_id VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    plan VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    public_id VARCHAR(10) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'doctor', 'user'
    tier VARCHAR(20) DEFAULT 'free', -- 'free', 'premium', 'enterprise'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tenant_users (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'owner', -- owner, admin, viewer
    PRIMARY KEY (user_id, tenant_id)
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    key_value VARCHAR(255) UNIQUE NOT NULL, -- Plain text as requested, or hashed if strict
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE doctor_patients (
    doctor_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    patient_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doctor_id, patient_id),
    CONSTRAINT check_different_users CHECK (doctor_id != patient_id)
);

CREATE INDEX idx_users_public_id ON users(public_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_tenants_public_id ON tenants(public_id);
CREATE INDEX idx_api_keys_value ON api_keys(key_value);
CREATE INDEX idx_doctor_patients_doctor ON doctor_patients(doctor_id);
CREATE INDEX idx_doctor_patients_patient ON doctor_patients(patient_id);
