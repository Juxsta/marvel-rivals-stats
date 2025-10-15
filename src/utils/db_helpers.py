"""Database query helper functions.

This module provides wrapper functions for common database operations,
including SELECT queries, INSERT operations, and batch inserts with
proper error handling and logging.
"""

import logging
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extensions import connection as PgConnection

logger = logging.getLogger(__name__)


def execute_query(
    conn: PgConnection, query: str, params: Optional[tuple] = None
) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return results as list of dictionaries.

    This is a wrapper for SELECT queries that returns results in a more
    convenient dictionary format with column names as keys.

    Args:
        conn: Database connection
        query: SQL SELECT query string
        params: Query parameters tuple (optional)

    Returns:
        List of dictionaries, where each dict represents a row with
        column names as keys

    Raises:
        psycopg2.Error: If query execution fails

    Example:
        >>> results = execute_query(conn, "SELECT * FROM players WHERE rank_tier = %s", ("Gold",))
        >>> print(results[0]['username'])
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())

            # Get column names from cursor description
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # Convert to list of dicts
                return [dict(zip(columns, row)) for row in rows]
            else:
                return []

    except psycopg2.Error as e:
        logger.error(f"Query execution failed: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def execute_insert(conn: PgConnection, query: str, params: tuple) -> int:
    """Execute a single INSERT query and return affected row count.

    This is a wrapper for single INSERT operations. For batch inserts,
    use execute_batch_insert() instead.

    Args:
        conn: Database connection
        query: SQL INSERT query string
        params: Query parameters tuple

    Returns:
        Number of rows affected (typically 1 for successful insert)

    Raises:
        psycopg2.Error: If insert execution fails

    Example:
        >>> rows = execute_insert(
        ...     conn,
        ...     "INSERT INTO players (username, rank_tier) VALUES (%s, %s)",
        ...     ("player123", "Gold")
        ... )
        >>> print(f"Inserted {rows} row(s)")
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            affected_rows = cursor.rowcount

            logger.debug(f"Insert executed: {affected_rows} row(s) affected")
            return affected_rows

    except psycopg2.Error as e:
        logger.error(f"Insert execution failed: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def execute_batch_insert(conn: PgConnection, query: str, params_list: List[tuple]) -> int:
    """Execute batch INSERT using executemany for better performance.

    This is more efficient than executing multiple individual INSERTs
    when inserting many rows at once.

    Args:
        conn: Database connection
        query: SQL INSERT query string with placeholders
        params_list: List of parameter tuples, one per row to insert

    Returns:
        Total number of rows affected

    Raises:
        psycopg2.Error: If batch insert execution fails

    Example:
        >>> params = [
        ...     ("player1", "Gold"),
        ...     ("player2", "Silver"),
        ...     ("player3", "Platinum")
        ... ]
        >>> rows = execute_batch_insert(
        ...     conn,
        ...     "INSERT INTO players (username, rank_tier) VALUES (%s, %s)",
        ...     params
        ... )
        >>> print(f"Inserted {rows} row(s)")
    """
    if not params_list:
        logger.warning("execute_batch_insert called with empty params_list")
        return 0

    try:
        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)
            affected_rows = cursor.rowcount

            logger.debug(
                f"Batch insert executed: {affected_rows} row(s) affected "
                f"from {len(params_list)} parameter set(s)"
            )
            return affected_rows

    except psycopg2.Error as e:
        logger.error(f"Batch insert execution failed: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Number of parameter sets: {len(params_list)}")
        logger.error(f"First parameter set: {params_list[0] if params_list else 'N/A'}")
        raise
