"""Integration tests for end-to-end data workflows.

Tests the complete data flow from database initialization through seed data
insertion and verification of relationships.
"""

import os
import pytest
import psycopg2


def _get_test_connection():
    """Get a direct database connection for testing (not from pool)."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def test_database_to_seed_data_workflow():
    """Test complete workflow: Database exists -> seed data -> verify data."""
    conn = _get_test_connection()

    try:
        with conn.cursor() as cur:
            # Verify all core tables exist
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]

            expected_tables = [
                'character_stats',
                'collection_metadata',
                'match_participants',
                'matches',
                'players',
                'schema_migrations',
                'synergy_stats'
            ]

            for table in expected_tables:
                assert table in tables, f"Expected table '{table}' should exist"

            # Verify we have seed data in players table
            cur.execute("SELECT COUNT(*) FROM players WHERE username LIKE 'SpiderGamer%' OR username LIKE 'IronDefender%'")
            player_count = cur.fetchone()[0]
            assert player_count > 0, "Should have sample players from seed data"

            # Verify we have matches
            cur.execute("SELECT COUNT(*) FROM matches WHERE match_id LIKE 'match_%'")
            match_count = cur.fetchone()[0]
            assert match_count > 0, "Should have sample matches from seed data"

            # Verify we have match participants
            cur.execute("SELECT COUNT(*) FROM match_participants")
            participant_count = cur.fetchone()[0]
            assert participant_count > 0, "Should have match participants from seed data"

    finally:
        conn.close()


def test_all_tables_have_expected_data():
    """Test that all tables have been seeded with expected data."""
    conn = _get_test_connection()

    try:
        with conn.cursor() as cur:
            # Players should have rank information
            cur.execute("""
                SELECT COUNT(*) FROM players
                WHERE rank_tier IS NOT NULL AND rank_score IS NOT NULL
            """)
            ranked_players = cur.fetchone()[0]
            assert ranked_players > 0, "Should have players with rank data"

            # Matches should have season information
            cur.execute("SELECT COUNT(*) FROM matches WHERE season IS NOT NULL")
            matches_with_season = cur.fetchone()[0]
            assert matches_with_season > 0, "Should have matches with season data"

            # Match participants should have complete stats
            cur.execute("""
                SELECT COUNT(*) FROM match_participants
                WHERE hero_name IS NOT NULL
                AND role IS NOT NULL
                AND team IS NOT NULL
            """)
            complete_participants = cur.fetchone()[0]
            assert complete_participants > 0, "Should have participants with complete data"

    finally:
        conn.close()


def test_foreign_key_relationships_end_to_end():
    """Test that foreign key relationships work correctly end-to-end."""
    conn = _get_test_connection()

    try:
        with conn.cursor() as cur:
            # Verify match_participants reference valid matches
            cur.execute("""
                SELECT COUNT(*)
                FROM match_participants mp
                LEFT JOIN matches m ON mp.match_id = m.match_id
                WHERE m.match_id IS NULL
            """)
            orphaned_from_matches = cur.fetchone()[0]
            assert orphaned_from_matches == 0, "All participants should reference valid matches"

            # Verify match_participants reference valid players
            cur.execute("""
                SELECT COUNT(*)
                FROM match_participants mp
                LEFT JOIN players p ON mp.username = p.username
                WHERE p.username IS NULL
            """)
            orphaned_from_players = cur.fetchone()[0]
            assert orphaned_from_players == 0, "All participants should reference valid players"

            # Verify we can join all three tables successfully
            cur.execute("""
                SELECT COUNT(*)
                FROM match_participants mp
                INNER JOIN matches m ON mp.match_id = m.match_id
                INNER JOIN players p ON mp.username = p.username
            """)
            complete_join_count = cur.fetchone()[0]
            assert complete_join_count > 0, "Should be able to join all tables successfully"

    finally:
        conn.close()
