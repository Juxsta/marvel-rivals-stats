#!/usr/bin/env python3
"""Initialize database and verify schema.

This script connects to the PostgreSQL database, checks if the schema exists,
runs migrations if needed, and verifies all tables are created properly.
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_connection():
    """Test database connectivity."""
    try:
        database_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        conn.close()
        print("✓ Database connection successful")
        return True
    except psycopg2.Error as e:
        print(f"✗ Database connection failed: {e}")
        return False


def run_migration_file(conn, migration_path):
    """Execute a migration SQL file."""
    try:
        with open(migration_path, "r") as f:
            sql = f.read()

        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()

        print(f"✓ Applied migration: {migration_path.name}")
        return True
    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Migration failed ({migration_path.name}): {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Migration file not found: {migration_path}")
        return False


def get_schema_version(conn):
    """Get current schema version from database."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(version) FROM schema_migrations")
            result = cur.fetchone()
            return result[0] if result and result[0] else 0
    except psycopg2.Error:
        # Table doesn't exist yet
        return 0


def verify_tables(conn):
    """Verify all expected tables exist."""
    expected_tables = [
        "schema_migrations",
        "players",
        "matches",
        "match_participants",
        "character_stats",
        "synergy_stats",
        "collection_metadata",
    ]

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            )
            existing_tables = [row[0] for row in cur.fetchall()]

        all_exist = all(table in existing_tables for table in expected_tables)

        if all_exist:
            print(f"✓ All {len(expected_tables)} tables verified:")
            for table in expected_tables:
                print(f"  - {table}")
        else:
            print("✗ Missing tables:")
            for table in expected_tables:
                if table not in existing_tables:
                    print(f"  - {table}")

        return all_exist
    except psycopg2.Error as e:
        print(f"✗ Table verification failed: {e}")
        return False


def main():
    """Main initialization function."""
    print("=" * 60)
    print("Marvel Rivals Stats Database Initialization")
    print("=" * 60)
    print()

    # Check connection
    if not check_connection():
        sys.exit(1)

    # Connect to database
    try:
        database_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(database_url)
    except psycopg2.Error as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)

    try:
        # Check current schema version
        current_version = get_schema_version(conn)
        print(f"Current schema version: {current_version}")
        print()

        # Find migration files
        migrations_dir = Path(__file__).parent.parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))

        if not migration_files:
            print("⚠ No migration files found")
        else:
            print(f"Found {len(migration_files)} migration files")
            print()

            # Run migrations if needed
            for migration_file in migration_files:
                # Extract version number from filename (e.g., 001_initial_schema.sql -> 1)
                try:
                    file_version = int(migration_file.stem.split("_")[0])
                except (ValueError, IndexError):
                    print(f"⚠ Skipping migration with invalid filename: {migration_file.name}")
                    continue

                if file_version > current_version:
                    print(f"Running migration {file_version}: {migration_file.name}")
                    if not run_migration_file(conn, migration_file):
                        print("Migration failed, aborting")
                        sys.exit(1)
                else:
                    print(f"⊗ Skipping already applied migration: {migration_file.name}")

        print()
        print("-" * 60)
        print("Verifying database schema...")
        print("-" * 60)

        # Verify tables
        if verify_tables(conn):
            # Get final schema version
            final_version = get_schema_version(conn)
            print()
            print(f"✓ Database initialized successfully! (Version {final_version})")
            print()
        else:
            print()
            print("✗ Database initialization incomplete")
            sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
