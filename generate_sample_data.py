import os
import random
import uuid
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
fake = Faker()

def generate_and_seed_data():
    db_url = os.getenv("DATABASE_URL")
    print(f"🎲 Generating 50+ Enterprise Customer Records using Faker...")

    users = [
        # Core Test Baseline Accounts
        ("usr_alex_01", "Alex Rivera", "alex@techcorp.io", "free", "active", "cus_stripe_alex123"),
        ("usr_sarah_02", "Sarah Chen", "sarah@innovate.co", "pro", "active", "cus_stripe_sarah456"),
        ("usr_marcus_03", "Marcus Vance", "marcus@dataflow.org", "enterprise", "suspended", "cus_stripe_marcus789"),
    ]

    logs = [
        # Core Test Baseline Logs
        ("tr_webhook_err_901", "ERROR", "payment-webhook-consumer", "Webhook delivery failed for customer: Timeout connecting to DB write replica during subscription upgrade payload ingestion"),
        ("tr_double_charge_402", "WARN", "billing-checkout", "Duplicate payment charge detected within 12 seconds for customer. Rapid button click bypassed idempotency lock."),
        ("tr_fraud_flag_777", "SECURITY", "auth-fraud-shield", "Auto-suspension applied to user: Rapid IP shift (US-East to EU-West) during session token refresh"),
    ]

    charges = [
        # Core Test Baseline Stripe Charges
        ("ch_alex_01", "cus_stripe_alex123", 2900, "succeeded", "Pro Tier Monthly Subscription", "in_alex_29"),
        ("ch_sarah_01", "cus_stripe_sarah456", 4900, "succeeded", "Pro Renewal Primary", "in_sarah_a"),
        ("ch_sarah_02", "cus_stripe_sarah456", 4900, "succeeded", "Pro Renewal Duplicate", "in_sarah_b"),
        ("ch_marcus_01", "cus_stripe_marcus789", 29900, "succeeded", "Enterprise Tier Annual", "in_marcus_ent"),
    ]

    tiers = ["free", "pro", "enterprise"]
    statuses = ["active", "suspended", "active", "active"]
    log_levels = ["ERROR", "WARN", "SECURITY", "INFO"]
    services = ["billing-checkout", "payment-webhook-consumer", "auth-fraud-shield", "api-gateway-v2", "db-replicator"]

    log_templates = [
        "Database write replica connection timeout during payload ingestion for user tier update",
        "Duplicate checkout payment intent detected within 10s window. Concurrency lock activated.",
        "Security threat alert: IP address velocity threshold exceeded during OAuth session refresh.",
        "Stripe webhook listener rate limit throttled (HTTP 429). Retry queue backlog engaged.",
        "SAML SSO identity provider certificate validation failed for tenant domain authentication.",
        "Workspace license allocation overflow: Attempted to invite user beyond plan seat quota."
    ]

    # Generate 50+ realistic synthetic enterprise profiles
    for i in range(4, 55):
        u_id = f"usr_{fake.hexify(text='^^^^^^^^')}"
        name = fake.name()
        company_domain = fake.domain_name()
        email = f"{name.lower().replace(' ', '.')}@{company_domain}"
        tier = random.choice(tiers)
        status = random.choice(statuses)
        stripe_id = f"cus_stripe_{fake.hexify(text='^^^^^^^^^^^^')}"

        users.append((u_id, name, email, tier, status, stripe_id))

        # Generate corresponding log trace
        trace_id = f"tr_{fake.hexify(text='^^^^^^^^^^^^')}"
        level = random.choice(log_levels)
        service = random.choice(services)
        message = f"{random.choice(log_templates)} (User ID: {u_id})"
        logs.append((trace_id, level, service, message))

        # Generate corresponding Stripe charge
        charge_id = f"ch_{fake.hexify(text='^^^^^^^^^^^^')}"
        amount = random.choice([2900, 4900, 9900, 29900, 49900])
        charge_status = random.choice(["succeeded", "succeeded", "succeeded", "failed"])
        desc = f"{tier.capitalize()} Subscription Plan"
        inv_id = f"in_{fake.hexify(text='^^^^^^^^')}"
        charges.append((charge_id, stripe_id, amount, charge_status, desc, inv_id))

    if db_url and (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
        print(f"🔌 Inserting 50+ generated records into Neon PostgreSQL at '{db_url[:35]}...'")
        import psycopg2
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # DDL Create Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                email VARCHAR(128) UNIQUE NOT NULL,
                subscription_tier VARCHAR(32) NOT NULL DEFAULT 'free',
                status VARCHAR(32) NOT NULL DEFAULT 'active',
                stripe_customer_id VARCHAR(64) UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS system_logs (
                id SERIAL PRIMARY KEY,
                trace_id VARCHAR(64) UNIQUE NOT NULL,
                level VARCHAR(16) NOT NULL,
                service VARCHAR(64) NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS stripe_charges (
                charge_id VARCHAR(64) PRIMARY KEY,
                customer_id VARCHAR(64) REFERENCES users(stripe_customer_id),
                amount INTEGER NOT NULL,
                status VARCHAR(32) NOT NULL,
                description TEXT,
                invoice_id VARCHAR(64),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Truncate clean slate
        cursor.execute("TRUNCATE TABLE stripe_charges, system_logs, users CASCADE;")

        # Batch Insert Users
        for u in users:
            cursor.execute("INSERT INTO users (id, name, email, subscription_tier, status, stripe_customer_id) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;", u)

        # Batch Insert Logs
        for l in logs:
            cursor.execute("INSERT INTO system_logs (trace_id, level, service, message) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;", l)

        # Batch Insert Stripe Charges
        for c in charges:
            cursor.execute("INSERT INTO stripe_charges (charge_id, customer_id, amount, status, description, invoice_id) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;", c)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Successfully seeded Neon PostgreSQL database with {len(users)} users, {len(logs)} logs, and {len(charges)} charges!")
    else:
        print("🔌 Inserting records into local SQLite database 'support_agent.db'...")
        import sqlite3
        conn = sqlite3.connect("support_agent.db")
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, email TEXT UNIQUE, subscription_tier TEXT, status TEXT, stripe_customer_id TEXT UNIQUE);
            CREATE TABLE IF NOT EXISTS system_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT UNIQUE, level TEXT, service TEXT, message TEXT);
            CREATE TABLE IF NOT EXISTS stripe_charges (charge_id TEXT PRIMARY KEY, customer_id TEXT, amount INTEGER, status TEXT, description TEXT, invoice_id TEXT);
            DELETE FROM stripe_charges; DELETE FROM system_logs; DELETE FROM users;
        """)

        for u in users:
            cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?, ?)", u)
        for l in logs:
            cursor.execute("INSERT OR IGNORE INTO system_logs (trace_id, level, service, message) VALUES (?, ?, ?, ?)", l)
        for c in charges:
            cursor.execute("INSERT OR IGNORE INTO stripe_charges VALUES (?, ?, ?, ?, ?, ?)", c)

        conn.commit()
        conn.close()
        print(f"✅ Successfully seeded SQLite database with {len(users)} users, {len(logs)} logs, and {len(charges)} charges!")

if __name__ == "__main__":
    generate_and_seed_data()
