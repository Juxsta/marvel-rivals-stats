# SPEC-005: Character Analysis MVP - End-to-End Data Pipeline

**Status**: Draft
**Author**: Development Team
**Created**: 2025-10-15
**Updated**: 2025-10-15
**Version**: 1.0.0
**Consolidates**: SPEC-001 (Player Discovery), SPEC-002 (Match Collection), SPEC-003 (Character Analysis)

---

## Problem Statement

Currently, Marvel Rivals players lack data-driven insights into character performance across different skill levels. While individual match results are available, there is no systematic way to understand:

1. **Character Win Rates by Rank**: How does Spider-Man perform in Bronze vs. Grandmaster?
2. **Statistical Confidence**: Which win rates are reliable vs. based on insufficient data?
3. **Teammate Synergies**: Which hero pairings have higher-than-expected win rates?

This specification consolidates three previous specs into a unified data pipeline that discovers players, collects their match histories, and performs statistical analysis to answer these questions with mathematical rigor.

## Goals

### Primary Goals

1. **Automated Data Collection**: Build an end-to-end pipeline that automatically discovers players and collects match data across all rank tiers
2. **Character Win Rate Analysis**: Calculate statistically rigorous win rates for all heroes, stratified by rank tier (Bronze → Celestial)
3. **Synergy Analysis**: Identify hero pairs that perform better together than expected based on their individual win rates
4. **Statistical Validity**: Ensure all results include confidence intervals and minimum sample size thresholds
5. **Exportable Results**: Generate JSON files for sharing, visualization, and integration with other tools

### Secondary Goals

- Respect API rate limits (7 requests/minute, 10k/day) with graceful backoff
- Make collection resumable after interruptions (track progress, deduplicate data)
- Cache analysis results in database for fast retrieval
- Provide comprehensive logging for monitoring and debugging

## Non-Goals

The following are explicitly out of scope for this MVP:

- Real-time match tracking or live statistics
- Player-specific performance profiling
- Hero matchup/counter-pick analysis
- Build, loadout, or gear recommendations
- Map-specific win rate analysis
- Team composition analysis (3+ hero synergies)
- Predictive modeling or machine learning
- Web UI or API endpoints (data collection and analysis only)

## User Stories

### US-1: Data Analyst Analyzing Character Performance

**As a** competitive Marvel Rivals data analyst,
**I want to** collect match data across all rank tiers and analyze character win rates,
**So that** I can identify which heroes perform best at each skill level with statistical confidence.

**Acceptance Criteria**:
- Pipeline discovers 500+ players stratified by rank
- Collects 50,000+ unique matches
- Calculates win rates for 40+ heroes
- Each win rate includes 95% confidence intervals
- Results filtered by minimum sample size (30 games per rank, 100 overall)

### US-2: Content Creator Building Tier Lists

**As a** Marvel Rivals content creator,
**I want to** export win rate data in JSON format,
**So that** I can create data-driven tier lists and guides for my audience.

**Acceptance Criteria**:
- JSON export contains all heroes with sufficient data
- Win rates stratified by rank tier
- Includes sample sizes and confidence intervals
- Format is documented and easy to parse

### US-3: Theory-Crafter Discovering Synergies

**As a** Marvel Rivals theory-crafter,
**I want to** identify which hero pairings have positive synergy (win more than expected),
**So that** I can recommend optimal team compositions.

**Acceptance Criteria**:
- For each hero, identify top 10 synergies
- Synergy score calculated as (actual_win_rate - expected_win_rate)
- Minimum 50 games together required
- Results include confidence intervals

## Proposed Solution

### Overview

We will build a four-phase data pipeline that runs sequentially:

```
Phase 1: PLAYER DISCOVERY
   ↓
   - Query Marvel Rivals API leaderboards
   - Apply stratified sampling (500 players across 8 rank tiers)
   - Store in database with deduplication

Phase 2: MATCH COLLECTION
   ↓
   - For each discovered player, fetch match history
   - Extract match metadata + all 12 participants
   - Deduplicate by match_id (same match seen from multiple players)
   - Respect API rate limits with delays

Phase 3: CHARACTER ANALYSIS
   ↓
   - Query match_participants table
   - Group by hero and rank tier
   - Calculate win rates with Wilson confidence intervals
   - Filter by minimum sample size
   - Cache results + export JSON

Phase 4: SYNERGY ANALYSIS
   ↓
   - For each hero, find teammates from same match
   - Calculate actual vs. expected win rates
   - Compute synergy scores
   - Filter by minimum games together
   - Cache results + export JSON
```

### Technical Design

#### Phase 1: Player Discovery

**Purpose**: Discover a stratified sample of 500 players across all rank tiers.

**Algorithm**:

```python
def discover_players(target_count=500, rank_quotas=DEFAULT_QUOTAS):
    """
    Discover players using stratified sampling

    Args:
        target_count: Total players to discover (default 500)
        rank_quotas: Dict[rank_tier, count] specifying players per rank

    Returns:
        int: Number of new players discovered
    """

    # 1. Fetch leaderboard data
    leaderboard_players = api.get_player_leaderboard(limit=1000)

    # 2. Fetch hero-specific leaderboards for diversity
    hero_players = []
    for hero_id in TOP_10_HEROES:
        hero_players.extend(api.get_hero_leaderboard(hero_id, limit=50))

    # 3. Combine and deduplicate by username
    all_players = deduplicate_by_username(leaderboard_players + hero_players)

    # 4. Group by rank tier
    players_by_rank = defaultdict(list)
    for player in all_players:
        players_by_rank[player['rank_tier']].append(player)

    # 5. Apply stratified sampling quotas
    selected_players = []
    for rank, quota in rank_quotas.items():
        rank_pool = players_by_rank.get(rank, [])
        sampled = random.sample(rank_pool, min(quota, len(rank_pool)))
        selected_players.extend(sampled)

    # 6. Store in database (with deduplication)
    for player in selected_players:
        db.execute("""
            INSERT INTO players (username, rank_tier, rank_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, (player['username'], player['rank_tier'], player['rank_score']))

    # 7. Update metadata
    db.set_metadata('players_discovered', len(selected_players))
    db.set_metadata('last_discovery_run', datetime.now())

    return len(selected_players)
```

**Default Rank Quotas**:

```python
DEFAULT_RANK_QUOTAS = {
    'Bronze': 50,       # 10%
    'Silver': 75,       # 15%
    'Gold': 100,        # 20%
    'Platinum': 100,    # 20%
    'Diamond': 75,      # 15%
    'Master': 50,       # 10%
    'Grandmaster': 25,  # 5%
    'Celestial': 25     # 5%
}
# Total: 500 players
```

**Rationale**: Quotas roughly match expected player distribution with oversampling of mid-ranks where most players reside. This ensures sufficient data at all skill levels.

#### Phase 2: Match Collection

**Purpose**: Collect 100-150 recent competitive matches per player.

**Algorithm**:

```python
def collect_matches(batch_size=100, rate_limit_delay=8.6):
    """
    Collect match histories for pending players

    Args:
        batch_size: Max players to process in this run
        rate_limit_delay: Seconds between API requests (7 req/min = 8.6s delay)

    Returns:
        dict: Collection statistics
    """

    # 1. Load pending players
    pending_players = db.execute("""
        SELECT username FROM players
        WHERE match_history_fetched = FALSE
        ORDER BY discovered_at
        LIMIT %s
    """, (batch_size,)).fetchall()

    stats = {
        'players_processed': 0,
        'matches_collected': 0,
        'matches_skipped': 0,
        'api_errors': 0
    }

    # 2. Process each player
    for player in pending_players:
        try:
            # 3. Fetch match history from API
            matches = api.get_player_match_history(
                username=player['username'],
                limit=150
            )

            # 4. Filter for current season + competitive mode
            matches = [m for m in matches
                      if m['mode'] == 'competitive'
                      and m['season'] == CURRENT_SEASON]

            # 5. Process each match
            for match in matches:
                # Check if match already exists (deduplication)
                exists = db.execute(
                    "SELECT 1 FROM matches WHERE match_id = %s",
                    (match['match_id'],)
                ).fetchone()

                if exists:
                    stats['matches_skipped'] += 1
                    continue

                # 6. Insert match metadata
                db.execute("""
                    INSERT INTO matches (match_id, mode, season, match_timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (match['match_id'], match['mode'],
                      match['season'], match['timestamp']))

                # 7. Insert all 12 participants
                for team in match['teams']:
                    team_num = team['team']
                    won = team['won']

                    for player_data in team['players']:
                        db.execute("""
                            INSERT INTO match_participants
                            (match_id, username, hero_id, hero_name, role,
                             team, won, kills, deaths, assists, damage, healing)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (match['match_id'], player_data['username'],
                              player_data['hero_id'], player_data['hero_name'],
                              player_data['role'], team_num, won,
                              player_data.get('kills', 0),
                              player_data.get('deaths', 0),
                              player_data.get('assists', 0),
                              player_data.get('damage', 0),
                              player_data.get('healing', 0)))

                stats['matches_collected'] += 1

            # 8. Mark player as collected
            db.execute("""
                UPDATE players
                SET match_history_fetched = TRUE, last_updated = NOW()
                WHERE username = %s
            """, (player['username'],))

            stats['players_processed'] += 1

            # 9. Rate limiting
            time.sleep(rate_limit_delay)

        except APIException as e:
            logger.error(f"API error for {player['username']}: {e}")
            stats['api_errors'] += 1
            continue  # Don't mark as collected on error

    # 10. Update metadata
    db.set_metadata('last_collection_run', datetime.now())
    db.set_metadata('total_matches_collected', db.count_matches())

    return stats
```

**Deduplication Strategy**: Matches are deduplicated by `match_id` since the same match will appear in multiple players' histories. The `INSERT` check prevents duplicates while still allowing us to discover matches from multiple sources.

**Rate Limiting**: With 7 requests/minute, we can collect from ~420 players per hour (7 * 60 minutes). For 500 players, this takes ~70 minutes. With 100-150 matches per player, we expect 50,000-75,000 total matches collected.

#### Phase 3: Character Win Rate Analysis

**Purpose**: Calculate win rates for each hero, stratified by rank tier, with statistical confidence intervals.

**Algorithm**:

```python
def analyze_character_win_rates(min_games_per_rank=30, min_games_overall=100):
    """
    Analyze win rates for all characters

    Args:
        min_games_per_rank: Minimum games to report rank-specific stats
        min_games_overall: Minimum games to report overall stats

    Returns:
        dict: Analysis results for all heroes
    """

    # 1. Get all unique heroes
    heroes = db.execute("""
        SELECT DISTINCT hero_name FROM match_participants
        ORDER BY hero_name
    """).fetchall()

    results = {}

    for hero_row in heroes:
        hero = hero_row['hero_name']

        # 2. Query all matches for this hero with player rank
        query = """
            SELECT mp.won, p.rank_tier
            FROM match_participants mp
            JOIN players p ON mp.username = p.username
            WHERE mp.hero_name = %s AND p.rank_tier IS NOT NULL
        """
        rows = db.execute(query, (hero,)).fetchall()

        if len(rows) < min_games_overall:
            continue  # Skip heroes with insufficient data

        # 3. Group by rank tier
        by_rank = defaultdict(lambda: {'wins': 0, 'losses': 0})
        for row in rows:
            rank = row['rank_tier']
            if row['won']:
                by_rank[rank]['wins'] += 1
            else:
                by_rank[rank]['losses'] += 1

        # 4. Calculate stats per rank
        rank_stats = {}
        for rank, data in by_rank.items():
            total = data['wins'] + data['losses']

            if total < min_games_per_rank:
                continue  # Skip ranks with insufficient data

            win_rate = data['wins'] / total
            ci_lower, ci_upper = wilson_confidence_interval(
                wins=data['wins'],
                total=total,
                confidence=0.95
            )

            rank_stats[rank] = {
                'total_games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': round(win_rate, 4),
                'confidence_interval_95': [round(ci_lower, 4), round(ci_upper, 4)]
            }

            # Cache in database
            db.execute("""
                INSERT INTO character_stats
                (hero_name, rank_tier, total_games, wins, losses, win_rate,
                 confidence_interval_lower, confidence_interval_upper)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hero_name, rank_tier)
                DO UPDATE SET
                    total_games = EXCLUDED.total_games,
                    wins = EXCLUDED.wins,
                    losses = EXCLUDED.losses,
                    win_rate = EXCLUDED.win_rate,
                    confidence_interval_lower = EXCLUDED.confidence_interval_lower,
                    confidence_interval_upper = EXCLUDED.confidence_interval_upper,
                    analyzed_at = CURRENT_TIMESTAMP
            """, (hero, rank, total, data['wins'], data['losses'],
                  win_rate, ci_lower, ci_upper))

        # 5. Calculate overall (all ranks combined)
        total_wins = sum(d['wins'] for d in by_rank.values())
        total_losses = sum(d['losses'] for d in by_rank.values())
        total_games = total_wins + total_losses

        overall_wr = total_wins / total_games
        ci_lower, ci_upper = wilson_confidence_interval(total_wins, total_games)

        overall_stats = {
            'total_games': total_games,
            'wins': total_wins,
            'losses': total_losses,
            'win_rate': round(overall_wr, 4),
            'confidence_interval_95': [round(ci_lower, 4), round(ci_upper, 4)]
        }

        # Cache overall stats
        db.execute("""
            INSERT INTO character_stats
            (hero_name, rank_tier, total_games, wins, losses, win_rate,
             confidence_interval_lower, confidence_interval_upper)
            VALUES (%s, NULL, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (hero_name, rank_tier)
            DO UPDATE SET
                total_games = EXCLUDED.total_games,
                wins = EXCLUDED.wins,
                losses = EXCLUDED.losses,
                win_rate = EXCLUDED.win_rate,
                confidence_interval_lower = EXCLUDED.confidence_interval_lower,
                confidence_interval_upper = EXCLUDED.confidence_interval_upper,
                analyzed_at = CURRENT_TIMESTAMP
        """, (hero, total_games, total_wins, total_losses,
              overall_wr, ci_lower, ci_upper))

        results[hero] = {
            'hero': hero,
            'overall': overall_stats,
            'by_rank': rank_stats,
            'analyzed_at': datetime.now().isoformat()
        }

    return results
```

**Wilson Score Confidence Interval**:

```python
from scipy.stats import norm

def wilson_confidence_interval(wins, total, confidence=0.95):
    """
    Calculate Wilson score confidence interval for binomial proportion

    More accurate than normal approximation for small sample sizes.

    Args:
        wins: Number of successes
        total: Total trials
        confidence: Confidence level (default 0.95 = 95%)

    Returns:
        tuple: (lower_bound, upper_bound)
    """
    if total == 0:
        return (0.0, 0.0)

    p = wins / total
    z = norm.ppf(1 - (1 - confidence) / 2)  # 1.96 for 95% confidence

    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    margin = z * sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominator

    return (max(0.0, center - margin), min(1.0, center + margin))
```

**Why Wilson Score?** Unlike the normal approximation, Wilson score intervals perform well even with small sample sizes and extreme proportions (very high or low win rates). This is critical for rare heroes or niche ranks.

#### Phase 4: Teammate Synergy Analysis

**Purpose**: Identify hero pairings that win more frequently than expected based on individual performance.

**Algorithm**:

```python
def analyze_teammate_synergies(min_games_together=50, rank_tier=None):
    """
    Analyze teammate synergies for all heroes

    Args:
        min_games_together: Minimum games to report synergy
        rank_tier: Specific rank to analyze (None = all ranks)

    Returns:
        dict: Synergy results for all heroes
    """

    # 1. Get character win rates (needed for expected calculation)
    char_win_rates = {}
    for row in db.execute("SELECT hero_name, win_rate FROM character_stats WHERE rank_tier IS NULL"):
        char_win_rates[row['hero_name']] = row['win_rate']

    # 2. Get all heroes
    heroes = list(char_win_rates.keys())

    results = {}

    for hero in heroes:
        # 3. Find all matches where this hero played
        hero_matches_query = """
            SELECT match_id, team, won
            FROM match_participants
            WHERE hero_name = %s
        """
        hero_matches = db.execute(hero_matches_query, (hero,)).fetchall()

        # 4. For each match, find teammates
        teammate_stats = defaultdict(lambda: {'games': 0, 'wins': 0})

        for match in hero_matches:
            # Get other players on same team
            teammates_query = """
                SELECT hero_name
                FROM match_participants
                WHERE match_id = %s AND team = %s AND hero_name != %s
            """
            teammates = db.execute(
                teammates_query,
                (match['match_id'], match['team'], hero)
            ).fetchall()

            # Update stats for each teammate
            for teammate in teammates:
                teammate_hero = teammate['hero_name']
                teammate_stats[teammate_hero]['games'] += 1
                if match['won']:
                    teammate_stats[teammate_hero]['wins'] += 1

        # 5. Calculate synergy scores
        synergies = []
        for teammate, stats in teammate_stats.items():
            if stats['games'] < min_games_together:
                continue

            # Actual win rate when paired
            actual_wr = stats['wins'] / stats['games']

            # Expected win rate (independence assumption)
            # P(A and B both win) ≈ P(A wins) * P(B wins)
            expected_wr = char_win_rates.get(hero, 0.5) * char_win_rates.get(teammate, 0.5)

            # Synergy score
            synergy_score = actual_wr - expected_wr

            # Confidence interval
            ci_lower, ci_upper = wilson_confidence_interval(
                wins=stats['wins'],
                total=stats['games']
            )

            synergies.append({
                'teammate': teammate,
                'games_together': stats['games'],
                'wins_together': stats['wins'],
                'actual_win_rate': round(actual_wr, 4),
                'expected_win_rate': round(expected_wr, 4),
                'synergy_score': round(synergy_score, 4),
                'confidence_interval_95': [round(ci_lower, 4), round(ci_upper, 4)]
            })

            # Cache in database
            db.execute("""
                INSERT INTO synergy_stats
                (hero_a, hero_b, rank_tier, games_together, wins_together,
                 win_rate, expected_win_rate, synergy_score)
                VALUES (%s, %s, NULL, %s, %s, %s, %s, %s)
                ON CONFLICT (hero_a, hero_b, rank_tier)
                DO UPDATE SET
                    games_together = EXCLUDED.games_together,
                    wins_together = EXCLUDED.wins_together,
                    win_rate = EXCLUDED.win_rate,
                    expected_win_rate = EXCLUDED.expected_win_rate,
                    synergy_score = EXCLUDED.synergy_score,
                    analyzed_at = CURRENT_TIMESTAMP
            """, (min(hero, teammate), max(hero, teammate),
                  stats['games'], stats['wins'], actual_wr,
                  expected_wr, synergy_score))

        # 6. Sort by synergy score (best synergies first)
        synergies.sort(key=lambda x: x['synergy_score'], reverse=True)

        results[hero] = {
            'hero': hero,
            'rank_tier': rank_tier or 'all',
            'synergies': synergies[:10],  # Top 10 synergies
            'analyzed_at': datetime.now().isoformat()
        }

    return results
```

**Synergy Score Interpretation**:
- **Positive Score** (e.g., +0.0777): Hero pair wins 7.77% more often than expected. Strong synergy!
- **Zero Score**: Performance matches expectation. No synergy effect.
- **Negative Score** (e.g., -0.0345): Hero pair underperforms. Possible anti-synergy or role overlap.

**Statistical Note**: The expected win rate assumes independence (heroes don't affect each other). Any deviation suggests interaction between heroes, which we quantify as synergy.

### API Integration

**Assumed Endpoints** (Marvel Rivals API):

```
GET /api/v1/leaderboard?rank={tier}&limit={n}
Returns: [{"username": str, "rank_tier": str, "rank_score": int}, ...]

GET /api/v1/leaderboard/hero/{hero_id}?limit={n}
Returns: [{"username": str, "hero_id": int, "rank_tier": str}, ...]

GET /api/v1/players/{username}/matches?limit={n}
Returns: {
  "matches": [
    {
      "match_id": str,
      "mode": str,
      "season": int,
      "timestamp": str (ISO 8601),
      "teams": [
        {
          "team": int,
          "won": bool,
          "players": [
            {
              "username": str,
              "hero_id": int,
              "hero_name": str,
              "role": str,
              "kills": int,
              "deaths": int,
              "assists": int,
              "damage": float,
              "healing": float
            }
          ]
        }
      ]
    }
  ]
}
```

**Rate Limits**:
- 7 requests per minute
- 10,000 requests per day
- 429 status code when exceeded

**Error Handling**:
- Retry with exponential backoff (1s, 2s, 4s, 8s)
- Max 3 retries before marking player as failed
- Log all API errors with timestamp

### Alternative Approaches Considered

#### Alternative 1: Real-Time Streaming Pipeline

**Description**: Stream matches in real-time using webhooks or polling.

**Rejected Because**:
- Adds significant complexity (event processing, queues)
- Requires always-on infrastructure
- MVP doesn't need real-time data
- Batch processing is sufficient for weekly/monthly analysis

#### Alternative 2: Sample from Match History Only (No Player Discovery)

**Description**: Start with a few known players and snowball through their match histories.

**Rejected Because**:
- Can't stratify by rank before collection starts
- Risk of sampling bias (network effects)
- Harder to ensure even distribution across ranks

#### Alternative 3: Use Normal Approximation for Confidence Intervals

**Description**: Use simpler `p ± z * sqrt(p(1-p)/n)` formula.

**Rejected Because**:
- Inaccurate for small samples (< 30 games)
- Inaccurate for extreme proportions (win rate near 0% or 100%)
- Wilson score is standard in statistical literature for binomial proportions

## Dependencies

### External Dependencies

- **Marvel Rivals API**: Assumed available at `https://api.marvelrivals.com`
- **PostgreSQL 16**: Running in Docker container (from SPEC-004)
- **Python 3.10+**: Runtime environment

### Python Libraries

All libraries already in `requirements.txt` except scipy:

```
psycopg2-binary==2.9.9      # PostgreSQL adapter
requests==2.31.0             # HTTP client
python-dotenv==1.0.0         # Environment config
scipy==1.11.4                # Statistical functions (NEW)
pytest==7.4.3                # Testing framework
```

### Internal Dependencies

- **SPEC-004 (Project Scaffolding)**: MUST BE COMPLETE
  - Docker Compose environment running
  - Database schema migrated (7 tables)
  - Connection pooling module (`src/db/connection.py`)
  - Rate limiter module (`src/api/rate_limiter.py`)

## Risks & Mitigations

| Risk | Severity | Probability | Impact | Mitigation |
|------|----------|-------------|--------|------------|
| API rate limits prevent full collection | High | Medium | Pipeline takes >24 hours or fails | Enforce 8.6s delay between requests, distribute over multiple days, implement resume logic |
| Insufficient sample sizes for rare heroes | Medium | High | Some heroes excluded from results | Document minimum sample sizes, flag low-confidence results, consider extending collection |
| Player rank data becomes stale | Medium | Medium | Win rates mixed across rank tiers | Accept for MVP, plan periodic re-collection in future enhancement |
| API endpoint structure is incorrect | High | Medium | Collection phase fails entirely | Mock API for testing, implement comprehensive error handling, validate with 5-player test |
| Database disk space exhausted | Low | Low | Pipeline crashes mid-collection | Monitor disk usage, implement retention policy, estimate 50GB for 75k matches |
| Statistical calculation bugs | High | Low | Invalid analysis results | Use well-tested scipy library, write unit tests with known inputs/outputs, manual spot checks |
| Hero names inconsistent across API | Medium | Low | Data fragmentation, undercounting | Normalize hero names (case-insensitive, trim whitespace), create hero mapping table if needed |

## Success Criteria

### Functional Acceptance Criteria

- **AC-1**: Pipeline discovers 400+ players (80% of target) stratified by rank quotas
- **AC-2**: Pipeline collects 50,000+ unique matches without duplicates
- **AC-3**: All collected matches have exactly 12 participants (6v6 format)
- **AC-4**: Pipeline completes without exceeding API rate limits (no 429 errors)
- **AC-5**: Win rates calculated for 35+ heroes (out of ~40 total)
- **AC-6**: All win rates include 95% confidence intervals
- **AC-7**: At least 20 heroes have rank-stratified results (5+ ranks with data)
- **AC-8**: Synergy analysis identifies top 10 teammates for 30+ heroes
- **AC-9**: Results exported to JSON with documented format
- **AC-10**: Pipeline is resumable (can stop and restart without data loss)

### Performance Benchmarks

- **Player Discovery**: 500 players in < 1 hour
- **Match Collection**: 50,000 matches in < 24 hours (with rate limiting)
- **Character Analysis**: All heroes analyzed in < 10 minutes
- **Synergy Analysis**: All hero pairs analyzed in < 30 minutes
- **Database Queries**: < 1 second response time for analytical queries

### Data Quality Metrics

- **Match Deduplication**: Zero duplicate match_ids in database
- **Player Deduplication**: Zero duplicate usernames in database
- **Referential Integrity**: All match_participants reference valid matches and players
- **Sample Size Compliance**: No results reported below minimum thresholds (30/100/50)
- **Timestamp Accuracy**: All timestamps in UTC, within 1 second of API response

## Testing Plan

### Unit Tests

**Statistical Functions** (`tests/test_analysis/test_statistics.py`):
- `test_wilson_confidence_interval_known_values()`: Verify against pre-calculated intervals
- `test_wilson_confidence_interval_edge_cases()`: Test n=0, n=1, p=0, p=1
- `test_synergy_score_calculation()`: Verify expected vs. actual logic

**Data Processing** (`tests/test_collectors/test_data_processing.py`):
- `test_deduplicate_players()`: Verify duplicate removal by username
- `test_group_by_rank()`: Verify rank stratification
- `test_filter_matches_by_season()`: Verify season filtering

### Integration Tests

**End-to-End Pipeline** (`tests/test_integration/test_pipeline.py`):
- `test_discovery_to_collection()`: Discover 5 players, collect their matches
- `test_collection_to_analysis()`: Collect matches, calculate win rates
- `test_full_pipeline_small_sample()`: Run all 4 phases with 10 players

**Database Tests** (`tests/test_db/test_schema.py`):
- `test_match_deduplication()`: Insert same match twice, verify only one row
- `test_foreign_key_constraints()`: Verify cascading deletes
- `test_unique_constraints()`: Verify character_stats and synergy_stats uniqueness

### Manual Verification Steps

1. **Discovery Phase**:
   ```bash
   python scripts/discover_players.py --limit 50
   psql -c "SELECT rank_tier, COUNT(*) FROM players GROUP BY rank_tier;"
   # Verify: ~50 players distributed across ranks
   ```

2. **Collection Phase**:
   ```bash
   python scripts/collect_matches.py --batch-size 10
   psql -c "SELECT COUNT(DISTINCT match_id) FROM matches;"
   psql -c "SELECT COUNT(*) FROM match_participants;"
   # Verify: Matches > 0, Participants = Matches * 12
   ```

3. **Analysis Phase**:
   ```bash
   python scripts/analyze_characters.py
   cat output/character_win_rates.json | jq '.["Spider-Man"]'
   # Verify: JSON format correct, confidence intervals reasonable
   ```

4. **Synergy Phase**:
   ```bash
   python scripts/analyze_synergies.py
   cat output/synergies.json | jq '.["Spider-Man"].synergies[0]'
   # Verify: Top synergy has positive score, sample size > 50
   ```

## Implementation Tasks

### High-Level Task Breakdown

**Task Group 1: Infrastructure & Dependencies** (4-6 hours)
- Add scipy to requirements.txt
- Verify SPEC-004 completion (database + Docker)
- Implement rate limiter module
- Create logging configuration

**Task Group 2: Player Discovery** (6-8 hours)
- Implement leaderboard API client
- Implement stratified sampling algorithm
- Create discovery script with CLI
- Add progress tracking and resume logic
- Write unit tests

**Task Group 3: Match Collection** (8-10 hours)
- Implement match history API client
- Create match collector with rate limiting
- Implement deduplication logic
- Add error handling and retry logic
- Create collection script with CLI
- Write unit tests

**Task Group 4: Character Analysis** (6-8 hours)
- Implement Wilson confidence interval function
- Create character analyzer module
- Implement database caching
- Create JSON export function
- Create analysis script with CLI
- Write unit tests

**Task Group 5: Synergy Analysis** (8-10 hours)
- Implement synergy calculation algorithm
- Create synergy analyzer module
- Implement database caching
- Create JSON export function
- Create synergy script with CLI
- Write unit tests

**Task Group 6: Integration & Testing** (6-8 hours)
- Write end-to-end integration tests
- Perform manual testing with small sample
- Run full pipeline with 100 players
- Performance benchmarking
- Bug fixes

**Task Group 7: Documentation** (2-4 hours)
- Update README with usage instructions
- Document JSON export formats
- Create troubleshooting guide
- Document statistical methodology

**Detailed task breakdown will be in `tasks.md`**

## Timeline

**Total Estimated Effort**: 40-54 hours (~1-1.5 weeks full-time, 2-3 weeks part-time)

**Recommended Schedule**:

- **Week 1**: Infrastructure + Discovery + Collection (complete data collection)
- **Week 2**: Analysis + Synergy + Testing (generate results)
- **Week 3**: Integration testing, bug fixes, documentation

**Critical Path**: Discovery → Collection → Analysis (sequential dependencies)

**Parallel Work**: Synergy analysis can be developed in parallel with character analysis after collection is complete

## Open Questions

### Resolved Questions

1. **Q**: How do we handle players who appear in multiple ranks?
   - **A**: Use player's rank at time of discovery. Accept that rank may drift over time.

2. **Q**: Should we weight recent matches more heavily?
   - **A**: No for MVP. All matches have equal weight. Consider time-decay in future enhancement.

3. **Q**: How do we handle 3+ hero synergies?
   - **A**: Out of scope for MVP. Focus on pairwise synergies. Full team comp analysis is future work.

4. **Q**: What if a player has < 100 matches available?
   - **A**: Collect all available matches. Not a blocker. Aggregate across players provides sufficient data.

### Pending Questions

1. **Q**: What is the actual Marvel Rivals API structure?
   - **Status**: Assumed based on common patterns. Needs verification once API access available.
   - **Action**: Create mock API server for testing. Adjust collectors when real API available.

2. **Q**: Should synergy analysis be rank-stratified like character analysis?
   - **Status**: Nice to have, but pairwise samples may be too small (< 50 games).
   - **Action**: Implement for all ranks first. Add rank stratification if sample sizes permit.

3. **Q**: How do we handle patches/balance changes?
   - **Status**: Not addressed in MVP. All matches treated equally regardless of patch.
   - **Action**: Future enhancement: Track patch versions, filter by date range.

4. **Q**: Should we analyze role-specific synergies (e.g., Duelist + Strategist)?
   - **Status**: Good future enhancement, not MVP requirement.
   - **Action**: Add to backlog for Phase 2.

## References

### Related Specifications

- **SPEC-001: Player Discovery System** - Detailed player discovery requirements (consolidated into this spec)
- **SPEC-002: Match History Collection** - Detailed collection requirements (consolidated into this spec)
- **SPEC-003: Character Win Rate Analysis** - Detailed analysis requirements (consolidated into this spec)
- **SPEC-004: Project Scaffolding & Docker Setup** - Infrastructure prerequisite

### Documentation

- **Database Schema**: `/home/ericreyes/github/marvel-rivals-stats/migrations/001_initial_schema.sql`
- **Project Plan**: `/home/ericreyes/github/marvel-rivals-stats/PLAN.md`
- **Requirements**: `/home/ericreyes/github/marvel-rivals-stats/agent-os/specs/20251015-character-analysis-mvp/planning/requirements.md`

### External Resources

- **Wilson Score Confidence Interval**: https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval
- **Stratified Sampling**: https://en.wikipedia.org/wiki/Stratified_sampling
- **Synergy Analysis Methods**: https://en.wikipedia.org/wiki/Interaction_(statistics)

---

## Approval

- [ ] Technical review complete
- [ ] Database schema verified (SPEC-004 dependency)
- [ ] API assumptions documented
- [ ] Statistical methodology reviewed
- [ ] Stakeholder approval
- [ ] Ready for task breakdown and implementation
