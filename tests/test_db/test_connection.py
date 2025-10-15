"""Test database connection and basic functionality.

This module tests PostgreSQL connectivity and basic database operations
to ensure the database is properly configured and accessible.
"""

import pytest
from src.db import get_connection


def test_database_connection():
    """Test that we can connect to PostgreSQL."""
    conn = get_connection()
    assert conn is not None

    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1

    conn.close()


def test_simple_query():
    """Test that we can execute a simple query."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        result = cur.fetchone()
        assert result is not None
        assert "PostgreSQL" in result[0]

    conn.close()


def test_create_drop_table():
    """Test that we can create and drop a test table."""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Create a temporary test table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_connection_table (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT
                )
            """)
            conn.commit()

            # Insert test data
            cur.execute("INSERT INTO test_connection_table (test_data) VALUES (%s)", ("test",))
            conn.commit()

            # Query test data
            cur.execute("SELECT test_data FROM test_connection_table WHERE test_data = %s", ("test",))
            result = cur.fetchone()
            assert result[0] == "test"

            # Drop the test table
            cur.execute("DROP TABLE test_connection_table")
            conn.commit()
    finally:
        conn.close()


def test_schema_version_table():
    """Test that schema migrations were applied and version table exists."""
    conn = get_connection()

    with conn.cursor() as cur:
        # Check if schema_migrations table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'schema_migrations'
            )
        """)
        result = cur.fetchone()
        assert result[0] is True, "schema_migrations table should exist after migrations"

    conn.close()
