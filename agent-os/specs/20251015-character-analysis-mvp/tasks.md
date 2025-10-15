# Tasks: SPEC-005 Character Analysis MVP

**Status**: In Progress
**Assignee**: Multiple
**Created**: 2025-10-15
**Target Completion**: 2025-11-05 (3 weeks)
**Estimated Total Time**: 40-54 hours

---

## Overview

This specification implements an end-to-end data pipeline for Marvel Rivals character analysis:
1. **Player Discovery** - Stratified sampling of 500 players across 8 rank tiers
2. **Match Collection** - Fetching 50,000+ matches with API rate limiting
3. **Character Win Rate Analysis** - Statistical analysis with Wilson confidence intervals
4. **Teammate Synergy Analysis** - Identifying positive/negative hero pairings

The implementation follows a sequential pipeline where each phase builds on the previous. Tasks are organized by specialist roles (database-engineer, api-engineer, testing-engineer) with clear dependencies and acceptance criteria.

**Key Principles**:
- Minimal test writing during development (2-8 tests per task group)
- Focus on critical path functionality
- Defer comprehensive testing to dedicated testing phase
- Each task group is independently verifiable

---

## Available Implementers

Based `/home/ericreyes/github/marvel-rivals-stats/agent-os/roles/implementers.yml`:

- **database-engineer**: Database schemas, queries, statistical analysis, complex SQL
- **api-engineer**: API integration, data collection, rate limiting, business logic
- **testing-engineer**: Test infrastructure, integration tests, test fixtures
- **Unassigned**: Documentation tasks, general infrastructure setup

---

## Task Breakdown

### Phase 1: Dependencies & Infrastructure Setup

#### Task Group 1: Dependencies & Module Structure
**Assigned implementer:** Unassigned (infrastructure task)
**Dependencies:** SPEC-004 (Project Scaffolding) must be complete
**Estimated Time:** 1-1.5 hours

- [x] **1.1**: Install scipy dependency
- [x] **1.2**: Create collectors module structure
- [x] **1.3**: Create analyzers module structure
- [x] **1.4**: Create scripts directory for CLI tools
- [x] **1.5**: Update pyproject.toml with new modules
- [x] **1.6**: Create output directory for exports

**Acceptance Criteria:**
- scipy successfully installed and importable
- All module directories created with proper __init__.py files
- Script placeholders exist with argparse structure
- Output directory ready for JSON exports
- All import statements work without errors

---

### Phase 2: Player Discovery System

#### Task Group 2: Player Discovery Implementation
**Assigned implementer:** api-engineer
**Dependencies:** Task Group 1
**Estimated Time:** 6-8 hours

- [x] **2.0**: Complete player discovery system

**Acceptance Criteria:**
- The 2-6 tests written in 2.1 pass
- Stratified sampling algorithm works correctly with configurable quotas
- API client successfully fetches leaderboard data
- Player deduplication prevents duplicates in database
- Metadata tracking records discovery progress
- CLI script runs successfully with --dry-run flag
- Total discovery time estimate: 6-8 hours

---

### Phase 3: Match Collection System

#### Task Group 3: Match Collection Implementation
**Assigned implementer:** api-engineer
**Dependencies:** Task Group 2
**Estimated Time:** 8-10 hours

- [x] **3.0**: Complete match collection system

**Acceptance Criteria:**
- The 2-6 tests written in 3.1 pass
- Match history API client successfully fetches player matches
- Match filtering correctly isolates competitive season matches
- Match deduplication prevents duplicate match_ids in database
- All 12 participants extracted and inserted for each match
- Collection is resumable (can stop and restart without data loss)
- Rate limiting enforced (8.6 seconds between requests)
- CLI script runs successfully with --dry-run flag
- Total collection time estimate: 8-10 hours

---

### Phase 4: Character Win Rate Analysis

#### Task Group 4: Character Win Rate Implementation
**Assigned implementer:** database-engineer
**Dependencies:** Task Group 3
**Estimated Time:** 6-8 hours

- [x] **4.0**: Complete character win rate analysis system

**Acceptance Criteria:**
- All 4 tests in 4.1 pass successfully
- Wilson confidence interval mathematically correct (verified with known values)
- Win rates calculated accurately for each rank tier
- Minimum sample size thresholds enforced (30 per rank, 100 overall)
- Results cached in character_stats table with proper ON CONFLICT handling
- JSON export contains all heroes with sufficient data
- CLI script runs successfully and produces valid output
- Top and bottom heroes correctly identified by win rate
- Total implementation time: 6-8 hours

---

### Phase 5: Teammate Synergy Analysis

#### Task Group 5: Teammate Synergy Implementation
**Assigned implementer:** database-engineer
**Dependencies:** Task Group 4
**Estimated Time:** 8-10 hours

- [x] **5.0**: Complete teammate synergy analysis system

**Acceptance Criteria:**
- All 5 tests in 5.1 pass successfully
- Character win rates successfully loaded from character_stats table cache
- Teammate pairs extracted correctly from match data
- Synergy score calculation mathematically correct (actual - expected)
- Expected win rate uses independence assumption (hero_wr * teammate_wr)
- Minimum games threshold enforced (50 games together)
- Top 10 synergies identified for each hero
- Results cached in synergy_stats table with hero_a < hero_b constraint
- JSON export contains synergies for all heroes with valid structure
- CLI script runs successfully and produces valid output
- Total implementation time: 8-10 hours

---

### Phase 6: Code Refactoring & Utilities

#### Task Group 6: Utility Module Implementation
**Assigned implementer:** api-engineer
**Dependencies:** Task Groups 4 & 5
**Estimated Time:** 2-3 hours

- [x] **6.0**: Complete utility functions refactoring
  - [x] **6.1**: Create statistics helper module
    - **Description**: Centralize statistical functions used across analyzers
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/src/utils/statistics.py`
    - **Functions to implement**:
      - `wilson_confidence_interval(wins, total, confidence=0.95)` - Moved from character_winrate.py
      - `calculate_win_rate(wins, losses)` - Simple win rate calculation
      - `calculate_expected_win_rate(wr_a, wr_b)` - For synergy analysis
    - **Files to modify**:
      - Update `src/analyzers/character_winrate.py` to import from statistics.py
      - Update `src/analyzers/teammate_synergy.py` to import from statistics.py
    - **Estimated time**: 45 minutes

  - [x] **6.2**: Verify API client helper functions
    - **Description**: Ensure API client methods are complete and working
    - **Files to review**: `/home/ericreyes/github/marvel-rivals-stats/src/api/client.py`
    - **Methods to verify**:
      - `get_leaderboard(limit)` - Working correctly
      - `get_hero_leaderboard(hero_id, limit)` - Working correctly
      - `get_player_matches(username, limit)` - Working correctly
    - **Note**: No changes needed if methods are already complete
    - **Estimated time**: 15 minutes

  - [x] **6.3**: Create database query helpers
    - **Description**: Centralize database query patterns
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/src/utils/db_helpers.py`
    - **Functions to implement**:
      - `execute_query(conn, query, params)` - Wrapper for SELECT queries returning List[Dict]
      - `execute_insert(conn, query, params)` - Wrapper for single INSERT
      - `execute_batch_insert(conn, query, params_list)` - Wrapper for executemany()
    - **Include**: Proper error handling and logging
    - **Estimated time**: 30 minutes

  - [x] **6.4**: Create logging configuration module
    - **Description**: Standardize logging setup across all modules
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/src/utils/logging_config.py`
    - **Functions to implement**:
      - `setup_logger(name, level='INFO')` - Configure logger with file and console handlers
    - **Format**: `[%(asctime)s] %(name)s - %(levelname)s - %(message)s`
    - **Handlers**:
      - File handler: logs/app.log
      - Console handler: stdout
    - **Note**: Create logs/ directory if it doesn't exist
    - **Estimated time**: 30 minutes

**Acceptance Criteria:**
- Statistics functions centralized in src.utils.statistics and importable
- API client methods (get_leaderboard, get_hero_leaderboard, get_player_matches) verified working
- Database helpers simplify query operations with proper error handling
- Logging configured consistently with file and console output
- No code duplication between collectors and analyzers
- All existing tests still pass after refactoring:
  - `pytest tests/test_analyzers/test_character_winrate.py -v`
  - `pytest tests/test_analyzers/test_teammate_synergy.py -v`
  - `pytest tests/test_collectors/ -v`
- Total implementation time: 2-3 hours

---

### Phase 7: Integration Testing

#### Task Group 7: Integration Testing
**Assigned implementer:** testing-engineer
**Dependencies:** Task Groups 2-6
**Estimated Time:** 3-4 hours

- [x] **7.0**: Complete integration testing for character analysis pipeline
  - [x] **7.1**: Review and run existing tests (20 minutes)
    - **Description**: Run all tests from Task Groups 2-5 and verify they pass
    - **Command**: `docker compose exec app pytest tests/test_collectors/ tests/test_analyzers/ -v`
    - **Expected**: All 19 tests should pass
    - **Document**: Current test count and any failures
    - **Estimated time**: 20 minutes

  - [x] **7.2**: Analyze test coverage gaps (30 minutes)
    - **Description**: Identify ONLY critical workflows lacking coverage
    - **Focus areas**:
      - End-to-end pipeline: discovery -> collection -> analysis -> synergy
      - Database integrity: deduplication, foreign keys, transactions
      - Error handling: API failures, rate limiting, rollback
    - **Skip**: Edge cases, performance tests, accessibility tests
    - **Deliverable**: Short list (5-10 items) of critical gaps
    - **Estimated time**: 30 minutes

  - [x] **7.3**: Write up to 10 strategic integration tests (2 hours)
    - **Description**: Write maximum 10 integration tests focusing on critical workflows
    - **File to create**: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_pipeline.py`
    - **Suggested tests** (pick most critical):
      1. Test full pipeline with small dataset (5 players)
      2. Test match deduplication across multiple players
      3. Test database transaction rollback on error
      4. Test resumable collection (restart after interruption)
      5. Test JSON export format validity
      6. Test confidence interval calculations end-to-end
      7. Test synergy score calculations with real data
      8. Test minimum sample size filtering
      9. Test API error handling (429/500)
      10. Test rate limiter enforces delays
    - **Use**: Mock API responses for faster execution
    - **Constraint**: Maximum 10 tests - be very selective
    - **Estimated time**: 2 hours

  - [x] **7.4**: Run feature-specific tests (15 minutes)
    - **Description**: Run all tests related to this feature
    - **Command**: `docker compose exec app pytest tests/test_collectors/ tests/test_analyzers/ tests/test_integration/test_pipeline.py -v`
    - **Expected**: ~20-28 tests total (19 existing + 0-10 new)
    - **Verify**: All tests pass
    - **Document**: Final test count and results
    - **Estimated time**: 15 minutes

  - [x] **7.5**: Manual validation checklist (45 minutes)
    - **Description**: Execute manual validation steps with small datasets
    - **Steps**:
      1. Run discovery script: `docker compose exec app python scripts/discover_players.py --dry-run --limit 10`
      2. Run collection script: `docker compose exec app python scripts/collect_matches.py --dry-run --batch-size 5`
      3. Run character analysis: `docker compose exec app python scripts/analyze_characters.py`
      4. Run synergy analysis: `docker compose exec app python scripts/analyze_synergies.py`
      5. Verify database integrity: Check for duplicates, orphaned records
      6. Verify JSON exports: Check format and data validity
    - **Document**: Results of each validation step
    - **Estimated time**: 45 minutes

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 20-28 tests total)
- Critical user workflows for this feature are covered
- No more than 10 additional tests added by testing-engineer
- Testing focused exclusively on this spec's feature requirements
- Manual validation checklist completed successfully
- Total integration testing time estimate: 3-4 hours
