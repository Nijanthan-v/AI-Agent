import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    db_url = os.getenv("DATABASE_URL")
    sql_file = os.path.join(os.path.dirname(__file__), "seed_database.sql")

    with open(sql_file, "r") as f:
        sql_script = f.read()

    if db_url and (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
        print(f"🔌 Connecting to PostgreSQL Database at '{db_url[:30]}...'")
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute(sql_script)
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ PostgreSQL Database initialized and seeded successfully with real sample data!")
            return
        except Exception as e:
            print(f"⚠️ PostgreSQL Connection Error: {e}. Falling back to SQLite local database...")

    print("🔌 Initializing local SQLite database 'support_agent.db'...")
    # SQLite compatibility adjustments for DDL
    sqlite_script = sql_script.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    sqlite_script = sqlite_script.replace("NOW() - INTERVAL '2 hours'", "datetime('now', '-2 hours')")
    sqlite_script = sqlite_script.replace("NOW() - INTERVAL '4 hours'", "datetime('now', '-4 hours')")
    sqlite_script = sqlite_script.replace("NOW() - INTERVAL '1 day'", "datetime('now', '-1 day')")
    sqlite_script = sqlite_script.replace("TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP", "TEXT DEFAULT CURRENT_TIMESTAMP")
    sqlite_script = sqlite_script.replace("TRUNCATE TABLE stripe_charges, system_logs, users CASCADE;", "DELETE FROM stripe_charges; DELETE FROM system_logs; DELETE FROM users;")

    conn = sqlite3.connect("support_agent.db")
    cursor = conn.cursor()
    cursor.executescript(sqlite_script)
    conn.commit()
    conn.close()
    print("✅ Local SQLite Database 'support_agent.db' initialized and seeded successfully!")

if __name__ == "__main__":
    setup_database()
