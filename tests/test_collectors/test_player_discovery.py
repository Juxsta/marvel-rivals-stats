"""Unit tests for player discovery module.

Tests focus on core logic: stratified sampling, deduplication, and rank grouping.
Does NOT test API integration (mocked).
"""

from unittest.mock import MagicMock

from src.collectors.player_discovery import (
    deduplicate_players_in_memory,
    group_by_rank,
    stratify_by_rank,
)


class TestStratifiedSampling:
    """Test stratified sampling respects rank quotas."""

    def test_stratify_by_rank_respects_quotas(self):
        """Test that stratified sampling returns correct number per rank."""
        # Create sample players across multiple ranks
        players = []
        for i in range(200):
            players.append(
                {
                    "username": f"player_{i}",
                    "rank_tier": "Gold" if i < 150 else "Bronze",
                    "rank_score": 1000 + i,
                }
            )

        quotas = {"Gold": 50, "Bronze": 25}

        result = stratify_by_rank(players, quotas)

        # Count results by rank
        rank_counts = {}
        for player in result:
            rank = player["rank_tier"]
            rank_counts[rank] = rank_counts.get(rank, 0) + 1

        assert rank_counts["Gold"] == 50
        assert rank_counts["Bronze"] == 25
        assert len(result) == 75

    def test_stratify_by_rank_handles_insufficient_players(self):
        """Test that sampling handles when quota exceeds available players."""
        players = [
            {"username": "player_1", "rank_tier": "Celestial", "rank_score": 3000},
            {"username": "player_2", "rank_tier": "Celestial", "rank_score": 2950},
        ]

        quotas = {"Celestial": 25}  # Want 25, only have 2

        result = stratify_by_rank(players, quotas)

        assert len(result) == 2  # Should return all available


class TestPlayerDeduplication:
    """Test player deduplication by username."""

    def test_deduplicate_by_username(self):
        """Test that duplicate usernames are removed."""
        players = [
            {"username": "player_1", "rank_tier": "Gold", "rank_score": 1500},
            {"username": "player_2", "rank_tier": "Silver", "rank_score": 1200},
            {"username": "player_1", "rank_tier": "Gold", "rank_score": 1510},  # Duplicate
        ]

        result = deduplicate_players_in_memory(players)

        assert len(result) == 2
        usernames = {p["username"] for p in result}
        assert usernames == {"player_1", "player_2"}


class TestRankGrouping:
    """Test rank grouping logic."""

    def test_group_by_rank(self):
        """Test that players are correctly grouped by rank tier."""
        players = [
            {"username": "player_1", "rank_tier": "Gold", "rank_score": 1500},
            {"username": "player_2", "rank_tier": "Silver", "rank_score": 1200},
            {"username": "player_3", "rank_tier": "Gold", "rank_score": 1550},
            {"username": "player_4", "rank_tier": "Platinum", "rank_score": 1800},
        ]

        result = group_by_rank(players)

        assert len(result["Gold"]) == 2
        assert len(result["Silver"]) == 1
        assert len(result["Platinum"]) == 1
        assert "Bronze" not in result or len(result["Bronze"]) == 0


class TestDatabaseInsertion:
    """Test database insertion logic with mocked connection."""

    def test_insert_players_with_mock_db(self):
        """Test that players are inserted correctly (mocked database)."""
        from src.collectors.player_discovery import insert_players

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 3

        players = [
            {"username": "player_1", "rank_tier": "Gold", "rank_score": 1500},
            {"username": "player_2", "rank_tier": "Silver", "rank_score": 1200},
            {"username": "player_3", "rank_tier": "Platinum", "rank_score": 1800},
        ]

        count = insert_players(mock_conn, players)

        assert count == 3
        assert mock_cursor.executemany.called  # Fixed: we use executemany, not execute
        assert mock_conn.commit.called
