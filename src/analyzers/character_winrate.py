"""Character win rate analysis with Wilson confidence intervals.

This module calculates win rates for all heroes stratified by rank tier,
using the Wilson score confidence interval for statistical rigor.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from psycopg2.extensions import connection as PgConnection

from src.utils.statistics import wilson_confidence_interval

# Configure logging
logger = logging.getLogger(__name__)

# Minimum sample size thresholds
MIN_GAMES_PER_RANK = 30
MIN_GAMES_OVERALL = 100


def calculate_win_rate_stats(wins: int, total: int) -> Dict:
    """Calculate win rate statistics including confidence interval.

    Args:
        wins: Number of wins
        total: Total number of games

    Returns:
        Dictionary with win rate stats
    """
    win_rate = wins / total if total > 0 else 0.0
    losses = total - wins
    ci_lower, ci_upper = wilson_confidence_interval(wins, total)

    return {
        "total_games": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 4),
        "confidence_interval_95": [ci_lower, ci_upper],
    }


def group_matches_by_rank(matches: List[Dict]) -> Dict[str, Dict]:
    """Group match results by rank tier.

    Args:
        matches: List of match result dicts with 'won' and 'rank_tier' keys

    Returns:
        Dictionary mapping rank_tier to {'wins': int, 'losses': int}
    """
    by_rank = defaultdict(lambda: {"wins": 0, "losses": 0})

    for match in matches:
        rank = match["rank_tier"]
        if match["won"]:
            by_rank[rank]["wins"] += 1
        else:
            by_rank[rank]["losses"] += 1

    return dict(by_rank)


def filter_by_min_games(rank_stats: Dict[str, Dict], min_games: int) -> Dict[str, Dict]:
    """Filter rank statistics by minimum game threshold.

    Args:
        rank_stats: Dictionary of rank statistics
        min_games: Minimum number of games required

    Returns:
        Filtered dictionary containing only ranks with sufficient games
    """
    return {
        rank: stats
        for rank, stats in rank_stats.items()
        if stats.get("total_games", 0) >= min_games
    }


def query_hero_matches(conn: PgConnection, hero_name: str) -> List[Dict]:
    """Query all matches for a specific hero with player rank information.

    Args:
        conn: Database connection
        hero_name: Name of the hero to query

    Returns:
        List of match result dictionaries with 'won' and 'rank_tier' keys
    """
    with conn.cursor() as cursor:
        query = """
            SELECT mp.won, p.rank_tier
            FROM match_participants mp
            JOIN players p ON mp.username = p.username
            WHERE mp.hero_name = %s AND p.rank_tier IS NOT NULL
        """
        cursor.execute(query, (hero_name,))

        matches = []
        for row in cursor.fetchall():
            matches.append({"won": row[0], "rank_tier": row[1]})

    return matches


def get_all_heroes(conn: PgConnection) -> List[str]:
    """Get list of all unique heroes from match participants.

    Args:
        conn: Database connection

    Returns:
        List of hero names
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT hero_name
            FROM match_participants
            ORDER BY hero_name
        """
        )
        heroes = [row[0] for row in cursor.fetchall()]

    return heroes


def cache_character_stats(
    conn: PgConnection, hero_name: str, rank_tier: Optional[str], stats: Dict
) -> None:
    """Cache character statistics in database.

    Args:
        conn: Database connection
        hero_name: Name of the hero
        rank_tier: Rank tier (None for overall stats)
        stats: Statistics dictionary
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO character_stats
            (hero_name, rank_tier, total_games, wins, losses, win_rate,
             confidence_interval_lower, confidence_interval_upper, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (hero_name, COALESCE(rank_tier, ''))
            DO UPDATE SET
                total_games = EXCLUDED.total_games,
                wins = EXCLUDED.wins,
                losses = EXCLUDED.losses,
                win_rate = EXCLUDED.win_rate,
                confidence_interval_lower = EXCLUDED.confidence_interval_lower,
                confidence_interval_upper = EXCLUDED.confidence_interval_upper,
                analyzed_at = CURRENT_TIMESTAMP
            """,
            (
                hero_name,
                rank_tier,
                stats["total_games"],
                stats["wins"],
                stats["losses"],
                stats["win_rate"],
                stats["confidence_interval_95"][0],
                stats["confidence_interval_95"][1],
            ),
        )


def analyze_character_win_rates(
    conn: PgConnection,
    min_games_per_rank: int = MIN_GAMES_PER_RANK,
    min_games_overall: int = MIN_GAMES_OVERALL,
) -> Dict[str, Dict]:
    """Analyze win rates for all characters stratified by rank.

    This is the main analysis function that:
    1. Queries all unique heroes
    2. For each hero, queries match results with player ranks
    3. Groups by rank tier
    4. Calculates win rates with Wilson confidence intervals
    5. Filters by minimum sample sizes
    6. Caches results in database
    7. Returns complete analysis

    Args:
        conn: Database connection
        min_games_per_rank: Minimum games to report rank-specific stats
        min_games_overall: Minimum games to report overall stats

    Returns:
        Dictionary mapping hero_name to analysis results
    """
    logger.info("Starting character win rate analysis")

    heroes = get_all_heroes(conn)
    logger.info(f"Found {len(heroes)} unique heroes")

    results = {}
    heroes_analyzed = 0

    for hero in heroes:
        logger.info(f"Analyzing {hero}...")

        # Query all matches for this hero
        matches = query_hero_matches(conn, hero)

        if len(matches) < min_games_overall:
            logger.info(f"  Skipping {hero}: only {len(matches)} games (min: {min_games_overall})")
            continue

        # Group by rank tier
        by_rank = group_matches_by_rank(matches)

        # Calculate stats per rank
        rank_stats = {}
        for rank, data in by_rank.items():
            total = data["wins"] + data["losses"]

            if total < min_games_per_rank:
                continue

            stats = calculate_win_rate_stats(data["wins"], total)
            rank_stats[rank] = stats

            # Cache in database
            cache_character_stats(conn, hero, rank, stats)

        # Calculate overall stats (all ranks combined)
        total_wins = sum(d["wins"] for d in by_rank.values())
        total_losses = sum(d["losses"] for d in by_rank.values())
        total_games = total_wins + total_losses

        overall_stats = calculate_win_rate_stats(total_wins, total_games)

        # Cache overall stats (rank_tier = NULL)
        cache_character_stats(conn, hero, None, overall_stats)

        # Commit after each hero to save progress
        conn.commit()

        results[hero] = {
            "hero": hero,
            "overall": overall_stats,
            "by_rank": rank_stats,
            "analyzed_at": datetime.now().isoformat(),
        }

        heroes_analyzed += 1
        logger.info(f"  {hero}: {total_games} games, {overall_stats['win_rate']} win rate")

    logger.info(f"Character analysis complete: {heroes_analyzed} heroes analyzed")
    return results


def export_to_json(results: Dict, output_path: str) -> None:
    """Export analysis results to JSON file.

    Args:
        results: Analysis results dictionary
        output_path: Path to output JSON file
    """
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results exported to {output_path}")
