"""Integration tests for end-to-end data workflows.

Tests the complete data flow from database initialization through seed data
insertion and verification of relationships.
"""

import os
from datetime import datetime, timedelta

import psycopg2
import pytest


def _get_test_connection():
    """Get a direct database connection for testing (not from pool)."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


@pytest.fixture
def seed_test_data():
    """Seed database with test data for workflow tests."""
    conn = _get_test_connection()

    try:
        with conn.cursor() as cur:
            # Clean any existing workflow test data first
            cur.execute("DELETE FROM match_participants WHERE match_id LIKE 'match_%'")
            cur.execute("DELETE FROM matches WHERE match_id LIKE 'match_%'")
            cur.execute(
                """
                DELETE FROM players
                WHERE username IN ('SpiderGamer2024', 'IronDefender', 'StrangeSupport', 'ThorMain', 'BlackWidowSniper')
            """
            )

            # Insert sample players
            players = [
                ("SpiderGamer2024", "Diamond", 4850),
                ("IronDefender", "Platinum", 4200),
                ("StrangeSupport", "Gold", 3700),
                ("ThorMain", "Diamond", 4920),
                ("BlackWidowSniper", "Platinum", 4350),
            ]

            for username, rank_tier, rank_score in players:
                cur.execute(
                    """
                    INSERT INTO players (username, rank_tier, rank_score, discovered_at, match_history_fetched)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (username, rank_tier, rank_score, datetime.now(), False),
                )

            # Insert sample matches
            base_time = datetime.now() - timedelta(days=1)
            matches = [
                ("match_001", "competitive", 9, base_time),
                ("match_002", "competitive", 9, base_time + timedelta(hours=1)),
                ("match_003", "competitive", 9, base_time + timedelta(hours=2)),
            ]

            for match_id, mode, season, match_timestamp in matches:
                cur.execute(
                    """
                    INSERT INTO matches (match_id, mode, season, match_timestamp)
                    VALUES (%s, %s, %s, %s)
                """,
                    (match_id, mode, season, match_timestamp),
                )

            # Insert sample match participants
            participants = [
                # Match 1 - Team 0 wins
                (
                    "match_001",
                    "SpiderGamer2024",
                    1001,
                    "Spider-Man",
                    "duelist",
                    0,
                    True,
                    15,
                    3,
                    8,
                    25000.00,
                    0,
                ),
                (
                    "match_001",
                    "StrangeSupport",
                    1015,
                    "Doctor Strange",
                    "strategist",
                    0,
                    True,
                    2,
                    1,
                    18,
                    8000.00,
                    32000.00,
                ),
                (
                    "match_001",
                    "IronDefender",
                    1009,
                    "Iron Man",
                    "duelist",
                    0,
                    True,
                    12,
                    4,
                    10,
                    28000.00,
                    0,
                ),
                (
                    "match_001",
                    "ThorMain",
                    1020,
                    "Thor",
                    "vanguard",
                    1,
                    False,
                    10,
                    8,
                    5,
                    18000.00,
                    0,
                ),
                (
                    "match_001",
                    "BlackWidowSniper",
                    1003,
                    "Black Widow",
                    "duelist",
                    1,
                    False,
                    14,
                    7,
                    4,
                    22000.00,
                    0,
                ),
                # Match 2 - Team 1 wins
                (
                    "match_002",
                    "SpiderGamer2024",
                    1001,
                    "Spider-Man",
                    "duelist",
                    0,
                    False,
                    11,
                    6,
                    7,
                    20000.00,
                    0,
                ),
                (
                    "match_002",
                    "IronDefender",
                    1004,
                    "Captain America",
                    "vanguard",
                    0,
                    False,
                    8,
                    5,
                    9,
                    15000.00,
                    0,
                ),
                ("match_002", "ThorMain", 1020, "Thor", "vanguard", 1, True, 12, 3, 8, 24000.00, 0),
                (
                    "match_002",
                    "BlackWidowSniper",
                    1003,
                    "Black Widow",
                    "duelist",
                    1,
                    True,
                    18,
                    4,
                    6,
                    30000.00,
                    0,
                ),
                (
                    "match_002",
                    "StrangeSupport",
                    1015,
                    "Doctor Strange",
                    "strategist",
                    1,
                    True,
                    3,
                    2,
                    15,
                    9000.00,
                    28000.00,
                ),
                # Match 3 - Team 0 wins
                ("match_003", "ThorMain", 1020, "Thor", "vanguard", 0, True, 9, 2, 12, 18000.00, 0),
                (
                    "match_003",
                    "BlackWidowSniper",
                    1007,
                    "Hawkeye",
                    "duelist",
                    0,
                    True,
                    16,
                    3,
                    8,
                    27000.00,
                    0,
                ),
                (
                    "match_003",
                    "StrangeSupport",
                    1026,
                    "Luna Snow",
                    "strategist",
                    0,
                    True,
                    1,
                    1,
                    20,
                    5000.00,
                    35000.00,
                ),
                (
                    "match_003",
                    "SpiderGamer2024",
                    1010,
                    "Star-Lord",
                    "duelist",
                    1,
                    False,
                    13,
                    7,
                    5,
                    23000.00,
                    0,
                ),
                (
                    "match_003",
                    "IronDefender",
                    1004,
                    "Captain America",
                    "vanguard",
                    1,
                    False,
                    7,
                    6,
                    8,
                    14000.00,
                    0,
                ),
            ]

            for participant_data in participants:
                cur.execute(
                    """
                    INSERT INTO match_participants
                    (match_id, username, hero_id, hero_name, role, team, won, kills, deaths, assists, damage, healing)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    participant_data,
                )

            conn.commit()

        yield conn

        # Cleanup after test
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM match_participants WHERE match_id LIKE 'match_%'")
                cur.execute("DELETE FROM matches WHERE match_id LIKE 'match_%'")
                cur.execute(
                    """
                    DELETE FROM players
                    WHERE username IN ('SpiderGamer2024', 'IronDefender', 'StrangeSupport', 'ThorMain', 'BlackWidowSniper')
                """
                )
            conn.commit()
        except:
            pass

    finally:
        conn.close()


def test_database_to_seed_data_workflow(seed_test_data):
    """Test complete workflow: Database exists -> seed data -> verify data."""
    conn = seed_test_data

    with conn.cursor() as cur:
        # Verify all core tables exist
        cur.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        )
        tables = [row[0] for row in cur.fetchall()]

        expected_tables = [
            "character_stats",
            "collection_metadata",
            "match_participants",
            "matches",
            "players",
            "schema_migrations",
            "synergy_stats",
        ]

        for table in expected_tables:
            assert table in tables, f"Expected table '{table}' should exist"

        # Verify we have seed data in players table
        cur.execute(
            "SELECT COUNT(*) FROM players WHERE username LIKE 'SpiderGamer%' OR username LIKE 'IronDefender%'"
        )
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


def test_all_tables_have_expected_data(seed_test_data):
    """Test that all tables have been seeded with expected data."""
    conn = seed_test_data

    with conn.cursor() as cur:
        # Players should have rank information
        cur.execute(
            """
            SELECT COUNT(*) FROM players
            WHERE rank_tier IS NOT NULL AND rank_score IS NOT NULL
        """
        )
        ranked_players = cur.fetchone()[0]
        assert ranked_players > 0, "Should have players with rank data"

        # Matches should have season information
        cur.execute("SELECT COUNT(*) FROM matches WHERE season IS NOT NULL")
        matches_with_season = cur.fetchone()[0]
        assert matches_with_season > 0, "Should have matches with season data"

        # Match participants should have complete stats
        cur.execute(
            """
            SELECT COUNT(*) FROM match_participants
            WHERE hero_name IS NOT NULL
            AND role IS NOT NULL
            AND team IS NOT NULL
        """
        )
        complete_participants = cur.fetchone()[0]
        assert complete_participants > 0, "Should have participants with complete data"


def test_foreign_key_relationships_end_to_end(seed_test_data):
    """Test that foreign key relationships work correctly end-to-end."""
    conn = seed_test_data

    with conn.cursor() as cur:
        # Verify match_participants reference valid matches
        cur.execute(
            """
            SELECT COUNT(*)
            FROM match_participants mp
            LEFT JOIN matches m ON mp.match_id = m.match_id
            WHERE m.match_id IS NULL
        """
        )
        orphaned_from_matches = cur.fetchone()[0]
        assert orphaned_from_matches == 0, "All participants should reference valid matches"

        # Verify match_participants reference valid players
        cur.execute(
            """
            SELECT COUNT(*)
            FROM match_participants mp
            LEFT JOIN players p ON mp.username = p.username
            WHERE p.username IS NULL
        """
        )
        orphaned_from_players = cur.fetchone()[0]
        assert orphaned_from_players == 0, "All participants should reference valid players"

        # Verify we can join all three tables successfully
        cur.execute(
            """
            SELECT COUNT(*)
            FROM match_participants mp
            INNER JOIN matches m ON mp.match_id = m.match_id
            INNER JOIN players p ON mp.username = p.username
        """
        )
        complete_join_count = cur.fetchone()[0]
        assert complete_join_count > 0, "Should be able to join all tables successfully"
