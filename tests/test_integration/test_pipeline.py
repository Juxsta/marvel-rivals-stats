"""Integration tests for the character analysis pipeline.

Tests end-to-end workflows focusing on critical paths:
- Pipeline deduplication and database integrity
- Error handling and recovery
- Statistical calculations
- Data export validation

Uses mocked API responses and minimal test data for fast, reliable execution.
Maximum 10 tests focusing ONLY on critical workflows.
"""

import json
import os
from unittest.mock import MagicMock

import psycopg2
import pytest

from src.analyzers.character_winrate import analyze_character_win_rates
from src.collectors.match_collector import collect_matches


def _get_test_connection():
    """Get a direct database connection for testing."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


@pytest.fixture
def clean_test_data():
    """Clean test data before and after each test with proper rollback handling."""
    conn = _get_test_connection()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # Clean tables in correct order (respecting foreign keys)
            # Clean character stats
            cur.execute(
                """
                DELETE FROM character_stats
                WHERE hero_name LIKE 'Spider%' OR hero_name LIKE 'Iron%'
                   OR hero_name LIKE 'Black%' OR hero_name = 'Rare Hero'
            """
            )
            # Clean synergy stats
            cur.execute(
                """
                DELETE FROM synergy_stats
                WHERE hero_a LIKE 'Spider%' OR hero_a LIKE 'Iron%'
            """
            )
            # Clean match participants with all test patterns
            cur.execute(
                """
                DELETE FROM match_participants
                WHERE match_id LIKE '%test%'
                   OR match_id LIKE 'match_%'
                   OR match_id LIKE 'ci_%'
                   OR match_id LIKE 'filter_%'
                   OR match_id LIKE 'export_%'
                   OR match_id LIKE 'shared_%'
                   OR match_id LIKE 'fk_%'
            """
            )
            # Clean matches with all test patterns
            cur.execute(
                """
                DELETE FROM matches
                WHERE match_id LIKE '%test%'
                   OR match_id LIKE 'match_%'
                   OR match_id LIKE 'ci_%'
                   OR match_id LIKE 'filter_%'
                   OR match_id LIKE 'export_%'
                   OR match_id LIKE 'shared_%'
                   OR match_id LIKE 'fk_%'
            """
            )
            # Clean players with all test patterns
            cur.execute(
                """
                DELETE FROM players
                WHERE username LIKE '%test%'
                   OR username LIKE '%player%'
                   OR username LIKE 'teammate%'
                   OR username LIKE 'opponent%'
                   OR username LIKE 'ci_%'
                   OR username LIKE 'filter_%'
                   OR username LIKE 'export_%'
                   OR username LIKE 'resume_%'
                   OR username LIKE 'rate_%'
                   OR username LIKE 'fk_%'
            """
            )
        conn.commit()

        yield conn

        # Cleanup after test with error handling
        try:
            conn.rollback()  # Rollback any pending transaction
            with conn.cursor() as cur:
                # Clean character stats
                cur.execute(
                    """
                    DELETE FROM character_stats
                    WHERE hero_name LIKE 'Spider%' OR hero_name LIKE 'Iron%'
                       OR hero_name LIKE 'Black%' OR hero_name = 'Rare Hero'
                """
                )
                # Clean synergy stats
                cur.execute(
                    """
                    DELETE FROM synergy_stats
                    WHERE hero_a LIKE 'Spider%' OR hero_a LIKE 'Iron%'
                """
                )
                # Clean match participants with all test patterns
                cur.execute(
                    """
                    DELETE FROM match_participants
                    WHERE match_id LIKE '%test%'
                       OR match_id LIKE 'match_%'
                       OR match_id LIKE 'ci_%'
                       OR match_id LIKE 'filter_%'
                       OR match_id LIKE 'export_%'
                       OR match_id LIKE 'shared_%'
                       OR match_id LIKE 'fk_%'
                """
                )
                # Clean matches with all test patterns
                cur.execute(
                    """
                    DELETE FROM matches
                    WHERE match_id LIKE '%test%'
                       OR match_id LIKE 'match_%'
                       OR match_id LIKE 'ci_%'
                       OR match_id LIKE 'filter_%'
                       OR match_id LIKE 'export_%'
                       OR match_id LIKE 'shared_%'
                       OR match_id LIKE 'fk_%'
                """
                )
                # Clean players with all test patterns
                cur.execute(
                    """
                    DELETE FROM players
                    WHERE username LIKE '%test%'
                       OR username LIKE '%player%'
                       OR username LIKE 'teammate%'
                       OR username LIKE 'opponent%'
                       OR username LIKE 'ci_%'
                       OR username LIKE 'filter_%'
                       OR username LIKE 'export_%'
                       OR username LIKE 'resume_%'
                       OR username LIKE 'rate_%'
                       OR username LIKE 'fk_%'
                """
                )
            conn.commit()
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def test_match_deduplication_across_players(clean_test_data):
    """Test that same match appearing in multiple players' histories is only stored once.

    CRITICAL: Validates deduplication - core requirement for data integrity.
    """
    conn = clean_test_data
    mock_api = MagicMock()

    # Create overlapping match data with single player
    shared_match = {
        "match_id": "shared_match_123",
        "mode": "competitive",
        "season": 1,
        "timestamp": "2025-10-15T10:00:00Z",
        "teams": [
            {
                "team": 0,
                "won": True,
                "players": [
                    {
                        "username": "player_a",
                        "hero_id": 101,
                        "hero_name": "Spider-Man",
                        "role": "duelist",
                        "kills": 15,
                        "deaths": 8,
                        "assists": 12,
                        "damage": 25000,
                        "healing": 0,
                    },
                ],
            },
            {
                "team": 1,
                "won": False,
                "players": [
                    {
                        "username": "player_b",
                        "hero_id": 102,
                        "hero_name": "Iron Man",
                        "role": "duelist",
                        "kills": 14,
                        "deaths": 10,
                        "assists": 9,
                        "damage": 24000,
                        "healing": 0,
                    },
                ],
            },
        ],
    }

    mock_api.get_player_matches.return_value = [shared_match]

    # Insert players first
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO players (username, rank_tier, rank_score) VALUES (%s, %s, %s)",
            [("player_a", "Gold", 1500), ("player_b", "Gold", 1500)],
        )
        conn.commit()

    # Collect matches for first player
    stats1 = collect_matches(mock_api, conn, batch_size=1, rate_limit_delay=0.1)
    assert stats1["matches_collected"] == 1, "First collection should insert match"

    # Collect matches for second player (same match)
    with conn.cursor() as cur:
        cur.execute("UPDATE players SET match_history_fetched = FALSE WHERE username = 'player_b'")
        conn.commit()

    stats2 = collect_matches(mock_api, conn, batch_size=1, rate_limit_delay=0.1)
    assert stats2["matches_skipped"] == 1, "Second collection should skip duplicate match"
    assert stats2["matches_collected"] == 0, "Second collection should not insert duplicate"

    # Verify only one match in database
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM matches WHERE match_id = 'shared_match_123'")
        count = cur.fetchone()[0]
        assert count == 1, "Should have exactly 1 match in database (deduplicated)"


def test_database_foreign_key_integrity(clean_test_data):
    """Test that foreign key relationships are maintained correctly.

    CRITICAL: Validates referential integrity - prevents orphaned records.
    """
    conn = clean_test_data

    # Insert a player
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO players (username, rank_tier, rank_score) VALUES (%s, %s, %s)",
            ("fk_test_player", "Gold", 1500),
        )
        conn.commit()

    # Insert a match
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO matches (match_id, mode, season, match_timestamp) VALUES (%s, %s, %s, %s)",
            ("fk_test_match", "competitive", 1, "2025-10-15T10:00:00Z"),
        )
        conn.commit()

    # Insert participant linking player to match
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO match_participants
               (match_id, username, hero_id, hero_name, role, team, won)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            ("fk_test_match", "fk_test_player", 101, "Spider-Man", "duelist", 0, True),
        )
        conn.commit()

    # Verify relationships exist
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM match_participants mp
            INNER JOIN matches m ON mp.match_id = m.match_id
            INNER JOIN players p ON mp.username = p.username
            WHERE mp.match_id = 'fk_test_match'
        """
        )
        count = cur.fetchone()[0]
        assert count == 1, "Foreign key relationships should allow join"


def test_resumable_collection_after_interruption(clean_test_data):
    """Test that collection can resume after interruption without data loss.

    CRITICAL: Validates resumability - ensures data pipeline can recover from failures.
    """
    conn = clean_test_data
    mock_api = MagicMock()
    mock_api.get_player_matches.return_value = []  # Empty matches for simplicity

    # Insert 3 players
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO players (username, rank_tier, rank_score, match_history_fetched) "
            "VALUES (%s, %s, %s, %s)",
            [
                ("resume_player1", "Gold", 1500, False),
                ("resume_player2", "Gold", 1500, False),
                ("resume_player3", "Gold", 1500, False),
            ],
        )
        conn.commit()

    # First collection: Process only 1 player (simulate interruption)
    stats1 = collect_matches(mock_api, conn, batch_size=1, rate_limit_delay=0.1)
    assert stats1["players_processed"] == 1, "First run should process 1 player"

    # Verify first player marked as collected
    with conn.cursor() as cur:
        cur.execute("SELECT match_history_fetched FROM players WHERE username = 'resume_player1'")
        fetched = cur.fetchone()[0]
        assert fetched is True, "First player should be marked as collected"

    # Second collection: Resume and process remaining 2 players
    stats2 = collect_matches(mock_api, conn, batch_size=10, rate_limit_delay=0.1)
    assert stats2["players_processed"] == 2, "Second run should process remaining 2 players"

    # Verify all players now collected
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM players "
            "WHERE username LIKE 'resume_player%' AND match_history_fetched = TRUE"
        )
        count = cur.fetchone()[0]
        assert count == 3, "All 3 players should be marked as collected"


def test_confidence_interval_calculations_end_to_end(clean_test_data):
    """Test that confidence intervals are calculated correctly through the entire pipeline.

    CRITICAL: Validates statistical correctness - ensures Wilson CI is applied properly.
    """
    conn = clean_test_data

    # Insert test data: Spider-Man with known win rate (60/100 = 0.6)
    with conn.cursor() as cur:
        # Insert 100 test players
        cur.executemany(
            "INSERT INTO players (username, rank_tier, rank_score) VALUES (%s, %s, %s)",
            [(f"ci_player_{i}", "Gold", 1500) for i in range(100)],
        )

        # Insert 100 matches
        for i in range(100):
            cur.execute(
                "INSERT INTO matches (match_id, mode, season, match_timestamp) "
                "VALUES (%s, %s, %s, %s)",
                (f"ci_match_{i}", "competitive", 1, "2025-10-15T10:00:00Z"),
            )

        # Insert participants: Spider-Man wins 60 times, loses 40 times
        participant_data = []
        for i in range(100):
            won = i < 60  # First 60 matches are wins
            participant_data.append(
                (f"ci_match_{i}", f"ci_player_{i}", 101, "Spider-Man", "duelist", 0, won)
            )

        cur.executemany(
            """INSERT INTO match_participants
               (match_id, username, hero_id, hero_name, role, team, won)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            participant_data,
        )
        conn.commit()

    # Run character analysis
    results = analyze_character_win_rates(conn, min_games_per_rank=30, min_games_overall=100)

    assert "Spider-Man" in results, "Spider-Man should be in results"

    spiderman_stats = results["Spider-Man"]["overall"]
    assert spiderman_stats["total_games"] == 100
    assert spiderman_stats["wins"] == 60
    assert spiderman_stats["win_rate"] == 0.6

    # Verify confidence interval exists and is reasonable
    ci = spiderman_stats["confidence_interval_95"]
    assert len(ci) == 2, "Should have lower and upper bounds"
    assert ci[0] < 0.6 < ci[1], "Win rate should be within confidence interval"
    assert ci[1] - ci[0] < 0.2, "Confidence interval should be reasonably narrow for 100 games"
    # Verify they are Python floats, not numpy floats
    assert isinstance(ci[0], float) and not str(type(ci[0])).__contains__(
        "numpy"
    ), "CI lower should be Python float"
    assert isinstance(ci[1], float) and not str(type(ci[1])).__contains__(
        "numpy"
    ), "CI upper should be Python float"


def test_minimum_sample_size_filtering(clean_test_data):
    """Test that results with insufficient sample sizes are filtered correctly.

    CRITICAL: Validates minimum sample size enforcement - prevents unreliable statistics.
    """
    conn = clean_test_data

    # Insert hero with only 5 games (below min_games_overall=100 threshold)
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO players (username, rank_tier, rank_score) VALUES (%s, %s, %s)",
            [(f"filter_player_{i}", "Gold", 1500) for i in range(5)],
        )

        for i in range(5):
            cur.execute(
                "INSERT INTO matches (match_id, mode, season, match_timestamp) "
                "VALUES (%s, %s, %s, %s)",
                (f"filter_match_{i}", "competitive", 1, "2025-10-15T10:00:00Z"),
            )

        cur.executemany(
            """INSERT INTO match_participants
               (match_id, username, hero_id, hero_name, role, team, won)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            [
                (f"filter_match_{i}", f"filter_player_{i}", 120, "Rare Hero", "duelist", 0, True)
                for i in range(5)
            ],
        )
        conn.commit()

    # Run analysis with default thresholds
    results = analyze_character_win_rates(conn, min_games_per_rank=30, min_games_overall=100)

    # Rare Hero should NOT be in results (only 5 games < 100 minimum)
    assert "Rare Hero" not in results, "Hero with < 100 games should be filtered out"

    # Run analysis with lower threshold
    results_low = analyze_character_win_rates(conn, min_games_per_rank=1, min_games_overall=5)

    # Rare Hero SHOULD be in results now
    assert (
        "Rare Hero" in results_low
    ), "Hero with >= 5 games should be included with lower threshold"


def test_json_export_format_validity(clean_test_data):
    """Test that JSON exports are valid and contain expected structure.

    CRITICAL: Validates export format - ensures downstream consumers can parse results.
    """
    conn = clean_test_data

    # Insert minimal test data
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO players (username, rank_tier, rank_score) VALUES (%s, %s, %s)",
            [(f"export_player_{i}", "Gold", 1500) for i in range(10)],
        )

        for i in range(10):
            cur.execute(
                "INSERT INTO matches (match_id, mode, season, match_timestamp) "
                "VALUES (%s, %s, %s, %s)",
                (f"export_match_{i}", "competitive", 1, "2025-10-15T10:00:00Z"),
            )

        cur.executemany(
            """INSERT INTO match_participants
               (match_id, username, hero_id, hero_name, role, team, won)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            [
                (f"export_match_{i}", f"export_player_{i}", 101, "Spider-Man", "duelist", 0, i < 6)
                for i in range(10)
            ],
        )
        conn.commit()

    # Run analysis
    results = analyze_character_win_rates(conn, min_games_per_rank=1, min_games_overall=5)

    # Verify JSON structure
    assert "Spider-Man" in results, "Should have Spider-Man in results"

    hero_data = results["Spider-Man"]

    # Check required fields exist
    assert "hero" in hero_data, "Should have 'hero' field"
    assert "overall" in hero_data, "Should have 'overall' field"
    assert "by_rank" in hero_data, "Should have 'by_rank' field"
    assert "analyzed_at" in hero_data, "Should have 'analyzed_at' field"

    overall = hero_data["overall"]
    assert "total_games" in overall, "Should have 'total_games'"
    assert "wins" in overall, "Should have 'wins'"
    assert "losses" in overall, "Should have 'losses'"
    assert "win_rate" in overall, "Should have 'win_rate'"
    assert "confidence_interval_95" in overall, "Should have 'confidence_interval_95'"

    # Verify JSON is serializable
    json_str = json.dumps(results)
    assert len(json_str) > 0, "Should be able to serialize to JSON"

    # Verify can deserialize
    parsed = json.loads(json_str)
    assert parsed["Spider-Man"]["hero"] == "Spider-Man", "Should deserialize correctly"


def test_rate_limiter_prevents_burst_requests(clean_test_data):
    """Test that rate limiting prevents burst API requests.

    CRITICAL: Validates rate limiting - prevents API ban and ensures compliance.
    """
    import time

    conn = clean_test_data
    mock_api = MagicMock()
    mock_api.get_player_matches.return_value = []

    # Insert 3 players
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO players (username, rank_tier, rank_score, match_history_fetched) "
            "VALUES (%s, %s, %s, %s)",
            [
                ("rate_player1", "Gold", 1500, False),
                ("rate_player2", "Gold", 1500, False),
                ("rate_player3", "Gold", 1500, False),
            ],
        )
        conn.commit()

    # Measure time to collect 3 players with rate limiting
    start_time = time.time()
    stats = collect_matches(mock_api, conn, batch_size=3, rate_limit_delay=0.2)
    elapsed = time.time() - start_time

    assert stats["players_processed"] == 3, "Should process 3 players"

    # With 0.2s delay between requests, 3 requests should take at least 0.6s
    # (0.2s after each request)
    assert (
        elapsed >= 0.6
    ), f"Rate limiting should enforce delays (took {elapsed:.2f}s, expected >= 0.6s)"
