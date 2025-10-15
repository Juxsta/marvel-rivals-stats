"""Statistical helper functions for win rate calculations.

This module provides centralized statistical functions used across analyzers,
including Wilson confidence intervals and win rate calculations.
"""

from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import binomtest, norm


def wilson_confidence_interval(
    wins: int, total: int, confidence: float = 0.95
) -> Tuple[float, float]:
    """Calculate Wilson score confidence interval for binomial proportion.

    More accurate than normal approximation for small sample sizes.
    The Wilson score interval is preferred in statistics for binomial proportions.

    Args:
        wins: Number of wins (successes)
        total: Total number of games (trials)
        confidence: Confidence level (default 0.95 = 95%)

    Returns:
        Tuple of (lower_bound, upper_bound) rounded to 4 decimal places as Python floats

    References:
        https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
    """
    if total == 0:
        return (0.0, 0.0)

    p = wins / total
    z = norm.ppf(1 - (1 - confidence) / 2)  # 1.96 for 95% confidence

    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * ((p * (1 - p) / total + z**2 / (4 * total**2)) ** 0.5) / denominator

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    # Convert to Python float to avoid numpy types in database
    return (float(round(lower, 4)), float(round(upper, 4)))


def calculate_win_rate(wins: int, losses: int) -> float:
    """Calculate win rate from wins and losses.

    Args:
        wins: Number of wins
        losses: Number of losses

    Returns:
        Win rate as a float (0.0 to 1.0), rounded to 4 decimal places
    """
    total = wins + losses
    if total == 0:
        return 0.0

    return round(wins / total, 4)


def calculate_expected_win_rate(wr_a: float, wr_b: float) -> float:
    """Calculate expected win rate using independence assumption.

    DEPRECATED: This multiplicative model is theoretically flawed for teammates
    on the same team. Use `expected_wr_average()` instead.

    Under the independence assumption, P(A and B both win) = P(A wins) * P(B wins).
    This incorrectly treats teammates as independent events, when their fates are
    perfectly correlated (both on same team).

    Used for synergy analysis to determine if hero pairs perform better or
    worse than expected based on their individual win rates.

    Args:
        wr_a: First hero's overall win rate
        wr_b: Second hero's overall win rate

    Returns:
        Expected win rate when paired together, rounded to 4 decimal places

    See Also:
        expected_wr_average: Recommended replacement using average baseline model
    """
    return round(wr_a * wr_b, 4)


def expected_wr_average(wr_a: float, wr_b: float) -> float:
    """Calculate expected win rate using average baseline model.

    Formula: Expected WR = (WR_A + WR_B) / 2

    Rationale: If two heroes contribute equally to team performance, their
    combined expected win rate is their average. This is the simplest
    theoretically sound baseline for teammates on the same team.

    Unlike the multiplicative model (WR_A × WR_B), the average model correctly
    treats teammates as correlated (both win or lose together), not independent.

    Args:
        wr_a: First hero's overall win rate (0.0 to 1.0)
        wr_b: Second hero's overall win rate (0.0 to 1.0)

    Returns:
        Expected win rate when paired together, rounded to 4 decimal places

    Example:
        >>> expected_wr_average(0.52, 0.55)
        0.5350
        >>> expected_wr_average(0.50, 0.50)
        0.5000
    """
    return round((wr_a + wr_b) / 2.0, 4)


def expected_wr_additive(wr_a: float, wr_b: float) -> float:
    """Calculate expected win rate using additive contributions model.

    Formula: Expected WR = 0.5 + (WR_A - 0.5) + (WR_B - 0.5)

    Rationale: Each hero contributes independently to deviation from the
    baseline 50% win rate. More sophisticated than the average model but
    produces similar results in practice.

    The result is capped at [0.0, 1.0] to maintain valid probability bounds.

    Args:
        wr_a: First hero's overall win rate (0.0 to 1.0)
        wr_b: Second hero's overall win rate (0.0 to 1.0)

    Returns:
        Expected win rate when paired together, capped at [0.0, 1.0], rounded to 4 decimal places

    Example:
        >>> expected_wr_additive(0.52, 0.55)
        0.5700
        >>> expected_wr_additive(0.90, 0.90)
        1.0000  # Capped at 100%
    """
    baseline = 0.5
    contrib_a = wr_a - baseline
    contrib_b = wr_b - baseline
    result = baseline + contrib_a + contrib_b
    # Cap at both 0.0 and 1.0
    return round(max(0.0, min(1.0, result)), 4)


def binomial_test_synergy(wins: int, total: int, expected_wr: float, alpha: float = 0.05) -> Dict:
    """Test if synergy differs significantly from expected baseline.

    Uses exact binomial test (two-sided) to determine if the observed win rate
    differs significantly from the expected win rate. The null hypothesis is
    that the true win rate equals the expected win rate.

    Formula: Uses scipy.stats.binomtest with alternative='two-sided'

    Args:
        wins: Number of wins together
        total: Total games together
        expected_wr: Expected win rate from baseline model (0.0 to 1.0)
        alpha: Significance level (default 0.05 for 95% confidence)

    Returns:
        Dictionary with:
            - p_value (float): Two-sided p-value, rounded to 4 decimals
            - significant (bool): True if p_value < alpha

    Example:
        >>> binomial_test_synergy(60, 100, 0.50, alpha=0.05)
        {'p_value': 0.0352, 'significant': True}
    """
    result = binomtest(wins, total, expected_wr, alternative="two-sided")

    return {
        "p_value": round(result.pvalue, 4),
        "significant": bool(result.pvalue < alpha),  # Convert numpy bool to Python bool
    }


def bonferroni_correction(synergies: List[Dict], alpha: float = 0.05) -> List[Dict]:
    """Apply Bonferroni correction for multiple comparisons.

    When testing N synergies simultaneously, the Bonferroni correction uses
    a more stringent significance level (alpha/N) to control the family-wise
    error rate (probability of any false positives).

    Formula: Corrected alpha = alpha / N, where N = number of comparisons

    Modifies the synergies list in-place by adding two fields:
        - significant_bonferroni (bool): True if p_value < corrected alpha
        - bonferroni_alpha (float): The corrected significance threshold

    Args:
        synergies: List of synergy dictionaries, each with 'p_value' key
        alpha: Family-wise error rate (default 0.05)

    Returns:
        Updated synergies list with Bonferroni correction fields

    Example:
        >>> synergies = [{'p_value': 0.01}, {'p_value': 0.04}]
        >>> corrected = bonferroni_correction(synergies, alpha=0.05)
        >>> corrected[0]['significant_bonferroni']
        True  # 0.01 < 0.025 (alpha/2)
        >>> corrected[1]['significant_bonferroni']
        False  # 0.04 > 0.025
    """
    n_comparisons = len(synergies)
    if n_comparisons == 0:
        return synergies

    corrected_alpha = alpha / n_comparisons

    for synergy in synergies:
        synergy["significant_bonferroni"] = synergy["p_value"] < corrected_alpha
        synergy["bonferroni_alpha"] = round(corrected_alpha, 6)

    return synergies


def calculate_required_sample_size(
    baseline_wr: float, effect_size: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Calculate required sample size to detect a synergy effect.

    Uses the formula for two-proportion z-test with specified significance
    level (alpha) and statistical power. Power is the probability of correctly
    detecting a true effect of the specified size.

    Formula:
        n = [(z_α * sqrt(p0*(1-p0)) + z_β * sqrt(p1*(1-p1))) / effect_size]²
        where:
            z_α = critical value for significance level (two-tailed)
            z_β = critical value for power (1 - β)
            p0 = baseline win rate
            p1 = baseline + effect_size

    Args:
        baseline_wr: Expected win rate from baseline model (0.0 to 1.0)
        effect_size: Minimum synergy to detect (e.g., 0.05 = 5%)
        alpha: Significance level (default 0.05 for 95% confidence)
        power: Statistical power (default 0.80 = 80% power)

    Returns:
        Required number of games to detect effect, rounded up to integer

    Example:
        >>> calculate_required_sample_size(0.50, 0.05)
        783  # Need ~783 games to detect 5% synergy with 80% power

    References:
        Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences
    """
    z_alpha = norm.ppf(1 - alpha / 2)  # Two-tailed
    z_beta = norm.ppf(power)

    p0 = baseline_wr
    p1 = baseline_wr + effect_size

    n = ((z_alpha * np.sqrt(p0 * (1 - p0)) + z_beta * np.sqrt(p1 * (1 - p1))) / effect_size) ** 2

    return int(np.ceil(n))
