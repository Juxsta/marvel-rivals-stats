#!/usr/bin/env python3
"""Apply database migration.

This script executes a specific migration SQL file against the database.
Usage: python run_migration.py <migration_file.sql>
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def run_migration(migration_file: str) -> None:
    """Execute a migration SQL file.

    Args:
        migration_file: Path to the migration SQL file.

    Raises:
        SystemExit: If migration fails.
    """
    migration_path = Path(migration_file)

    if not migration_path.exists():
        print(f"✗ Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"Running migration: {migration_path.name}")
    print("-" * 60)

    try:
        database_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(database_url)
    except psycopg2.Error as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)

    try:
        # Read migration SQL
        with open(migration_path, 'r') as f:
            sql = f.read()

        # Execute migration
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()

        print(f"✓ Migration applied: {migration_path.name}")

    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    except Exception as e:
        conn.rollback()
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        print()
        print("Example:")
        print("  python run_migration.py migrations/001_initial_schema.sql")
        sys.exit(1)

    run_migration(sys.argv[1])
