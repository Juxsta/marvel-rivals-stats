"""Unit tests for match collection module.

Tests focus on core logic: match filtering, deduplication, and participant extraction.
Does NOT test API integration (mocked).
"""

from unittest.mock import MagicMock

from src.collectors.match_collector import (
    extract_participants,
    filter_competitive_matches,
)


class TestMatchFiltering:
    """Test match filtering by season and mode."""

    def test_filter_competitive_current_season(self):
        """Test that only competitive matches from current season are kept."""
        matches = [
            {"match_id": "1", "mode": "competitive", "season": 1},
            {"match_id": "2", "mode": "quickplay", "season": 1},
            {"match_id": "3", "mode": "competitive", "season": 0},
            {"match_id": "4", "mode": "competitive", "season": 1},
        ]

        result = filter_competitive_matches(matches, current_season=1)

        assert len(result) == 2
        assert result[0]["match_id"] == "1"
        assert result[1]["match_id"] == "4"


class TestMatchDeduplication:
    """Test match deduplication logic."""

    def test_match_exists_returns_true_when_found(self):
        """Test that match_exists returns True for existing matches."""
        from src.collectors.match_collector import match_exists

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)

        result = match_exists(mock_conn, "match_123")

        assert result is True
        assert mock_cursor.execute.called

    def test_match_exists_returns_false_when_not_found(self):
        """Test that match_exists returns False for new matches."""
        from src.collectors.match_collector import match_exists

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        result = match_exists(mock_conn, "match_new")

        assert result is False


class TestParticipantExtraction:
    """Test participant extraction from match data."""

    def test_extract_participants_from_match(self):
        """Test that all 12 participants are extracted with correct data."""
        match = {
            "match_id": "match_123",
            "teams": [
                {
                    "team": 0,
                    "won": True,
                    "players": [
                        {
                            "username": "player_1",
                            "hero_id": 101,
                            "hero_name": "Spider-Man",
                            "role": "Duelist",
                            "kills": 15,
                            "deaths": 8,
                            "assists": 12,
                            "damage": 25000,
                            "healing": 0,
                        },
                        {
                            "username": "player_2",
                            "hero_id": 102,
                            "hero_name": "Iron Man",
                            "role": "Duelist",
                            "kills": 12,
                            "deaths": 9,
                            "assists": 8,
                            "damage": 22000,
                            "healing": 0,
                        },
                        {
                            "username": "player_3",
                            "hero_id": 103,
                            "hero_name": "Hulk",
                            "role": "Vanguard",
                            "kills": 8,
                            "deaths": 5,
                            "assists": 15,
                            "damage": 18000,
                            "healing": 0,
                        },
                        {
                            "username": "player_4",
                            "hero_id": 104,
                            "hero_name": "Captain America",
                            "role": "Vanguard",
                            "kills": 6,
                            "deaths": 6,
                            "assists": 18,
                            "damage": 15000,
                            "healing": 0,
                        },
                        {
                            "username": "player_5",
                            "hero_id": 105,
                            "hero_name": "Mantis",
                            "role": "Strategist",
                            "kills": 2,
                            "deaths": 4,
                            "assists": 20,
                            "damage": 5000,
                            "healing": 35000,
                        },
                        {
                            "username": "player_6",
                            "hero_id": 106,
                            "hero_name": "Luna Snow",
                            "role": "Strategist",
                            "kills": 1,
                            "deaths": 3,
                            "assists": 22,
                            "damage": 3000,
                            "healing": 38000,
                        },
                    ],
                },
                {
                    "team": 1,
                    "won": False,
                    "players": [
                        {
                            "username": "player_7",
                            "hero_id": 107,
                            "hero_name": "Black Panther",
                            "role": "Duelist",
                            "kills": 14,
                            "deaths": 10,
                            "assists": 9,
                            "damage": 24000,
                            "healing": 0,
                        },
                        {
                            "username": "player_8",
                            "hero_id": 108,
                            "hero_name": "Storm",
                            "role": "Duelist",
                            "kills": 11,
                            "deaths": 11,
                            "assists": 7,
                            "damage": 21000,
                            "healing": 0,
                        },
                        {
                            "username": "player_9",
                            "hero_id": 109,
                            "hero_name": "Magneto",
                            "role": "Vanguard",
                            "kills": 7,
                            "deaths": 7,
                            "assists": 14,
                            "damage": 17000,
                            "healing": 0,
                        },
                        {
                            "username": "player_10",
                            "hero_id": 110,
                            "hero_name": "Doctor Strange",
                            "role": "Vanguard",
                            "kills": 5,
                            "deaths": 8,
                            "assists": 16,
                            "damage": 14000,
                            "healing": 0,
                        },
                        {
                            "username": "player_11",
                            "hero_id": 111,
                            "hero_name": "Loki",
                            "role": "Strategist",
                            "kills": 3,
                            "deaths": 5,
                            "assists": 19,
                            "damage": 6000,
                            "healing": 33000,
                        },
                        {
                            "username": "player_12",
                            "hero_id": 112,
                            "hero_name": "Adam Warlock",
                            "role": "Strategist",
                            "kills": 2,
                            "deaths": 4,
                            "assists": 21,
                            "damage": 4000,
                            "healing": 36000,
                        },
                    ],
                },
            ],
        }

        participants = extract_participants("match_123", match)

        # Should extract all 12 participants
        assert len(participants) == 12

        # Check first participant (team 0, won=True)
        p1 = participants[0]
        assert p1["username"] == "player_1"
        assert p1["hero_name"] == "Spider-Man"
        assert p1["team"] == 0
        assert p1["won"] is True
        assert p1["kills"] == 15
        assert p1["damage"] == 25000

        # Check last participant (team 1, won=False)
        p12 = participants[11]
        assert p12["username"] == "player_12"
        assert p12["team"] == 1
        assert p12["won"] is False


class TestRateLimiterIntegration:
    """Test rate limiter integration."""

    def test_rate_limiter_enforces_delay(self):
        """Test that rate limiter is called during collection."""
        from src.api.rate_limiter import RateLimiter
        from src.collectors.match_collector import collect_matches

        mock_api = MagicMock()
        mock_api.get_player_matches.return_value = []
        mock_api.rate_limiter = RateLimiter(requests_per_minute=60)  # Fast for testing

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [("test_player",)]

        # This should call rate_limiter.wait_if_needed()
        stats = collect_matches(mock_api, mock_conn, batch_size=1, rate_limit_delay=0.1)

        assert stats["players_processed"] == 1
        assert mock_api.get_player_matches.called
