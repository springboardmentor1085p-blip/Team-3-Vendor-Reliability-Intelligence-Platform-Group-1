-- =====================================================================
-- VENDOR RELIABILITY INTELLIGENCE & PROCUREMENT RISK MANAGEMENT PLATFORM
-- PostgreSQL Database Schema (Industry-Standard Design)
-- Stack reference: FastAPI + SQLAlchemy + Alembic + PostgreSQL + Redis
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0. EXTENSIONS
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- for fuzzy/text search on vendor names

-- ---------------------------------------------------------------------
-- 1. ENUM TYPES  (centralizes status vocab -> avoids "magic strings")
-- ---------------------------------------------------------------------
CREATE TYPE user_status_enum        AS ENUM ('active','inactive','suspended','locked');
CREATE TYPE vendor_status_enum      AS ENUM ('pending','approved','rejected','suspended','blacklisted');
CREATE TYPE approval_status_enum    AS ENUM ('pending','approved','rejected');
CREATE TYPE po_status_enum          AS ENUM ('pending','approved','ordered','delivered','completed','cancelled');
CREATE TYPE request_status_enum     AS ENUM ('pending','approved','rejected','converted_to_po','cancelled');
CREATE TYPE delivery_status_enum    AS ENUM ('not_dispatched','in_transit','delivered','delayed','returned');
CREATE TYPE invoice_status_enum     AS ENUM ('pending','partially_paid','paid','overdue','disputed');
CREATE TYPE contract_status_enum    AS ENUM ('draft','active','expired','terminated','renewed');
CREATE TYPE compliance_status_enum  AS ENUM ('compliant','non_compliant','under_review','waived');
CREATE TYPE risk_level_enum         AS ENUM ('low','medium','high','critical');
CREATE TYPE priority_enum           AS ENUM ('low','medium','high','urgent');
CREATE TYPE notification_channel_enum AS ENUM ('in_app','email','sms');
CREATE TYPE issue_status_enum       AS ENUM ('open','in_progress','resolved','closed');
CREATE TYPE report_format_enum      AS ENUM ('pdf','excel');

-- ---------------------------------------------------------------------
-- 2. AUTH & ROLE MANAGEMENT
-- ---------------------------------------------------------------------
CREATE TABLE roles (
    role_id         SMALLSERIAL PRIMARY KEY,
    role_name       VARCHAR(50) NOT NULL UNIQUE,   -- Administrator, Procurement Manager, Supply Chain Manager,
                                                    -- Vendor, Finance Officer, Auditor
    description     VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id         SMALLINT NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT,
    full_name       VARCHAR(120) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    password_hash   VARCHAR(255) NOT NULL,
    status          user_status_enum NOT NULL DEFAULT 'active',
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_status ON users(status);

CREATE TABLE password_reset_tokens (
    token_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    used_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_prt_user ON password_reset_tokens(user_id);

-- ---------------------------------------------------------------------
-- 3. VENDOR MANAGEMENT
-- ---------------------------------------------------------------------
CREATE TABLE vendor_categories (
    category_id     SMALLSERIAL PRIMARY KEY,
    category_name   VARCHAR(80) NOT NULL UNIQUE,   -- Raw Material, Equipment, IT, Service, Logistics, Maintenance
    description     VARCHAR(255)
);

CREATE TABLE vendors (
    vendor_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_code     VARCHAR(20) NOT NULL UNIQUE,
    company_name    VARCHAR(150) NOT NULL,
    category_id     SMALLINT NOT NULL REFERENCES vendor_categories(category_id),
    linked_user_id  UUID REFERENCES users(user_id) ON DELETE SET NULL,  -- vendor portal login
    tax_id          VARCHAR(50),
    website         VARCHAR(200),
    address_line    VARCHAR(200),
    city            VARCHAR(80),
    state           VARCHAR(80),
    country         VARCHAR(80),
    postal_code     VARCHAR(20),
    status          vendor_status_enum NOT NULL DEFAULT 'pending',
    approved_by     UUID REFERENCES users(user_id),
    approved_at     TIMESTAMPTZ,
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_vendors_category ON vendors(category_id);
CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_name_trgm ON vendors USING gin (company_name gin_trgm_ops);

CREATE TABLE vendor_contacts (
    contact_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    contact_name    VARCHAR(120) NOT NULL,
    designation     VARCHAR(80),
    email           VARCHAR(150),
    phone           VARCHAR(20),
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_contacts_vendor ON vendor_contacts(vendor_id);

CREATE TABLE vendor_documents (
    document_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    document_type   VARCHAR(80) NOT NULL,          -- license, insurance, tax_cert, etc.
    file_path       VARCHAR(400) NOT NULL,         -- S3 object key
    uploaded_by     UUID REFERENCES users(user_id),
    expiry_date     DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_documents_vendor ON vendor_documents(vendor_id);

-- ---------------------------------------------------------------------
-- 4. PROCUREMENT MANAGEMENT
-- ---------------------------------------------------------------------
CREATE TABLE procurement_requests (
    request_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number  VARCHAR(30) NOT NULL UNIQUE,
    requested_by    UUID NOT NULL REFERENCES users(user_id),
    department      VARCHAR(100),
    item_description TEXT NOT NULL,
    quantity        NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
    estimated_cost  NUMERIC(14,2) CHECK (estimated_cost >= 0),
    priority        priority_enum NOT NULL DEFAULT 'medium',
    required_by_date DATE,
    status          request_status_enum NOT NULL DEFAULT 'pending',
    approved_by     UUID REFERENCES users(user_id),
    approved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_requests_status ON procurement_requests(status);
CREATE INDEX idx_requests_requester ON procurement_requests(requested_by);

CREATE TABLE purchase_orders (
    po_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number           VARCHAR(30) NOT NULL UNIQUE,
    request_id          UUID REFERENCES procurement_requests(request_id),
    vendor_id           UUID NOT NULL REFERENCES vendors(vendor_id),
    created_by          UUID NOT NULL REFERENCES users(user_id),
    order_date          DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_delivery_date DATE,
    actual_delivery_date   DATE,
    payment_terms       VARCHAR(100),
    total_amount        NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    status              po_status_enum NOT NULL DEFAULT 'pending',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_po_vendor ON purchase_orders(vendor_id);
CREATE INDEX idx_po_status ON purchase_orders(status);
CREATE INDEX idx_po_dates ON purchase_orders(order_date, expected_delivery_date);

CREATE TABLE purchase_order_items (
    po_item_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id           UUID NOT NULL REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
    item_name       VARCHAR(150) NOT NULL,
    description     VARCHAR(400),
    uom             VARCHAR(20),                   -- unit of measure
    quantity        NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    total_price     NUMERIC(14,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);
CREATE INDEX idx_poitems_po ON purchase_order_items(po_id);

CREATE TABLE invoices (
    invoice_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number  VARCHAR(30) NOT NULL UNIQUE,
    po_id           UUID NOT NULL REFERENCES purchase_orders(po_id),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id),
    invoice_date    DATE NOT NULL,
    due_date        DATE,
    amount          NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
    tax_amount      NUMERIC(14,2) NOT NULL DEFAULT 0,
    status          invoice_status_enum NOT NULL DEFAULT 'pending',
    paid_date       DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_invoices_po ON invoices(po_id);
CREATE INDEX idx_invoices_vendor ON invoices(vendor_id);
CREATE INDEX idx_invoices_status ON invoices(status);

CREATE TABLE delivery_tracking (
    delivery_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id           UUID NOT NULL REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
    tracking_number VARCHAR(80),
    carrier         VARCHAR(100),
    dispatch_date   DATE,
    expected_date   DATE,
    delivered_date  DATE,
    delivery_status delivery_status_enum NOT NULL DEFAULT 'not_dispatched',
    remarks         VARCHAR(300),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_delivery_po ON delivery_tracking(po_id);

-- ---------------------------------------------------------------------
-- 5. VENDOR PERFORMANCE
-- ---------------------------------------------------------------------
CREATE TABLE vendor_performance_metrics (
    metric_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    po_id           UUID REFERENCES purchase_orders(po_id),
    metric_type     VARCHAR(60) NOT NULL,      -- on_time_delivery, delayed_delivery, quality_rating,
                                                -- response_time, issue_resolution_time, completion_rate
    metric_value    NUMERIC(10,2) NOT NULL,
    recorded_by     UUID REFERENCES users(user_id),
    recorded_date   DATE NOT NULL DEFAULT CURRENT_DATE
);
CREATE INDEX idx_perf_vendor_type ON vendor_performance_metrics(vendor_id, metric_type);

CREATE TABLE vendor_ratings (
    rating_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    po_id           UUID REFERENCES purchase_orders(po_id),
    rated_by        UUID NOT NULL REFERENCES users(user_id),
    quality_rating      SMALLINT CHECK (quality_rating BETWEEN 1 AND 5),
    delivery_rating      SMALLINT CHECK (delivery_rating BETWEEN 1 AND 5),
    communication_rating SMALLINT CHECK (communication_rating BETWEEN 1 AND 5),
    overall_rating       NUMERIC(3,2),
    comments        TEXT,
    rating_date     DATE NOT NULL DEFAULT CURRENT_DATE
);
CREATE INDEX idx_ratings_vendor ON vendor_ratings(vendor_id);

CREATE TABLE vendor_issues (
    issue_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    po_id           UUID REFERENCES purchase_orders(po_id),
    reported_by     UUID NOT NULL REFERENCES users(user_id),
    issue_type      VARCHAR(80) NOT NULL,
    description     TEXT,
    status          issue_status_enum NOT NULL DEFAULT 'open',
    reported_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ,
    resolution_time_hours NUMERIC(10,2) GENERATED ALWAYS AS
        (EXTRACT(EPOCH FROM (resolved_at - reported_at)) / 3600.0) STORED
);
CREATE INDEX idx_issues_vendor ON vendor_issues(vendor_id);

-- ---------------------------------------------------------------------
-- 6. VENDOR RELIABILITY SCORING
-- ---------------------------------------------------------------------
CREATE TABLE vendor_reliability_scores (
    score_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id           UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    delivery_score      NUMERIC(5,2) NOT NULL DEFAULT 0,
    quality_score       NUMERIC(5,2) NOT NULL DEFAULT 0,
    communication_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    compliance_score    NUMERIC(5,2) NOT NULL DEFAULT 0,
    purchase_history_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    issue_resolution_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    overall_score       NUMERIC(5,2) NOT NULL DEFAULT 0,
    risk_level          risk_level_enum NOT NULL DEFAULT 'medium',
    calculated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (vendor_id)                          -- one "current" score row per vendor
);

CREATE TABLE reliability_score_history (
    history_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    overall_score   NUMERIC(5,2) NOT NULL,
    risk_level      risk_level_enum NOT NULL,
    calculated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_score_history_vendor_date ON reliability_score_history(vendor_id, calculated_at);

-- ---------------------------------------------------------------------
-- 7. CONTRACT & COMPLIANCE
-- ---------------------------------------------------------------------
CREATE TABLE contracts (
    contract_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_number VARCHAR(30) NOT NULL UNIQUE,
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    contract_type   VARCHAR(80),
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    contract_value  NUMERIC(14,2),
    status          contract_status_enum NOT NULL DEFAULT 'draft',
    document_path   VARCHAR(400),
    created_by      UUID REFERENCES users(user_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date >= start_date)
);
CREATE INDEX idx_contracts_vendor ON contracts(vendor_id);
CREATE INDEX idx_contracts_end_date ON contracts(end_date);

CREATE TABLE certifications (
    certification_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id           UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    certification_name  VARCHAR(150) NOT NULL,
    issuing_authority    VARCHAR(150),
    issue_date          DATE,
    expiry_date         DATE,
    document_path       VARCHAR(400),
    status               VARCHAR(30) NOT NULL DEFAULT 'valid'
);
CREATE INDEX idx_certifications_vendor ON certifications(vendor_id);

CREATE TABLE compliance_records (
    compliance_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id       UUID NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    contract_id     UUID REFERENCES contracts(contract_id),
    compliance_type VARCHAR(100) NOT NULL,
    status          compliance_status_enum NOT NULL DEFAULT 'under_review',
    checked_by      UUID REFERENCES users(user_id),
    checked_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    remarks         VARCHAR(300)
);
CREATE INDEX idx_compliance_vendor ON compliance_records(vendor_id);

-- ---------------------------------------------------------------------
-- 8. COMMUNICATION
-- ---------------------------------------------------------------------
CREATE TABLE messages (
    message_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id       UUID NOT NULL REFERENCES users(user_id),
    receiver_id     UUID NOT NULL REFERENCES users(user_id),
    vendor_id       UUID REFERENCES vendors(vendor_id),
    po_id           UUID REFERENCES purchase_orders(po_id),
    subject         VARCHAR(200),
    message_body    TEXT NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_receiver ON messages(receiver_id, is_read);
CREATE INDEX idx_messages_vendor ON messages(vendor_id);

CREATE TABLE message_attachments (
    attachment_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    file_name       VARCHAR(200) NOT NULL,
    file_path       VARCHAR(400) NOT NULL,
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE activity_logs (
    log_id          BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES users(user_id),
    entity_type     VARCHAR(60) NOT NULL,      -- 'vendor','purchase_order','contract', etc.
    entity_id       UUID,
    action          VARCHAR(60) NOT NULL,      -- 'created','updated','approved','deleted'
    description     VARCHAR(300),
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_activity_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_activity_user ON activity_logs(user_id);

-- ---------------------------------------------------------------------
-- 9. NOTIFICATIONS
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    channel         notification_channel_enum NOT NULL DEFAULT 'in_app',
    notification_type VARCHAR(60) NOT NULL,    -- procurement_alert, delivery_delay, contract_expiry, etc.
    title           VARCHAR(150) NOT NULL,
    message         VARCHAR(500) NOT NULL,
    related_entity_type VARCHAR(60),
    related_entity_id   UUID,
    priority        priority_enum NOT NULL DEFAULT 'medium',
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- ---------------------------------------------------------------------
-- 10. REPORTS
-- ---------------------------------------------------------------------
CREATE TABLE reports (
    report_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type     VARCHAR(80) NOT NULL,      -- vendor_performance, procurement, compliance, contract
    generated_by    UUID NOT NULL REFERENCES users(user_id),
    parameters      JSONB,                     -- filter criteria used to generate the report
    file_path       VARCHAR(400),
    format          report_format_enum NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_reports_type ON reports(report_type);

-- ---------------------------------------------------------------------
-- 11. TRIGGERS — auto-maintain updated_at columns
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_users
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at_vendors
    BEFORE UPDATE ON vendors
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at_requests
    BEFORE UPDATE ON procurement_requests
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

CREATE TRIGGER set_updated_at_po
    BEFORE UPDATE ON purchase_orders
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

-- ---------------------------------------------------------------------
-- 12. SEED DATA (roles & vendor categories referenced by the SRS)
-- ---------------------------------------------------------------------
INSERT INTO roles (role_name, description) VALUES
    ('Administrator','Full system access'),
    ('Procurement Manager','Manages procurement workflow and purchase orders'),
    ('Supply Chain Manager','Oversees vendor performance and reliability'),
    ('Vendor','External vendor portal user'),
    ('Finance Officer','Manages invoices and payments'),
    ('Auditor','Read-only compliance and audit access');

INSERT INTO vendor_categories (category_name) VALUES
    ('Raw Material Suppliers'),
    ('Equipment Vendors'),
    ('IT Vendors'),
    ('Service Providers'),
    ('Logistics Partners'),
    ('Maintenance Vendors');

-- ---------------------------------------------------------------------
-- 13. SAMPLE QUERIES USED ACROSS MODULES
-- ---------------------------------------------------------------------

-- 13.1 Vendor Reliability Module — current reliability leaderboard
-- SELECT v.company_name, s.overall_score, s.risk_level
-- FROM vendor_reliability_scores s
-- JOIN vendors v ON v.vendor_id = s.vendor_id
-- ORDER BY s.overall_score DESC
-- LIMIT 20;

-- 13.2 Vendor Performance Module — on-time delivery rate per vendor (last 90 days)
-- SELECT v.vendor_id, v.company_name,
--        ROUND(100.0 * SUM(CASE WHEN d.delivered_date <= po.expected_delivery_date THEN 1 ELSE 0 END)
--              / NULLIF(COUNT(*),0), 2) AS on_time_delivery_pct
-- FROM purchase_orders po
-- JOIN vendors v ON v.vendor_id = po.vendor_id
-- JOIN delivery_tracking d ON d.po_id = po.po_id
-- WHERE po.order_date >= CURRENT_DATE - INTERVAL '90 days'
-- GROUP BY v.vendor_id, v.company_name;

-- 13.3 Procurement Dashboard — active purchase orders summary
-- SELECT status, COUNT(*) AS total_orders, SUM(total_amount) AS total_value
-- FROM purchase_orders
-- WHERE status NOT IN ('completed','cancelled')
-- GROUP BY status;

-- 13.4 Contract & Compliance Module — contracts expiring in next 30 days
-- SELECT c.contract_number, v.company_name, c.end_date
-- FROM contracts c
-- JOIN vendors v ON v.vendor_id = c.vendor_id
-- WHERE c.status = 'active'
--   AND c.end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
-- ORDER BY c.end_date;

-- 13.5 Reliability Module — recompute overall score (weighted formula, matches SRS factors)
-- UPDATE vendor_reliability_scores s
-- SET overall_score = ROUND(
--       0.25 * s.delivery_score +
--       0.20 * s.quality_score +
--       0.15 * s.communication_score +
--       0.20 * s.compliance_score +
--       0.10 * s.purchase_history_score +
--       0.10 * s.issue_resolution_score, 2),
--     risk_level = CASE
--       WHEN 0.25*s.delivery_score + 0.20*s.quality_score + 0.15*s.communication_score
--          + 0.20*s.compliance_score + 0.10*s.purchase_history_score + 0.10*s.issue_resolution_score >= 80 THEN 'low'
--       WHEN ... >= 60 THEN 'medium'
--       WHEN ... >= 40 THEN 'high'
--       ELSE 'critical' END,
--     calculated_at = now()
-- WHERE s.vendor_id = :vendor_id;

-- 13.6 Vendor Issue tracking — average resolution time by vendor
-- SELECT v.company_name, ROUND(AVG(i.resolution_time_hours),2) AS avg_resolution_hours
-- FROM vendor_issues i
-- JOIN vendors v ON v.vendor_id = i.vendor_id
-- WHERE i.status = 'resolved'
-- GROUP BY v.company_name
-- ORDER BY avg_resolution_hours;
