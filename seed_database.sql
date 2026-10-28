-- 1. Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    email VARCHAR(128) UNIQUE NOT NULL,
    subscription_tier VARCHAR(32) NOT NULL DEFAULT 'free',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    stripe_customer_id VARCHAR(64) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create System Diagnostic Logs Table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    trace_id VARCHAR(64) UNIQUE NOT NULL,
    level VARCHAR(16) NOT NULL,
    service VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Stripe Charges Table
CREATE TABLE IF NOT EXISTS stripe_charges (
    charge_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) REFERENCES users(stripe_customer_id),
    amount INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL,
    description TEXT,
    invoice_id VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create Persistent Diagnostic Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    user_email VARCHAR(128) NOT NULL,
    stripe_customer_id VARCHAR(64),
    issue_description TEXT NOT NULL,
    trace_id VARCHAR(64),
    root_cause TEXT,
    proposed_action VARCHAR(64),
    proposed_action_details TEXT,
    customer_response_message TEXT,
    audit_passed BOOLEAN DEFAULT TRUE,
    audit_error TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'awaiting_approval',
    operator_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);

-- Seed Sample Data (Clean slate insert)
TRUNCATE TABLE stripe_charges, system_logs, users CASCADE;

-- Insert Real Sample Customers
INSERT INTO users (id, name, email, subscription_tier, status, stripe_customer_id) VALUES
('usr_alex_01', 'Alex Rivera', 'alex@techcorp.io', 'free', 'active', 'cus_stripe_alex123'),
('usr_sarah_02', 'Sarah Chen', 'sarah@innovate.co', 'pro', 'active', 'cus_stripe_sarah456'),
('usr_marcus_03', 'Marcus Vance', 'marcus@dataflow.org', 'enterprise', 'suspended', 'cus_stripe_marcus789');

-- Insert Real System Error Log Traces
INSERT INTO system_logs (trace_id, level, service, message, timestamp) VALUES
('tr_webhook_err_901', 'ERROR', 'payment-webhook-consumer', 'Webhook delivery failed for customer: Timeout connecting to DB write replica during subscription upgrade payload ingestion', NOW() - INTERVAL '2 hours'),
('tr_double_charge_402', 'WARN', 'billing-checkout', 'Duplicate payment charge detected within 12 seconds for customer. Rapid button click bypassed idempotency lock.', NOW() - INTERVAL '4 hours'),
('tr_fraud_flag_777', 'SECURITY', 'auth-fraud-shield', 'Auto-suspension applied to user: Rapid IP shift (US-East to EU-West) during session token refresh', NOW() - INTERVAL '1 day');

-- Insert Real Stripe Gateway Transactions
INSERT INTO stripe_charges (charge_id, customer_id, amount, status, description, invoice_id) VALUES
('ch_alex_01', 'cus_stripe_alex123', 2900, 'succeeded', 'Pro Tier Monthly Subscription', 'in_alex_29'),
('ch_sarah_01', 'cus_stripe_sarah456', 4900, 'succeeded', 'Pro Renewal Primary', 'in_sarah_a'),
('ch_sarah_02', 'cus_stripe_sarah456', 4900, 'succeeded', 'Pro Renewal Duplicate', 'in_sarah_b'),
('ch_marcus_01', 'cus_stripe_marcus789', 29900, 'succeeded', 'Enterprise Tier Annual', 'in_marcus_ent');
