"""Test sample data seeding functionality.

This module tests that the seed_sample_data script correctly inserts
sample data for testing and development purposes.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.seed_sample_data import main as seed_main  # noqa: E402
from src.db import get_connection  # noqa: E402


def test_seed_script_creates_records():
    """Test that seed script inserts expected number of records."""
    # Run the seed script to ensure data exists (uses ON CONFLICT DO NOTHING)
    seed_main()

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Check players
            cur.execute("SELECT COUNT(*) FROM players")
            player_count = cur.fetchone()[0]
            assert player_count >= 5, "Should have at least 5 sample players"

            # Check matches
            cur.execute("SELECT COUNT(*) FROM matches")
            match_count = cur.fetchone()[0]
            assert match_count >= 3, "Should have at least 3 sample matches"

            # Check match participants
            cur.execute("SELECT COUNT(*) FROM match_participants")
            participant_count = cur.fetchone()[0]
            assert participant_count >= 15, "Should have at least 15 match participants"
    finally:
        conn.close()


def test_seed_data_foreign_keys_valid():
    """Test that seeded data maintains valid foreign key relationships."""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Check that all match_participants reference valid matches
            cur.execute(
                """
                SELECT COUNT(*)
                FROM match_participants mp
                WHERE NOT EXISTS (
                    SELECT 1 FROM matches m WHERE m.match_id = mp.match_id
                )
            """
            )
            invalid_matches = cur.fetchone()[0]
            assert invalid_matches == 0, "All match participants should reference valid matches"

            # Check that all match_participants reference valid players
            cur.execute(
                """
                SELECT COUNT(*)
                FROM match_participants mp
                WHERE NOT EXISTS (
                    SELECT 1 FROM players p WHERE p.username = mp.username
                )
            """
            )
            invalid_players = cur.fetchone()[0]
            assert invalid_players == 0, "All match participants should reference valid players"
    finally:
        conn.close()


def test_seed_data_has_realistic_values():
    """Test that seeded data contains realistic Marvel Rivals data."""
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Check that heroes have valid roles
            cur.execute(
                """
                SELECT COUNT(*)
                FROM match_participants
                WHERE role NOT IN ('vanguard', 'duelist', 'strategist')
            """
            )
            invalid_roles = cur.fetchone()[0]
            assert invalid_roles == 0, "All heroes should have valid roles"

            # Check that teams are 0 or 1
            cur.execute(
                """
                SELECT COUNT(*)
                FROM match_participants
                WHERE team NOT IN (0, 1)
            """
            )
            invalid_teams = cur.fetchone()[0]
            assert invalid_teams == 0, "All participants should be on team 0 or 1"

            # Check that players have rank tiers
            cur.execute(
                """
                SELECT COUNT(*)
                FROM players
                WHERE rank_tier IS NOT NULL
            """
            )
            players_with_rank = cur.fetchone()[0]
            assert players_with_rank > 0, "Sample players should have rank tiers"
    finally:
        conn.close()
