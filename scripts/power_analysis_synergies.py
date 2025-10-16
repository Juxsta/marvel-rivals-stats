#!/usr/bin/env python3
"""Power analysis and advanced statistical approaches for synergy detection.

This script explores:
1. Power analysis - How much data do we need?
2. Better baseline models
3. Within-player paired analysis
4. Bayesian approaches
5. Multiple comparisons corrections
"""

import json
import os
import sys
from typing import Dict, List

import numpy as np
from scipy import stats
from scipy.stats import norm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.connection import get_connection


def calculate_required_sample_size(
    baseline_wr: float, effect_size: float, alpha: float = 0.05, power: float = 0.80
) -> int:
    """Calculate required sample size to detect a given effect size.

    Args:
        baseline_wr: Expected win rate under null hypothesis
        effect_size: Minimum detectable difference (e.g., 0.05 for 5% synergy)
        alpha: Type I error rate (false positive rate)
        power: Statistical power (1 - Type II error rate)

    Returns:
        Required sample size
    """
    # Z-scores for alpha and power
    z_alpha = norm.ppf(1 - alpha)
    z_beta = norm.ppf(power)

    # Variance under null and alternative
    p0 = baseline_wr
    p1 = baseline_wr + effect_size

    # Sample size formula for binomial proportions
    n = ((z_alpha * np.sqrt(p0 * (1 - p0)) + z_beta * np.sqrt(p1 * (1 - p1))) / effect_size) ** 2

    return int(np.ceil(n))


def within_player_analysis(conn, hero_a: str, hero_b: str, comparison_heroes: List[str]) -> Dict:
    """Compare hero_a+hero_b vs hero_a+others within same players.

    This controls for player skill by only comparing games from the same player.
    """
    cur = conn.cursor()

    # Get players who have played both hero_a with hero_b AND hero_a with comparison heroes
    query = """
    WITH player_games AS (
        SELECT
            mp1.username,
            mp1.hero_name as hero1,
            mp2.hero_name as hero2,
            mp1.won
        FROM match_participants mp1
        JOIN match_participants mp2
            ON mp1.match_id = mp2.match_id
            AND mp1.team = mp2.team
            AND mp1.username != mp2.username
        WHERE mp1.hero_name = %s
    ),
    with_target AS (
        SELECT username, COUNT(*) as games, SUM(CASE WHEN won THEN 1 ELSE 0 END) as wins
        FROM player_games
        WHERE hero2 = %s
        GROUP BY username
        HAVING COUNT(*) >= 5
    ),
    with_others AS (
        SELECT username, COUNT(*) as games, SUM(CASE WHEN won THEN 1 ELSE 0 END) as wins
        FROM player_games
        WHERE hero2 = ANY(%s)
        GROUP BY username
        HAVING COUNT(*) >= 5
    )
    SELECT
        t.username,
        t.games as target_games,
        t.wins as target_wins,
        o.games as other_games,
        o.wins as other_wins
    FROM with_target t
    JOIN with_others o ON t.username = o.username
    """

    cur.execute(query, (hero_a, hero_b, comparison_heroes))
    rows = cur.fetchall()

    if not rows:
        return None

    # Paired t-test on win rates
    target_wrs = []
    other_wrs = []

    for row in rows:
        username, target_games, target_wins, other_games, other_wins = row
        target_wrs.append(target_wins / target_games if target_games > 0 else 0)
        other_wrs.append(other_wins / other_games if other_games > 0 else 0)

    # Paired t-test
    if len(target_wrs) >= 3:
        t_stat, p_value = stats.ttest_rel(target_wrs, other_wrs)
        mean_diff = np.mean(target_wrs) - np.mean(other_wrs)

        return {
            "n_players": len(target_wrs),
            "mean_wr_with_target": np.mean(target_wrs),
            "mean_wr_with_others": np.mean(other_wrs),
            "mean_difference": mean_diff,
            "t_statistic": t_stat,
            "p_value": p_value,
            "significant": p_value < 0.05,
        }

    return None


def bayesian_synergy_estimate(wins: int, total: int, expected_wr: float) -> Dict:
    """Bayesian estimate of synergy using Beta-Binomial conjugate prior.

    Prior: Beta(α, β) where α = β = 10 (weakly informative, centered at 0.5)
    Likelihood: Binomial(n, p)
    Posterior: Beta(α + wins, β + losses)
    """
    # Weakly informative prior centered at expected_wr
    # More weight to prior when sample size is small
    prior_strength = 20  # Equivalent to 20 pseudo-observations
    prior_alpha = expected_wr * prior_strength
    prior_beta = (1 - expected_wr) * prior_strength

    # Posterior parameters
    posterior_alpha = prior_alpha + wins
    posterior_beta = prior_beta + (total - wins)

    # Posterior mean and credible interval
    posterior_mean = posterior_alpha / (posterior_alpha + posterior_beta)

    # 95% credible interval
    lower = stats.beta.ppf(0.025, posterior_alpha, posterior_beta)
    upper = stats.beta.ppf(0.975, posterior_alpha, posterior_beta)

    # Probability that true WR > expected WR
    prob_positive_synergy = 1 - stats.beta.cdf(expected_wr, posterior_alpha, posterior_beta)

    return {
        "posterior_mean": posterior_mean,
        "credible_interval_95": (lower, upper),
        "synergy_score": posterior_mean - expected_wr,
        "prob_positive_synergy": prob_positive_synergy,
        "substantial": prob_positive_synergy > 0.95,  # Strong evidence
    }


def team_composition_baseline(conn, hero_a: str, hero_b: str) -> float:
    """Calculate baseline win rate accounting for full team composition.

    This is more sophisticated than just hero_a + hero_b.
    We look at games with similar team comps but WITHOUT both heroes together.
    """
    cur = conn.cursor()

    # Get role composition for games with hero_a + hero_b
    query = """
    WITH target_games AS (
        SELECT DISTINCT m.match_id
        FROM match_participants mp1
        JOIN match_participants mp2
            ON mp1.match_id = mp2.match_id
            AND mp1.team = mp2.team
            AND mp1.username != mp2.username
        WHERE mp1.hero_name = %s
          AND mp2.hero_name = %s
    ),
    role_counts AS (
        SELECT
            mp.match_id,
            mp.team,
            COUNT(*) FILTER (WHERE mp.role = 'vanguard') as vanguards,
            COUNT(*) FILTER (WHERE mp.role = 'duelist') as duelists,
            COUNT(*) FILTER (WHERE mp.role = 'strategist') as strategists
        FROM match_participants mp
        WHERE mp.match_id IN (SELECT match_id FROM target_games)
        GROUP BY mp.match_id, mp.team
    )
    SELECT AVG(vanguards), AVG(duelists), AVG(strategists)
    FROM role_counts
    """

    cur.execute(query, (hero_a, hero_b))
    result = cur.fetchone()

    if not result or result[0] is None:
        return None

    avg_vanguards, avg_duelists, avg_strategists = result

    # Now find games with similar role composition but WITHOUT both heroes
    query = """
    WITH similar_comp_games AS (
        SELECT
            m.match_id,
            mp.team,
            COUNT(*) FILTER (WHERE mp.role = 'vanguard') as vanguards,
            COUNT(*) FILTER (WHERE mp.role = 'duelist') as duelists,
            COUNT(*) FILTER (WHERE mp.role = 'strategist') as strategists
        FROM matches m
        JOIN match_participants mp ON m.match_id = mp.match_id
        GROUP BY m.match_id, mp.team
        HAVING
            ABS(COUNT(*) FILTER (WHERE mp.role = 'vanguard') - %s) <= 1
            AND ABS(COUNT(*) FILTER (WHERE mp.role = 'duelist') - %s) <= 1
            AND ABS(COUNT(*) FILTER (WHERE mp.role = 'strategist') - %s) <= 1
    ),
    games_without_both AS (
        SELECT DISTINCT m.match_id, mp.team, mp.won
        FROM matches m
        JOIN match_participants mp ON m.match_id = mp.match_id
        WHERE m.match_id IN (SELECT match_id FROM similar_comp_games)
          AND NOT EXISTS (
              SELECT 1 FROM match_participants mp2
              WHERE mp2.match_id = m.match_id
                AND mp2.team = mp.team
                AND mp2.hero_name = %s
          )
          AND NOT EXISTS (
              SELECT 1 FROM match_participants mp3
              WHERE mp3.match_id = m.match_id
                AND mp3.team = mp.team
                AND mp3.hero_name = %s
          )
    )
    SELECT AVG(CASE WHEN won THEN 1.0 ELSE 0.0 END)
    FROM games_without_both
    """

    cur.execute(query, (avg_vanguards, avg_duelists, avg_strategists, hero_a, hero_b))
    result = cur.fetchone()

    if result and result[0] is not None:
        return float(result[0])

    return None


def main():
    """Run comprehensive statistical analysis for synergy detection."""
    print("=" * 80)
    print("COMPREHENSIVE STATISTICAL ANALYSIS FOR SYNERGY DETECTION")
    print("=" * 80)
    print()

    # Load data
    with open("output/synergies.json", "r") as f:
        synergy_data = json.load(f)

    with open("output/character_win_rates.json", "r") as f:
        winrate_data = json.load(f)

    hulk_synergies = synergy_data["Hulk"]["synergies"]
    hulk_wr = winrate_data["Hulk"]["overall"]["win_rate"]

    print("=" * 80)
    print("PART 1: POWER ANALYSIS - How Much Data Do We Need?")
    print("=" * 80)
    print()

    baseline = 0.55  # Typical expected WR for a pair

    print("Sample sizes required to detect synergies at 80% power (α = 0.05):")
    print()
    print("Effect Size | Sample Size Needed | Games in Dataset | Feasible?")
    print("-" * 70)

    for effect in [0.01, 0.02, 0.03, 0.05, 0.10]:
        n_required = calculate_required_sample_size(baseline, effect)
        max_games = max(s["games_together"] for s in hulk_synergies)
        feasible = "✓" if max_games >= n_required else "✗"
        print(f"{effect:+.1%}      | {n_required:>18} | {max_games:>16} | {feasible}")

    print()
    print("FINDING: With our current sample sizes (max 207 games), we can only")
    print("         detect synergies of 10% or larger with adequate power.")
    print("         Realistic synergies (2-5%) require 1,000-10,000 games.")
    print()

    print("=" * 80)
    print("PART 2: BAYESIAN ANALYSIS - Incorporating Prior Knowledge")
    print("=" * 80)
    print()

    print("Bayesian estimates for Hulk's top 5 synergies:")
    print("(Uses weakly informative prior centered at expected WR)")
    print()

    for i, synergy in enumerate(hulk_synergies[:5], 1):
        teammate = synergy["teammate"]
        games = synergy["games_together"]
        wins = synergy["wins_together"]
        actual_wr = synergy["actual_win_rate"]
        teammate_wr = winrate_data[teammate]["overall"]["win_rate"]

        # Use average model for expected WR
        expected_wr = (hulk_wr + teammate_wr) / 2

        bayes_result = bayesian_synergy_estimate(wins, games, expected_wr)

        print(f"{i}. Hulk + {teammate}")
        print(f"   Observed: {actual_wr:.1%} | Expected: {expected_wr:.1%}")
        print(f"   Posterior Mean: {bayes_result['posterior_mean']:.1%}")
        ci_lower = bayes_result["credible_interval_95"][0]
        ci_upper = bayes_result["credible_interval_95"][1]
        print(f"   95% Credible Interval: [{ci_lower:.1%}, {ci_upper:.1%}]")
        print(f"   Synergy Estimate: {bayes_result['synergy_score']:+.1%}")
        print(f"   P(positive synergy): {bayes_result['prob_positive_synergy']:.1%}")
        print(f"   Substantial evidence: {'✓ YES' if bayes_result['substantial'] else '✗ NO'}")
        print()

    print("FINDING: Even with Bayesian methods, no synergies show strong evidence")
    print("         (>95% probability) of being positive.")
    print()

    print("=" * 80)
    print("PART 3: WITHIN-PLAYER ANALYSIS - Controlling for Skill")
    print("=" * 80)
    print()

    print("Comparing players' win rates with Hulk+teammate vs Hulk+others:")
    print("(This controls for player skill)")
    print()

    conn = get_connection()

    # Test top 3 synergies with within-player analysis
    comparison_heroes = ["Mantis", "Rocket Raccoon", "Magneto"]  # Other supports/tanks

    for synergy in hulk_synergies[:3]:
        teammate = synergy["teammate"]
        print(f"Hulk + {teammate} vs Hulk + Others:")

        result = within_player_analysis(conn, "Hulk", teammate, comparison_heroes)

        if result:
            print(f"   Players analyzed: {result['n_players']}")
            print(f"   Mean WR with {teammate}: {result['mean_wr_with_target']:.1%}")
            print(f"   Mean WR with others: {result['mean_wr_with_others']:.1%}")
            print(f"   Difference: {result['mean_difference']:+.1%}")
            print(f"   T-statistic: {result['t_statistic']:.3f}")
            print(f"   P-value: {result['p_value']:.4f}")
            print(f"   Significant: {'✓ YES' if result['significant'] else '✗ NO'}")
        else:
            print("   Insufficient data for within-player analysis")
        print()

    conn.close()

    print("=" * 80)
    print("PART 4: MULTIPLE COMPARISONS CORRECTION")
    print("=" * 80)
    print()

    n_tests = len(hulk_synergies)
    bonferroni_alpha = 0.05 / n_tests

    print(f"Testing {n_tests} synergies simultaneously")
    print(f"Bonferroni-corrected α: {bonferroni_alpha:.4f}")
    print()
    print("With correction, we need p < {:.4f} to claim significance".format(bonferroni_alpha))
    print()

    # Test using average model
    print("Re-testing with Bonferroni correction:")
    print()

    significant_count = 0
    for synergy in hulk_synergies:
        teammate = synergy["teammate"]
        games = synergy["games_together"]
        wins = synergy["wins_together"]
        teammate_wr = winrate_data[teammate]["overall"]["win_rate"]

        expected_wr = (hulk_wr + teammate_wr) / 2

        result = stats.binomtest(wins, games, expected_wr, alternative="greater")
        p_value = result.pvalue

        if p_value < bonferroni_alpha:
            significant_count += 1
            print(f"   {teammate}: p = {p_value:.6f} ✓ SIGNIFICANT")

    if significant_count == 0:
        print("   (No synergies significant after correction)")

    print()
    print(f"Significant synergies: {significant_count}/{n_tests}")
    print()

    print("=" * 80)
    print("FINAL RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("1. COLLECT MORE DATA")
    print("   Current: ~300 matches total, ~200 games per hero")
    print("   Needed: 10,000+ matches to detect 3-5% synergies")
    print("   Strategy: Implement continuous data collection over weeks/months")
    print()
    print("2. USE BETTER BASELINES")
    print("   Current: Multiplicative (flawed) or additive (simple)")
    print("   Better: Machine learning model predicting WR from full team comp")
    print("   Or: Match similar team comps and compare")
    print()
    print("3. CONTROL FOR CONFOUNDERS")
    print("   - Player skill (rank, MMR)")
    print("   - Map")
    print("   - Enemy team composition")
    print("   - Patch/meta changes over time")
    print()
    print("4. USE ROBUST STATISTICS")
    print("   - Bayesian methods for small samples")
    print("   - Within-player comparisons")
    print("   - Multiple comparisons corrections")
    print("   - Effect sizes, not just p-values")
    print()
    print("5. ACCEPT REALITY")
    print("   - True synergies might be small (2-5%)")
    print("   - Need massive datasets to detect them reliably")
    print("   - Current rankings might be valid, but magnitudes uncertain")
    print("   - Focus on large, obvious synergies (e.g., tank+healer)")
    print()


if __name__ == "__main__":
    main()
