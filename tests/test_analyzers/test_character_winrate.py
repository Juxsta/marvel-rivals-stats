"""Tests for character win rate analysis module.

Focused tests for core statistical calculations and win rate analysis logic.
"""

from src.analyzers.character_winrate import (
    calculate_win_rate_stats,
    filter_by_min_games,
    group_matches_by_rank,
    wilson_confidence_interval,
)


def test_wilson_confidence_interval_known_values():
    """Test Wilson CI calculation with known mathematical values."""
    # Test case: 81 wins out of 100 trials
    # Verified Wilson 95% CI: [0.7222, 0.8749]
    lower, upper = wilson_confidence_interval(wins=81, total=100, confidence=0.95)

    assert lower == 0.7222, f"Lower bound should be 0.7222, got {lower}"
    assert upper == 0.8749, f"Upper bound should be 0.8749, got {upper}"

    # Test edge case: 0 wins
    lower, upper = wilson_confidence_interval(wins=0, total=50, confidence=0.95)
    assert lower == 0.0, "Lower bound for 0 wins should be 0.0"
    assert upper < 0.1, "Upper bound for 0 wins should be small"

    # Test edge case: 0 total (divide by zero protection)
    lower, upper = wilson_confidence_interval(wins=0, total=0, confidence=0.95)
    assert lower == 0.0 and upper == 0.0, "0 total should return (0.0, 0.0)"


def test_calculate_win_rate_stats():
    """Test win rate and confidence interval calculation."""
    # Test normal case
    stats = calculate_win_rate_stats(wins=60, total=100)

    assert stats["total_games"] == 100
    assert stats["wins"] == 60
    assert stats["losses"] == 40
    assert stats["win_rate"] == 0.6000
    assert len(stats["confidence_interval_95"]) == 2
    assert stats["confidence_interval_95"][0] < 0.6 < stats["confidence_interval_95"][1]


def test_group_matches_by_rank():
    """Test grouping match results by rank tier."""
    # Mock match data: [(won, rank_tier), ...]
    matches = [
        {"won": True, "rank_tier": "Gold"},
        {"won": False, "rank_tier": "Gold"},
        {"won": True, "rank_tier": "Gold"},
        {"won": True, "rank_tier": "Platinum"},
        {"won": False, "rank_tier": "Platinum"},
    ]

    grouped = group_matches_by_rank(matches)

    assert "Gold" in grouped
    assert "Platinum" in grouped
    assert grouped["Gold"]["wins"] == 2
    assert grouped["Gold"]["losses"] == 1
    assert grouped["Platinum"]["wins"] == 1
    assert grouped["Platinum"]["losses"] == 1


def test_filter_by_min_games():
    """Test filtering ranks by minimum game threshold."""
    rank_stats = {
        "Gold": {"total_games": 100, "wins": 55, "losses": 45},
        "Platinum": {"total_games": 25, "wins": 15, "losses": 10},  # Below threshold
        "Diamond": {"total_games": 50, "wins": 30, "losses": 20},
    }

    filtered = filter_by_min_games(rank_stats, min_games=30)

    assert "Gold" in filtered, "Gold has 100 games, should pass"
    assert "Diamond" in filtered, "Diamond has 50 games, should pass"
    assert "Platinum" not in filtered, "Platinum has only 25 games, should be filtered"
