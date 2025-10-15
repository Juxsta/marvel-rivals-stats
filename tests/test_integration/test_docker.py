"""Integration tests for Docker service health and configuration.

Tests that verify Docker services are properly configured, healthy,
and can communicate with each other.
"""

import os
import pytest
import subprocess


def test_postgres_reachable_from_app():
    """Test that PostgreSQL is reachable from the app container."""
    from src.db import get_connection

    # If we can get a connection, PostgreSQL is reachable
    conn = get_connection()
    assert conn is not None, "Should be able to connect to PostgreSQL from app container"

    with conn.cursor() as cur:
        # Execute a simple query to verify database is functional
        cur.execute("SELECT current_database()")
        db_name = cur.fetchone()[0]
        assert db_name == os.getenv("DATABASE_NAME", "marvel_rivals")

    conn.close()


def test_psql_commands_executable():
    """Test that we can execute psql commands in the PostgreSQL container."""
    # This test runs from inside the app container, so we verify the connection works
    # by running a query through our connection module
    from src.db import get_connection

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Test that we can list tables (equivalent to \dt in psql)
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            table_count = cur.fetchone()[0]
            assert table_count >= 7, "Should have at least 7 tables in public schema"

            # Test that we can get database version (equivalent to SELECT version())
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            assert "PostgreSQL" in version, "Should be able to query PostgreSQL version"

    finally:
        conn.close()


def test_environment_variables_loaded():
    """Test that environment variables are loaded correctly in the container."""
    # Verify critical database environment variables
    assert os.getenv("DATABASE_HOST") is not None, "DATABASE_HOST should be set"
    assert os.getenv("DATABASE_NAME") is not None, "DATABASE_NAME should be set"
    assert os.getenv("DATABASE_USER") is not None, "DATABASE_USER should be set"
    assert os.getenv("DATABASE_PASSWORD") is not None, "DATABASE_PASSWORD should be set"

    # Verify application environment variables
    assert os.getenv("APP_ENV") is not None, "APP_ENV should be set"
    assert os.getenv("CURRENT_SEASON") is not None, "CURRENT_SEASON should be set"

    # Verify Python environment variables
    assert os.getenv("PYTHONUNBUFFERED") == "1", "PYTHONUNBUFFERED should be set to 1"
    assert os.getenv("PYTHONDONTWRITEBYTECODE") == "1", "PYTHONDONTWRITEBYTECODE should be set to 1"
