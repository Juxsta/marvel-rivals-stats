# Specification: Test Quality and CI/CD Implementation

## Goal
Fix all 12 failing integration tests and implement GitHub Actions CI/CD pipeline to enable automated testing and confident code merges.

## User Stories
- As a developer, I want all tests to pass so that I can confidently merge code changes
- As a developer, I want automated CI checks on every PR so that I catch bugs before they reach main
- As a contributor, I want clear test failure messages so that I can quickly diagnose and fix issues
- As a maintainer, I want tests to run automatically on push so that I know the codebase is healthy

## Core Requirements

### Functional Requirements
- All 59 tests must pass (0% failure rate)
- GitHub Actions workflow runs on push to main and pull requests
- CI pipeline runs linting, unit tests, and integration tests separately
- Integration tests use PostgreSQL service container
- Test fixtures properly isolated with no race conditions
- Numpy types correctly serialized for database operations
- Tests validate business logic rather than trivial behavior

### Non-Functional Requirements
- Test suite completes in under 5 minutes in CI
- CI pipeline uses free GitHub Actions tier efficiently
- Tests are deterministic and reproducible
- Database test isolation prevents data leakage between tests
- Clear error messages for test failures

## Visual Design
Not applicable - this is a backend testing and CI implementation.

## Reusable Components

### Existing Code to Leverage
- **Docker Compose PostgreSQL setup**: `/home/ericreyes/github/marvel-rivals-stats/docker-compose.yml` already defines PostgreSQL container that can be adapted for CI
- **Migration scripts**: `/home/ericreyes/github/marvel-rivals-stats/migrations/` contain schema initialization that CI needs
- **Test fixtures**: `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_synergy_analysis.py` contains well-designed fixture pattern (`synergy_test_data`) with proper setup/teardown
- **Existing pytest config**: `/home/ericreyes/github/marvel-rivals-stats/pyproject.toml` defines black, ruff, and mypy configurations
- **Environment template**: `/home/ericreyes/github/marvel-rivals-stats/.env.example` shows required environment variables

### New Components Required
- **GitHub Actions workflow file**: `.github/workflows/ci.yml` - no existing CI workflow exists
- **Test isolation utilities**: Helper functions for database transaction rollback or unique test data generation
- **Numpy serialization layer**: Conversion functions to transform numpy types to Python types before database insert

## Technical Approach

### Database: Test Fixture Improvements

**Problem**: Integration tests failing due to duplicate keys, missing data, and numpy serialization issues.

**Solution**:
1. **Fixture Isolation Pattern**:
   - Use unique test data identifiers (e.g., `test_{test_name}_{uuid}` for IDs)
   - Implement proper cleanup in fixture teardown (delete test data)
   - Consider using pytest-postgresql for isolated test databases per test
   - Use `conn.autocommit = False` and rollback on teardown

2. **Numpy Type Conversion**:
   - Create utility function `convert_numpy_types()` to transform numpy.int64, numpy.float64 to Python int/float
   - Apply conversion in test fixtures before database insert
   - Pattern: `int(value) if isinstance(value, np.integer) else value`

3. **Seed Data Management**:
   - Ensure seed data fixtures run before tests that depend on them
   - Add explicit checks that required data exists before running tests
   - Use pytest fixture dependencies: `@pytest.fixture` with `usefixtures` decorator

### API: None (no API changes needed)

### Frontend: None (no frontend in this project)

### Testing: CI Pipeline Implementation

**GitHub Actions Workflow Structure**:

File: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install black ruff mypy
      - run: black --check src/ scripts/ tests/
      - run: ruff check src/ scripts/ tests/
      - run: mypy src/ scripts/

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ -v --ignore=tests/test_integration/

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: marvel_rivals_test
          POSTGRES_USER: marvel_stats
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: |
          # Run migrations
          for migration in migrations/*.sql; do
            PGPASSWORD=test_password psql -h localhost -U marvel_stats -d marvel_rivals_test -f "$migration"
          done
        shell: bash
      - run: pytest tests/test_integration/ -v
        env:
          DATABASE_URL: postgresql://marvel_stats:test_password@localhost:5432/marvel_rivals_test
          MARVEL_RIVALS_API_KEY: mock_key_for_testing
```

**Key Features**:
- Three separate jobs: linting, unit tests, integration tests
- PostgreSQL service container for integration tests
- Automatic database initialization using migration scripts
- Environment variables for test database connection
- No Docker Compose needed in CI (simplifies setup)

### Testing: Specific Test Fixes

**Fix 1: Numpy Serialization (4 tests)**
- Files: `tests/test_integration/test_player_discovery.py`, `tests/test_integration/test_match_collection.py`
- Root cause: Fixtures insert numpy int64 values that PostgreSQL tries to interpret as schema names
- Solution: Add type conversion in fixtures before insert
- Example: `rank_score = int(rank_score) if isinstance(rank_score, np.integer) else rank_score`

**Fix 2: Fixture Isolation (4 tests)**
- File: `tests/test_integration/test_character_analysis.py`
- Root cause: Multiple tests insert same match_id causing unique constraint violations
- Solution: Use unique match IDs per test (e.g., `f"match_{test_name}_{i}"`)
- Alternative: Use database transaction rollback pattern from `synergy_test_data` fixture

**Fix 3: Missing Seed Data (3 tests)**
- File: `tests/test_integration/test_synergy_analysis.py` (old tests, not the new passing ones)
- Root cause: Tests expect data but fixtures don't create it or cleanup is too aggressive
- Solution: Ensure fixture creates required data and verify it exists before test runs
- Add: `assert player_count > 0, "Fixture should have created test players"`

**Fix 4: Assertion Mismatch (1 test)**
- File: `tests/test_integration/test_character_analysis.py::test_confidence_intervals`
- Root cause: Hardcoded expected value doesn't match calculated value
- Solution: Use `pytest.approx()` for floating point comparisons
- Example: `assert value == pytest.approx(0.55, abs=0.05)`

## Out of Scope
- Adding new test coverage for untested features
- Performance testing or load testing
- End-to-end UI testing (no frontend exists)
- Testing external Marvel Rivals API (mock in tests)
- Migration to different test framework
- Test coverage percentage requirements (focus on fixing existing tests)
- Deployment pipeline (only CI, not CD)

## Success Criteria
- All 59 tests pass locally and in CI (100% pass rate)
- GitHub Actions workflow runs successfully on every push and PR
- No test failures due to fixture isolation issues
- No numpy serialization errors in database operations
- CI pipeline completes in under 5 minutes
- README.md updated with CI badge and test running instructions
- All test fixes follow project's "test business logic" philosophy (no trivial tests added)
- Integration tests can run repeatedly without manual database cleanup

## Dependencies & Integration Points

**Environment Variables Required for CI**:
- `DATABASE_URL`: PostgreSQL connection string
- `MARVEL_RIVALS_API_KEY`: Mock value for tests (not real API key)

**External Services**:
- GitHub Actions (free tier)
- PostgreSQL service container (GitHub Actions provides this)

**Migration Files**:
- `migrations/001_initial_schema.sql`: Must run first
- `migrations/002_add_indexes.sql`: Must run after schema
- `migrations/003_add_synergy_statistical_fields.sql`: Must run for synergy tests

## Implementation Notes

**Phase 1: Fix Test Fixtures** (Priority: High)
1. Start with numpy serialization fix (affects 4 tests)
   - Create `tests/test_utils/type_conversion.py` with helper functions
   - Update affected fixtures to use type conversion
   - Verify fixes with local test runs

2. Fix fixture isolation (affects 4 tests)
   - Review `test_character_analysis.py` fixtures
   - Implement unique ID pattern or transaction rollback
   - Model after successful `synergy_test_data` fixture pattern

3. Fix seed data issues (affects 3 tests)
   - Ensure fixtures create required data
   - Add assertions that data exists before test logic
   - Check fixture dependency order

4. Fix assertion mismatch (affects 1 test)
   - Update hardcoded expected values
   - Use `pytest.approx()` for float comparisons

**Phase 2: Implement GitHub Actions CI** (Priority: High)
1. Create `.github/workflows/` directory
2. Write `ci.yml` workflow file
3. Test locally using `act` tool (GitHub Actions local runner)
4. Push to GitHub and verify workflow runs
5. Fix any CI-specific issues (environment variables, paths, etc.)
6. Add CI badge to README.md

**Phase 3: Documentation Updates** (Priority: Medium)
1. Update README.md:
   - Add CI badge at top
   - Update "Testing" section with CI information
   - Add "Contributing" section mentioning CI checks

2. Update `docs/development.md`:
   - Document CI pipeline
   - Explain how to run tests locally before pushing
   - Troubleshooting CI failures

**Test Philosophy Alignment**:
All test fixes must align with project standards:
- Tests validate business logic, not implementation details
- No tests for trivial getters/setters or library code
- Tests focus on critical paths and edge cases
- Integration tests validate end-to-end workflows
- Avoid testing for the sake of testing

**Common Patterns to Follow**:
1. **Fixture Setup/Teardown Pattern** (from `synergy_test_data`):
   ```python
   @pytest.fixture
   def test_fixture():
       conn = _get_test_connection()
       conn.autocommit = False
       try:
           # Setup: Create test data
           with conn.cursor() as cur:
               cur.execute("INSERT INTO...")
           conn.commit()
           yield conn
       finally:
           # Teardown: Clean up test data
           try:
               conn.rollback()
               with conn.cursor() as cur:
                   cur.execute("DELETE FROM...")
               conn.commit()
           except:
               pass
           conn.close()
   ```

2. **Type Conversion Pattern**:
   ```python
   def convert_numpy_types(value):
       """Convert numpy types to Python native types."""
       if isinstance(value, np.integer):
           return int(value)
       elif isinstance(value, np.floating):
           return float(value)
       elif isinstance(value, np.ndarray):
           return value.tolist()
       return value
   ```

3. **Unique Test Data Pattern**:
   ```python
   import uuid

   def create_test_match_id(test_name):
       """Create unique match ID for test isolation."""
       return f"test_{test_name}_{uuid.uuid4().hex[:8]}"
   ```

## Risk Mitigation

**Risk 1**: Numpy serialization fix is more complex than expected
- **Mitigation**: Start with simple type conversion approach; if that fails, investigate psycopg2 adapters

**Risk 2**: CI pipeline costs exceed free tier (if private repo)
- **Mitigation**: Workflow only runs on push/PR to main; optimize job parallelization

**Risk 3**: PostgreSQL service container setup issues in CI
- **Mitigation**: Use standard GitHub Actions PostgreSQL setup; test migrations locally first

**Risk 4**: Breaking existing functionality while fixing tests
- **Mitigation**: Fix tests incrementally; run full suite after each fix; use git branches

**Risk 5**: Test execution time exceeds 5 minutes
- **Mitigation**: Run linting, unit tests, integration tests in parallel jobs; optimize slow tests

## Timeline Estimate

**Phase 1: Fix Failing Tests** (4-6 hours)
- Numpy serialization: 1-2 hours
- Fixture isolation: 1-2 hours
- Seed data issues: 1 hour
- Assertion mismatch: 30 minutes
- Verification: 30 minutes

**Phase 2: Implement CI Pipeline** (2-3 hours)
- Create workflow file: 1 hour
- Test and debug: 1-2 hours

**Phase 3: Documentation Updates** (1-2 hours)
- README updates: 30 minutes
- Development docs: 30 minutes
- Badge and final touches: 30 minutes

**Total Estimated Time**: 7-11 hours

## Verification Steps

After implementation, verify:
1. Run `pytest tests/ -v` locally - all 59 tests pass
2. Push to GitHub - CI workflow runs successfully
3. Create test PR - CI runs and reports status
4. Check CI logs - migrations run correctly, tests pass
5. Verify badge displays in README
6. Run tests multiple times - no flakiness or data leakage
7. Check CI execution time - under 5 minutes
