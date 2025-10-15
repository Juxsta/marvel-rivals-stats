"""Player discovery module for stratified sampling from Marvel Rivals API.

This module implements player discovery using stratified sampling across rank tiers.
Players are fetched from leaderboards, deduplicated, and stored in the database.
"""

import logging
import random
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from psycopg2.extensions import connection as PgConnection

from ..api.client import MarvelRivalsClient

# Configure logging
logger = logging.getLogger(__name__)

# Default rank quotas for stratified sampling (total: 500 players)
DEFAULT_RANK_QUOTAS = {
    "Bronze": 50,  # 10%
    "Silver": 75,  # 15%
    "Gold": 100,  # 20%
    "Platinum": 100,  # 20%
    "Diamond": 75,  # 15%
    "Master": 50,  # 10%
    "Grandmaster": 25,  # 5%
    "Celestial": 25,  # 5%
}

# Top heroes for diversity sampling (placeholder - should be configured)
TOP_HEROES_FOR_DIVERSITY = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,  # Hero IDs - adjust based on actual game data
]


def fetch_leaderboard_players(api_client: MarvelRivalsClient, limit: int = 1000) -> List[Dict]:
    """Fetch player data from general leaderboard.

    Args:
        api_client: MarvelRivalsClient instance
        limit: Maximum number of players to fetch

    Returns:
        List of player dictionaries with username, rank_tier, rank_score

    Raises:
        Exception: If API call fails (logged but not propagated)
    """
    try:
        logger.info(f"Fetching leaderboard players (limit={limit})")
        players = api_client.get_leaderboard(limit=limit)
        logger.info(f"Successfully fetched {len(players)} leaderboard players")
        return players
    except Exception as e:
        logger.error(f"Failed to fetch leaderboard players: {e}")
        return []


def fetch_hero_leaderboard_players(
    api_client: MarvelRivalsClient, hero_ids: List[int], limit_per_hero: int = 50
) -> List[Dict]:
    """Fetch players from hero-specific leaderboards for diversity.

    Args:
        api_client: MarvelRivalsClient instance
        hero_ids: List of hero IDs to fetch leaderboards for
        limit_per_hero: Number of players to fetch per hero

    Returns:
        List of player dictionaries aggregated across all hero leaderboards
    """
    all_players = []

    for hero_id in hero_ids:
        try:
            logger.info(f"Fetching hero leaderboard for hero_id={hero_id}")
            players = api_client.get_hero_leaderboard(hero_id=hero_id, limit=limit_per_hero)
            all_players.extend(players)
            logger.info(f"Fetched {len(players)} players for hero_id={hero_id}")
        except Exception as e:
            logger.error(f"Failed to fetch hero leaderboard for hero_id={hero_id}: {e}")
            continue

    logger.info(f"Total players fetched from hero leaderboards: {len(all_players)}")
    return all_players


def deduplicate_players_in_memory(players: List[Dict]) -> List[Dict]:
    """Remove duplicate players by username (in-memory deduplication).

    Args:
        players: List of player dictionaries

    Returns:
        List of unique players (first occurrence kept)
    """
    seen = set()
    unique_players = []

    for player in players:
        username = player["username"]
        if username not in seen:
            seen.add(username)
            unique_players.append(player)

    logger.info(f"Deduplicated {len(players)} -> {len(unique_players)} players in memory")
    return unique_players


def group_by_rank(players: List[Dict]) -> Dict[str, List[Dict]]:
    """Group players by rank tier.

    Args:
        players: List of player dictionaries

    Returns:
        Dictionary mapping rank_tier to list of players
    """
    players_by_rank = defaultdict(list)

    for player in players:
        rank_tier = player.get("rank_tier")
        if rank_tier:
            players_by_rank[rank_tier].append(player)

    logger.info(f"Grouped players into {len(players_by_rank)} ranks")
    for rank, rank_players in players_by_rank.items():
        logger.debug(f"  {rank}: {len(rank_players)} players")

    return dict(players_by_rank)


def stratify_by_rank(players: List[Dict], quotas: Dict[str, int]) -> List[Dict]:
    """Apply stratified sampling using rank quotas.

    Args:
        players: List of player dictionaries
        quotas: Dictionary mapping rank_tier to desired sample size

    Returns:
        List of sampled players according to quotas
    """
    players_by_rank = group_by_rank(players)
    selected_players = []

    for rank, quota in quotas.items():
        rank_pool = players_by_rank.get(rank, [])
        sample_size = min(quota, len(rank_pool))

        if sample_size > 0:
            sampled = random.sample(rank_pool, sample_size)
            selected_players.extend(sampled)
            logger.info(
                f"Sampled {sample_size}/{quota} players from {rank} (pool: {len(rank_pool)})"
            )
        else:
            logger.warning(f"No players available for rank {rank} (quota: {quota})")

    logger.info(f"Total players after stratified sampling: {len(selected_players)}")
    return selected_players


def deduplicate_players_in_db(conn: PgConnection, players: List[Dict]) -> Tuple[int, int]:
    """Check which players already exist in database.

    Args:
        conn: Database connection
        players: List of player dictionaries

    Returns:
        Tuple of (new_count, existing_count)
    """
    if not players:
        return 0, 0

    usernames = [p["username"] for p in players]

    with conn.cursor() as cursor:
        cursor.execute("SELECT username FROM players WHERE username = ANY(%s)", (usernames,))
        existing_usernames = {row[0] for row in cursor.fetchall()}

    new_count = len(usernames) - len(existing_usernames)
    existing_count = len(existing_usernames)

    logger.info(f"Database deduplication: {new_count} new, {existing_count} existing")
    return new_count, existing_count


def insert_players(conn: PgConnection, players: List[Dict]) -> int:
    """Insert new players into database with rank information.

    Args:
        conn: Database connection
        players: List of player dictionaries

    Returns:
        Number of players inserted
    """
    if not players:
        logger.warning("No players to insert")
        return 0

    with conn.cursor() as cursor:
        # Prepare data for batch insert
        player_data = [(p["username"], p.get("rank_tier"), p.get("rank_score")) for p in players]

        # Use executemany for batch insertion with ON CONFLICT to handle race conditions
        cursor.executemany(
            """
            INSERT INTO players (username, rank_tier, rank_score, discovered_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (username) DO UPDATE
            SET rank_tier = EXCLUDED.rank_tier,
                rank_score = EXCLUDED.rank_score,
                discovered_at = NOW()
            """,
            player_data,
        )

        inserted_count = cursor.rowcount
        conn.commit()

        logger.info(f"Inserted/updated {inserted_count} players into database")
        return inserted_count


def update_discovery_metadata(conn: PgConnection, total_discovered: int) -> None:
    """Update collection metadata to track discovery progress.

    Args:
        conn: Database connection
        total_discovered: Total number of players discovered in this run
    """
    with conn.cursor() as cursor:
        # Update total players discovered
        cursor.execute(
            """
            INSERT INTO collection_metadata (key, value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW()
            """,
            ("total_players_discovered", str(total_discovered)),
        )

        # Update last discovery run timestamp
        cursor.execute(
            """
            INSERT INTO collection_metadata (key, value, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW()
            """,
            ("last_discovery_run", datetime.now().isoformat()),
        )

        conn.commit()
        logger.info(f"Updated discovery metadata: {total_discovered} players discovered")


def discover_players(
    api_client: MarvelRivalsClient,
    db_conn: PgConnection,
    target_count: int = 500,
    quotas: Optional[Dict[str, int]] = None,
) -> Dict:
    """Discover players using stratified sampling from API leaderboards.

    This is the main orchestration function that:
    1. Fetches players from general leaderboard
    2. Fetches players from hero-specific leaderboards
    3. Deduplicates in memory
    4. Applies stratified sampling by rank
    5. Deduplicates against database
    6. Inserts new players
    7. Updates metadata

    Args:
        api_client: MarvelRivalsClient instance
        db_conn: Database connection
        target_count: Target total number of players to discover
        quotas: Rank quotas (defaults to DEFAULT_RANK_QUOTAS)

    Returns:
        Dictionary with statistics:
        - total_fetched: Total players fetched from API
        - new_players: Number of new players added
        - existing_players: Number of already-known players
        - by_rank: Breakdown by rank tier
    """
    if quotas is None:
        quotas = DEFAULT_RANK_QUOTAS

    logger.info(f"Starting player discovery (target={target_count})")

    # Step 1: Fetch leaderboard players
    leaderboard_players = fetch_leaderboard_players(api_client, limit=1000)

    # Step 2: Fetch hero-specific leaderboard players for diversity
    hero_players = fetch_hero_leaderboard_players(
        api_client, hero_ids=TOP_HEROES_FOR_DIVERSITY, limit_per_hero=50
    )

    # Step 3: Combine and deduplicate in memory
    all_players = leaderboard_players + hero_players
    logger.info(f"Total players before deduplication: {len(all_players)}")

    unique_players = deduplicate_players_in_memory(all_players)

    # Step 4: Apply stratified sampling
    selected_players = stratify_by_rank(unique_players, quotas)

    # Step 5: Deduplicate against database
    new_count, existing_count = deduplicate_players_in_db(db_conn, selected_players)

    # Step 6: Insert new players (ON CONFLICT handles any race conditions)
    inserted_count = insert_players(db_conn, selected_players)

    # Step 7: Update metadata
    update_discovery_metadata(db_conn, inserted_count)

    # Calculate breakdown by rank
    by_rank = {}
    for rank in quotas.keys():
        rank_players = [p for p in selected_players if p.get("rank_tier") == rank]
        by_rank[rank] = len(rank_players)

    stats = {
        "total_fetched": len(all_players),
        "unique_fetched": len(unique_players),
        "sampled": len(selected_players),
        "new_players": new_count,
        "existing_players": existing_count,
        "inserted": inserted_count,
        "by_rank": by_rank,
    }

    logger.info(f"Player discovery complete: {stats}")
    return stats
