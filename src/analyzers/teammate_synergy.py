"""Teammate synergy analysis for Marvel Rivals heroes.

This module identifies hero pairings with positive/negative win rates compared
to expected values based on individual hero performance.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from psycopg2.extensions import connection as PgConnection

from src.utils.statistics import (
    binomial_test_synergy,
    bonferroni_correction,
    calculate_required_sample_size,
    expected_wr_average,
    wilson_confidence_interval,
)

# Configure logging
logger = logging.getLogger(__name__)

# Minimum games together threshold
MIN_GAMES_TOGETHER = 50

# Top N synergies to return per hero
TOP_N_SYNERGIES = 10

# Sample size confidence thresholds
SAMPLE_SIZE_HIGH_CONFIDENCE = 500
SAMPLE_SIZE_MEDIUM_CONFIDENCE = 100


def _convert_numpy_type(value: Any) -> Any:
    """Convert numpy types to Python native types for database compatibility.

    Args:
        value: Value that may be a numpy type

    Returns:
        Python native type equivalent
    """
    if isinstance(value, np.integer):
        return int(value)
    elif isinstance(value, np.floating):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, np.bool_):
        return bool(value)
    return value


def calculate_synergy_score(actual_wr: float, expected_wr: float) -> float:
    """Calculate synergy score as difference from expected win rate.

    Positive score = better than expected (positive synergy)
    Negative score = worse than expected (anti-synergy)
    Zero score = performance matches expectation

    Args:
        actual_wr: Actual win rate when paired together
        expected_wr: Expected win rate from baseline model

    Returns:
        Synergy score rounded to 4 decimal places
    """
    return round(actual_wr - expected_wr, 4)


def add_sample_size_warning(games_together: int) -> Tuple[str, Optional[str]]:
    """Add sample size warning based on number of games.

    Args:
        games_together: Number of games played together

    Returns:
        Tuple of (confidence_level, warning_message)
    """
    if games_together >= SAMPLE_SIZE_HIGH_CONFIDENCE:
        return ("high", None)
    elif games_together >= SAMPLE_SIZE_MEDIUM_CONFIDENCE:
        return (
            "medium",
            f"Moderate sample size ({games_together} games). "
            "Results may have wide confidence intervals.",
        )
    else:
        return (
            "low",
            f"Low sample size ({games_together} games). "
            "Results are unreliable. Interpret with caution.",
        )


def calculate_power_analysis(max_games_together: int, baseline_wr: float = 0.5) -> Dict:
    """Calculate power analysis for synergy detection.

    Determines required sample sizes to detect various effect sizes
    (3%, 5%, 10% synergies) with 80% statistical power at alpha=0.05.

    Args:
        max_games_together: Maximum games together in current dataset
        baseline_wr: Representative baseline win rate for calculations (default 0.5)

    Returns:
        Dictionary with power analysis information
    """
    # Calculate required sample sizes for different effect sizes
    required_3pct = calculate_required_sample_size(baseline_wr, 0.03)
    required_5pct = calculate_required_sample_size(baseline_wr, 0.05)
    required_10pct = calculate_required_sample_size(baseline_wr, 0.10)

    # Determine what effect sizes can be detected with current data
    if max_games_together >= required_3pct:
        detectable = ">=3%"
    elif max_games_together >= required_5pct:
        detectable = ">=5%"
    elif max_games_together >= required_10pct:
        detectable = ">=10%"
    else:
        detectable = ">10% (low power)"

    return {
        "current_max_samples": max_games_together,
        "required_for_3pct_synergy": required_3pct,
        "required_for_5pct_synergy": required_5pct,
        "required_for_10pct_synergy": required_10pct,
        "can_detect_effects": detectable,
    }


def extract_teammates_from_match(teammates: List[str], hero: str) -> List[str]:
    """Extract teammate hero names from match, excluding the hero itself.

    Args:
        teammates: List of hero names in the match
        hero: The hero to exclude

    Returns:
        List of teammate hero names
    """
    return [t for t in teammates if t != hero]


def filter_by_min_games(teammate_stats: Dict[str, Dict], min_games: int) -> Dict[str, Dict]:
    """Filter teammate statistics by minimum games threshold.

    Args:
        teammate_stats: Dictionary mapping teammate to stats
        min_games: Minimum games required

    Returns:
        Filtered dictionary containing only teammates with sufficient games
    """
    return {
        teammate: stats for teammate, stats in teammate_stats.items() if stats["games"] >= min_games
    }


def load_character_win_rates(conn: PgConnection) -> Dict[str, float]:
    """Load cached character win rates from character_stats table.

    Loads overall win rates (rank_tier IS NULL) for all heroes.

    Args:
        conn: Database connection

    Returns:
        Dictionary mapping hero_name to win_rate
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT hero_name, win_rate
            FROM character_stats
            WHERE rank_tier IS NULL
            ORDER BY hero_name
        """
        )

        win_rates = {}
        for row in cursor.fetchall():
            win_rates[row[0]] = float(row[1])

    logger.info(f"Loaded win rates for {len(win_rates)} heroes")
    return win_rates


def query_hero_matches(conn: PgConnection, hero_name: str) -> List[Dict]:
    """Query all matches where a hero played.

    Returns match_id, team, and won status for each match.

    Args:
        conn: Database connection
        hero_name: Name of the hero

    Returns:
        List of match dictionaries with match_id, team, won keys
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT match_id, team, won
            FROM match_participants
            WHERE hero_name = %s
            ORDER BY match_id
        """,
            (hero_name,),
        )

        matches = []
        for row in cursor.fetchall():
            matches.append({"match_id": row[0], "team": row[1], "won": row[2]})

    return matches


def query_match_teammates(
    conn: PgConnection, match_id: str, team: int, exclude_hero: str
) -> List[str]:
    """Query teammates in a specific match.

    Args:
        conn: Database connection
        match_id: Match identifier
        team: Team number (0 or 1)
        exclude_hero: Hero to exclude from results

    Returns:
        List of teammate hero names
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT hero_name
            FROM match_participants
            WHERE match_id = %s AND team = %s AND hero_name != %s
        """,
            (match_id, team, exclude_hero),
        )

        teammates = [row[0] for row in cursor.fetchall()]

    return teammates


def cache_synergy_stats(
    conn: PgConnection,
    hero_a: str,
    hero_b: str,
    rank_tier: Optional[str],
    games_together: int,
    wins_together: int,
    win_rate: float,
    expected_win_rate: float,
    synergy_score: float,
    confidence_lower: float,
    confidence_upper: float,
    p_value: float,
    sample_size_warning: Optional[str],
    baseline_model: str = "average",
) -> None:
    """Cache synergy statistics in database.

    Ensures hero_a < hero_b alphabetically to prevent duplicates.
    Converts all numpy types to Python types before database insertion.

    Args:
        conn: Database connection
        hero_a: First hero name
        hero_b: Second hero name
        rank_tier: Rank tier (None for overall stats)
        games_together: Number of games played together
        wins_together: Number of wins together
        win_rate: Actual win rate when paired
        expected_win_rate: Expected win rate from baseline model
        synergy_score: Difference (actual - expected)
        confidence_lower: Lower bound of 95% CI
        confidence_upper: Upper bound of 95% CI
        p_value: Statistical significance p-value
        sample_size_warning: Warning message for small samples
        baseline_model: Baseline model used (default 'average')
    """
    # Ensure alphabetical order
    if hero_a > hero_b:
        hero_a, hero_b = hero_b, hero_a

    # Convert all numpy types to Python types for database compatibility
    games_together = _convert_numpy_type(games_together)
    wins_together = _convert_numpy_type(wins_together)
    win_rate = _convert_numpy_type(win_rate)
    expected_win_rate = _convert_numpy_type(expected_win_rate)
    synergy_score = _convert_numpy_type(synergy_score)
    confidence_lower = _convert_numpy_type(confidence_lower)
    confidence_upper = _convert_numpy_type(confidence_upper)
    p_value = _convert_numpy_type(p_value)

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO synergy_stats
            (hero_a, hero_b, rank_tier, games_together, wins_together,
             win_rate, expected_win_rate, synergy_score,
             confidence_lower, confidence_upper, p_value,
             sample_size_warning, baseline_model, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (hero_a, hero_b, COALESCE(rank_tier, ''))
            DO UPDATE SET
                games_together = EXCLUDED.games_together,
                wins_together = EXCLUDED.wins_together,
                win_rate = EXCLUDED.win_rate,
                expected_win_rate = EXCLUDED.expected_win_rate,
                synergy_score = EXCLUDED.synergy_score,
                confidence_lower = EXCLUDED.confidence_lower,
                confidence_upper = EXCLUDED.confidence_upper,
                p_value = EXCLUDED.p_value,
                sample_size_warning = EXCLUDED.sample_size_warning,
                baseline_model = EXCLUDED.baseline_model,
                analyzed_at = CURRENT_TIMESTAMP
            """,
            (
                hero_a,
                hero_b,
                rank_tier,
                games_together,
                wins_together,
                win_rate,
                expected_win_rate,
                synergy_score,
                confidence_lower,
                confidence_upper,
                p_value,
                sample_size_warning,
                baseline_model,
            ),
        )


def analyze_teammate_synergies(
    conn: PgConnection,
    min_games_together: int = MIN_GAMES_TOGETHER,
    rank_tier: Optional[str] = None,
    alpha: float = 0.05,
) -> Dict[str, Dict]:
    """Analyze teammate synergies for all heroes.

    This is the main analysis function that:
    1. Loads cached character win rates
    2. For each hero, queries all matches they played
    3. Extracts teammates from each match
    4. Calculates actual vs expected win rates (using average baseline)
    5. Computes synergy scores with statistical significance testing
    6. Applies Bonferroni correction for multiple comparisons
    7. Adds sample size warnings
    8. Caches results in database
    9. Returns top N synergies per hero

    Args:
        conn: Database connection
        min_games_together: Minimum games to report synergy (default 50)
        rank_tier: Specific rank to analyze (None = all ranks)
        alpha: Significance level for hypothesis tests (default 0.05)

    Returns:
        Dictionary mapping hero_name to synergy analysis results
    """
    logger.info("Starting teammate synergy analysis")

    # Load character win rates for expected calculation
    char_win_rates = load_character_win_rates(conn)

    if not char_win_rates:
        logger.error("No character win rates found. Run character analysis first.")
        return {}

    heroes = list(char_win_rates.keys())
    logger.info(f"Analyzing synergies for {len(heroes)} heroes")

    results = {}
    heroes_analyzed = 0

    for hero in heroes:
        logger.info(f"Analyzing {hero}...")

        # Find all matches where this hero played
        hero_matches = query_hero_matches(conn, hero)

        if not hero_matches:
            logger.info(f"  Skipping {hero}: no matches found")
            continue

        # Track stats for each teammate
        teammate_stats = defaultdict(lambda: {"games": 0, "wins": 0})

        # For each match, find teammates
        for match in hero_matches:
            teammates = query_match_teammates(conn, match["match_id"], match["team"], hero)

            # Update stats for each teammate
            for teammate in teammates:
                teammate_stats[teammate]["games"] += 1
                if match["won"]:
                    teammate_stats[teammate]["wins"] += 1

        # Calculate synergy scores
        synergies = []
        max_games = 0  # Track max sample size for power analysis

        for teammate, stats in teammate_stats.items():
            if stats["games"] < min_games_together:
                continue

            # Track maximum games together for power analysis
            max_games = max(max_games, stats["games"])

            # Skip if teammate doesn't have cached win rate
            if teammate not in char_win_rates:
                logger.warning(f"  Teammate {teammate} not in character_stats, skipping")
                continue

            # Actual win rate when paired
            actual_wr = stats["wins"] / stats["games"]

            # Expected win rate using average baseline model
            hero_wr = char_win_rates[hero]
            teammate_wr = char_win_rates[teammate]
            expected_wr = expected_wr_average(hero_wr, teammate_wr)

            # Synergy score
            synergy_score = calculate_synergy_score(actual_wr, expected_wr)

            # Confidence interval for actual win rate
            ci_lower, ci_upper = wilson_confidence_interval(
                wins=stats["wins"], total=stats["games"]
            )

            # Statistical significance test
            sig_result = binomial_test_synergy(
                wins=stats["wins"], total=stats["games"], expected_wr=expected_wr, alpha=alpha
            )

            # Sample size warning
            confidence_level, warning = add_sample_size_warning(stats["games"])

            synergy_data = {
                "teammate": teammate,
                "games_together": stats["games"],
                "wins_together": stats["wins"],
                "actual_win_rate": round(actual_wr, 4),
                "expected_win_rate": expected_wr,
                "synergy_score": synergy_score,
                "confidence_interval_95": [
                    float(ci_lower),
                    float(ci_upper),
                ],  # Ensure Python floats
                "p_value": float(sig_result["p_value"]),  # Ensure Python float
                "significant": sig_result["significant"],
                "confidence_level": confidence_level,
                "sample_size_warning": warning,
            }

            synergies.append(synergy_data)

        # Apply Bonferroni correction to all synergies for this hero
        if synergies:
            synergies = bonferroni_correction(synergies, alpha=alpha)

        # Sort by synergy score (best synergies first)
        synergies.sort(key=lambda x: x["synergy_score"], reverse=True)

        # Cache each synergy in database
        for synergy in synergies:
            cache_synergy_stats(
                conn,
                hero,
                synergy["teammate"],
                rank_tier,
                synergy["games_together"],
                synergy["wins_together"],
                synergy["actual_win_rate"],
                synergy["expected_win_rate"],
                synergy["synergy_score"],
                synergy["confidence_interval_95"][0],
                synergy["confidence_interval_95"][1],
                synergy["p_value"],
                synergy["sample_size_warning"],
                baseline_model="average",
            )

        # Commit after each hero to save progress
        conn.commit()

        # Logging for transparency
        n_synergies = len(synergies)
        n_significant = sum(s["significant"] for s in synergies)
        n_significant_bonf = sum(s["significant_bonferroni"] for s in synergies)
        n_low_sample = sum(s["confidence_level"] == "low" for s in synergies)

        logger.info(f"  {hero}: {n_synergies} synergies tested")
        logger.info(f"    Significant (uncorrected): {n_significant}/{n_synergies}")
        logger.info(f"    Significant (Bonferroni): {n_significant_bonf}/{n_synergies}")
        logger.info(f"    Low sample size warnings: {n_low_sample}/{n_synergies}")
        if synergies:
            logger.info(
                f"    Top synergy: {synergies[0]['teammate']} "
                f"({synergies[0]['synergy_score']:+.4f})"
            )

        # Calculate power analysis for this hero
        power_analysis = calculate_power_analysis(max_games) if max_games > 0 else None

        results[hero] = {
            "hero": hero,
            "rank_tier": rank_tier if rank_tier else "all",
            "synergies": synergies[:TOP_N_SYNERGIES],  # Top 10
            "power_analysis": power_analysis,
            "analyzed_at": datetime.now().isoformat(),
        }

        heroes_analyzed += 1

    logger.info(f"Synergy analysis complete: {heroes_analyzed} heroes analyzed")
    return results


def export_to_json(results: Dict, output_path: str) -> None:
    """Export synergy analysis results to JSON file with enhanced metadata.

    Adds methodology version, baseline model, and analysis timestamp to the
    exported data to support backward compatibility tracking and future
    methodology changes.

    Args:
        results: Synergy analysis results dictionary (hero -> data)
        output_path: Path to output JSON file
    """
    # Create enhanced export structure with metadata
    export_data = {
        "methodology_version": "2.0",
        "baseline_model": "average",
        "analysis_date": datetime.now().isoformat(),
        "heroes": results,
    }

    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)

    logger.info(f"Results exported to {output_path}")
