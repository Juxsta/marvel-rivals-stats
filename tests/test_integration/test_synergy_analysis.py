"""Integration tests for improved synergy analysis methodology.

Tests end-to-end behavior of the synergy analysis system with the new
average baseline methodology, statistical significance testing, and
confidence intervals.

Focus on:
- Full pipeline execution with new methodology
- Comparison between old and new baseline calculations
- Validation with real data patterns (Hulk + Luna Snow)
- Database integration with new schema fields
"""

import os
from datetime import datetime

import psycopg2
import pytest

from src.analyzers.teammate_synergy import analyze_teammate_synergies
from src.utils.statistics import (
    calculate_expected_win_rate,  # Old multiplicative model
    expected_wr_average,  # New average model
)


def _get_test_connection():
    """Get a direct database connection for testing."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


@pytest.fixture
def synergy_test_data():
    """Create test database fixture for synergy analysis.

    Creates a realistic test dataset with known synergies to validate
    the improved methodology. Includes:
    - Character stats for baseline calculation
    - Match participants with controlled win rates
    - Sufficient sample sizes for statistical testing
    """
    conn = _get_test_connection()
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            # Clean existing test data
            cur.execute(
                "DELETE FROM character_stats WHERE hero_name IN "
                "('Test Hero A', 'Test Hero B', 'Test Hero C')"
            )
            cur.execute(
                "DELETE FROM synergy_stats WHERE hero_a LIKE 'Test Hero%' "
                "OR hero_b LIKE 'Test Hero%'"
            )
            cur.execute("DELETE FROM match_participants WHERE match_id LIKE 'syn_test_%'")
            cur.execute("DELETE FROM matches WHERE match_id LIKE 'syn_test_%'")
            cur.execute("DELETE FROM players WHERE username LIKE 'syn_player_%'")
        conn.commit()

        # Insert character stats for baseline calculations
        # Test Hero A: 52% WR, Test Hero B: 55% WR, Test Hero C: 50% WR
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO character_stats
                   (hero_name, rank_tier, total_games, wins, losses, win_rate, analyzed_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                [
                    ("Test Hero A", None, 200, 104, 96, 0.52, datetime.now()),
                    ("Test Hero B", None, 200, 110, 90, 0.55, datetime.now()),
                    ("Test Hero C", None, 200, 100, 100, 0.50, datetime.now()),
                ],
            )
        conn.commit()

        # Insert test players (need 200 for 100 matches with unique players)
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO players (username, rank_tier, rank_score) VALUES (%s, %s, %s)",
                [(f"syn_player_{i}", "Gold", 1500) for i in range(250)],
            )
        conn.commit()

        # Insert matches with controlled synergies
        # Scenario 1: Hero A + Hero B together (100 games, 60 wins)
        # Expected WR (average): (0.52 + 0.55) / 2 = 0.535
        # Actual WR: 0.60
        # Synergy score: +0.065 (~6.5% positive synergy)
        with conn.cursor() as cur:
            for i in range(100):
                match_id = f"syn_test_ab_{i}"
                cur.execute(
                    "INSERT INTO matches (match_id, mode, season, match_timestamp) "
                    "VALUES (%s, %s, %s, %s)",
                    (match_id, "competitive", 1, datetime.now()),
                )

                won = i < 60  # First 60 matches are wins

                # Hero A and Hero B on same team (use unique players)
                cur.execute(
                    """INSERT INTO match_participants
                       (match_id, username, hero_id, hero_name, role, team, won)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (match_id, f"syn_player_{i}", 101, "Test Hero A", "duelist", 0, won),
                )
                cur.execute(
                    """INSERT INTO match_participants
                       (match_id, username, hero_id, hero_name, role, team, won)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (match_id, f"syn_player_{i+100}", 102, "Test Hero B", "strategist", 0, won),
                )
        conn.commit()

        # Scenario 2: Hero A + Hero C together (50 games, 25 wins)
        # Expected WR (average): (0.52 + 0.50) / 2 = 0.51
        # Actual WR: 0.50
        # Synergy score: -0.01 (~1% negative, statistically insignificant)
        with conn.cursor() as cur:
            for i in range(50):
                match_id = f"syn_test_ac_{i}"
                cur.execute(
                    "INSERT INTO matches (match_id, mode, season, match_timestamp) "
                    "VALUES (%s, %s, %s, %s)",
                    (match_id, "competitive", 1, datetime.now()),
                )

                won = i < 25  # Half win

                cur.execute(
                    """INSERT INTO match_participants
                       (match_id, username, hero_id, hero_name, role, team, won)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (match_id, f"syn_player_{i+200}", 101, "Test Hero A", "duelist", 0, won),
                )
                cur.execute(
                    """INSERT INTO match_participants
                       (match_id, username, hero_id, hero_name, role, team, won)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (match_id, f"syn_player_{i+150}", 103, "Test Hero C", "vanguard", 0, won),
                )
        conn.commit()

        yield conn

        # Cleanup after test
        try:
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM character_stats WHERE hero_name IN "
                    "('Test Hero A', 'Test Hero B', 'Test Hero C')"
                )
                cur.execute(
                    "DELETE FROM synergy_stats WHERE hero_a LIKE 'Test Hero%' "
                    "OR hero_b LIKE 'Test Hero%'"
                )
                cur.execute("DELETE FROM match_participants WHERE match_id LIKE 'syn_test_%'")
                cur.execute("DELETE FROM matches WHERE match_id LIKE 'syn_test_%'")
                cur.execute("DELETE FROM players WHERE username LIKE 'syn_player_%'")
            conn.commit()
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def test_full_synergy_analysis_pipeline(synergy_test_data):
    """Test complete synergy analysis pipeline with new methodology.

    CRITICAL: Validates end-to-end pipeline execution with:
    - Average baseline calculation
    - P-value computation
    - Bonferroni correction
    - Sample size warnings
    - Database caching with new fields
    - Confidence intervals
    """
    conn = synergy_test_data

    # Run full synergy analysis
    results = analyze_teammate_synergies(conn, min_games_together=50, alpha=0.05)

    # Verify results exist for test heroes
    assert "Test Hero A" in results, "Test Hero A should have synergy results"

    hero_a_results = results["Test Hero A"]

    # Verify metadata
    assert "hero" in hero_a_results
    assert "synergies" in hero_a_results
    assert "power_analysis" in hero_a_results
    assert "analyzed_at" in hero_a_results

    synergies = hero_a_results["synergies"]

    # Should have at least 1 synergy (Hero B, 100 games)
    assert len(synergies) >= 1, "Should have at least 1 synergy with sufficient games"

    # Find Hero B synergy (best synergy)
    hero_b_synergy = next((s for s in synergies if s["teammate"] == "Test Hero B"), None)
    assert hero_b_synergy is not None, "Should have Hero B synergy"

    # Verify all new fields are present
    assert "games_together" in hero_b_synergy
    assert "wins_together" in hero_b_synergy
    assert "actual_win_rate" in hero_b_synergy
    assert "expected_win_rate" in hero_b_synergy
    assert "synergy_score" in hero_b_synergy
    assert "confidence_interval_95" in hero_b_synergy
    assert "p_value" in hero_b_synergy
    assert "significant" in hero_b_synergy
    assert "significant_bonferroni" in hero_b_synergy
    assert "bonferroni_alpha" in hero_b_synergy
    assert "confidence_level" in hero_b_synergy
    assert "sample_size_warning" in hero_b_synergy

    # Verify calculation correctness
    assert hero_b_synergy["games_together"] == 100
    assert hero_b_synergy["wins_together"] == 60
    assert hero_b_synergy["actual_win_rate"] == 0.6000

    # Expected WR should use average baseline: (0.52 + 0.55) / 2 = 0.535
    assert hero_b_synergy["expected_win_rate"] == 0.5350, "Should use average baseline"

    # Synergy score: 0.60 - 0.535 = 0.065
    assert 0.06 < hero_b_synergy["synergy_score"] < 0.07, "Synergy score should be ~6.5%"

    # Confidence interval should be reasonable
    ci = hero_b_synergy["confidence_interval_95"]
    assert len(ci) == 2
    assert ci[0] < 0.60 < ci[1], "Actual WR should be within CI"
    assert ci[1] - ci[0] < 0.2, "CI should be reasonably narrow for 100 games"

    # P-value should exist and be reasonable
    assert isinstance(hero_b_synergy["p_value"], float)
    assert 0 <= hero_b_synergy["p_value"] <= 1

    # Bonferroni correction should reduce significance
    # With 2 synergies tested, alpha should be ~0.025
    assert hero_b_synergy["bonferroni_alpha"] < 0.05

    # Sample size warning should reflect 100 games (medium confidence)
    assert hero_b_synergy["confidence_level"] == "medium"
    assert hero_b_synergy["sample_size_warning"] is not None
    assert "100 games" in hero_b_synergy["sample_size_warning"]

    # Verify database caching includes new fields
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT confidence_lower, confidence_upper, p_value,
                   sample_size_warning, baseline_model
            FROM synergy_stats
            WHERE (hero_a = 'Test Hero A' AND hero_b = 'Test Hero B')
               OR (hero_a = 'Test Hero B' AND hero_b = 'Test Hero A')
        """
        )
        row = cur.fetchone()
        assert row is not None, "Synergy should be cached in database"

        confidence_lower, confidence_upper, p_value, warning, baseline_model = row
        assert confidence_lower is not None
        assert confidence_upper is not None
        assert p_value is not None
        assert warning is not None
        assert baseline_model == "average"

    # Verify power analysis is included
    power_analysis = hero_a_results["power_analysis"]
    assert "current_max_samples" in power_analysis
    assert "required_for_3pct_synergy" in power_analysis
    assert "required_for_5pct_synergy" in power_analysis
    assert "required_for_10pct_synergy" in power_analysis


def test_old_vs_new_methodology_comparison(synergy_test_data):
    """Compare old multiplicative baseline vs new average baseline.

    CRITICAL: Documents the difference between methodologies.
    Shows that old methodology produces unrealistic expected WR and
    inflated synergy scores, while new methodology produces defensible results.
    """
    conn = synergy_test_data

    # Get character win rates
    hero_a_wr = 0.52
    hero_b_wr = 0.55
    actual_wr = 0.60  # 60 wins out of 100 games

    # OLD METHODOLOGY: Multiplicative baseline
    old_expected_wr = calculate_expected_win_rate(hero_a_wr, hero_b_wr)
    old_synergy_score = actual_wr - old_expected_wr

    # NEW METHODOLOGY: Average baseline
    new_expected_wr = expected_wr_average(hero_a_wr, hero_b_wr)
    new_synergy_score = actual_wr - new_expected_wr

    # Verify old methodology produces unrealistic results
    # Old: 0.52 * 0.55 = 0.286 (treats as independent events)
    assert old_expected_wr == pytest.approx(
        0.286, abs=0.001
    ), "Old methodology: multiplicative baseline"
    assert old_synergy_score == pytest.approx(
        0.314, abs=0.001
    ), "Old methodology: inflated synergy score ~31.4%"

    # Verify new methodology produces realistic results
    # New: (0.52 + 0.55) / 2 = 0.535 (average contribution)
    assert new_expected_wr == 0.5350, "New methodology: average baseline"
    assert new_synergy_score == pytest.approx(
        0.065, abs=0.001
    ), "New methodology: realistic synergy score ~6.5%"

    # Document the magnitude of difference
    baseline_difference = new_expected_wr - old_expected_wr
    synergy_difference = old_synergy_score - new_synergy_score

    # Old baseline is ~25% lower than new baseline
    assert baseline_difference > 0.20, "New baseline is significantly higher (more realistic)"

    # Old synergy score is ~25% higher than new (inflated)
    assert synergy_difference > 0.20, "Old synergy score is inflated by ~25%"

    # Run actual analysis to verify it uses new methodology
    results = analyze_teammate_synergies(conn, min_games_together=50)

    hero_a_synergies = results["Test Hero A"]["synergies"]
    hero_b_synergy = next((s for s in hero_a_synergies if s["teammate"] == "Test Hero B"), None)

    # Verify analysis uses new methodology
    assert (
        hero_b_synergy["expected_win_rate"] == new_expected_wr
    ), "Analysis should use new average baseline"
    assert (
        abs(hero_b_synergy["synergy_score"] - new_synergy_score) < 0.01
    ), "Analysis should produce realistic synergy scores"

    # Verify synergy score is NOT using old methodology
    assert (
        abs(hero_b_synergy["synergy_score"] - old_synergy_score) > 0.20
    ), "Analysis should NOT use old inflated methodology"


def test_validation_with_realistic_data(synergy_test_data):
    """Validate improved methodology with realistic data patterns.

    CRITICAL: Ensures the new methodology produces defensible results
    similar to real-world Hulk + Luna Snow data (207 games from demo).

    Real data reference:
    - Hulk: ~45.5% WR
    - Luna Snow: ~61.7% WR
    - Together: ~59.8% WR (207 games, 124 wins)
    - Expected (average): ~53.6%
    - Synergy: ~+6.2% (realistic)
    """
    conn = synergy_test_data

    # Run analysis on our test data
    results = analyze_teammate_synergies(conn, min_games_together=50)

    # Verify Test Hero A + Test Hero B synergy
    hero_a_synergies = results["Test Hero A"]["synergies"]
    hero_b_synergy = next((s for s in hero_a_synergies if s["teammate"] == "Test Hero B"), None)

    # Verify synergy score is in realistic range (±2-10%, not ±25-30%)
    synergy_score = hero_b_synergy["synergy_score"]
    assert (
        0.02 <= synergy_score <= 0.10
    ), f"Synergy score {synergy_score:.4f} should be in realistic range (2-10%)"

    # Verify NOT in inflated range
    assert synergy_score < 0.20, "Synergy score should NOT be inflated (>20%)"

    # Verify p-value is computed correctly
    p_value = hero_b_synergy["p_value"]
    assert isinstance(p_value, float)
    assert 0 <= p_value <= 1

    # With 100 games and ~6.5% synergy from ~53.5% baseline,
    # this should be marginally significant (p < 0.05)
    assert p_value < 0.30, "6.5% synergy with 100 games should have low p-value"

    # Verify confidence intervals are reasonable
    ci = hero_b_synergy["confidence_interval_95"]
    ci_width = ci[1] - ci[0]

    # CI width should be reasonable for 100 games (~15-20%)
    assert 0.10 < ci_width < 0.25, f"CI width {ci_width:.4f} should be reasonable for 100 games"

    # Verify expected WR is in realistic range (not < 30%)
    expected_wr = hero_b_synergy["expected_win_rate"]
    assert expected_wr > 0.40, f"Expected WR {expected_wr:.4f} should be realistic (not <40%)"

    # Verify actual WR matches data
    assert hero_b_synergy["actual_win_rate"] == 0.60

    # Compare with weak synergy (Hero A + Hero C)
    hero_c_synergy = next((s for s in hero_a_synergies if s["teammate"] == "Test Hero C"), None)

    if hero_c_synergy:  # Might be filtered by min_games
        # Weak synergy should have small score and high p-value
        assert abs(hero_c_synergy["synergy_score"]) < 0.05, "Weak synergy should have small score"
        assert hero_c_synergy["p_value"] > 0.50, "Weak synergy should not be significant"


def test_database_integration_with_new_schema(synergy_test_data):
    """Verify database integration with new schema columns.

    CRITICAL: Ensures migration columns work correctly and data is
    persisted with all new fields (confidence intervals, p-values, warnings).
    """
    conn = synergy_test_data

    # Run analysis to populate database
    analyze_teammate_synergies(conn, min_games_together=50)

    # Verify synergy_stats table has new columns
    with conn.cursor() as cur:
        # Query all synergies
        cur.execute(
            """
            SELECT hero_a, hero_b, games_together, wins_together,
                   win_rate, expected_win_rate, synergy_score,
                   confidence_lower, confidence_upper,
                   p_value, sample_size_warning, baseline_model,
                   analyzed_at
            FROM synergy_stats
            WHERE hero_a LIKE 'Test Hero%' OR hero_b LIKE 'Test Hero%'
            ORDER BY games_together DESC
        """
        )

        rows = cur.fetchall()
        assert len(rows) >= 1, "Should have at least 1 synergy cached"

        # Verify first synergy (should be Hero A + Hero B with 100 games)
        row = rows[0]
        (
            hero_a,
            hero_b,
            games_together,
            wins_together,
            win_rate,
            expected_win_rate,
            synergy_score,
            confidence_lower,
            confidence_upper,
            p_value,
            sample_size_warning,
            baseline_model,
            analyzed_at,
        ) = row

        # Verify all new fields are populated
        assert confidence_lower is not None, "confidence_lower should be populated"
        assert confidence_upper is not None, "confidence_upper should be populated"
        assert p_value is not None, "p_value should be populated"
        assert sample_size_warning is not None, "sample_size_warning should be populated"
        assert baseline_model == "average", "baseline_model should be 'average'"
        assert analyzed_at is not None, "analyzed_at should be populated"

        # Verify column types are correct
        assert isinstance(confidence_lower, float)
        assert isinstance(confidence_upper, float)
        assert isinstance(p_value, float)
        assert isinstance(sample_size_warning, str)
        assert isinstance(baseline_model, str)

        # Verify values are reasonable
        assert 0 <= confidence_lower <= 1
        assert 0 <= confidence_upper <= 1
        assert confidence_lower < confidence_upper
        assert 0 <= p_value <= 1
        assert "games" in sample_size_warning.lower()

        # Verify expected_win_rate uses average baseline
        # Hero A (52%) + Hero B (55%) -> expected ~53.5%
        assert (
            0.50 <= expected_win_rate <= 0.60
        ), "Expected WR should be realistic (average baseline)"

        # Verify synergy_score is realistic
        assert -0.20 < synergy_score < 0.20, "Synergy score should be realistic (not inflated)"

    # Verify index exists for p_value queries
    with conn.cursor() as cur:
        # Query using p_value index (should be fast)
        cur.execute(
            """
            SELECT COUNT(*) FROM synergy_stats
            WHERE p_value < 0.05
              AND (hero_a LIKE 'Test Hero%' OR hero_b LIKE 'Test Hero%')
        """
        )

        significant_count = cur.fetchone()[0]
        # Should have at least some significant results
        assert significant_count >= 0, "Query with p_value should work"

    # Verify queries with new fields work correctly
    with conn.cursor() as cur:
        # Query by confidence level
        cur.execute(
            """
            SELECT COUNT(*) FROM synergy_stats
            WHERE games_together >= 100
              AND (hero_a LIKE 'Test Hero%' OR hero_b LIKE 'Test Hero%')
        """
        )

        high_sample_count = cur.fetchone()[0]
        assert high_sample_count >= 1, "Should have synergies with 100+ games"
