-- =====================================================================
-- Migration: Add user_settings Table
-- Industry-Standard PostgreSQL Schema Extension
-- =====================================================================

CREATE TABLE IF NOT EXISTS user_settings (
    setting_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    company_name        VARCHAR(255) DEFAULT 'Enterprise Vendor Reliability Corp',
    company_email       VARCHAR(255),
    company_phone       VARCHAR(50),
    company_address     VARCHAR(255),
    email_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    sms_notifications   BOOLEAN NOT NULL DEFAULT FALSE,
    vendor_alerts       BOOLEAN NOT NULL DEFAULT TRUE,
    contract_alerts     BOOLEAN NOT NULL DEFAULT TRUE,
    security_2fa        BOOLEAN NOT NULL DEFAULT FALSE,
    language            VARCHAR(20) DEFAULT 'English',
    theme               VARCHAR(20) DEFAULT 'light',
    timezone            VARCHAR(50) DEFAULT 'Asia/Kolkata',
    preferred_currency  VARCHAR(10) DEFAULT 'INR',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user ON user_settings(user_id);
