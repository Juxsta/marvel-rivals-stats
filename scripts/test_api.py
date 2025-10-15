#!/usr/bin/env python3
"""Test script to verify API client initialization.

This script initializes the MarvelRivalsClient and verifies configuration.
Actual API calls will be implemented in Phase 1 (data collection).
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api import MarvelRivalsClient


def main() -> None:
    """Initialize and test API client configuration."""
    load_dotenv()

    api_key = os.getenv("MARVEL_RIVALS_API_KEY")
    if not api_key:
        print("❌ Error: MARVEL_RIVALS_API_KEY not set in .env file")
        print("📝 Copy .env.example to .env and add your API key")
        sys.exit(1)

    rate_limit = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "7"))

    print("🔌 Initializing Marvel Rivals API client...")
    try:
        client = MarvelRivalsClient(api_key=api_key, requests_per_minute=rate_limit)
        print("✅ API client initialized successfully")
        print("\n📊 Configuration:")
        print(f"   Rate limit: {rate_limit} requests/minute")
        print(f"   Min delay: {client.rate_limiter.get_delay():.2f}s between requests")
        print(f"   API Key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
        print("\n📝 Note: Actual API calls will be implemented in Phase 1")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
