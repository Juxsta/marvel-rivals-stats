"""Unit tests for teammate synergy analysis.

These tests focus on core synergy calculation logic without database integration.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.analyzers.teammate_synergy import (
    add_sample_size_warning,
    analyze_teammate_synergies,
    cache_synergy_stats,
    calculate_synergy_score,
    extract_teammates_from_match,
    filter_by_min_games,
)
from src.utils.statistics import calculate_expected_win_rate


def test_calculate_synergy_score():
    """Test synergy score calculation: actual_wr - expected_wr."""
    # Basic case: positive synergy
    actual_wr = 0.60
    expected_wr = 0.52
    synergy_score = calculate_synergy_score(actual_wr, expected_wr)
    assert synergy_score == pytest.approx(0.08, abs=0.001)

    # Negative synergy
    actual_wr = 0.45
    expected_wr = 0.52
    synergy_score = calculate_synergy_score(actual_wr, expected_wr)
    assert synergy_score == pytest.approx(-0.07, abs=0.001)

    # No synergy (expected = actual)
    actual_wr = 0.50
    expected_wr = 0.50
    synergy_score = calculate_synergy_score(actual_wr, expected_wr)
    assert synergy_score == pytest.approx(0.0, abs=0.001)


def test_calculate_expected_win_rate():
    """Test expected win rate calculation using independence assumption."""
    # Both heroes have 50% win rate
    hero_wr = 0.50
    teammate_wr = 0.50
    expected_wr = calculate_expected_win_rate(hero_wr, teammate_wr)
    assert expected_wr == pytest.approx(0.25, abs=0.001)

    # One hero strong, one weak
    hero_wr = 0.60
    teammate_wr = 0.40
    expected_wr = calculate_expected_win_rate(hero_wr, teammate_wr)
    assert expected_wr == pytest.approx(0.24, abs=0.001)

    # Both heroes strong
    hero_wr = 0.55
    teammate_wr = 0.55
    expected_wr = calculate_expected_win_rate(hero_wr, teammate_wr)
    assert expected_wr == pytest.approx(0.3025, abs=0.001)


def test_extract_teammates_from_match():
    """Test teammate extraction from match data."""
    match_data = {
        "match_id": "match_123",
        "team": 0,
        "hero": "Spider-Man",
        "teammates": ["Luna Snow", "Iron Man", "Venom", "Peni Parker"],
    }

    teammates = extract_teammates_from_match(match_data["teammates"], match_data["hero"])

    assert len(teammates) == 4
    assert "Luna Snow" in teammates
    assert "Spider-Man" not in teammates  # Hero excluded


def test_filter_by_min_games():
    """Test filtering teammate stats by minimum games threshold."""
    teammate_stats = {
        "Luna Snow": {"games": 87, "wins": 52},
        "Iron Man": {"games": 45, "wins": 23},
        "Venom": {"games": 12, "wins": 6},  # Below threshold
    }

    min_games = 50
    filtered = filter_by_min_games(teammate_stats, min_games)

    assert len(filtered) == 1
    assert "Luna Snow" in filtered
    assert filtered["Luna Snow"]["games"] == 87

    # Test with lower threshold
    min_games = 10
    filtered = filter_by_min_games(teammate_stats, min_games)

    assert len(filtered) == 3  # All should pass


def test_synergy_score_rounding():
    """Test that synergy scores are rounded to 4 decimal places."""
    actual_wr = 0.5977011494
    expected_wr = 0.5200000000
    synergy_score = calculate_synergy_score(actual_wr, expected_wr)

    # Should round to 4 decimal places
    assert synergy_score == pytest.approx(0.0777, abs=0.0001)
    assert round(synergy_score, 4) == 0.0777


def test_add_sample_size_warning():
    """Test sample size warning generation."""
    # High confidence
    level, warning = add_sample_size_warning(500)
    assert level == "high"
    assert warning is None

    # Medium confidence
    level, warning = add_sample_size_warning(200)
    assert level == "medium"
    assert warning is not None
    assert "200 games" in warning

    # Low confidence
    level, warning = add_sample_size_warning(50)
    assert level == "low"
    assert warning is not None
    assert "50 games" in warning


# New tests for improved methodology (Task Group 3)


@patch("src.analyzers.teammate_synergy.query_match_teammates")
@patch("src.analyzers.teammate_synergy.query_hero_matches")
@patch("src.analyzers.teammate_synergy.load_character_win_rates")
def test_synergies_use_average_baseline(mock_load_wr, mock_hero_matches, mock_teammates):
    """Test that synergies use average baseline (not multiplicative)."""
    # Mock character win rates
    mock_load_wr.return_value = {"Hero A": 0.52, "Hero B": 0.55}

    # Mock Hero A plays 100 matches with Hero B (60 wins)
    mock_hero_matches.side_effect = [
        # Hero A matches
        [{"match_id": f"match{i}", "team": 0, "won": i < 60} for i in range(100)],
        # Hero B matches (empty)
        [],
    ]

    # Mock teammates - always return Hero B
    mock_teammates.return_value = ["Hero B"]

    # Mock database connection
    conn = Mock()
    conn.commit = Mock()
    conn.cursor.return_value.__enter__ = Mock()
    conn.cursor.return_value.__exit__ = Mock()
    conn.cursor.return_value.__enter__.return_value.execute = Mock()

    # Run analysis
    results = analyze_teammate_synergies(conn, min_games_together=50)

    # Verify results
    assert "Hero A" in results
    synergies = results["Hero A"]["synergies"]
    assert len(synergies) == 1

    synergy = synergies[0]
    # Average baseline: (0.52 + 0.55) / 2 = 0.535
    assert synergy["expected_win_rate"] == 0.5350
    # Actual: 60/100 = 0.60
    assert synergy["actual_win_rate"] == 0.6000


@patch("src.analyzers.teammate_synergy.query_match_teammates")
@patch("src.analyzers.teammate_synergy.query_hero_matches")
@patch("src.analyzers.teammate_synergy.load_character_win_rates")
def test_p_values_are_calculated(mock_load_wr, mock_hero_matches, mock_teammates):
    """Test that p-values are calculated for each synergy."""
    # Mock character win rates
    mock_load_wr.return_value = {"Hero A": 0.50, "Hero B": 0.50}

    # Hero A plays 100 matches with Hero B (65 wins = significant)
    mock_hero_matches.side_effect = [
        [{"match_id": f"match{i}", "team": 0, "won": i < 65} for i in range(100)],
        [],
    ]

    mock_teammates.return_value = ["Hero B"]

    conn = Mock()
    conn.commit = Mock()
    conn.cursor.return_value.__enter__ = Mock()
    conn.cursor.return_value.__exit__ = Mock()
    conn.cursor.return_value.__enter__.return_value.execute = Mock()

    results = analyze_teammate_synergies(conn, min_games_together=50)

    synergy = results["Hero A"]["synergies"][0]
    # Should have p_value and significant fields
    assert "p_value" in synergy
    assert "significant" in synergy
    assert isinstance(synergy["p_value"], float)
    assert isinstance(synergy["significant"], bool)
    # 65% win rate when expecting 50% should be significant
    assert synergy["significant"] is True


@patch("src.analyzers.teammate_synergy.query_match_teammates")
@patch("src.analyzers.teammate_synergy.query_hero_matches")
@patch("src.analyzers.teammate_synergy.load_character_win_rates")
def test_bonferroni_correction_applied(mock_load_wr, mock_hero_matches, mock_teammates):
    """Test that Bonferroni correction is applied to synergies."""
    # Mock character win rates
    mock_load_wr.return_value = {"Hero A": 0.50, "Hero B": 0.50, "Hero C": 0.50, "Hero D": 0.50}

    # Track which teammate to return based on call count
    call_count = [0]

    def mock_teammates_side_effect(*args):
        call_count[0] += 1
        # First 50 calls return B, next 50 return C, next 50 return D
        if call_count[0] <= 50:
            return ["Hero B"]
        elif call_count[0] <= 100:
            return ["Hero C"]
        else:
            return ["Hero D"]

    mock_teammates.side_effect = mock_teammates_side_effect

    # Hero A plays 150 matches (50 with each teammate)
    mock_hero_matches.side_effect = [
        # Hero A: 150 matches
        [{"match_id": f"match{i}", "team": 0, "won": True} for i in range(150)],
        # Others: empty
        [],
        [],
        [],
    ]

    conn = Mock()
    conn.commit = Mock()
    conn.cursor.return_value.__enter__ = Mock()
    conn.cursor.return_value.__exit__ = Mock()
    conn.cursor.return_value.__enter__.return_value.execute = Mock()

    results = analyze_teammate_synergies(conn, min_games_together=50)

    synergies = results["Hero A"]["synergies"]
    # Should have 3 synergies
    assert len(synergies) == 3
    for synergy in synergies:
        assert "significant_bonferroni" in synergy
        assert "bonferroni_alpha" in synergy
        # Bonferroni alpha should be ~0.05/3 = 0.0167
        assert 0.01 < synergy["bonferroni_alpha"] < 0.02


@patch("src.analyzers.teammate_synergy.query_match_teammates")
@patch("src.analyzers.teammate_synergy.query_hero_matches")
@patch("src.analyzers.teammate_synergy.load_character_win_rates")
def test_sample_size_warnings_generated(mock_load_wr, mock_hero_matches, mock_teammates):
    """Test that warnings are generated for small samples."""
    # Mock character win rates
    mock_load_wr.return_value = {"Hero A": 0.50, "Hero B": 0.50}

    # Hero A plays 150 matches with Hero B (medium confidence)
    mock_hero_matches.side_effect = [
        [{"match_id": f"match{i}", "team": 0, "won": True} for i in range(150)],
        [],
    ]

    mock_teammates.return_value = ["Hero B"]

    conn = Mock()
    conn.commit = Mock()
    conn.cursor.return_value.__enter__ = Mock()
    conn.cursor.return_value.__exit__ = Mock()
    conn.cursor.return_value.__enter__.return_value.execute = Mock()

    results = analyze_teammate_synergies(conn, min_games_together=50)

    synergy = results["Hero A"]["synergies"][0]
    # Should have confidence level and warning
    assert "confidence_level" in synergy
    assert "sample_size_warning" in synergy
    # 150 games = medium confidence (100-499)
    assert synergy["confidence_level"] == "medium"
    assert synergy["sample_size_warning"] is not None
    assert "150 games" in synergy["sample_size_warning"]


def test_database_caching_includes_new_fields():
    """Test that database caching includes all new fields."""
    conn = Mock()
    cursor_mock = MagicMock()
    # Properly mock the context manager
    conn.cursor.return_value.__enter__ = Mock(return_value=cursor_mock)
    conn.cursor.return_value.__exit__ = Mock()

    # Call cache_synergy_stats with new parameters
    cache_synergy_stats(
        conn,
        hero_a="Hero A",
        hero_b="Hero B",
        rank_tier=None,
        games_together=100,
        wins_together=60,
        win_rate=0.6000,
        expected_win_rate=0.5000,
        synergy_score=0.1000,
        confidence_lower=0.5000,
        confidence_upper=0.7000,
        p_value=0.0352,
        sample_size_warning=None,
        baseline_model="average",
    )

    # Verify INSERT was called with all fields
    cursor_mock.execute.assert_called_once()
    call_args = cursor_mock.execute.call_args
    sql = call_args[0][0]
    params = call_args[0][1]

    # Check SQL includes new columns
    assert "confidence_lower" in sql
    assert "confidence_upper" in sql
    assert "p_value" in sql
    assert "sample_size_warning" in sql
    assert "baseline_model" in sql

    # Check parameters include new values
    assert 0.5000 in params  # confidence_lower
    assert 0.7000 in params  # confidence_upper
    assert 0.0352 in params  # p_value
    assert "average" in params  # baseline_model


@patch("src.analyzers.teammate_synergy.query_match_teammates")
@patch("src.analyzers.teammate_synergy.query_hero_matches")
@patch("src.analyzers.teammate_synergy.load_character_win_rates")
def test_confidence_intervals_included(mock_load_wr, mock_hero_matches, mock_teammates):
    """Test that confidence intervals are included in results."""
    # Mock character win rates
    mock_load_wr.return_value = {"Hero A": 0.50, "Hero B": 0.50}

    # Hero A plays 100 matches with Hero B
    mock_hero_matches.side_effect = [
        [{"match_id": f"match{i}", "team": 0, "won": True} for i in range(100)],
        [],
    ]

    mock_teammates.return_value = ["Hero B"]

    conn = Mock()
    conn.commit = Mock()
    conn.cursor.return_value.__enter__ = Mock()
    conn.cursor.return_value.__exit__ = Mock()
    conn.cursor.return_value.__enter__.return_value.execute = Mock()

    results = analyze_teammate_synergies(conn, min_games_together=50)

    synergy = results["Hero A"]["synergies"][0]
    # Should have confidence interval
    assert "confidence_interval_95" in synergy
    ci = synergy["confidence_interval_95"]
    assert isinstance(ci, list)
    assert len(ci) == 2
    # Lower bound should be less than upper bound
    assert ci[0] < ci[1]
    # Bounds should be reasonable (between 0 and 1)
    assert 0 <= ci[0] <= 1
    assert 0 <= ci[1] <= 1
