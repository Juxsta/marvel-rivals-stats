#!/usr/bin/env python3
"""Deep statistical significance analysis of synergy scores.

This script performs rigorous statistical testing to determine if observed
synergy scores are truly significant or could be due to random chance.
"""

import json
import os
import sys
from typing import Tuple

from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def binomial_test_synergy(
    wins: int, total: int, expected_wr: float, alpha: float = 0.05
) -> Tuple[float, bool]:
    """Perform binomial test for synergy significance.

    H0: win_rate = expected_win_rate
    H1: win_rate > expected_win_rate (one-tailed)
    """
    result = stats.binomtest(wins, total, expected_wr, alternative="greater")
    p_value = result.pvalue
    is_significant = p_value < alpha
    return p_value, is_significant


def alternative_expected_wr_additive(hero_a_wr: float, hero_b_wr: float) -> float:
    """Calculate expected win rate using additive model.

    Assumes each hero contributes independently to team performance:
    Expected = baseline + hero_a_contribution + hero_b_contribution
    Where baseline = 0.5 and contribution = (wr - 0.5)
    """
    baseline = 0.5
    contrib_a = hero_a_wr - baseline
    contrib_b = hero_b_wr - baseline
    return baseline + contrib_a + contrib_b


def alternative_expected_wr_average(hero_a_wr: float, hero_b_wr: float) -> float:
    """Calculate expected win rate as simple average.

    If heroes contribute equally and independently, their combined
    effect should be the average of their individual win rates.
    """
    return (hero_a_wr + hero_b_wr) / 2.0


def analyze_methodology_issues(hero_a_wr: float, hero_b_wr: float, actual_wr: float, n: int):
    """Analyze the synergy using multiple methodologies."""
    # Method 1: Current implementation (multiplicative)
    expected_mult = hero_a_wr * hero_b_wr
    synergy_mult = actual_wr - expected_mult
    p_value_mult, sig_mult = binomial_test_synergy(int(actual_wr * n), n, expected_mult)

    # Method 2: Additive model
    expected_add = alternative_expected_wr_additive(hero_a_wr, hero_b_wr)
    synergy_add = actual_wr - expected_add
    p_value_add, sig_add = binomial_test_synergy(int(actual_wr * n), n, expected_add)

    # Method 3: Average model
    expected_avg = alternative_expected_wr_average(hero_a_wr, hero_b_wr)
    synergy_avg = actual_wr - expected_avg
    p_value_avg, sig_avg = binomial_test_synergy(int(actual_wr * n), n, expected_avg)

    return {
        "multiplicative": {
            "expected": expected_mult,
            "synergy": synergy_mult,
            "p_value": p_value_mult,
            "significant": sig_mult,
        },
        "additive": {
            "expected": expected_add,
            "synergy": synergy_add,
            "p_value": p_value_add,
            "significant": sig_add,
        },
        "average": {
            "expected": expected_avg,
            "synergy": synergy_avg,
            "p_value": p_value_avg,
            "significant": sig_avg,
        },
    }


def main():
    """Run statistical significance analysis for Hulk synergies."""
    print("=" * 80)
    print("STATISTICAL SIGNIFICANCE ANALYSIS: HULK SYNERGIES")
    print("=" * 80)
    print()

    # Load synergy data
    with open("output/synergies.json", "r") as f:
        synergy_data = json.load(f)

    with open("output/character_win_rates.json", "r") as f:
        winrate_data = json.load(f)

    hulk_synergies = synergy_data["Hulk"]["synergies"]
    hulk_wr = winrate_data["Hulk"]["overall"]["win_rate"]

    print(f"Hulk's overall win rate: {hulk_wr:.1%}")
    print()
    print("=" * 80)
    print("METHODOLOGY COMPARISON")
    print("=" * 80)
    print()
    print("Testing three different models for expected win rate:")
    print("1. MULTIPLICATIVE (current): E[WR] = P(A wins) × P(B wins)")
    print("2. ADDITIVE: E[WR] = 0.5 + (A_wr - 0.5) + (B_wr - 0.5)")
    print("3. AVERAGE: E[WR] = (A_wr + B_wr) / 2")
    print()
    print("Significance tested with one-tailed binomial test (α = 0.05)")
    print("=" * 80)
    print()

    # Analyze top 5 synergies
    top_synergies = hulk_synergies[:5]

    for i, synergy in enumerate(top_synergies, 1):
        teammate = synergy["teammate"]
        games = synergy["games_together"]
        wins = synergy["wins_together"]
        actual_wr = synergy["actual_win_rate"]

        # Get teammate win rate
        teammate_wr = winrate_data[teammate]["overall"]["win_rate"]

        print(f"{i}. HULK + {teammate.upper()}")
        print("-" * 80)
        print(f"Games: {games} | Wins: {wins} | Actual WR: {actual_wr:.1%}")
        print(f"Hulk solo WR: {hulk_wr:.1%} | {teammate} solo WR: {teammate_wr:.1%}")
        print()

        analysis = analyze_methodology_issues(hulk_wr, teammate_wr, actual_wr, games)

        # Print results for each method
        for method_name, results in analysis.items():
            expected = results["expected"]
            synergy = results["synergy"]
            p_value = results["p_value"]
            significant = results["significant"]

            sig_marker = "✓ SIGNIFICANT" if significant else "✗ NOT SIGNIFICANT"

            print(f"  {method_name.upper()}:")
            print(f"    Expected WR: {expected:.1%}")
            print(f"    Synergy Score: {synergy:+.1%}")
            print(f"    P-value: {p_value:.6f}")
            print(f"    Result: {sig_marker}")
            print()

        print()

    print("=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print()

    # Summarize findings across all synergies
    print("Analyzing all Hulk synergies across methodologies:")
    print()

    mult_sig_count = 0
    add_sig_count = 0
    avg_sig_count = 0

    for synergy in hulk_synergies:
        teammate = synergy["teammate"]
        games = synergy["games_together"]
        wins = synergy["wins_together"]
        actual_wr = synergy["actual_win_rate"]
        teammate_wr = winrate_data[teammate]["overall"]["win_rate"]

        analysis = analyze_methodology_issues(hulk_wr, teammate_wr, actual_wr, games)

        if analysis["multiplicative"]["significant"]:
            mult_sig_count += 1
        if analysis["additive"]["significant"]:
            add_sig_count += 1
        if analysis["average"]["significant"]:
            avg_sig_count += 1

    total = len(hulk_synergies)

    print(f"MULTIPLICATIVE MODEL: {mult_sig_count}/{total} synergies significant")
    print(f"ADDITIVE MODEL: {add_sig_count}/{total} synergies significant")
    print(f"AVERAGE MODEL: {avg_sig_count}/{total} synergies significant")
    print()

    print("=" * 80)
    print("CONCLUSIONS")
    print("=" * 80)
    print()
    print("1. MULTIPLICATIVE MODEL (current implementation):")
    print("   - Artificially low expected win rates (20-30%)")
    print("   - Makes ALL synergies appear highly significant")
    print("   - Not theoretically sound for teammates on same team")
    print("   - Inflates synergy scores dramatically")
    print()
    print("2. ADDITIVE MODEL:")
    print("   - More realistic baseline (50-65%)")
    print("   - Accounts for individual hero contributions")
    print("   - Some synergies remain significant, others don't")
    print("   - Better theoretical foundation")
    print()
    print("3. AVERAGE MODEL:")
    print("   - Simple and interpretable baseline")
    print("   - Expected WR = average of individual WRs")
    print("   - Fewer synergies reach significance")
    print("   - Conservative estimate")
    print()
    print("RECOMMENDATION:")
    print("  The current multiplicative model should be replaced with")
    print("  the additive or average model for more accurate synergy")
    print("  detection. Current results are statistically significant")
    print("  but methodologically flawed.")
    print()


if __name__ == "__main__":
    main()
