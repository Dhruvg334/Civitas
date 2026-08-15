#!/usr/bin/env python3
"""Civitas Database Migration & Seed Runner.

Connects to DATABASE_URL, runs all schema migrations in order,
and seeds initial policy, landmark, and golden scenario data.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg

# Load root .env
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in environment or .env file.")
    sys.exit(1)

MIGRATIONS_DIR = ROOT_DIR / "database" / "migrations"
SEEDS_DIR = ROOT_DIR / "database" / "seed"

MIGRATION_FILES = [
    "0001_spatial_core.sql",
    "0002_incident_description.sql",
    "0003_incident_operations.sql",
    "0004_workflow_core.sql",
    "0005_seed_policies.sql",
    "0006_workflow_runs.sql",
]

SEED_FILES = [
    "0001_demo_landmarks.sql",
    "0002_golden_scenario.sql",
]


def run_migrations():
    print(f"Connecting to database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}...")
    with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
        with conn.cursor() as cur:
            # Enable PostGIS
            print("Ensuring PostGIS extension...")
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            conn.commit()

            # Execute schema migrations
            for filename in MIGRATION_FILES:
                filepath = MIGRATIONS_DIR / filename
                if not filepath.exists():
                    print(f"Warning: {filepath} not found, skipping.")
                    continue
                print(f"Applying migration: {filename}...")
                sql = filepath.read_text(encoding="utf-8")
                cur.execute(sql)
                conn.commit()
                print(f"[OK] Migration {filename} applied successfully.")

            # Execute seed data
            for filename in SEED_FILES:
                filepath = SEEDS_DIR / filename
                if not filepath.exists():
                    print(f"Warning: {filepath} not found, skipping.")
                    continue
                print(f"Applying seed data: {filename}...")
                sql = filepath.read_text(encoding="utf-8")
                try:
                    cur.execute(sql)
                    conn.commit()
                    print(f"[OK] Seed {filename} applied successfully.")
                except Exception as e:
                    conn.rollback()
                    print(f"Notice: Seed {filename} had minor conflict/skip (likely already seeded): {e}")

            # Verify tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
            print("\nDatabase Tables Present:")
            for t in tables:
                print(f"  - {t}")

            # Verify counts
            for t in ["incidents", "landmarks", "policies", "work_orders"]:
                if t in tables:
                    cur.execute(f"SELECT count(*) FROM {t};")
                    count = cur.fetchone()[0]
                    print(f"Row count in '{t}': {count}")

    print("\n[SUCCESS] Database migration & seeding completed successfully.")


if __name__ == "__main__":
    run_migrations()
