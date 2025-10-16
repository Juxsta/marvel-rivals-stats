# Task 5: Teammate Synergy Implementation

## Overview
**Task Reference:** Task Group 5 from `/home/ericreyes/github/marvel-rivals-stats/agent-os/specs/20251015-character-analysis-mvp/tasks.md`
**Implemented By:** database-engineer
**Date:** 2025-10-15
**Status:** Complete

### Task Description
Implement the teammate synergy analysis system that identifies hero pairings with positive/negative win rates compared to expected values based on individual hero performance. The system calculates synergy scores using the independence assumption: positive scores indicate pairs that win more than expected, while negative scores indicate anti-synergies.

## Implementation Summary

The teammate synergy analysis system analyzes hero pairings across all matches to identify which combinations perform better or worse than expected. The core algorithm:

1. Loads cached character win rates from the `character_stats` table (from Task Group 4)
2. For each hero, queries all matches they participated in
3. Extracts teammates from each match (same team, excluding the hero itself)
4. Aggregates statistics: games together and wins together for each teammate pair
5. Calculates actual win rate when paired together
6. Calculates expected win rate using independence assumption: `expected_wr = hero_a_wr × hero_b_wr`
7. Computes synergy score: `synergy_score = actual_wr - expected_wr`
8. Filters pairs by minimum games threshold (50 games default)
9. Caches results in `synergy_stats` table with alphabetical ordering constraint
10. Returns top 10 synergies per hero sorted by synergy score

The implementation emphasizes performance logging (this is an expensive operation: N heroes × M matches × ~5 teammates per match) and mathematical correctness of the independence assumption.

## Files Changed/Created

### New Files
- `tests/test_analyzers/test_teammate_synergy.py` - Unit tests for synergy calculation logic (5 tests covering core calculations)
- `src/analyzers/teammate_synergy.py` - Main synergy analysis module with statistical calculations and database queries

### Modified Files
- `scripts/analyze_synergies.py` - CLI script for running synergy analysis (replaced placeholder implementation)
- `agent-os/specs/20251015-character-analysis-mvp/tasks.md` - Added Task Group 5 with all subtasks marked complete

### Deleted Files
- None

## Key Implementation Details

### Synergy Score Calculation
**Location:** `src/analyzers/teammate_synergy.py` (lines 38-54)

The synergy score is calculated as the difference between actual and expected win rates:

```python
def calculate_synergy_score(actual_wr: float, expected_wr: float) -> float:
    """Calculate synergy score as difference from expected win rate.

    Positive score = better than expected (positive synergy)
    Negative score = worse than expected (anti-synergy)
    Zero score = performance matches expectation
    """
    return round(actual_wr - expected_wr, 4)
```

**Rationale:** This simple difference metric is easy to interpret: a synergy score of +0.0777 means the pair wins 7.77% more often than expected, indicating strong positive synergy. The independence assumption (heroes don't affect each other) provides the baseline expectation.

### Expected Win Rate (Independence Assumption)
**Location:** `src/analyzers/teammate_synergy.py` (lines 21-35)

The expected win rate assumes heroes perform independently:

```python
def calculate_expected_win_rate(hero_wr: float, teammate_wr: float) -> float:
    """Calculate expected win rate using independence assumption.

    Under independence: P(A and B both win) = P(A wins) * P(B wins)
    """
    return hero_wr * teammate_wr
```

**Rationale:** This probabilistic approach assumes that if Spider-Man wins 55% of his games and Luna Snow wins 52% of her games, we'd expect them to win together 28.6% of the time (0.55 × 0.52 = 0.286) if they don't influence each other. Any deviation from this expectation indicates synergy or anti-synergy.

### Teammate Extraction from Matches
**Location:** `src/analyzers/teammate_synergy.py` (lines 129-165)

For each hero, the algorithm queries all matches they played in, then for each match, queries teammates on the same team:

```python
def query_match_teammates(
    conn: PgConnection,
    match_id: str,
    team: int,
    exclude_hero: str
) -> List[str]:
    """Query teammates in a specific match.

    SQL: SELECT hero_name FROM match_participants
         WHERE match_id = %s AND team = %s AND hero_name != %s
    """
```

**Rationale:** This two-step query approach (matches first, then teammates) is necessary because each match can have up to 6 players per team, and we need to track which specific heroes were on the same team in each match. The `exclude_hero` parameter ensures we don't count a hero as their own teammate.

### Database Caching with Alphabetical Constraint
**Location:** `src/analyzers/teammate_synergy.py` (lines 168-213)

The caching function enforces alphabetical ordering to prevent duplicate synergy pairs:

```python
def cache_synergy_stats(...):
    # Ensure alphabetical order
    if hero_a > hero_b:
        hero_a, hero_b = hero_b, hero_a

    INSERT INTO synergy_stats (hero_a, hero_b, ...)
    ON CONFLICT (hero_a, hero_b, COALESCE(rank_tier, ''))
    DO UPDATE SET ...
```

**Rationale:** The database schema has a CHECK constraint `hero_a < hero_b` to prevent storing both (Spider-Man, Luna Snow) and (Luna Snow, Spider-Man). By normalizing to alphabetical order before insertion, we ensure only one entry exists per pair, which simplifies queries and prevents data duplication.

### Performance Optimization and Logging
**Location:** `src/analyzers/teammate_synergy.py` (lines 216-355)

The main analysis function logs progress for each hero analyzed:

```python
for hero in heroes:
    logger.info(f"Analyzing {hero}...")
    # ... analysis logic ...
    logger.info(
        f"  {hero}: {len(synergies)} total synergies, "
        f"top synergy: {synergies[0]['teammate']} "
        f"({synergies[0]['synergy_score']:.4f})"
    )
```

**Rationale:** This is a computationally expensive operation (for 40 heroes with 1000 matches each and 5 teammates per match, that's 200,000 teammate extractions). Frequent logging helps monitor progress and identify performance bottlenecks. The algorithm commits after each hero to save incremental progress.

## Database Changes

### Migrations
- None (used existing schema from SPEC-004)

### Schema Impact
The implementation uses the existing `synergy_stats` table with these key fields:
- `hero_a, hero_b` (TEXT, NOT NULL): Hero pair with alphabetical constraint
- `rank_tier` (TEXT, nullable): Rank stratification (NULL = all ranks)
- `games_together, wins_together` (INTEGER): Raw statistics
- `win_rate, expected_win_rate, synergy_score` (DECIMAL): Calculated metrics
- `analyzed_at` (TIMESTAMP): Analysis timestamp

The unique index `idx_synergy_stats_unique` on `(hero_a, hero_b, COALESCE(rank_tier, ''))` ensures no duplicate pairs.

## Dependencies

### New Dependencies Added
- None (all dependencies already installed in Task Group 1)

### Configuration Changes
- None

## Testing

### Test Files Created/Updated
- `tests/test_analyzers/test_teammate_synergy.py` - 5 focused unit tests

### Test Coverage
- Unit tests: Complete (5 tests)
  - `test_calculate_synergy_score` - Verifies synergy score calculation (actual - expected)
  - `test_calculate_expected_win_rate` - Verifies independence assumption formula
  - `test_extract_teammates_from_match` - Verifies teammate extraction logic
  - `test_filter_by_min_games` - Verifies minimum games threshold filtering
  - `test_synergy_score_rounding` - Verifies 4 decimal place rounding
- Integration tests: None (deferred to Task Group 6)
- Edge cases covered:
  - Positive, negative, and zero synergy scores
  - Different hero win rate combinations
  - Minimum games threshold enforcement
  - Proper teammate exclusion (hero not counted as their own teammate)

### Manual Testing Performed
1. Ran all unit tests: `docker compose exec app pytest tests/test_analyzers/test_teammate_synergy.py -v`
   - Result: All 5 tests passed
2. Verified CLI script help: `docker compose exec app python scripts/analyze_synergies.py --help`
   - Result: Help output shows all command-line options correctly
3. Code review: Verified synergy score calculation matches spec.md algorithm (lines 554-582)

## User Standards & Preferences Compliance

### backend/queries.md
**File Reference:** `/home/ericreyes/github/marvel-rivals-stats/agent-os/standards/backend/queries.md`

**How Implementation Complies:**
The teammate synergy queries use proper parameterized queries with type hints and clear function signatures. The `query_hero_matches()` and `query_match_teammates()` functions follow the standard pattern of accepting a PgConnection, using context managers for cursor handling, and returning typed results (List[Dict] and List[str] respectively). All queries use `%s` placeholders for safe parameter binding.

**Deviations:** None

### backend/models.md
**File Reference:** `/home/ericreyes/github/marvel-rivals-stats/agent-os/standards/backend/models.md`

**How Implementation Complies:**
The implementation uses the existing database models from SPEC-004 without modification. The `synergy_stats` table structure follows the standard model pattern with proper constraints (CHECK for alphabetical ordering, unique index for deduplication) and nullable fields (rank_tier) handled correctly in queries.

**Deviations:** None

### global/coding-style.md
**File Reference:** `/home/ericreyes/github/marvel-rivals-stats/agent-os/standards/global/coding-style.md`

**How Implementation Complies:**
All functions include comprehensive docstrings with Args, Returns, and description sections. Type hints are used throughout (Dict[str, float], List[str], Optional[str]). The code follows Python naming conventions (snake_case for functions, UPPER_CASE for constants like MIN_GAMES_TOGETHER). Line length stays under 100 characters where practical. Logging uses structured messages at appropriate levels (INFO for progress, WARNING for missing data).

**Deviations:** None

### global/error-handling.md
**File Reference:** `/home/ericreyes/github/marvel-rivals-stats/agent-os/standards/global/error-handling.md`

**How Implementation Complies:**
The CLI script wraps the main execution in try/except blocks and logs errors with full stack traces (`exc_info=True`). The analysis function handles missing data gracefully (e.g., teammates not in character_stats are logged and skipped). Database errors bubble up to the CLI layer for proper handling and user-friendly error messages.

**Deviations:** None

### testing/test-writing.md
**File Reference:** `/home/ericreyes/github/marvel-rivals-stats/agent-os/standards/testing/test-writing.md`

**How Implementation Complies:**
Tests focus on core calculation logic without database integration (minimal testing philosophy). The 5 tests cover the most critical functionality: synergy score calculation, expected win rate formula, and data filtering. Test names clearly describe what is being tested. Tests use pytest.approx for floating-point comparisons with appropriate tolerance (abs=0.001).

**Deviations:** None

## Integration Points

### APIs/Endpoints
- None (this is a data analysis module, not an API)

### External Services
- None

### Internal Dependencies
- **character_stats table** (from Task Group 4): Source of cached character win rates for expected value calculations
- **match_participants table** (from Task Group 3): Source of match data for teammate extraction
- **wilson_confidence_interval()** (from character_winrate.py): Reused for confidence interval calculations on actual win rates

## Known Issues & Limitations

### Issues
None identified

### Limitations
1. **Performance on Large Datasets**
   - Description: Analysis is O(N × M × T) where N = heroes, M = matches per hero, T = teammates per match. For 40 heroes with 1000 matches each, this is ~200,000 database queries.
   - Reason: The algorithm queries teammates for each match individually rather than using a single aggregation query.
   - Future Consideration: Optimize with a single SQL query using window functions or JOIN aggregations to reduce query count from 200,000 to 1.

2. **Independence Assumption Simplification**
   - Description: The expected win rate assumes heroes don't affect each other (P(A and B) = P(A) × P(B)), which may not hold for heroes with role synergies (e.g., tank + healer).
   - Reason: This is the simplest statistical baseline. More complex models (e.g., logistic regression) would require significantly more implementation complexity.
   - Future Consideration: Add role-specific baseline expectations or use machine learning models for expected win rates.

3. **Rank Stratification Not Implemented**
   - Description: Analysis only supports all-ranks aggregation (rank_tier=NULL). Per-rank synergy analysis is not implemented.
   - Reason: Sample sizes for hero pairs at specific ranks may be too small (< 50 games) for statistical significance.
   - Future Consideration: Implement rank-stratified analysis if data collection reaches sufficient volume (e.g., 100,000+ matches).

## Performance Considerations

The synergy analysis is the most expensive operation in the entire pipeline:
- **Time Complexity**: O(N × M × T) where N = number of heroes, M = matches per hero, T = teammates per match
- **Estimated Runtime**: For 40 heroes with 1000 matches each and 5 teammates per match = ~200,000 teammate queries
- **Database Load**: Each hero requires 1000+ queries (1 for matches + 1 per match for teammates)

**Optimization Opportunities**:
1. Batch teammate queries using `WHERE match_id IN (...)` to reduce round trips
2. Use a single SQL aggregation query with JOINs to calculate all synergies in one pass
3. Add database indexes on (match_id, team) in match_participants table for faster teammate lookups

**Current Mitigation**:
- Progress logging every hero to monitor performance
- Database commits after each hero to save incremental progress
- Clear documentation of computational complexity in code comments

## Security Considerations

All database queries use parameterized statements with `%s` placeholders to prevent SQL injection. No user input is directly concatenated into SQL queries. The CLI script validates file paths before writing (creates parent directories if needed) and handles file write errors gracefully.

## Dependencies for Other Tasks

This implementation completes the core data pipeline for SPEC-005. The synergy analysis results can be used by:
- Task Group 6 (Integration & Testing): End-to-end pipeline testing with real data
- Task Group 7 (Documentation): Documenting the synergy analysis methodology and JSON export format
- Future enhancements: Web UI for visualizing synergies, API endpoints for querying synergy data

## Notes

### Implementation Observations
1. The synergy score formula (actual - expected) is remarkably simple yet effective for identifying hero pairs that outperform expectations.
2. The alphabetical ordering constraint (hero_a < hero_b) in the database schema elegantly prevents duplicate synergy pairs without application-layer deduplication logic.
3. Reusing `wilson_confidence_interval()` from character_winrate.py demonstrates good code reuse and consistency across analysis modules.
4. The two-step query approach (matches first, then teammates per match) is necessary but could be optimized with SQL window functions or aggregation queries.

### Lessons Learned
1. **Frequent Logging is Critical**: For long-running operations, logging progress for each hero helps monitor execution and identify performance issues.
2. **Test Calculation Logic Separately**: By testing core functions (calculate_synergy_score, calculate_expected_win_rate) without database integration, we achieved fast, focused tests that verify mathematical correctness.
3. **Database Constraints Simplify Code**: The CHECK constraint `hero_a < hero_b` in the schema eliminates the need for application-layer validation and deduplication.

### Future Enhancements
1. **Performance Optimization**: Rewrite main query as single SQL aggregation to reduce from 200,000 queries to 1
2. **Rank Stratification**: Add per-rank synergy analysis if data volume permits
3. **Statistical Significance**: Add p-value calculation to identify statistically significant synergies (currently just use confidence intervals)
4. **Role-Based Analysis**: Extend to analyze role combinations (e.g., Duelist + Strategist synergies)
