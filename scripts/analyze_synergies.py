#!/usr/bin/env python3
"""CLI script for analyzing teammate synergies in Marvel Rivals.

This script analyzes hero pairings to identify positive/negative synergies
compared to expected win rates based on individual hero performance.

Uses statistically rigorous methodology with average baseline model,
Wilson confidence intervals, significance testing, and Bonferroni correction.

Usage:
    # Run with defaults
    python scripts/analyze_synergies.py

    # Use average baseline (default)
    python scripts/analyze_synergies.py --baseline average

    # More conservative significance threshold
    python scripts/analyze_synergies.py --alpha 0.01

    # Only report pairs with 100+ games
    python scripts/analyze_synergies.py --min-sample-size 100

    # Custom output and no export
    python scripts/analyze_synergies.py --output output/synergies.json
    python scripts/analyze_synergies.py --no-export  # Database only
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analyzers.teammate_synergy import (  # noqa: E402
    MIN_GAMES_TOGETHER,
    analyze_teammate_synergies,
    export_to_json,
)
from src.db.connection import get_connection  # noqa: E402
from src.utils.statistics import calculate_required_sample_size  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze teammate synergies for Marvel Rivals heroes with statistical rigor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with defaults (average baseline, min 50 games, export to JSON)
  python scripts/analyze_synergies.py

  # Use average baseline (default)
  python scripts/analyze_synergies.py --baseline average

  # Use additive baseline model
  python scripts/analyze_synergies.py --baseline additive

  # More conservative significance threshold (1% instead of 5%)
  python scripts/analyze_synergies.py --alpha 0.01

  # Only report pairs with 100+ games
  python scripts/analyze_synergies.py --min-sample-size 100

  # Database caching only (no JSON export)
  python scripts/analyze_synergies.py --no-export

  # Custom output path
  python scripts/analyze_synergies.py --output my_synergies.json

  # Combine options
  python scripts/analyze_synergies.py --baseline average --alpha 0.01 --min-sample-size 100
        """,
    )

    parser.add_argument(
        "--baseline",
        type=str,
        choices=["average", "additive"],
        default="average",
        help="Baseline model for expected win rate (default: average)",
    )

    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for hypothesis tests (default: 0.05, valid range: 0.001-0.10)",
    )

    parser.add_argument(
        "--min-sample-size",
        type=int,
        default=MIN_GAMES_TOGETHER,
        help=f"Minimum games to report a synergy (default: {MIN_GAMES_TOGETHER})",
    )

    parser.add_argument(
        "--min-games",
        type=int,
        default=None,
        help="(Deprecated: use --min-sample-size) Minimum games together to report synergy",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/synergies.json",
        help="Output JSON file path (default: output/synergies.json)",
    )

    parser.add_argument(
        "--no-export", action="store_true", help="Skip JSON export (database caching only)"
    )

    parser.add_argument(
        "--rank-tier",
        type=str,
        default=None,
        help="Analyze specific rank tier (default: all ranks)",
    )

    return parser.parse_args()


def validate_args(args):
    """Validate command-line arguments.

    Args:
        args: Parsed arguments object

    Raises:
        ValueError: If arguments are invalid
    """
    # Validate alpha range
    if not 0.001 <= args.alpha <= 0.10:
        raise ValueError(f"Alpha must be between 0.001 and 0.10, got {args.alpha}")

    # Handle deprecated --min-games flag
    if args.min_games is not None:
        logger.warning("Warning: --min-games is deprecated, use --min-sample-size instead")
        args.min_sample_size = args.min_games

    # Validate min_sample_size is positive
    if args.min_sample_size < 1:
        raise ValueError(f"Minimum sample size must be at least 1, got {args.min_sample_size}")


def print_summary(results: dict, alpha: float):
    """Print summary of synergy analysis results with statistical significance.

    Args:
        results: Synergy analysis results dictionary
        alpha: Significance level used for testing
    """
    if not results:
        logger.warning("No results to display")
        return

    logger.info("\n" + "=" * 80)
    logger.info("SYNERGY ANALYSIS SUMMARY")
    logger.info("=" * 80)

    # Count total heroes with synergies
    total_heroes = len(results)
    logger.info(f"\nTotal heroes analyzed: {total_heroes}")

    # Collect all synergies for statistical summary
    all_synergies = []
    for hero, data in results.items():
        for synergy in data["synergies"]:
            all_synergies.append(
                {
                    "hero": hero,
                    "teammate": synergy["teammate"],
                    "synergy_score": synergy["synergy_score"],
                    "games": synergy["games_together"],
                    "actual_wr": synergy["actual_win_rate"],
                    "expected_wr": synergy["expected_win_rate"],
                    "ci_lower": synergy["confidence_interval_95"][0],
                    "ci_upper": synergy["confidence_interval_95"][1],
                    "p_value": synergy["p_value"],
                    "significant": synergy["significant"],
                    "significant_bonferroni": synergy["significant_bonferroni"],
                    "bonferroni_alpha": synergy.get("bonferroni_alpha", 0.0),
                    "confidence_level": synergy["confidence_level"],
                    "warning": synergy["sample_size_warning"],
                }
            )

    if not all_synergies:
        logger.info("\nNo synergies found (check minimum games threshold)")
        return

    # Statistical Significance Summary
    logger.info("\n" + "-" * 80)
    logger.info("STATISTICAL SIGNIFICANCE SUMMARY")
    logger.info("-" * 80)

    n_total = len(all_synergies)
    n_significant = sum(1 for s in all_synergies if s["significant"])
    n_significant_bonf = sum(1 for s in all_synergies if s["significant_bonferroni"])

    # Get bonferroni alpha (should be same for all)
    bonf_alpha = all_synergies[0]["bonferroni_alpha"] if all_synergies else 0.0

    logger.info(f"Total synergies tested: {n_total}")
    logger.info(
        f"Significant (uncorrected α={alpha:.3f}): "
        f"{n_significant}/{n_total} ({n_significant/n_total*100:.1f}%)"
    )
    logger.info(
        f"Significant (Bonferroni α={bonf_alpha:.6f}): "
        f"{n_significant_bonf}/{n_total} ({n_significant_bonf/n_total*100:.1f}%)"
    )

    if n_significant_bonf > 0:
        logger.info(
            f"\nNote: {n_significant_bonf} synergies marked with (*) are "
            f"statistically significant after Bonferroni correction"
        )
    else:
        logger.info(
            "\nNote: No synergies reached statistical significance after Bonferroni correction"
        )
        logger.info(
            "      This suggests current sample sizes are insufficient for reliable detection."
        )

    # Sample size distribution
    n_low = sum(1 for s in all_synergies if s["confidence_level"] == "low")
    n_medium = sum(1 for s in all_synergies if s["confidence_level"] == "medium")
    n_high = sum(1 for s in all_synergies if s["confidence_level"] == "high")

    logger.info("\nSample Size Distribution:")
    logger.info(f"  High confidence (≥500 games): {n_high}/{n_total}")
    logger.info(f"  Medium confidence (100-499 games): {n_medium}/{n_total}")
    logger.info(f"  Low confidence (<100 games): {n_low}/{n_total}")

    # Sort by synergy score
    all_synergies.sort(key=lambda x: x["synergy_score"], reverse=True)

    logger.info("\n" + "-" * 80)
    logger.info("TOP 5 STRONGEST SYNERGIES (Overall)")
    logger.info("-" * 80)
    for i, synergy in enumerate(all_synergies[:5], 1):
        bonf_marker = "*" if synergy["significant_bonferroni"] else " "
        ci_str = f"[CI: {synergy['ci_lower']:.1%}-{synergy['ci_upper']:.1%}]"
        warning_str = f" ⚠ {synergy['confidence_level'].upper()}" if synergy["warning"] else ""

        logger.info(
            f"{i}.{bonf_marker} {synergy['hero']} + {synergy['teammate']}: "
            f"+{synergy['synergy_score']:.4f} "
            f"({synergy['actual_wr']:.2%} vs {synergy['expected_wr']:.2%}, "
            f"{synergy['games']} games) {ci_str}{warning_str}"
        )

    logger.info("\n" + "-" * 80)
    logger.info("TOP 5 WEAKEST SYNERGIES (Anti-Synergies)")
    logger.info("-" * 80)
    for i, synergy in enumerate(all_synergies[-5:][::-1], 1):
        bonf_marker = "*" if synergy["significant_bonferroni"] else " "
        ci_str = f"[CI: {synergy['ci_lower']:.1%}-{synergy['ci_upper']:.1%}]"
        warning_str = f" ⚠ {synergy['confidence_level'].upper()}" if synergy["warning"] else ""

        logger.info(
            f"{i}.{bonf_marker} {synergy['hero']} + {synergy['teammate']}: "
            f"{synergy['synergy_score']:.4f} "
            f"({synergy['actual_wr']:.2%} vs {synergy['expected_wr']:.2%}, "
            f"{synergy['games']} games) {ci_str}{warning_str}"
        )

    # Show sample hero synergies
    sample_heroes = list(results.keys())[:3]
    logger.info("\n" + "-" * 80)
    logger.info("SAMPLE HERO SYNERGIES")
    logger.info("-" * 80)
    for hero in sample_heroes:
        data = results[hero]
        if data["synergies"]:
            top_synergy = data["synergies"][0]
            bonf_marker = "*" if top_synergy.get("significant_bonferroni", False) else " "
            ci_lower = top_synergy["confidence_interval_95"][0]
            ci_upper = top_synergy["confidence_interval_95"][1]
            ci_str = f"[CI: {ci_lower:.1%}-{ci_upper:.1%}]"

            logger.info(
                f"\n{hero}:"
                f"\n  Best:{bonf_marker} {top_synergy['teammate']} "
                f"({top_synergy['synergy_score']:+.4f}, "
                f"{top_synergy['games_together']} games) {ci_str}"
            )

            if len(data["synergies"]) > 1:
                worst_synergy = data["synergies"][-1]
                bonf_marker = "*" if worst_synergy.get("significant_bonferroni", False) else " "
                ci_lower = worst_synergy["confidence_interval_95"][0]
                ci_upper = worst_synergy["confidence_interval_95"][1]
                ci_str = f"[CI: {ci_lower:.1%}-{ci_upper:.1%}]"

                logger.info(
                    f"  Worst:{bonf_marker} {worst_synergy['teammate']} "
                    f"({worst_synergy['synergy_score']:+.4f}, "
                    f"{worst_synergy['games_together']} games) {ci_str}"
                )

    # Power Analysis Section
    logger.info("\n" + "=" * 80)
    logger.info("POWER ANALYSIS: SAMPLE SIZE REQUIREMENTS")
    logger.info("=" * 80)
    logger.info("\nTo detect synergies with 80% statistical power at α=0.05:")

    # Calculate for common baseline (0.5) and different effect sizes
    baseline = 0.5
    effect_sizes = [(0.03, "3%"), (0.05, "5%"), (0.10, "10%")]

    logger.info("")
    for effect, label in effect_sizes:
        required = calculate_required_sample_size(baseline, effect, alpha=0.05, power=0.80)
        logger.info(f"  {label} synergy effect: ~{required:,} games required")

    # Show current max sample size
    max_games = max(s["games"] for s in all_synergies)
    logger.info(f"\nCurrent maximum sample size: {max_games} games")

    # Interpretation
    logger.info("\nInterpretation:")
    if max_games < 500:
        logger.info("  ⚠ Current data is insufficient for detecting realistic (3-7%) synergies.")
        logger.info("     Most hero pairs need 500-2,000 games for reliable statistical detection.")
        logger.info("     Rankings are still useful, but effect sizes may be unreliable.")
    elif max_games < 1000:
        logger.info("  ⚠ Current data can detect medium (5-10%) synergies for some pairs.")
        logger.info("     Small (3-5%) synergies still require more games for reliable detection.")
    else:
        logger.info("  ✓ Current data is sufficient for detecting moderate (5%+) synergies.")
        logger.info("     Small (3%) synergies may still require additional games.")

    logger.info("\n" + "=" * 80)


def main():
    """Main execution function."""
    args = parse_args()

    # Validate arguments
    try:
        validate_args(args)
    except ValueError as e:
        logger.error(f"Invalid arguments: {e}")
        sys.exit(1)

    logger.info("Marvel Rivals - Teammate Synergy Analysis")
    logger.info("=" * 80)
    logger.info(f"Baseline model: {args.baseline}")
    logger.info(f"Significance level (alpha): {args.alpha}")
    logger.info(f"Minimum sample size: {args.min_sample_size} games")
    logger.info(f"Rank tier: {args.rank_tier if args.rank_tier else 'All ranks'}")
    logger.info(f"Export enabled: {not args.no_export}")
    if not args.no_export:
        logger.info(f"Output path: {args.output}")
    logger.info("=" * 80)

    try:
        # Get database connection
        logger.info("Connecting to database...")
        conn = get_connection()

        # Run synergy analysis
        logger.info("Starting synergy analysis...")
        results = analyze_teammate_synergies(
            conn=conn,
            min_games_together=args.min_sample_size,
            rank_tier=args.rank_tier,
            alpha=args.alpha,
        )

        if not results:
            logger.error("No synergies found. Ensure character analysis has been run first.")
            sys.exit(1)

        # Export to JSON
        if not args.no_export:
            # Ensure output directory exists
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Exporting results to {args.output}...")
            export_to_json(results, str(output_path))

        # Print summary
        print_summary(results, args.alpha)

        # Close connection
        conn.close()
        logger.info("\nAnalysis complete!")

    except Exception as e:
        logger.error(f"Error during synergy analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
