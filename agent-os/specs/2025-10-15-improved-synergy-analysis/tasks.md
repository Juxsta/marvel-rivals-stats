# Task Breakdown: Improved Synergy Analysis Methodology

## Overview
Total Task Groups: 8 (Phase 1: 8 groups, Phase 2: Optional Bayesian enhancement)
Estimated Timeline: Phase 1 = 1-2 days, Phase 2 = 1-2 days (optional)

## Available Implementers
- **database-engineer**: Database migrations, models, schemas, queries
- **api-engineer**: API endpoints, business logic, analyzers, CLI scripts
- **testing-engineer**: Unit tests, integration tests, test fixtures
- **unassigned**: Utilities, documentation, simple refactoring

---

## PHASE 1: METHODOLOGY FIX

### Task Group 1: Statistical Utilities Enhancement
**Assigned implementer:** api-engineer
**Dependencies:** None
**Estimated Complexity:** Medium (5-7 functions, statistical formulas)

- [x] 1.0 Add new statistical utility functions to `src/utils/statistics.py`
  - [x] 1.1 Write 2-4 focused tests for new statistical functions
    - Test `expected_wr_average()` with edge cases (0%, 50%, 100% win rates)
    - Test `binomial_test_synergy()` with known examples
    - Test `bonferroni_correction()` with multiple p-values
    - Test `calculate_required_sample_size()` against statistical tables
  - [x] 1.2 Add `expected_wr_average()` function
    - Implement average baseline model: `(wr_a + wr_b) / 2`
    - Add comprehensive docstring explaining rationale
    - Round to 4 decimal places for consistency
    - Handle edge cases (0.0, 1.0 win rates)
  - [x] 1.3 Add `expected_wr_additive()` function (optional baseline)
    - Implement additive model: `0.5 + (wr_a - 0.5) + (wr_b - 0.5)`
    - Cap result at 1.0 maximum
    - Document when to use vs average model
  - [x] 1.4 Add `binomial_test_synergy()` function
    - Use `scipy.stats.binomtest()` for two-sided test
    - Accept wins, total, expected_wr, alpha parameters
    - Return dict with p_value and significant boolean
    - Round p_value to 4 decimal places
  - [x] 1.5 Add `bonferroni_correction()` function
    - Accept list of synergy dictionaries with p_value keys
    - Calculate corrected alpha: `alpha / n_comparisons`
    - Add `significant_bonferroni` and `bonferroni_alpha` fields
    - Return updated synergies list
  - [x] 1.6 Add `calculate_required_sample_size()` function
    - Implement formula for two-proportion z-test
    - Use scipy.stats.norm for z-scores
    - Parameters: baseline_wr, effect_size, alpha=0.05, power=0.80
    - Return integer sample size (rounded up)
  - [x] 1.7 Add deprecation warning to `calculate_expected_win_rate()`
    - Add docstring note that multiplicative model is deprecated
    - Reference new `expected_wr_average()` function
    - Keep function for backward compatibility (Phase 1)
  - [x] 1.8 Run utility tests only
    - Execute ONLY the 2-4 tests written in 1.1
    - Verify all new functions work correctly
    - Do NOT run entire test suite

**Acceptance Criteria:**
- The 2-4 tests written in 1.1 pass
- All new statistical functions implemented with clear docstrings
- Functions return correctly rounded values (4 decimals)
- Edge cases handled (0%, 100% win rates)
- Deprecation warning added to old function

---

### Task Group 2: Database Schema Updates
**Assigned implementer:** database-engineer
**Dependencies:** None (can run in parallel with Task Group 1)
**Estimated Complexity:** Low (2-3 migration tasks)

- [x] 2.0 Update database schema for enhanced synergy analysis
  - [x] 2.1 Create migration script for new columns
    - Add `confidence_lower REAL` to `synergy_stats`
    - Add `confidence_upper REAL` to `synergy_stats`
    - Add `p_value REAL` to `synergy_stats`
    - Add `sample_size_warning TEXT` to `synergy_stats`
    - Add `baseline_model TEXT DEFAULT 'average'` to `synergy_stats`
    - Use individual columns (not JSONB) for queryability
  - [x] 2.2 Create index for significance queries
    - Add index on `p_value` column: `CREATE INDEX idx_synergy_significance ON synergy_stats(p_value) WHERE p_value IS NOT NULL`
    - Improves query performance for filtering significant synergies
  - [x] 2.3 Test migration script
    - Run migration on test database
    - Verify new columns exist with correct types
    - Verify defaults apply correctly
    - Verify index created successfully

**Acceptance Criteria:**
- Migration script runs without errors
- New columns added to `synergy_stats` table
- Index created for p_value queries
- Existing data unaffected (backward compatible)
- Migration can be rolled back if needed

---

### Task Group 3: Core Synergy Analysis Refactor
**Assigned implementer:** api-engineer
**Dependencies:** Task Group 1 (requires new statistical utilities)
**Estimated Complexity:** High (6-8 modifications to core analyzer)

- [x] 3.0 Refactor `src/analyzers/teammate_synergy.py` to use new methodology
  - [x] 3.1 Write 2-6 focused tests for refactored analyzer
    - Test synergy calculation with average baseline
    - Test confidence interval inclusion in results
    - Test p-value calculation and significance flags
    - Test Bonferroni correction application
    - Test sample size warning generation
    - Test database caching with new fields
  - [x] 3.2 Update imports in `teammate_synergy.py`
    - Import `expected_wr_average` from `src.utils.statistics`
    - Import `binomial_test_synergy` from `src.utils.statistics`
    - Import `bonferroni_correction` from `src.utils.statistics`
    - Import `calculate_required_sample_size` from `src.utils.statistics`
  - [x] 3.3 Replace baseline calculation in `analyze_teammate_synergies()`
    - Change from `calculate_expected_win_rate()` to `expected_wr_average()`
    - Update variable name to clarify model used
    - Add comment explaining average model rationale
  - [x] 3.4 Add p-value calculation for each synergy
    - Call `binomial_test_synergy()` with wins, games, expected_wr
    - Add `p_value` and `significant` fields to synergy_data dict
    - Perform test after calculating synergy_score
  - [x] 3.5 Apply Bonferroni correction to all synergies
    - Collect all synergies for a hero before sorting
    - Call `bonferroni_correction()` on full synergies list
    - Add `significant_bonferroni` and `bonferroni_alpha` fields
    - Log count of significant results (uncorrected vs corrected)
  - [x] 3.6 Add sample size warnings to synergy results
    - Define thresholds: high=500, medium=100
    - Add `confidence_level` field: 'high', 'medium', 'low'
    - Add `warning` field with appropriate message for low/medium
    - Include warning in synergy_data dict
  - [x] 3.7 Update `cache_synergy_stats()` function
    - Add new fields to INSERT statement: confidence_lower, confidence_upper, p_value, sample_size_warning, baseline_model
    - Update ON CONFLICT clause to include new fields
    - Pass confidence interval bounds from Wilson CI
    - Pass p_value from binomial test
    - Set baseline_model to 'average'
  - [x] 3.8 Update logging for transparency
    - Log number of synergies tested per hero
    - Log count of significant results (uncorrected): `sum(s['significant'] for s in synergies)`
    - Log count of significant results (Bonferroni): `sum(s['significant_bonferroni'] for s in synergies)`
    - Log count of low sample size warnings
  - [x] 3.9 Run analyzer tests only
    - Execute ONLY the 2-6 tests written in 3.1
    - Verify synergies calculated with new methodology
    - Do NOT run entire test suite at this stage

**Acceptance Criteria:**
- The 2-6 tests written in 3.1 pass
- Analyzer uses average baseline model instead of multiplicative
- All synergies include p_value, significance flags, and warnings
- Bonferroni correction applied correctly
- Database caching includes all new fields
- Logging provides transparency about statistical results

---

### Task Group 4: CLI Script Updates
**Assigned implementer:** api-engineer
**Dependencies:** Task Group 3 (requires refactored analyzer)
**Estimated Complexity:** Medium (4-5 CLI enhancements)

- [x] 4.0 Update `scripts/analyze_synergies.py` CLI with new flags and output
  - [x] 4.1 Add `--baseline` argument to parser
    - Choices: ['average', 'additive']
    - Default: 'average'
    - Help text: "Baseline model for expected win rate"
    - Pass to analyzer function
  - [x] 4.2 Add `--alpha` argument to parser
    - Type: float
    - Default: 0.05
    - Help text: "Significance level for hypothesis tests"
    - Validate range: 0.001 to 0.10
  - [x] 4.3 Add `--min-sample-size` argument to parser
    - Type: int
    - Default: 50 (current MIN_GAMES_TOGETHER)
    - Help text: "Minimum games to report a synergy"
    - Update existing --min-games to use this
  - [x] 4.4 Update `print_summary()` to show new statistics
    - Add section: "Statistical Significance Summary"
    - Show count of synergies significant at uncorrected alpha
    - Show count of synergies significant with Bonferroni correction
    - Show Bonferroni corrected alpha value
    - Display confidence intervals in synergy listings: `[CI: 52%-68%]`
    - Add asterisk (*) for Bonferroni-significant synergies
    - Show warnings for low sample sizes
  - [x] 4.5 Add power analysis summary section
    - After main results, add "Power Analysis" section
    - Call `calculate_required_sample_size()` for 3%, 5%, 10% effects
    - Display: "To detect 5% synergy with 80% power: 600 games required"
    - Show current max sample size vs requirements
    - Add interpretation: "Current data insufficient for detecting <10% synergies"
  - [x] 4.6 Update argparse examples in docstring
    - Add example: `python scripts/analyze_synergies.py --baseline average --alpha 0.01`
    - Add example: `python scripts/analyze_synergies.py --min-sample-size 100`
    - Update help text with new flags

**Acceptance Criteria:**
- New CLI flags work correctly (--baseline, --alpha, --min-sample-size)
- Summary output includes significance statistics
- Confidence intervals displayed for all synergies
- Power analysis section educates users about sample size needs
- Bonferroni-significant synergies clearly marked
- Help text and examples updated

---

### Task Group 5: JSON Export Format Updates
**Assigned implementer:** api-engineer
**Dependencies:** Task Group 3 (requires refactored analyzer)
**Estimated Complexity:** Low (2-3 export updates)

- [x] 5.0 Update JSON export format with new fields
  - [x] 5.1 Update `export_to_json()` function in `teammate_synergy.py`
    - Verify all new synergy_data fields included in export
    - Add `methodology_version: "2.0"` field to root
    - Add `baseline_model` field to root
    - Ensure backward compatibility (no fields removed)
  - [x] 5.2 Add power_analysis section to JSON export
    - Calculate sample sizes for 3%, 5%, 10% effects
    - Add to each hero's results: `power_analysis` object
    - Include: `current_max_samples`, `required_for_3pct`, `required_for_5pct`, `required_for_10pct`
    - Use representative baseline (e.g., 0.5) for calculations
  - [x] 5.3 Test JSON export structure
    - Export sample results to test file
    - Verify all new fields present
    - Verify JSON is valid (parseable)
    - Verify existing tools can read new format

**Acceptance Criteria:**
- JSON export includes all new fields from analyzer
- Power analysis data included for each hero
- Methodology version field added for tracking
- Backward compatible (existing fields unchanged)
- Valid JSON structure

---

### Task Group 6: Unit Tests
**Assigned implementer:** testing-engineer
**Dependencies:** Task Groups 1, 3, 4 (requires implementation complete)
**Estimated Complexity:** Medium (6-8 test cases)

- [x] 6.0 Write comprehensive unit tests for new methodology
  - [x] 6.1 Test baseline model functions (2 tests)
    - Test `expected_wr_average()` edge cases: (0.5, 0.5)→0.5, (0.6, 0.4)→0.5, (0.7, 0.5)→0.6
    - Test `expected_wr_additive()` caps at 1.0: (0.9, 0.9)→1.0
  - [x] 6.2 Test statistical significance functions (3 tests)
    - Test `binomial_test_synergy()` returns correct p_value structure
    - Test `bonferroni_correction()` with known p-values: [0.01, 0.04, 0.10] with alpha=0.05, n=3
    - Test Wilson CI integration with new analyzer flow
  - [x] 6.3 Test sample size calculation (2 tests)
    - Test `calculate_required_sample_size()` for 5% effect at baseline=0.5: expect ~600-700 games
    - Test formula with different effect sizes (3%, 10%)
  - [x] 6.4 Update existing synergy analyzer tests (3 tests)
    - Update `test_analyze_teammate_synergies()` to expect new fields
    - Update assertions to check for p_value, confidence_interval_95, significant_bonferroni
    - Update expected baseline calculation (will be higher than old multiplicative)
  - [x] 6.5 Run all unit tests for statistical utilities and analyzer
    - Run tests for `src/utils/statistics.py`
    - Run tests for `src/analyzers/teammate_synergy.py`
    - Verify all tests pass (18 total: 6 statistical + 12 analyzer)

**Acceptance Criteria:**
- All 18 unit tests pass (6 statistical utilities + 12 analyzer tests)
- Edge cases covered (0%, 100% win rates, sample size extremes)
- Statistical formulas verified against known examples
- Existing tests updated to reflect new methodology
- Test coverage for all new functions

---

### Task Group 7: Integration Tests
**Assigned implementer:** testing-engineer
**Dependencies:** Task Group 6 (requires unit tests passing)
**Estimated Complexity:** Medium (3-4 integration tests)

- [x] 7.0 Write integration tests for end-to-end pipeline
  - [x] 7.1 Create test database fixture
    - Generate synthetic match data with known synergies
    - Include matches for 5-10 test heroes
    - Ensure sufficient sample sizes (100+ games per pair)
    - Seed character_stats table with individual win rates
  - [x] 7.2 Test full analysis pipeline (1 test)
    - Run `analyze_teammate_synergies()` on test database
    - Verify all new fields present in results
    - Verify Bonferroni correction reduces significant count
    - Verify warnings generated for small samples
    - Check database caching includes new columns
  - [x] 7.3 Comparison test: old vs new methodology (1 test)
    - Calculate same synergy with old multiplicative model
    - Calculate same synergy with new average model
    - Verify new baseline is higher (e.g., 0.535 vs 0.286)
    - Verify synergy score is smaller (e.g., +6.4% vs +39.1%)
    - Document magnitude of change
  - [x] 7.4 Validation test with Hulk data (1 test)
    - Run analysis on actual Hulk + Luna Snow pair (207 games, 124 wins)
    - Expected baseline: ~53.5% (average of individual rates)
    - Expected synergy: ~+6% (not +39%)
    - Verify p_value computed correctly
    - Verify realistic score range (±2-10%, not ±25-30%)
  - [x] 7.5 Run all integration tests
    - Execute 3 integration tests
    - Verify end-to-end pipeline works
    - Do NOT run entire test suite, only integration tests for this feature

**Acceptance Criteria:**
- All 3 integration tests pass
- End-to-end pipeline produces correct results
- Old vs new methodology comparison shows expected differences
- Validation with real data (Hulk) confirms realistic scores
- Database caching works with new schema

---

### Task Group 8: Documentation
**Assigned implementer:** unassigned
**Dependencies:** Task Groups 1-7 (requires implementation complete)
**Estimated Complexity:** Medium (5 documentation files)

- [x] 8.0 Update project documentation for methodology change
  - [x] 8.1 Update README.md
    - Add "Methodology Improvement" subsection under Synergy Analysis
    - Mention change from multiplicative to average baseline
    - Link to STATISTICS.md for details
    - Update example output to show confidence intervals
    - Note: "v2.0 uses statistically defensible methodology"
  - [x] 8.2 Update STATISTICS.md
    - Add section: "Synergy Analysis Methodology"
    - Explain average baseline model with formula
    - Add subsection: "Why Not Multiplicative?" explaining flaw
    - Document statistical testing approach (Wilson CI, binomial test, Bonferroni)
    - Add example calculation with Hulk + Luna Snow
    - Include sample size requirements table (3%→1700 games, 5%→600 games, 10%→150 games)
  - [x] 8.3 Create MIGRATION_SYNERGY_V2.md
    - Section: "Why Did Results Change?" - explain multiplicative flaw
    - Section: "Before vs After" - comparison table with examples
    - Section: "What Stayed the Same?" - rankings, database schema
    - Section: "What Changed?" - baseline, magnitudes, significance
    - Section: "FAQ" - address common questions
    - Provide reassurance that new results are correct
  - [x] 8.4 Update troubleshooting.md
    - Add entry: "Why did synergy scores decrease after updating?"
    - Explain old methodology was flawed, new is correct
    - Add entry: "What does 'insufficient sample size' warning mean?"
    - Explain thresholds: <100 games = unreliable, 100-500 = moderate, 500+ = reliable
    - Document sample size requirements for detecting realistic synergies
  - [x] 8.5 Create CHANGELOG.md entry
    - Version: [2.0.0] - 2025-10-15
    - Section: "Changed - BREAKING" - methodology fix
    - Describe change from multiplicative to average baseline
    - List new features: confidence intervals, significance testing, warnings
    - Section: "Migration Guide" - link to MIGRATION_SYNERGY_V2.md
    - Note: synergy scores now realistic (±3-7%) instead of inflated (±25-30%)

**Acceptance Criteria:**
- README.md updated with methodology improvement notice
- STATISTICS.md includes detailed explanation of new methodology
- MIGRATION_SYNERGY_V2.md created with comprehensive guide
- troubleshooting.md includes entries for common questions
- CHANGELOG.md documents breaking change and migration path
- All documentation uses clear, non-technical language where possible

---

## PHASE 2: BAYESIAN ANALYSIS (OPTIONAL)

### Task Group 9: Bayesian Implementation
**Assigned implementer:** api-engineer
**Dependencies:** Phase 1 complete
**Estimated Complexity:** Medium (5-6 Bayesian enhancements)
**Status:** Optional - only implement if requested

- [ ] 9.0 Add Bayesian synergy estimation alongside frequentist analysis
  - [ ] 9.1 Write 2-4 focused tests for Bayesian functions
    - Test `bayesian_synergy_estimate()` posterior calculation
    - Test credible interval computation
    - Test probability of positive synergy
    - Test prior strength parameter sensitivity
  - [ ] 9.2 Add `bayesian_synergy_estimate()` to `src/utils/statistics.py`
    - Implement Beta-Binomial conjugate prior
    - Accept wins, total, expected_wr, prior_strength parameters
    - Calculate posterior: Beta(α + wins, β + losses)
    - Compute posterior mean and 95% credible interval
    - Calculate P(true WR > expected WR)
    - Return dict with posterior_mean, credible_interval, prob_positive_synergy
  - [ ] 9.3 Add `--bayesian` flag to `scripts/analyze_synergies.py`
    - Boolean flag (action='store_true')
    - Help text: "Include Bayesian estimates alongside frequentist results"
    - Pass to analyzer function
  - [ ] 9.4 Integrate Bayesian estimation in analyzer
    - When `--bayesian` flag set, call `bayesian_synergy_estimate()` for each synergy
    - Add fields: `bayesian_posterior_mean`, `bayesian_credible_interval_95`, `prob_positive_synergy`
    - Include in synergy_data dict and JSON export
  - [ ] 9.5 Update output formatting for Bayesian results
    - Add subsection in summary: "Bayesian Estimates"
    - Display credible intervals: [Bayesian CI: 48%-64%]
    - Show P(positive synergy) as percentage
    - Note substantial evidence when prob > 95%
  - [ ] 9.6 Document Bayesian interpretation
    - Add section to STATISTICS.md: "Bayesian Analysis (Optional)"
    - Explain Beta-Binomial conjugate prior
    - Describe credible intervals vs confidence intervals
    - Provide guidance on when to use Bayesian approach (small samples)
  - [ ] 9.7 Run Bayesian tests only
    - Execute ONLY the 2-4 tests written in 9.1
    - Verify Bayesian calculations correct
    - Do NOT run entire test suite

**Acceptance Criteria:**
- The 2-4 tests written in 9.1 pass
- Bayesian estimation function implemented correctly
- `--bayesian` flag works and produces additional output
- Bayesian results included in JSON export when enabled
- Documentation explains Bayesian interpretation clearly
- Prior strength configurable (default: 20)

---

## Execution Order

### Sequential Dependencies
1. **Task Group 1** (Statistical Utilities) MUST complete before Task Group 3 (Analyzer Refactor)
2. **Task Group 2** (Database Schema) can run in parallel with Task Group 1
3. **Task Group 3** (Analyzer Refactor) MUST complete before Task Groups 4, 5
4. **Task Groups 4, 5** (CLI and Export) can run in parallel
5. **Task Group 6** (Unit Tests) requires Task Groups 1, 3, 4 complete
6. **Task Group 7** (Integration Tests) requires Task Group 6 complete
7. **Task Group 8** (Documentation) should be last (requires all implementation complete)

### Recommended Implementation Sequence
1. **Start**: Task Groups 1 and 2 in parallel
2. **Then**: Task Group 3 (after 1 completes)
3. **Then**: Task Groups 4 and 5 in parallel (after 3 completes)
4. **Then**: Task Group 6 (after 4 and 5 complete)
5. **Then**: Task Group 7 (after 6 completes)
6. **Finally**: Task Group 8 (after all implementation and testing complete)
7. **Optional**: Task Group 9 (Phase 2, if requested)

---

## Testing Philosophy

Following project standards for minimal testing during development:

- **Write 2-6 tests per task group** - focus on critical behaviors only
- **Test behavior, not implementation** - verify what code does, not how
- **Run only feature-specific tests** - do NOT run entire test suite during development
- **Final verification** - Task Group 7 runs full integration tests
- **Total expected tests**: ~16-24 tests maximum for Phase 1

### Test Distribution
- Task Group 1: 5 tests (statistical utilities)
- Task Group 3: 6 tests (analyzer refactor)
- Task Group 6: 1 additional test (Wilson CI integration)
- Task Group 7: 3-4 tests (integration tests)
- **Total**: 15-16 tests (focused, high-value coverage)

---

## Notes

### Code Reuse Opportunities
- **Wilson CI**: Already implemented in `src/utils/statistics.py` (reuse directly)
- **Database caching pattern**: Follow approach from `src/analyzers/character_winrate.py`
- **CLI structure**: Follow patterns from `scripts/analyze_characters.py`
- **Logging patterns**: Maintain consistency with existing analyzers

### Key Files to Modify
1. `src/utils/statistics.py` - Add 5-7 new functions (Task Group 1)
2. `src/analyzers/teammate_synergy.py` - Refactor core analysis (Task Group 3)
3. `scripts/analyze_synergies.py` - Add CLI flags and output (Task Group 4)
4. `tests/test_analyzers/test_teammate_synergy.py` - Update existing tests (Task Group 6)

### Performance Considerations
- No performance concerns (analysis is fast)
- New calculations are O(1) per synergy
- Bonferroni correction is O(N) where N = number of synergies
- Database indexes created for p_value queries (Task Group 2)

### Backward Compatibility
- Database schema: additive only (no columns removed)
- JSON export: additive only (new fields added)
- CLI flags: new flags added, existing flags work unchanged
- Old `calculate_expected_win_rate()` kept with deprecation warning

### Risk Mitigation
- **User confusion about smaller scores**: Addressed by comprehensive documentation (Task Group 8)
- **All synergies non-significant**: Expected with current data - power analysis educates users
- **Comparison with old results**: Integration test documents differences (Task Group 7.3)
