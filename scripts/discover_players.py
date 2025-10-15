#!/usr/bin/env python3
"""Player Discovery CLI Script.

Discovers and samples players from Marvel Rivals API leaderboards using stratified sampling.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.api.client import APIException, MarvelRivalsClient
from src.collectors.player_discovery import DEFAULT_RANK_QUOTAS, discover_players
from src.db.connection import get_connection

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for player discovery script."""
    parser = argparse.ArgumentParser(
        description="Discover players from Marvel Rivals leaderboards using stratified sampling"
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=500,
        help="Target number of players to discover (default: 500)",
    )
    parser.add_argument(
        "--quotas-json",
        type=str,
        help="JSON string with custom rank quotas (e.g., '{\"Gold\": 150}')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview discovery without inserting into database",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Player Discovery Script")
    print("=" * 60)
    print(f"Target count: {args.target_count}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Parse custom quotas if provided
    quotas = DEFAULT_RANK_QUOTAS
    if args.quotas_json:
        try:
            custom_quotas = json.loads(args.quotas_json)
            quotas.update(custom_quotas)
            print(f"Using custom quotas: {custom_quotas}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --quotas-json: {e}")
            sys.exit(1)

    print(f"Rank quotas: {quotas}")
    print()

    if args.dry_run:
        print("DRY RUN MODE - No database changes will be made")
        print()

    try:
        # Initialize API client
        logger.info("Initializing Marvel Rivals API client")
        api_client = MarvelRivalsClient()
        print("✓ API client initialized")

        # Get database connection
        if not args.dry_run:
            logger.info("Connecting to database")
            db_conn = get_connection()
            print("✓ Database connection established")
        else:
            db_conn = None
            print("✓ Database connection skipped (dry run)")

        print()
        print("Starting player discovery...")
        print("-" * 60)

        if args.dry_run:
            print("Note: Dry run mode - simulating discovery process")
            print("In production, this would:")
            print("  1. Fetch players from API leaderboards")
            print("  2. Apply stratified sampling by rank")
            print("  3. Deduplicate against database")
            print("  4. Insert new players")
            print("  5. Update collection metadata")
            print()
            print("To run for real, omit the --dry-run flag")
        else:
            # Run discovery
            stats = discover_players(
                api_client=api_client,
                db_conn=db_conn,
                target_count=args.target_count,
                quotas=quotas,
            )

            # Print results
            print()
            print("=" * 60)
            print("Discovery Complete!")
            print("=" * 60)
            print(f"Total players fetched from API: {stats['total_fetched']}")
            print(f"Unique players after deduplication: {stats['unique_fetched']}")
            print(f"Players after stratified sampling: {stats['sampled']}")
            print(f"New players added to database: {stats['new_players']}")
            print(f"Existing players (skipped): {stats['existing_players']}")
            print(f"Total inserted/updated: {stats['inserted']}")
            print()
            print("Players by rank:")
            for rank, count in sorted(stats["by_rank"].items()):
                print(f"  {rank:15s}: {count:3d}")
            print()

    except ValueError as e:
        print(f"Error: {e}")
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except APIException as e:
        print(f"API Error: {e}")
        logger.error(f"API error during discovery: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.exception("Unexpected error during player discovery")
        sys.exit(1)
    finally:
        # Clean up database connection
        if db_conn:
            db_conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    main()
