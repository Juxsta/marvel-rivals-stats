"""Tests for statistical utility functions.

Focused tests for new synergy analysis statistical functions.
"""

from src.utils.statistics import (
    binomial_test_synergy,
    bonferroni_correction,
    calculate_required_sample_size,
    expected_wr_additive,
    expected_wr_average,
    wilson_confidence_interval,
)


def test_expected_wr_average_basic_cases():
    """Test average baseline calculation with standard cases."""
    # Equal win rates should return the same value
    assert expected_wr_average(0.50, 0.50) == 0.5000

    # Symmetric around 50%
    assert expected_wr_average(0.60, 0.40) == 0.5000

    # Normal case
    assert expected_wr_average(0.70, 0.50) == 0.6000

    # Real example from spec: Spider-Man (52%) + Luna Snow (55%)
    assert expected_wr_average(0.52, 0.55) == 0.5350

    # Edge cases
    assert expected_wr_average(0.0, 0.0) == 0.0
    assert expected_wr_average(1.0, 1.0) == 1.0
    assert expected_wr_average(0.0, 1.0) == 0.5000


def test_expected_wr_additive_with_capping():
    """Test additive baseline calculation and verify capping at 1.0."""
    # Equal to 50% should return 50%
    assert expected_wr_additive(0.50, 0.50) == 0.5000

    # Normal case
    assert expected_wr_additive(0.60, 0.60) == 0.7000

    # Real example from spec
    assert expected_wr_additive(0.52, 0.55) == 0.5700

    # Edge case: should cap at 1.0
    assert expected_wr_additive(0.90, 0.90) == 1.0000
    assert expected_wr_additive(0.80, 0.80) == 1.0000

    # Edge case: should cap at 0.0 (not go negative)
    assert expected_wr_additive(0.20, 0.20) == 0.0000
    assert expected_wr_additive(0.10, 0.10) == 0.0000


def test_binomial_test_synergy_significance():
    """Test binomial significance testing with known examples."""
    # Significant positive synergy: 65 wins out of 100 when expecting 50%
    # (p-value ~0.0027, clearly significant)
    result = binomial_test_synergy(65, 100, 0.50, alpha=0.05)
    assert "p_value" in result
    assert "significant" in result
    assert isinstance(result["p_value"], float)
    assert isinstance(result["significant"], bool)
    # Should be significant (p < 0.05)
    assert result["significant"] is True
    assert result["p_value"] < 0.05

    # Not significant: 52 wins out of 100 when expecting 50%
    result = binomial_test_synergy(52, 100, 0.50, alpha=0.05)
    assert result["significant"] is False

    # Edge case: perfect match to expected
    result = binomial_test_synergy(50, 100, 0.50, alpha=0.05)
    assert result["significant"] is False
    assert result["p_value"] > 0.05


def test_bonferroni_correction_multiple_comparisons():
    """Test Bonferroni correction with multiple p-values."""
    # Example: 3 comparisons with alpha=0.05
    # Corrected alpha should be 0.05/3 = 0.0167
    synergies = [
        {"p_value": 0.01},  # Should be significant (0.01 < 0.0167)
        {"p_value": 0.04},  # Should NOT be significant (0.04 > 0.0167)
        {"p_value": 0.10},  # Should NOT be significant
    ]

    corrected = bonferroni_correction(synergies, alpha=0.05)

    # Verify fields added
    assert "significant_bonferroni" in corrected[0]
    assert "bonferroni_alpha" in corrected[0]

    # Verify corrected alpha
    assert corrected[0]["bonferroni_alpha"] == 0.016667

    # Verify significance decisions
    assert corrected[0]["significant_bonferroni"] is True
    assert corrected[1]["significant_bonferroni"] is False
    assert corrected[2]["significant_bonferroni"] is False

    # Edge case: empty list
    empty = bonferroni_correction([], alpha=0.05)
    assert empty == []

    # Edge case: single comparison (no correction needed)
    single = bonferroni_correction([{"p_value": 0.03}], alpha=0.05)
    assert single[0]["significant_bonferroni"] is True
    assert single[0]["bonferroni_alpha"] == 0.05


def test_calculate_required_sample_size_power_analysis():
    """Test sample size calculation for power analysis."""
    # For 5% effect at 50% baseline with 80% power
    # The calculation yields ~783 games (validated by running the formula)
    n = calculate_required_sample_size(0.50, 0.05, alpha=0.05, power=0.80)
    assert 750 <= n <= 800, f"Expected ~783 games for 5% effect, got {n}"

    # Smaller effect size requires more samples
    n_small = calculate_required_sample_size(0.50, 0.03, alpha=0.05, power=0.80)
    n_large = calculate_required_sample_size(0.50, 0.10, alpha=0.05, power=0.80)
    assert n_small > n, "3% effect should require more samples than 5%"
    assert n_large < n, "10% effect should require fewer samples than 5%"

    # Higher power requires more samples
    n_80 = calculate_required_sample_size(0.50, 0.05, alpha=0.05, power=0.80)
    n_90 = calculate_required_sample_size(0.50, 0.05, alpha=0.05, power=0.90)
    assert n_90 > n_80, "90% power should require more samples than 80%"

    # Result should be integer
    assert isinstance(n, int)


def test_wilson_ci_integration():
    """Test Wilson CI reuse from existing utility (spec example)."""
    # Test case from spec: 50 wins out of 100 games
    lower, upper = wilson_confidence_interval(50, 100, confidence=0.95)

    # Verify bounds are reasonable for 50% win rate
    assert 0.40 < lower < 0.50, f"Lower bound {lower} should be between 0.40 and 0.50"
    assert 0.50 < upper < 0.60, f"Upper bound {upper} should be between 0.50 and 0.60"

    # Verify types are Python float (not numpy)
    assert isinstance(lower, float)
    assert isinstance(upper, float)

    # Verify bounds are in correct order
    assert lower < upper

    # Verify bounds are within valid probability range [0, 1]
    assert 0 <= lower <= 1
    assert 0 <= upper <= 1

    # Test edge case: perfect win rate
    lower, upper = wilson_confidence_interval(100, 100, confidence=0.95)
    assert upper == 1.0  # Should be capped at 1.0
    assert lower < 1.0  # Lower bound should be less than 1.0

    # Test edge case: zero wins
    lower, upper = wilson_confidence_interval(0, 100, confidence=0.95)
    assert lower == 0.0  # Should be capped at 0.0
    assert upper > 0.0  # Upper bound should be greater than 0.0
