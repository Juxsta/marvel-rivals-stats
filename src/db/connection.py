"""PostgreSQL database connection management.

This module provides connection pooling and connection management utilities
for interacting with the PostgreSQL database.
"""

import logging
import os
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2 import pool
from psycopg2.extensions import connection as PgConnection

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[pool.SimpleConnectionPool] = None


def get_connection_pool() -> pool.SimpleConnectionPool:
    """Get or create the PostgreSQL connection pool.

    Returns:
        SimpleConnectionPool: The connection pool instance.

    Raises:
        psycopg2.Error: If connection pool creation fails.
    """
    global _connection_pool

    if _connection_pool is None:
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                # Use DATABASE_URL if available (complete connection string)
                _connection_pool = pool.SimpleConnectionPool(
                    minconn=1, maxconn=10, dsn=database_url
                )
                logger.info("Database connection pool created using DATABASE_URL")
            else:
                # Build connection from individual parameters
                _connection_pool = pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=os.getenv("DATABASE_HOST", "postgres"),
                    port=os.getenv("DATABASE_PORT", "5432"),
                    database=os.getenv("DATABASE_NAME", "marvel_rivals"),
                    user=os.getenv("DATABASE_USER", "marvel_stats"),
                    password=os.getenv("DATABASE_PASSWORD"),
                )
                logger.info("Database connection pool created using individual parameters")
        except psycopg2.Error as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise

    return _connection_pool


def get_connection() -> PgConnection:
    """Get a database connection from the pool.

    Returns:
        PgConnection: A PostgreSQL connection object.

    Raises:
        psycopg2.Error: If connection cannot be obtained.
    """
    try:
        conn_pool = get_connection_pool()
        conn = conn_pool.getconn()
        logger.debug("Database connection obtained from pool")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to get database connection: {e}")
        raise


def close_pool() -> None:
    """Close all connections in the pool.

    This should be called when shutting down the application.
    """
    global _connection_pool

    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Database connection pool closed")
