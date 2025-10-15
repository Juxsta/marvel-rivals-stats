"""Match collection module for fetching player match histories.

This module implements match collection with rate limiting, deduplication,
and extraction of all 12 participants per match.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List

from psycopg2.extensions import connection as PgConnection

from ..api.client import APIException, MarvelRivalsClient

# Configure logging
logger = logging.getLogger(__name__)

# Current season for filtering
CURRENT_SEASON = 1


def fetch_player_matches(
    api_client: MarvelRivalsClient, username: str, limit: int = 150
) -> List[Dict]:
    """Fetch match history for a single player from API.

    Args:
        api_client: MarvelRivalsClient instance
        username: Player username to fetch matches for
        limit: Maximum number of matches to retrieve

    Returns:
        List of match dictionaries (empty list on error)
    """
    try:
        logger.debug(f"Fetching matches for {username} (limit={limit})")
        matches = api_client.get_player_matches(username=username, limit=limit)
        logger.info(f"Fetched {len(matches)} matches for {username}")
        return matches
    except APIException as e:
        logger.error(f"API error fetching matches for {username}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching matches for {username}: {e}")
        return []


def filter_competitive_matches(
    matches: List[Dict], current_season: int = CURRENT_SEASON
) -> List[Dict]:
    """Filter matches by season and game mode.

    Args:
        matches: List of match dictionaries
        current_season: Current season number to filter by

    Returns:
        Filtered list containing only competitive matches from current season
    """
    filtered = [
        m for m in matches if m.get("mode") == "competitive" and m.get("season") == current_season
    ]
    logger.debug(
        f"Filtered {len(matches)} -> {len(filtered)} competitive season {current_season} matches"
    )
    return filtered


def match_exists(conn: PgConnection, match_id: str) -> bool:
    """Check if match already exists in database.

    Args:
        conn: Database connection
        match_id: Match ID to check

    Returns:
        True if match exists, False otherwise
    """
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM matches WHERE match_id = %s", (match_id,))
        result = cursor.fetchone()
        return result is not None


def insert_match(conn: PgConnection, match: Dict) -> bool:
    """Insert match metadata into matches table.

    Args:
        conn: Database connection
        match: Match dictionary with metadata

    Returns:
        True if inserted, False if skipped (already exists)
    """
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                """
                INSERT INTO matches (match_id, mode, season, match_timestamp)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (match_id) DO NOTHING
                """,
                (match["match_id"], match.get("mode"), match.get("season"), match.get("timestamp")),
            )
            inserted = cursor.rowcount > 0
            conn.commit()
            return inserted
        except Exception as e:
            logger.error(f"Failed to insert match {match['match_id']}: {e}")
            conn.rollback()
            return False


def extract_participants(match_id: str, match: Dict) -> List[Dict]:
    """Extract all 12 participants from match data.

    Args:
        match_id: Match ID
        match: Match dictionary containing teams and players

    Returns:
        List of participant dictionaries ready for database insertion
    """
    participants = []

    for team_data in match.get("teams", []):
        team_num = team_data.get("team", 0)
        won = team_data.get("won", False)

        for player_data in team_data.get("players", []):
            participant = {
                "match_id": match_id,
                "username": player_data["username"],
                "hero_id": player_data.get("hero_id"),
                "hero_name": player_data["hero_name"],
                "role": player_data.get("role", "").lower(),  # Normalize to lowercase
                "team": team_num,
                "won": won,
                "kills": player_data.get("kills", 0),
                "deaths": player_data.get("deaths", 0),
                "assists": player_data.get("assists", 0),
                "damage": player_data.get("damage", 0),
                "healing": player_data.get("healing", 0),
            }
            participants.append(participant)

    logger.debug(f"Extracted {len(participants)} participants from match {match_id}")
    return participants


def insert_match_participants(conn: PgConnection, participants: List[Dict]) -> int:
    """Insert match participants into database.

    Args:
        conn: Database connection
        participants: List of participant dictionaries

    Returns:
        Number of participants inserted
    """
    if not participants:
        return 0

    with conn.cursor() as cursor:
        try:
            # Prepare data for batch insert
            participant_data = [
                (
                    p["match_id"],
                    p["username"],
                    p["hero_id"],
                    p["hero_name"],
                    p["role"],
                    p["team"],
                    p["won"],
                    p["kills"],
                    p["deaths"],
                    p["assists"],
                    p["damage"],
                    p["healing"],
                )
                for p in participants
            ]

            # Batch insert with executemany
            cursor.executemany(
                """
                INSERT INTO match_participants
                (match_id, username, hero_id, hero_name, role, team, won,
                 kills, deaths, assists, damage, healing)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id, username) DO NOTHING
                """,
                participant_data,
            )

            inserted_count = cursor.rowcount
            conn.commit()

            logger.debug(f"Inserted {inserted_count} participants")
            return inserted_count

        except Exception as e:
            logger.error(f"Failed to insert participants: {e}")
            conn.rollback()
            return 0


def get_pending_players(conn: PgConnection, batch_size: int = 100) -> List[str]:
    """Get list of players who haven't had their match history fetched.

    Args:
        conn: Database connection
        batch_size: Maximum number of players to return

    Returns:
        List of player usernames
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT username FROM players
            WHERE match_history_fetched = FALSE
            ORDER BY discovered_at
            LIMIT %s
            """,
            (batch_size,),
        )
        rows = cursor.fetchall()
        usernames = [row[0] for row in rows]
        logger.info(f"Found {len(usernames)} pending players")
        return usernames


def mark_player_collected(conn: PgConnection, username: str) -> None:
    """Mark a player as having their match history collected.

    Args:
        conn: Database connection
        username: Player username
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE players
            SET match_history_fetched = TRUE, last_updated = NOW()
            WHERE username = %s
            """,
            (username,),
        )
        conn.commit()
        logger.debug(f"Marked {username} as collected")


def update_collection_metadata(conn: PgConnection, stats: Dict) -> None:
    """Update collection metadata to track progress.

    Args:
        conn: Database connection
        stats: Statistics dictionary from collection run
    """
    with conn.cursor() as cursor:
        # Update last collection run timestamp
        cursor.execute(
            """
            INSERT INTO collection_metadata (key, value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW()
            """,
            ("last_collection_run", datetime.now().isoformat()),
        )

        # Update total matches collected
        cursor.execute(
            """
            INSERT INTO collection_metadata (key, value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW()
            """,
            ("total_matches_collected", str(stats.get("matches_collected", 0))),
        )

        conn.commit()
        logger.info("Updated collection metadata")


def collect_matches(
    api_client: MarvelRivalsClient,
    db_conn: PgConnection,
    batch_size: int = 100,
    rate_limit_delay: float = 8.6,
) -> Dict:
    """Collect match histories for pending players with rate limiting.

    This is the main orchestration function that:
    1. Loads pending players from database
    2. Fetches match history for each player
    3. Filters competitive matches
    4. Deduplicates and inserts matches + participants
    5. Updates player status and metadata
    6. Enforces rate limiting between requests

    Args:
        api_client: MarvelRivalsClient instance
        db_conn: Database connection
        batch_size: Maximum players to process in this run
        rate_limit_delay: Seconds to wait between API requests (default 8.6 = 7 req/min)

    Returns:
        Dictionary with statistics:
        - players_processed: Number of players processed
        - matches_collected: Number of new matches inserted
        - matches_skipped: Number of duplicate matches skipped
        - participants_inserted: Total participants inserted
        - api_errors: Number of API errors encountered
    """
    logger.info(f"Starting match collection (batch_size={batch_size}, delay={rate_limit_delay}s)")

    # Statistics tracking
    stats = {
        "players_processed": 0,
        "matches_collected": 0,
        "matches_skipped": 0,
        "participants_inserted": 0,
        "api_errors": 0,
    }

    # Step 1: Load pending players
    pending_players = get_pending_players(db_conn, batch_size)

    if not pending_players:
        logger.info("No pending players to process")
        return stats

    logger.info(f"Processing {len(pending_players)} pending players")

    # Step 2: Process each player
    for idx, username in enumerate(pending_players, 1):
        try:
            # Step 3: Fetch match history from API
            matches = fetch_player_matches(api_client, username, limit=150)

            if not matches:
                logger.warning(f"No matches returned for {username}")
                # Still mark as collected to avoid re-processing
                mark_player_collected(db_conn, username)
                stats["players_processed"] += 1
                stats["api_errors"] += 1
                time.sleep(rate_limit_delay)
                continue

            # Step 4: Filter for current season + competitive mode
            competitive_matches = filter_competitive_matches(matches, CURRENT_SEASON)

            # Step 5: Process each match
            for match in competitive_matches:
                match_id = match.get("match_id")

                if not match_id:
                    logger.warning(f"Match missing match_id, skipping: {match}")
                    continue

                # Check if match already exists (deduplication)
                if match_exists(db_conn, match_id):
                    stats["matches_skipped"] += 1
                    continue

                # Step 6: Insert match metadata
                if not insert_match(db_conn, match):
                    logger.warning(f"Failed to insert match {match_id}")
                    continue

                # Step 7: Extract and insert all 12 participants
                participants = extract_participants(match_id, match)

                if len(participants) != 12:
                    logger.warning(
                        f"Match {match_id} has {len(participants)} participants (expected 12)"
                    )

                participants_count = insert_match_participants(db_conn, participants)
                stats["participants_inserted"] += participants_count
                stats["matches_collected"] += 1

            # Step 8: Mark player as collected
            mark_player_collected(db_conn, username)
            stats["players_processed"] += 1

            # Log progress every 10 players
            if idx % 10 == 0:
                logger.info(
                    f"Progress: {idx}/{len(pending_players)} players processed, "
                    f"{stats['matches_collected']} matches collected, "
                    f"{stats['api_errors']} errors"
                )

            # Step 9: Rate limiting
            time.sleep(rate_limit_delay)

        except Exception as e:
            logger.error(f"Unexpected error processing {username}: {e}")
            stats["api_errors"] += 1
            # Don't mark as collected on unexpected errors
            continue

    # Step 10: Update metadata
    update_collection_metadata(db_conn, stats)

    logger.info(
        f"Match collection complete: {stats['players_processed']} players, "
        f"{stats['matches_collected']} matches, {stats['matches_skipped']} skipped, "
        f"{stats['api_errors']} errors"
    )

    return stats
