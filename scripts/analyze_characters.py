#!/usr/bin/env python3
"""Character Analysis CLI Script.

Analyzes character win rates across rank tiers with Wilson confidence intervals.
Exports results to JSON and caches in database.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.analyzers.character_winrate import analyze_character_win_rates, export_to_json
from src.db.connection import close_pool, get_connection

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for character analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze character win rates with Wilson confidence intervals"
    )
    parser.add_argument(
        "--min-games-per-rank",
        type=int,
        default=30,
        help="Minimum games required per rank tier (default: 30)",
    )
    parser.add_argument(
        "--min-games-overall",
        type=int,
        default=100,
        help="Minimum total games required for overall stats (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/character_win_rates.json",
        help="Output file path for JSON export (default: output/character_win_rates.json)",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip JSON export (only cache in database)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Character Win Rate Analysis")
    logger.info("=" * 60)
    logger.info(f"Min games per rank: {args.min_games_per_rank}")
    logger.info(f"Min games overall: {args.min_games_overall}")
    if not args.no_export:
        logger.info(f"Output file: {args.output}")
    logger.info("=" * 60)

    try:
        # Get database connection
        conn = get_connection()
        logger.info("Database connection established")

        # Run analysis
        results = analyze_character_win_rates(
            conn=conn,
            min_games_per_rank=args.min_games_per_rank,
            min_games_overall=args.min_games_overall,
        )

        if not results:
            logger.warning("No heroes met minimum sample size requirements")
            return

        # Export to JSON
        if not args.no_export:
            # Ensure output directory exists
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            export_to_json(results, str(output_path))
            logger.info(f"Successfully exported {len(results)} heroes to {args.output}")

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("ANALYSIS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total heroes analyzed: {len(results)}")

        # Find top 5 heroes by win rate
        sorted_heroes = sorted(
            results.items(), key=lambda x: x[1]["overall"]["win_rate"], reverse=True
        )

        logger.info("\nTop 5 Heroes by Win Rate:")
        for i, (hero, data) in enumerate(sorted_heroes[:5], 1):
            overall = data["overall"]
            ci = overall["confidence_interval_95"]
            logger.info(
                f"  {i}. {hero}: {overall['win_rate']:.1%} "
                f"({overall['total_games']} games, 95% CI: [{ci[0]:.1%}, {ci[1]:.1%}])"
            )

        logger.info("\nBottom 5 Heroes by Win Rate:")
        for i, (hero, data) in enumerate(sorted_heroes[-5:][::-1], 1):
            overall = data["overall"]
            ci = overall["confidence_interval_95"]
            logger.info(
                f"  {i}. {hero}: {overall['win_rate']:.1%} "
                f"({overall['total_games']} games, 95% CI: [{ci[0]:.1%}, {ci[1]:.1%}])"
            )

        logger.info("=" * 60)
        logger.info("Analysis complete!")

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        close_pool()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()
