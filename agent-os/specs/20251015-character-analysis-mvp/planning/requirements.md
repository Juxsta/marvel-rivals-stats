# Requirements: Character Analysis MVP

**Spec ID**: SPEC-005
**Status**: Draft
**Created**: 2025-10-15
**Consolidates**: SPEC-001 (Player Discovery), SPEC-002 (Match Collection), SPEC-003 (Character Analysis)

---

## Executive Summary

This specification merges the player discovery, match collection, and character analysis workflows into a single end-to-end data pipeline. The goal is to collect a statistically significant sample of match data, then analyze a specific character's win rates across different rank tiers and identify teammate synergies that increase win probability.

**Primary Use Case**: "For hero X, what is their win rate at each rank, and which teammates maximize their win probability?"

---

## User Goals

1. **Sample character-specific match data** across all rank tiers
2. **Calculate win rates** for a specific hero, stratified by rank (Bronze → Celestial)
3. **Identify teammate synergies** - which hero pairings have higher-than-expected win rates
4. **Provide statistical confidence** - include confidence intervals and minimum sample sizes
5. **Enable data export** - JSON output for sharing/visualization

---

## Consolidated Requirements

### Functional Requirements

#### FR1: Player Discovery System
- **FR1.1**: Discover players from Marvel Rivals API leaderboards
- **FR1.2**: Stratify discovery by rank tier (Bronze, Silver, Gold, Platinum, Diamond, Master, Grandmaster, Celestial)
- **FR1.3**: Apply configurable quotas per rank (default: 500 total players)
  - Bronze: 50 players
  - Silver: 75 players
  - Gold: 100 players
  - Platinum: 100 players
  - Diamond: 75 players
  - Master: 50 players
  - Grandmaster: 25 players
  - Celestial: 25 players
- **FR1.4**: Deduplicate players (don't re-discover existing players)
- **FR1.5**: Store player username, rank_tier, rank_score, discovered_at in database
- **FR1.6**: Mark players with match_history_fetched flag for tracking collection progress

#### FR2: Match History Collection
- **FR2.1**: Fetch match history for each discovered player (100-150 matches per player)
- **FR2.2**: Deduplicate matches by match_id (store each match only once)
- **FR2.3**: Extract match metadata:
  - match_id (unique identifier)
  - timestamp (when match was played)
  - map_name (e.g., "Tokyo 2099")
  - game_mode (e.g., "Ranked")
  - season (e.g., "Season 1")
- **FR2.4**: Extract match participants (12 players per match):
  - username
  - hero_name
  - role (Vanguard/Duelist/Strategist)
  - team (Red/Blue)
  - won (boolean)
  - kills, deaths, damage, healing (performance stats)
- **FR2.5**: Respect API rate limits (7 requests/minute, 10,000 requests/day)
- **FR2.6**: Support resumable collection (track which players have been fetched)
- **FR2.7**: Handle API errors gracefully (retry with exponential backoff)

#### FR3: Character Win Rate Analysis
- **FR3.1**: Calculate win rates for all heroes with sufficient data
- **FR3.2**: Stratify results by rank tier
- **FR3.3**: Calculate Wilson score confidence intervals (95% confidence)
- **FR3.4**: Filter results by minimum sample size:
  - Per-rank: 30 games minimum
  - Overall: 100 games minimum
- **FR3.5**: Output format:
  ```json
  {
    "hero_name": "Spider-Man",
    "overall": {
      "total_games": 1247,
      "wins": 689,
      "losses": 558,
      "win_rate": 0.5524,
      "confidence_interval_95": [0.5245, 0.5801]
    },
    "by_rank": {
      "Gold": {
        "total_games": 234,
        "wins": 135,
        "losses": 99,
        "win_rate": 0.5769,
        "confidence_interval_95": [0.5129, 0.6389]
      }
    }
  }
  ```
- **FR3.6**: Cache results in character_stats table with analyzed_at timestamp
- **FR3.7**: Export results to JSON file

#### FR4: Teammate Synergy Analysis (NEW)
- **FR4.1**: For a given hero, identify all teammates they've played with
- **FR4.2**: Calculate actual win rate when paired with each teammate
- **FR4.3**: Calculate expected win rate (baseline = hero's solo win rate × teammate's solo win rate)
- **FR4.4**: Compute synergy score: `(actual_win_rate - expected_win_rate)`
- **FR4.5**: Filter by minimum sample size (50 games together minimum)
- **FR4.6**: Rank teammates by synergy score (highest = best synergy)
- **FR4.7**: Calculate confidence intervals for synergy scores
- **FR4.8**: Output format:
  ```json
  {
    "hero": "Spider-Man",
    "rank_tier": "Gold",
    "synergies": [
      {
        "teammate": "Luna Snow",
        "games_together": 87,
        "wins_together": 52,
        "actual_win_rate": 0.5977,
        "expected_win_rate": 0.5200,
        "synergy_score": 0.0777,
        "confidence_interval_95": [0.4894, 0.6982]
      }
    ]
  }
  ```
- **FR4.9**: Cache results in synergy_stats table
- **FR4.10**: Export results to JSON file

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Collection pipeline must complete 500 players in < 24 hours
- **NFR1.2**: Analysis must complete for all heroes in < 10 minutes
- **NFR1.3**: Database queries must use indexes (response time < 1 second)
- **NFR1.4**: Connection pooling to handle concurrent operations

#### NFR2: Data Quality
- **NFR2.1**: No duplicate matches in database
- **NFR2.2**: No duplicate players in database
- **NFR2.3**: All match participants must reference valid matches (foreign key integrity)
- **NFR2.4**: Timestamps must be accurate (UTC timezone)

#### NFR3: Reliability
- **NFR3.1**: Collection must be resumable after interruption
- **NFR3.2**: API errors must not crash the pipeline (graceful degradation)
- **NFR3.3**: Database transactions must be atomic (rollback on failure)
- **NFR3.4**: Logging must capture all errors and warnings

#### NFR4: Statistical Rigor
- **NFR4.1**: Use Wilson score confidence intervals (not normal approximation)
- **NFR4.2**: Document all statistical assumptions
- **NFR4.3**: Include sample sizes in all outputs
- **NFR4.4**: Flag low-confidence results (sample size < threshold)

#### NFR5: Maintainability
- **NFR5.1**: Modular code structure (separate collectors, analyzers, utilities)
- **NFR5.2**: Comprehensive logging at INFO level
- **NFR5.3**: Configuration via environment variables
- **NFR5.4**: Unit tests for statistical functions
- **NFR5.5**: Integration tests for full pipeline

---

## Data Flow

```
┌─────────────────┐
│ 1. Discovery    │  Fetch leaderboards → Stratified sampling → Store players
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Collection   │  For each player → Fetch match history → Deduplicate → Store matches
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Analysis     │  Query match_participants → Group by hero/rank → Calculate win rates
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Synergy      │  For each hero → Find teammates → Calculate synergy scores → Export
└─────────────────┘
```

---

## Database Schema Requirements

### Existing Tables (from SPEC-004)
- ✅ `players` - Stores discovered players with rank information
- ✅ `matches` - Stores unique matches (deduplicated by match_id)
- ✅ `match_participants` - Links players to matches with performance stats
- ✅ `character_stats` - Caches calculated character win rates
- ✅ `synergy_stats` - Tracks two-hero synergy statistics
- ✅ `collection_metadata` - Stores collection progress metadata

### Schema Modifications Required
- **None** - Existing schema from SPEC-004 fully supports all requirements

---

## API Requirements

### Marvel Rivals API Endpoints (Assumed)
1. **Leaderboard Endpoint**: `/api/v1/leaderboard?rank={rank_tier}&limit=100`
   - Returns: List of players with username, rank_score
2. **Match History Endpoint**: `/api/v1/players/{username}/matches?limit=150`
   - Returns: List of matches with participants and stats
3. **Rate Limits**:
   - 7 requests per minute
   - 10,000 requests per day
   - 429 status code when exceeded

---

## Statistical Methodology

### Win Rate Confidence Intervals
Use **Wilson score interval** (more accurate than normal approximation for small samples):

```python
from scipy.stats import norm

def wilson_confidence_interval(wins, total, confidence=0.95):
    if total == 0:
        return (0, 0)

    p = wins / total
    z = norm.ppf(1 - (1 - confidence) / 2)  # 1.96 for 95%
    denominator = 1 + z**2 / total

    center = (p + z**2 / (2*total)) / denominator
    margin = z * ((p * (1 - p) / total + z**2 / (4 * total**2)) ** 0.5) / denominator

    return (max(0, center - margin), min(1, center + margin))
```

### Synergy Score Calculation
```python
# Actual win rate when paired
actual_wr = wins_together / games_together

# Expected win rate (independence assumption)
expected_wr = hero_a_win_rate * hero_b_win_rate

# Synergy score (positive = better than expected)
synergy_score = actual_wr - expected_wr
```

**Interpretation**:
- `synergy_score > 0`: Hero pair wins more than expected (positive synergy)
- `synergy_score < 0`: Hero pair wins less than expected (negative synergy)
- `synergy_score ≈ 0`: No synergy effect (independent performance)

### Sample Size Requirements
- **Per-rank win rates**: Minimum 30 games
- **Overall win rates**: Minimum 100 games
- **Synergy analysis**: Minimum 50 games together
- **Rationale**: Balances statistical power with data availability

---

## Success Criteria

### Acceptance Criteria
1. **AC1**: Pipeline discovers 500 players stratified by rank quotas
2. **AC2**: Pipeline collects 50,000+ unique matches (100 matches × 500 players)
3. **AC3**: Pipeline respects API rate limits (no 429 errors)
4. **AC4**: All 40+ heroes analyzed with win rates per rank tier
5. **AC5**: Synergy analysis identifies top 10 teammates for each hero
6. **AC6**: Results exported to JSON with confidence intervals
7. **AC7**: Pipeline is resumable (can restart without data loss)
8. **AC8**: All tests pass (unit + integration)

### Performance Benchmarks
- Discovery: 500 players in < 1 hour
- Collection: 50,000 matches in < 24 hours
- Analysis: All heroes in < 10 minutes
- Synergy: All hero pairs in < 30 minutes

---

## Out of Scope

- Real-time/live match tracking
- Player-specific performance tracking
- Hero matchup analysis (counter-picks)
- Build/loadout recommendations
- Map-specific win rates
- Team composition analysis (3+ hero synergies)
- Predictive modeling (ML)

---

## Dependencies

### External Dependencies
- Marvel Rivals API (assumed available)
- PostgreSQL 16 (from SPEC-004)
- Python 3.10+ (from SPEC-004)

### Python Libraries
- `psycopg2-binary` - PostgreSQL adapter (already in requirements.txt)
- `requests` - HTTP client for API calls (already in requirements.txt)
- `scipy` - Statistical functions (Wilson score)
- `python-dotenv` - Environment configuration (already in requirements.txt)

### Internal Dependencies
- SPEC-004 (Project Scaffolding) - **MUST BE COMPLETE**
  - Docker Compose setup
  - Database schema and migrations
  - Connection pooling module
  - Rate limiter

---

## Risks & Mitigations

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| API rate limits prevent data collection | High | Medium | Implement exponential backoff, distribute collection over 24+ hours |
| Insufficient sample sizes for rare heroes | Medium | High | Document sample sizes, filter low-confidence results |
| Player rank data becomes stale | Medium | Medium | Re-fetch player ranks periodically (future enhancement) |
| API endpoint changes/unavailable | High | Low | Mock API for testing, graceful error handling |
| Database fills disk space | Medium | Low | Monitor disk usage, implement data retention policy |
| Statistical calculations have bugs | High | Low | Use scipy library, add unit tests, manual verification |

---

## Implementation Phases

### Phase 1: Player Discovery (Week 1)
- Implement `collectors/player_discovery.py`
- Stratified sampling algorithm
- Database insertion with deduplication
- Progress tracking

### Phase 2: Match Collection (Week 1-2)
- Implement `collectors/match_collector.py`
- Rate-limited API client
- Match deduplication
- Resumable collection
- Progress reporting

### Phase 3: Character Analysis (Week 2)
- Implement `analyzers/character_winrate.py`
- Wilson confidence interval calculation
- Rank stratification
- Database caching
- JSON export

### Phase 4: Synergy Analysis (Week 2-3)
- Implement `analyzers/teammate_synergy.py`
- Synergy score calculation
- Confidence intervals
- Database caching
- JSON export

### Phase 5: Integration & Testing (Week 3)
- End-to-end integration tests
- Performance benchmarking
- Documentation updates
- Bug fixes

---

## Open Questions

1. ✅ **How do we handle players who play multiple ranks?**
   - **Answer**: Use player's rank at time of match (stored in match_participants via join with players table)

2. ✅ **Should we weight recent matches more heavily?**
   - **Answer**: No for MVP, all matches equal weight

3. ✅ **How do we handle 3+ hero synergies (full team comps)?**
   - **Answer**: Out of scope for MVP, focus on pairwise synergies

4. ⏳ **What is the actual Marvel Rivals API structure?**
   - **Status**: Assumed based on common patterns, needs verification

5. ⏳ **Should we analyze synergies within roles (e.g., Duelist + Strategist)?**
   - **Status**: Good future enhancement, not MVP requirement

---

## References

- **SPEC-001**: Player Discovery System (player quotas, stratified sampling)
- **SPEC-002**: Match History Collection (deduplication, rate limiting)
- **SPEC-003**: Character Win Rate Analysis (Wilson score, confidence intervals)
- **SPEC-004**: Project Scaffolding & Docker Setup (database schema, infrastructure)
- **Wilson Score Interval**: https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval
- **Database Schema**: `/home/ericreyes/github/marvel-rivals-stats/migrations/001_initial_schema.sql`

---

## Approval

- [ ] Technical review complete
- [ ] Stakeholder approval
- [ ] Ready for implementation
