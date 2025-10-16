# Task Breakdown: Test Quality and CI/CD Implementation

## Overview
**Total Task Groups:** 9
**Total Estimated Time:** 7-11 hours
**Assigned Implementers:** testing-engineer, general-purpose
**Critical Path:** Phase 1 (Test Fixes) → Phase 2 (CI Implementation) → Phase 3 (Documentation)

## Dependencies

```
┌────────────────── PHASE 1: Fix Failing Tests (4-6 hours) ──────────────────┐
│                                                                              │
│  Task Group 1: Numpy Serialization (1-2h) ────┐                            │
│  Task Group 2: Fixture Isolation (1-2h) ──────┼──→ All Tests Pass          │
│  Task Group 3: Seed Data Issues (1h) ─────────┤                            │
│  Task Group 4: Assertion Mismatch (30m) ──────┘                            │
│                                                                              │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ↓
┌────────────────── PHASE 2: Implement CI/CD (2-3 hours) ────────────────────┐
│                                                                              │
│  Task Group 5: Create GitHub Actions Workflow (1h)                          │
│                                    │                                         │
│                                    ↓                                         │
│  Task Group 6: Test CI Locally (30m-1h)                                     │
│                                    │                                         │
│                                    ↓                                         │
│  Task Group 7: Deploy and Verify CI (30m-1h)                                │
│                                                                              │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ↓
┌────────────────── PHASE 3: Documentation (1-2 hours) ──────────────────────┐
│                                                                              │
│  Task Group 8: Update Documentation (1-1.5h)                                │
│                                    │                                         │
│                                    ↓                                         │
│  Task Group 9: Test Audit - Optional (30m-1h)                               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Task List

### PHASE 1: Fix Failing Tests

---

#### Task Group 1: Fix Numpy Serialization Issues
**Assigned Implementer:** testing-engineer
**Dependencies:** None
**Estimated Time:** 1-2 hours
**Priority:** High (blocks CI implementation)

**Problem Statement:**
4 integration tests fail with numpy type serialization errors when inserting test data into PostgreSQL. Numpy int64/float64 types are being passed to psycopg2, which PostgreSQL misinterprets as schema names.

**Affected Tests:**
- `tests/test_integration/test_pipeline.py` - 2 tests
- `tests/test_integration/test_workflow.py` - 2 tests

**Tasks:**
- [x] 1.1 Investigate numpy serialization failures
  - Run failing tests to confirm error messages
  - Identify which fixtures are inserting numpy types
  - Document specific fields causing issues (likely rank_score, win_rate, etc.)

- [x] 1.2 Create type conversion utility module
  - Create `tests/test_utils/type_conversion.py`
  - Implement `convert_numpy_types(value)` function
  - Handle numpy.integer → Python int
  - Handle numpy.floating → Python float
  - Handle numpy.ndarray → Python list
  - Add docstrings and type hints

- [x] 1.3 Update affected test fixtures
  - Locate fixtures in `tests/test_integration/test_pipeline.py`
  - Locate fixtures in `tests/test_integration/test_workflow.py`
  - Import type conversion utility
  - Apply type conversion before database INSERT operations
  - Follow pattern: `value = convert_numpy_types(value)`

- [x] 1.4 Verify numpy serialization fixes
  - Run: `pytest tests/test_integration/test_pipeline.py -v`
  - Run: `pytest tests/test_integration/test_workflow.py -v`
  - Confirm all 4 previously failing tests now pass
  - Check no new failures introduced

**Acceptance Criteria:**
- Type conversion utility handles all numpy types correctly
- All 4 affected tests pass without numpy serialization errors
- Type conversion applied consistently across all test fixtures
- No impact on tests that were already passing

**Files to Modify:**
- Create: `/home/ericreyes/github/marvel-rivals-stats/tests/test_utils/type_conversion.py`
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_pipeline.py`
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_workflow.py`

**Rollback Plan:**
If type conversion introduces new issues, revert changes and investigate using psycopg2 adapters instead.

---

#### Task Group 2: Fix Fixture Isolation Issues
**Assigned Implementer:** testing-engineer
**Dependencies:** None (can run in parallel with Task Group 1)
**Estimated Time:** 1-2 hours
**Priority:** High (blocks CI implementation)

**Problem Statement:**
4 integration tests fail due to duplicate key violations. Multiple tests insert data with the same IDs, causing unique constraint violations when tests run together. Tests lack proper isolation.

**Affected Tests:**
- `tests/test_integration/test_pipeline.py` - 2 tests
- `tests/test_integration/test_workflow.py` - 2 tests

**Tasks:**
- [x] 2.1 Analyze fixture isolation failures
  - Run failing tests individually and together to confirm root cause
  - Identify which fixtures share IDs (match_id, player_id, etc.)
  - Review successful pattern in `test_synergy_analysis.py::synergy_test_data`
  - Document current cleanup/teardown mechanisms

- [x] 2.2 Implement unique test data ID pattern
  - Create helper function `create_unique_test_id(test_name, prefix="test")`
  - Use UUID or timestamp to ensure uniqueness
  - Pattern: `f"{prefix}_{test_name}_{uuid.uuid4().hex[:8]}"`
  - Add to `tests/test_utils/` module

- [x] 2.3 Update fixtures with unique IDs
  - Update affected fixtures to use unique ID generator
  - Apply to match_id, player_id, character_id fields
  - Ensure IDs are unique per test invocation, not per test file

- [x] 2.4 Implement proper cleanup/teardown
  - Review existing cleanup in `conftest.py`
  - Add explicit DELETE statements in fixture teardown
  - Use try/finally blocks to ensure cleanup runs
  - Model after `synergy_test_data` fixture pattern
  - Consider transaction rollback approach

- [x] 2.5 Verify fixture isolation fixes
  - Run: `pytest tests/test_integration/ -v`
  - Run tests multiple times to verify no race conditions
  - Confirm all 4 previously failing tests now pass
  - Verify no data leakage between tests

**Acceptance Criteria:**
- Each test uses unique IDs that don't conflict with other tests
- Proper cleanup ensures no data persists after test completion
- Tests can run in any order without failures
- Tests can run multiple times consecutively without cleanup issues
- All 4 affected tests pass consistently

**Files to Modify:**
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_utils/type_conversion.py` (or create new utilities file)
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_pipeline.py`
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_workflow.py`
- Potentially: `/home/ericreyes/github/marvel-rivals-stats/tests/conftest.py`

**Rollback Plan:**
If unique IDs cause issues, fall back to transaction rollback pattern exclusively.

---

#### Task Group 3: Fix Seed Data Issues
**Assigned Implementer:** testing-engineer
**Dependencies:** None (can run in parallel with Task Groups 1-2)
**Estimated Time:** 1 hour
**Priority:** High (blocks CI implementation)

**Problem Statement:**
3 integration tests fail because they expect seed data to exist, but fixtures either don't create the data or cleanup is too aggressive and removes required data before tests run.

**Affected Tests:**
- `tests/test_integration/test_synergy_analysis.py` - 3 older tests (not the new passing ones)

**Tasks:**
- [x] 3.1 Identify missing seed data
  - Run failing tests with verbose output
  - Document which tables/data tests expect to exist
  - Check fixture dependencies and execution order
  - Identify if issue is missing creation or premature cleanup

- [x] 3.2 Review fixture dependency chain
  - Map out fixture dependencies using `usefixtures` decorator
  - Ensure parent fixtures run before child fixtures
  - Verify seed data fixtures are properly scoped (session, module, function)
  - Check if `autouse=True` is needed for any fixtures

- [x] 3.3 Add seed data creation where missing
  - Update or create fixtures to generate required seed data
  - Follow pattern from working `synergy_test_data` fixture
  - Ensure data is created in correct order (foreign key dependencies)
  - Add meaningful test data that aligns with test expectations

- [x] 3.4 Add data existence assertions
  - Add pre-test assertions to verify seed data exists
  - Pattern: `assert player_count > 0, "Fixture should have created test players"`
  - Add debug logging to show what data was created
  - Fail fast with clear error messages if data missing

- [x] 3.5 Verify seed data fixes
  - Run: `pytest tests/test_integration/test_synergy_analysis.py -v`
  - Confirm all 3 previously failing tests now pass
  - Verify seed data is created in correct order
  - Check no impact on the 2 already-passing synergy tests

**Acceptance Criteria:**
- All required seed data is created before tests run
- Fixtures have correct dependency order
- Tests include assertions verifying data exists before proceeding
- All 3 affected tests pass consistently
- No regression in already-passing tests

**Files to Modify:**
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_synergy_analysis.py`
- Potentially: `/home/ericreyes/github/marvel-rivals-stats/tests/conftest.py`

**Rollback Plan:**
If seed data changes break working tests, isolate seed data creation per test instead of sharing fixtures.

---

#### Task Group 4: Fix Assertion Mismatch
**Assigned Implementer:** testing-engineer
**Dependencies:** None (can run in parallel with Task Groups 1-3)
**Estimated Time:** 30 minutes
**Priority:** High (blocks CI implementation)

**Problem Statement:**
1 integration test fails due to hardcoded expected values that don't match the actual calculated values. Likely a floating-point precision issue requiring `pytest.approx()`.

**Affected Tests:**
- `tests/test_integration/test_synergy_analysis.py::test_confidence_intervals` (or similar)

**Tasks:**
- [x] 4.1 Identify assertion mismatch
  - Run failing test to see expected vs actual values
  - Document the discrepancy (e.g., expected 0.55, got 0.5498)
  - Determine if issue is floating-point precision or logic error

- [x] 4.2 Update assertion with pytest.approx()
  - Replace exact equality with `pytest.approx(expected, abs=tolerance)`
  - Use appropriate tolerance (e.g., abs=0.05 for percentages, abs=0.01 for small floats)
  - Pattern: `assert actual == pytest.approx(expected, abs=0.05)`
  - Add comment explaining why approximation is needed

- [x] 4.3 Verify assertion fix
  - Run: `pytest tests/test_integration/test_synergy_analysis.py -v`
  - Confirm the 1 previously failing test now passes
  - Verify tolerance is appropriate (not too loose)
  - Check no regression in other synergy tests

**Acceptance Criteria:**
- Assertion uses `pytest.approx()` with appropriate tolerance
- Test passes consistently
- Tolerance is justified (not masking a real bug)
- Clear comment explains the approximation

**Files to Modify:**
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_synergy_analysis.py`

**Rollback Plan:**
If `pytest.approx()` masks a real bug, investigate calculation logic instead of assertion.

---

### PHASE 2: Implement CI/CD Pipeline

---

#### Task Group 5: Create GitHub Actions Workflow
**Assigned Implementer:** general-purpose
**Dependencies:** Task Groups 1-4 (all tests must pass first)
**Estimated Time:** 1 hour
**Priority:** High

**Problem Statement:**
No CI/CD pipeline exists. Need automated testing on every push and pull request to catch issues early and ensure code quality.

**Tasks:**
- [ ] 5.1 Create GitHub Actions workflow directory
  - Create directory: `.github/workflows/`
  - Verify directory structure is correct

- [ ] 5.2 Create CI workflow file
  - Create file: `.github/workflows/ci.yml`
  - Follow structure from spec (3 jobs: lint, unit-tests, integration-tests)
  - Use Ubuntu latest runner
  - Use Python 3.10 (match project requirement)

- [ ] 5.3 Configure lint job
  - Set up Python 3.10
  - Install: black, ruff, mypy
  - Run: `black --check src/ scripts/ tests/`
  - Run: `ruff check src/ scripts/ tests/`
  - Run: `mypy src/ scripts/`
  - Job should fail fast if linting fails

- [ ] 5.4 Configure unit tests job
  - Set up Python 3.10
  - Install: `pip install -r requirements.txt -r requirements-dev.txt`
  - Run: `pytest tests/ -v --ignore=tests/test_integration/`
  - Only run unit tests (exclude integration tests)

- [ ] 5.5 Configure integration tests job
  - Set up PostgreSQL service container (postgres:16-alpine)
  - Environment variables:
    - POSTGRES_DB: marvel_rivals_test
    - POSTGRES_USER: marvel_stats
    - POSTGRES_PASSWORD: test_password
  - Health check: pg_isready with retries
  - Port mapping: 5432:5432

- [ ] 5.6 Add database migration step
  - Run migrations from `migrations/` directory in order
  - Use psql command line client
  - Pattern: `for migration in migrations/*.sql; do psql -h localhost -U marvel_stats -d marvel_rivals_test -f "$migration"; done`
  - Set PGPASSWORD environment variable

- [ ] 5.7 Run integration tests
  - Run: `pytest tests/test_integration/ -v`
  - Set environment variables:
    - DATABASE_URL: postgresql://marvel_stats:test_password@localhost:5432/marvel_rivals_test
    - MARVEL_RIVALS_API_KEY: mock_key_for_testing

- [ ] 5.8 Configure workflow triggers
  - Trigger on: push to main branch
  - Trigger on: pull requests to main branch
  - Add clear job names and descriptions

**Acceptance Criteria:**
- Workflow file is valid YAML
- All three jobs are properly configured
- PostgreSQL service container is set up correctly
- Migrations run in correct order
- Environment variables are properly set
- Workflow structure matches spec template

**Files to Create:**
- Create: `/home/ericreyes/github/marvel-rivals-stats/.github/workflows/ci.yml`

**Rollback Plan:**
If workflow has issues, disable it by renaming file extension until fixed.

---

#### Task Group 6: Test CI Pipeline Locally
**Assigned Implementer:** general-purpose
**Dependencies:** Task Group 5
**Estimated Time:** 30 minutes - 1 hour
**Priority:** High

**Problem Statement:**
Need to verify CI workflow works before pushing to GitHub to avoid wasting GitHub Actions minutes and iterating on live CI.

**Tasks:**
- [ ] 6.1 Install act tool
  - Install act: `curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash`
  - Or: `brew install act` (if on macOS)
  - Or: Download from GitHub releases
  - Verify installation: `act --version`

- [ ] 6.2 Test lint job locally
  - Run: `act -j lint`
  - Verify black, ruff, mypy run correctly
  - Fix any linting errors found
  - Confirm job completes successfully

- [ ] 6.3 Test unit tests job locally
  - Run: `act -j unit-tests`
  - Verify tests run and pass
  - Check for any dependency issues
  - Confirm job completes successfully

- [ ] 6.4 Test integration tests job locally
  - Run: `act -j integration-tests`
  - Verify PostgreSQL container starts
  - Verify migrations run successfully
  - Verify integration tests pass
  - Debug any local-specific issues

- [ ] 6.5 Run full workflow locally
  - Run: `act push` (simulates push event)
  - Verify all jobs run in parallel or sequence as expected
  - Check total execution time (should be under 5 minutes)
  - Fix any issues discovered

**Acceptance Criteria:**
- Act tool installed and working
- All jobs pass locally with act
- No errors or warnings in workflow execution
- Execution time is reasonable (under 5 minutes)
- Workflow behaves as expected

**Files to Modify:**
- Update: `/home/ericreyes/github/marvel-rivals-stats/.github/workflows/ci.yml` (if issues found)

**Rollback Plan:**
If act testing reveals major issues, fix workflow before proceeding to Task Group 7.

**Note:** Act may not perfectly replicate GitHub Actions environment, so some issues may only appear in real CI.

---

#### Task Group 7: Deploy and Verify CI Pipeline
**Assigned Implementer:** general-purpose
**Dependencies:** Task Group 6
**Estimated Time:** 30 minutes - 1 hour
**Priority:** High

**Problem Statement:**
Need to deploy CI workflow to GitHub and verify it runs correctly in the real GitHub Actions environment.

**Tasks:**
- [ ] 7.1 Commit and push workflow to GitHub
  - Stage workflow file: `git add .github/workflows/ci.yml`
  - Commit: `git commit -m "Add GitHub Actions CI pipeline for automated testing"`
  - Push to main branch: `git push origin main`
  - Do NOT push if any tests are still failing locally

- [ ] 7.2 Verify workflow triggers on push
  - Navigate to GitHub repository Actions tab
  - Confirm workflow run appears for the push
  - Monitor workflow execution in real-time
  - Check all jobs start and complete

- [ ] 7.3 Review workflow logs
  - Review lint job logs for any warnings
  - Review unit tests job logs for test output
  - Review integration tests job logs:
    - PostgreSQL container startup
    - Migration execution
    - Test execution and results
  - Verify all jobs pass (green checkmarks)

- [ ] 7.4 Test workflow on pull request
  - Create a test branch: `git checkout -b test-ci-pr`
  - Make a trivial change (e.g., update README)
  - Commit and push: `git push origin test-ci-pr`
  - Create pull request to main branch
  - Verify workflow runs on PR
  - Verify status checks appear on PR

- [ ] 7.5 Debug any remote-specific issues
  - If workflow fails, review error logs
  - Common issues:
    - Environment variable access
    - File path differences
    - Permission issues
    - Service container networking
  - Fix issues and push updates
  - Iterate until workflow passes

- [ ] 7.6 Verify workflow stability
  - Re-run workflow manually to confirm consistency
  - Check execution time (should be under 5 minutes)
  - Confirm no flaky tests or intermittent failures

**Acceptance Criteria:**
- Workflow deployed to GitHub successfully
- Workflow runs on push to main
- Workflow runs on pull requests to main
- All jobs pass consistently
- Execution time is under 5 minutes
- No flaky or intermittent failures
- Status checks appear on pull requests

**Files to Modify:**
- Update: `/home/ericreyes/github/marvel-rivals-stats/.github/workflows/ci.yml` (if remote issues found)

**Rollback Plan:**
If workflow causes issues, disable by removing or renaming workflow file, fix issues, and re-enable.

---

### PHASE 3: Documentation and Cleanup

---

#### Task Group 8: Update Documentation
**Assigned Implementer:** general-purpose
**Dependencies:** Task Group 7
**Estimated Time:** 1-1.5 hours
**Priority:** Medium

**Problem Statement:**
Documentation needs to reflect new CI pipeline and provide guidance for developers on running tests and understanding CI failures.

**Tasks:**
- [x] 8.1 Add CI badge to README
  - Add GitHub Actions badge at top of README.md
  - Badge URL: `https://github.com/[owner]/[repo]/actions/workflows/ci.yml/badge.svg`
  - Link to Actions page: `https://github.com/[owner]/[repo]/actions`
  - Format: `[![CI](badge-url)](actions-url)`
  - Place prominently near project title

- [x] 8.2 Update Testing section in README
  - Document how to run tests locally:
    - All tests: `pytest tests/ -v`
    - Unit tests only: `pytest tests/ -v --ignore=tests/test_integration/`
    - Integration tests only: `pytest tests/test_integration/ -v`
  - Add section on CI checks:
    - "All pull requests must pass CI checks before merging"
    - Link to Actions tab for CI history
  - Document test requirements:
    - PostgreSQL must be running for integration tests
    - Environment variables must be set (DATABASE_URL)

- [x] 8.3 Add Contributing section to README
  - Create or update Contributing section
  - Mention CI checks run on all PRs
  - Encourage running tests locally before pushing
  - Link to development documentation

- [x] 8.4 Update docs/development.md
  - Create file if it doesn't exist
  - Document CI pipeline structure:
    - Three jobs: lint, unit-tests, integration-tests
    - PostgreSQL service container for integration tests
    - Migration execution process
  - Explain how to run tests locally before pushing
  - Add section on debugging test failures

- [x] 8.5 Add troubleshooting guide
  - Create or update docs/troubleshooting.md
  - Add "Test Failures" section:
    - Common fixture isolation issues
    - Numpy serialization errors
    - Database connection issues
    - Migration failures
  - Add "CI Failures" section:
    - How to read GitHub Actions logs
    - Common CI-specific issues
    - How to test workflow locally with act

- [x] 8.6 Add inline comments to CI workflow
  - Add comments explaining each job
  - Document why PostgreSQL service is configured as it is
  - Explain migration execution pattern
  - Add comments on environment variable usage
  - Make workflow self-documenting

**Acceptance Criteria:**
- CI badge displays correctly in README and shows current status
- Testing documentation is clear and complete
- Contributing section mentions CI requirements
- Development docs explain CI pipeline
- Troubleshooting guide covers common issues
- CI workflow file is well-commented
- All documentation is accurate and helpful

**Files to Modify:**
- Update: `/home/ericreyes/github/marvel-rivals-stats/README.md`
- Update or Create: `/home/ericreyes/github/marvel-rivals-stats/docs/development.md`
- Update or Create: `/home/ericreyes/github/marvel-rivals-stats/docs/troubleshooting.md`
- Update: `/home/ericreyes/github/marvel-rivals-stats/.github/workflows/ci.yml`

**Rollback Plan:**
Documentation changes are low-risk and can be updated incrementally based on feedback.

---

#### Task Group 9: Test Audit and Cleanup (OPTIONAL)
**Assigned Implementer:** testing-engineer
**Dependencies:** Task Groups 1-8
**Estimated Time:** 30 minutes - 1 hour
**Priority:** Low (optional, nice-to-have)

**Problem Statement:**
Per spec, some tests may be "trivial" and not test meaningful business logic. Audit existing tests and remove or consolidate tests that don't add value.

**Test Philosophy (from spec):**
- Tests should validate business logic (e.g., synergy calculation correctness)
- Tests should cover edge cases (e.g., 0 wins, 100% win rate)
- Tests should cover error handling (e.g., missing data, invalid inputs)
- Tests should NOT test trivial getters/setters
- Tests should NOT test library code (pytest, scipy, etc.)
- Tests should NOT test implementation details

**Tasks:**
- [ ] 9.1 Review all test files for trivial tests
  - Review: `tests/test_integration/test_pipeline.py`
  - Review: `tests/test_integration/test_workflow.py`
  - Review: `tests/test_integration/test_synergy_analysis.py`
  - Review: `tests/test_integration/test_docker.py`
  - Identify tests that are trivial or redundant

- [ ] 9.2 Categorize tests for removal
  - Document tests that:
    - Test basic getters/setters
    - Test library functionality (not our code)
    - Test implementation details (should test behavior)
    - Are duplicates of other tests
    - Don't test meaningful business logic
  - Get approval before removing any tests

- [ ] 9.3 Remove or consolidate trivial tests
  - Remove identified trivial tests
  - Consolidate redundant tests into single comprehensive test
  - Ensure no business logic coverage is lost
  - Document what was removed and why

- [ ] 9.4 Verify all remaining tests pass
  - Run: `pytest tests/ -v`
  - Confirm all tests still pass after cleanup
  - Verify no critical coverage was lost
  - Check that test suite still covers all user stories

- [ ] 9.5 Document test audit results
  - Create summary of tests removed
  - Explain rationale for each removal
  - Note any business logic coverage gaps discovered
  - Recommend any future testing improvements

**Acceptance Criteria:**
- All remaining tests validate meaningful business logic
- No trivial or redundant tests remain
- Test suite still passes (100% pass rate)
- No critical coverage lost during cleanup
- Audit results documented
- Test suite is leaner and more focused

**Files to Modify:**
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_pipeline.py`
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_workflow.py`
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_synergy_analysis.py`
- Update: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_docker.py`
- Create: `/home/ericreyes/github/marvel-rivals-stats/docs/test-audit.md` (audit summary)

**Rollback Plan:**
If test removal causes coverage concerns, restore removed tests and reconsider approach.

**Note:** This task group is OPTIONAL and should only be done if time permits. It's not blocking for CI/CD implementation.

---

## Testing Strategy

### Phase 1 Verification (After Each Task Group)
```bash
# After Task Group 1 (Numpy Serialization)
pytest tests/test_integration/test_pipeline.py -v
pytest tests/test_integration/test_workflow.py -v
# Expected: 4 previously failing tests now pass

# After Task Group 2 (Fixture Isolation)
pytest tests/test_integration/ -v
# Expected: 4 previously failing tests now pass, no race conditions

# After Task Group 3 (Seed Data)
pytest tests/test_integration/test_synergy_analysis.py -v
# Expected: 3 previously failing tests now pass

# After Task Group 4 (Assertion Mismatch)
pytest tests/test_integration/test_synergy_analysis.py -v
# Expected: 1 previously failing test now pass
```

### Phase 1 Complete Verification
```bash
# Run ALL tests to confirm 100% pass rate
pytest tests/ -v
# Expected: 59/59 tests pass (0% failure rate)

# Run multiple times to confirm no flakiness
pytest tests/ -v --count=3
# Expected: All runs pass consistently
```

### Phase 2 Verification (CI Pipeline)
```bash
# Local testing with act
act -j lint                # Expected: Linting passes
act -j unit-tests          # Expected: Unit tests pass
act -j integration-tests   # Expected: Integration tests pass
act push                   # Expected: All jobs pass

# Remote testing on GitHub
# Push to main → Check Actions tab
# Create PR → Verify status checks appear
# Expected: All jobs pass in under 5 minutes
```

### Phase 3 Verification (Documentation)
```bash
# Verify documentation accuracy
# Check README.md badge displays correctly
# Click badge → Should link to Actions page
# Follow test running instructions → Should work as documented
# Review troubleshooting guide → Should be accurate
```

---

## Rollback Strategy

### If Test Fixes Break Something
1. **Isolate the issue**: Run tests individually to identify which fix caused the problem
2. **Revert specific fix**: Use `git revert` to undo the problematic commit
3. **Analyze and retry**: Understand why fix failed, adjust approach, retry
4. **Communicate**: Update task tracker if a different approach is needed

### If CI Pipeline Fails
1. **Disable workflow**: Rename `.github/workflows/ci.yml` to `ci.yml.disabled`
2. **Analyze logs**: Review GitHub Actions logs to identify failure point
3. **Test locally**: Use `act` to reproduce and fix the issue
4. **Re-enable**: Rename back to `ci.yml` once fixed
5. **Verify**: Confirm workflow runs successfully

### If Documentation is Incorrect
1. **Fix immediately**: Documentation changes are low-risk, update and push
2. **Verify instructions**: Test documented commands to ensure they work
3. **Get feedback**: Ask team members to review if uncertain

---

## Execution Order Rationale

### Why Phase 1 Must Complete First
- CI pipeline will fail if tests are failing
- No point setting up automated testing for a broken test suite
- Test fixes inform CI configuration (database setup, environment variables)

### Why Task Groups 1-4 Can Run in Parallel
- Each addresses different failing tests
- No dependencies between numpy serialization, fixture isolation, seed data, and assertions
- Parallel work saves time (if multiple engineers available)

### Why Phase 2 Requires Phase 1 Complete
- CI deployment requires all 59 tests passing
- Can't verify CI works if tests are failing
- Migration setup in CI needs to match what makes tests pass locally

### Why Phase 3 Requires Phase 2 Complete
- Documentation should reflect final CI configuration
- CI badge needs working CI to display correctly
- Troubleshooting guide should cover actual CI behavior

### Why Task Group 9 is Optional and Last
- Test audit is nice-to-have, not critical
- Should only be done if all other work is complete
- Removes tests rather than fixing them (riskier)
- Requires stable test suite as baseline

---

## Success Metrics

### Phase 1 Success
- [ ] All 59 tests pass locally (100% pass rate)
- [ ] Tests can run multiple times without failures
- [ ] No data leakage between tests
- [ ] No numpy serialization errors

### Phase 2 Success
- [ ] GitHub Actions workflow runs on every push
- [ ] GitHub Actions workflow runs on every PR
- [ ] All CI jobs pass (lint, unit-tests, integration-tests)
- [ ] CI execution time is under 5 minutes
- [ ] Status checks appear on pull requests

### Phase 3 Success
- [ ] CI badge displays in README and shows current status
- [ ] Testing documentation is accurate and complete
- [ ] Developers can run tests following documentation
- [ ] Troubleshooting guide helps debug common issues
- [ ] CI workflow file is well-commented and self-documenting

### Overall Success
- [ ] 100% test pass rate (59/59 tests)
- [ ] Automated CI on all pushes and PRs
- [ ] Complete and accurate documentation
- [ ] Developer confidence in code quality
- [ ] Clear path for contributors to run tests and understand CI

---

## Notes

### Implementer Assignments
- **testing-engineer**: Handles all test fixes (Task Groups 1-4, 9) because this is their specialty
- **general-purpose**: Handles CI/CD implementation and documentation (Task Groups 5-8) because it requires multiple skills (YAML, Docker, PostgreSQL, documentation)

### Time Estimates
- **Optimistic**: 7 hours (if all fixes work first try)
- **Realistic**: 9 hours (with some debugging and iteration)
- **Pessimistic**: 11 hours (if multiple approaches needed)

### Parallel Execution Opportunities
- Task Groups 1-4 can all run in parallel (if multiple engineers available)
- This could reduce Phase 1 from 4-6 hours to 1-2 hours of wall-clock time

### Critical Path
The critical path is: Any one of Task Groups 1-4 → Task Group 5 → Task Group 6 → Task Group 7 → Task Group 8

This means the minimum time to complete is approximately:
- 1-2 hours (one test fix group)
- 1 hour (create workflow)
- 0.5-1 hour (test locally)
- 0.5-1 hour (deploy and verify)
- 1-1.5 hours (documentation)
**Total minimum: 4-6.5 hours** (if all test fixes happen in parallel)

### Standards Compliance
This task breakdown aligns with:
- **Test Writing Standards**: Focus on business logic, not trivial tests
- **Global Conventions**: Clear documentation, version control best practices
- **Tech Stack**: Uses pytest, PostgreSQL, GitHub Actions (standard tools)
