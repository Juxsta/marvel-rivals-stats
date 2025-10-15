#!/usr/bin/env python3
"""Match Collection CLI Script.

Collects match histories for discovered players with rate limiting and deduplication.
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.api.client import APIException, MarvelRivalsClient
from src.collectors.match_collector import collect_matches
from src.db.connection import get_connection

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\n\nShutdown requested (Ctrl+C)...")
    print("Finishing current player and saving progress...")
    shutdown_requested = True


def main():
    """Main entry point for match collection script."""
    parser = argparse.ArgumentParser(
        description="Collect match histories from Marvel Rivals API with rate limiting"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Maximum number of players to process in this run (default: 100)",
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=8.6,
        help="Seconds to wait between API requests (default: 8.6 = 7 req/min)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview collection without inserting into database",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Match Collection Script")
    print("=" * 60)
    print(f"Batch size: {args.batch_size} players")
    print(f"Rate limit delay: {args.rate_limit_delay}s between requests")
    print(f"Dry run: {args.dry_run}")
    print()

    # Calculate estimated time
    estimated_minutes = (args.batch_size * args.rate_limit_delay) / 60
    print(f"Estimated time: ~{estimated_minutes:.1f} minutes for {args.batch_size} players")
    print()

    if args.dry_run:
        print("DRY RUN MODE - No database changes will be made")
        print()

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    db_conn = None

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
        print("Starting match collection...")
        print("-" * 60)

        if args.dry_run:
            print("Note: Dry run mode - simulating collection process")
            print("In production, this would:")
            print("  1. Load pending players from database")
            print("  2. Fetch match history for each player (100-150 matches)")
            print("  3. Filter for competitive matches in current season")
            print("  4. Deduplicate matches by match_id")
            print("  5. Insert match metadata + all 12 participants")
            print("  6. Mark players as collected")
            print("  7. Enforce rate limiting (8.6s between requests)")
            print()
            print("To run for real, omit the --dry-run flag")
            return

        # Run collection
        stats = collect_matches(
            api_client=api_client,
            db_conn=db_conn,
            batch_size=args.batch_size,
            rate_limit_delay=args.rate_limit_delay,
        )

        # Print results
        print()
        print("=" * 60)
        print("Collection Complete!")
        print("=" * 60)
        print(f"Players processed: {stats['players_processed']}")
        print(f"Matches collected: {stats['matches_collected']} (new)")
        print(f"Matches skipped: {stats['matches_skipped']} (duplicates)")
        print(f"Participants inserted: {stats['participants_inserted']}")
        print(f"API errors: {stats['api_errors']}")
        print()

        if stats["matches_collected"] > 0:
            avg_participants = stats["participants_inserted"] / stats["matches_collected"]
            print(f"Average participants per match: {avg_participants:.1f} (expected: 12)")
            print()

        # Summary statistics
        if stats["players_processed"] > 0:
            avg_matches = stats["matches_collected"] / stats["players_processed"]
            print(f"Average new matches per player: {avg_matches:.1f}")
            print()

        print("Collection progress saved. Run again to continue with next batch.")

    except ValueError as e:
        print(f"Error: {e}")
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except APIException as e:
        print(f"API Error: {e}")
        logger.error(f"API error during collection: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nShutdown interrupted. Partial progress may be saved.")
        logger.warning("Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.exception("Unexpected error during match collection")
        sys.exit(1)
    finally:
        # Clean up database connection
        if db_conn:
            try:
                db_conn.commit()  # Ensure any pending transactions are committed
                db_conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")


if __name__ == "__main__":
    main()
