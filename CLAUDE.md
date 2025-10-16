# Marvel Rivals Stats Analyzer - Claude AI Context

This file provides context for Claude AI code reviewers (via GitHub Actions) and development assistants.

## Project Overview

**Marvel Rivals Stats Analyzer** is a Python-based statistical analysis system for the game Marvel Rivals. It collects player data, analyzes hero performance, and identifies synergies between heroes using rigorous statistical methods.

### Key Features
- **Player Discovery**: Stratified sampling from API leaderboards across all rank tiers
- **Match Collection**: Rate-limited API collection with deduplication
- **Character Analysis**: Win rate analysis by rank tier with Wilson confidence intervals
- **Synergy Detection**: Statistical hypothesis testing for hero pairings using binomial tests and Bonferroni correction
- **Database**: PostgreSQL with connection pooling and migrations
- **CI/CD**: GitHub Actions with comprehensive testing

## Technology Stack

### Core
- **Python 3.10**: Main language
- **PostgreSQL 16**: Primary database
- **Docker**: Development environment and service orchestration

### Libraries
- `psycopg2`: PostgreSQL adapter with connection pooling
- `requests`: HTTP client for Marvel Rivals API
- `numpy`: Numerical computations
- `scipy`: Statistical tests (binomial test, Wilson CI)
- `python-dotenv`: Environment configuration

### Development Tools
- `pytest`: Testing framework (42 unit tests, 17 integration tests)
- `black`: Code formatting (line length 100)
- `ruff`: Fast Python linter
- `mypy`: Static type checking

## Architecture

### Directory Structure
```
marvel-rivals-stats/
├── src/                    # Core library code (strict type checking)
│   ├── api/               # API client and rate limiting
│   ├── analyzers/         # Statistical analysis modules
│   ├── collectors/        # Data collection orchestration
│   ├── db/               # Database connection and helpers
│   └── utils/            # Shared utilities (statistics, type conversion)
├── scripts/               # CLI utilities (relaxed type checking)
│   ├── discover_players.py
│   ├── collect_matches.py
│   ├── analyze_characters.py
│   └── analyze_synergies.py
├── tests/
│   ├── test_analyzers/   # Unit tests for analysis logic
│   ├── test_collectors/  # Unit tests for collectors
│   ├── test_utils/       # Unit tests for utilities
│   └── test_integration/ # Integration tests requiring database
├── migrations/           # PostgreSQL schema migrations
└── .github/workflows/    # CI/CD configuration
```

### Database Schema
- **players**: Discovered players with rank information
- **matches**: Deduplicated match records
- **match_participants**: Player performance in each match
- **character_stats**: Aggregated hero win rates by rank
- **synergy_stats**: Hero pairing statistics with p-values and CIs
- **collection_metadata**: Progress tracking
- **schema_migrations**: Migration version tracking

## Code Quality Standards

### CRITICAL: 100% Test Pass Rate Required

**All tests MUST pass before merging**:
- ✅ Unit Tests: 42/42 (100%)
- ✅ Integration Tests: 17/17 (100%)
- ✅ Code Quality: black, ruff, mypy

**If any test fails, the PR is not ready for merge.**

### Code Formatting
- **Black**: Line length 100, target Python 3.10
- **Must pass**: `black --check src/ scripts/ tests/`
- Auto-format: `black src/ scripts/ tests/`

### Linting
- **Ruff**: E, W, F, I, D rules enabled
- **Must pass**: `ruff check src/ scripts/ tests/`
- Line length: 100 characters max
- Docstring convention: Google style

### Type Checking
- **Mypy**: Strict checking for `src/`, relaxed for `scripts/`
- **Must pass**: `mypy src/`
- Type stubs installed: types-psycopg2, types-requests
- Ignore missing imports: numpy, scipy, dotenv

### Testing Philosophy

**Unit Tests** (`tests/test_*` except `test_integration/`):
- Pure logic testing, no external dependencies
- Fast execution (< 1 second total)
- Mock database connections, API calls
- Test business logic, statistical calculations, data transformations

**Integration Tests** (`tests/test_integration/`):
- Require live PostgreSQL database
- Test end-to-end workflows
- Verify database schema, migrations
- Test data pipeline integrity
- Use pytest fixtures for cleanup

## Migration Guidelines

### File Naming Convention
**CRITICAL**: Migrations MUST use zero-padded three-digit prefixes:
```
✅ 001_initial_schema.sql
✅ 002_add_indexes.sql
✅ 010_add_user_profiles.sql
❌ 1_initial.sql           # Wrong: not zero-padded
❌ add_users.sql           # Wrong: no number prefix
```

**Why**: CI applies migrations in alphabetical order using `ls migrations/*.sql | sort`

### Migration Best Practices
1. **Idempotent**: Use `IF NOT EXISTS` / `IF EXISTS`
2. **Never modify merged migrations**: Create new migration to fix issues
3. **Test locally** before committing
4. **No rollback files in migrations/**: Store separately or document in comments
5. **Alphabetical = Execution order**: 001 runs before 002

## Review Guidelines for Claude

When reviewing PRs, focus on:

### 1. **Test Coverage & Quality** (HIGHEST PRIORITY)
- ❌ **BLOCK**: Any failing tests (must be 100% pass rate)
- ❌ **BLOCK**: Missing tests for new functionality
- ⚠️ **WARN**: Tests that don't test business logic (trivial tests)
- ⚠️ **WARN**: Integration tests that could be unit tests
- ✅ **APPROVE**: Comprehensive test coverage with realistic scenarios

### 2. **Code Quality Standards**
- ❌ **BLOCK**: Black/ruff/mypy failures
- ❌ **BLOCK**: Lines >100 characters
- ⚠️ **WARN**: Missing docstrings (Google style)
- ⚠️ **WARN**: Missing type hints in `src/`
- ✅ **APPROVE**: Clean, formatted, well-documented code

### 3. **Database & Migrations**
- ❌ **BLOCK**: Migration files without zero-padded numbers
- ❌ **BLOCK**: Non-idempotent migrations
- ❌ **BLOCK**: Rollback files in `migrations/` directory
- ⚠️ **WARN**: Migrations without comments explaining purpose
- ⚠️ **WARN**: Missing migration tests
- ✅ **APPROVE**: Proper migration naming, idempotent SQL, tested locally

### 4. **Statistical Correctness** (Project-Specific)
- ❌ **BLOCK**: Using raw win rates without confidence intervals
- ❌ **BLOCK**: P-values without multiple comparison correction
- ⚠️ **WARN**: Sample size < 30 without warning
- ⚠️ **WARN**: Statistical tests without power analysis consideration
- ✅ **APPROVE**: Proper Wilson CIs, Bonferroni correction, sample size warnings

### 5. **Type Conversion & Numpy**
- ❌ **BLOCK**: Numpy types passed to PostgreSQL (causes serialization errors)
- ⚠️ **WARN**: Direct database insertion without type conversion
- ✅ **APPROVE**: Using `convert_numpy_types()` from `src.utils.type_conversion`

### 6. **API & Rate Limiting**
- ❌ **BLOCK**: API calls without rate limiting
- ❌ **BLOCK**: Hard-coded API keys
- ⚠️ **WARN**: Missing retry logic for transient failures
- ✅ **APPROVE**: Proper rate limiting (8.6s delay), error handling

### 7. **Git Workflow**
- ❌ **BLOCK**: Direct commits to `main`
- ❌ **BLOCK**: PRs without descriptive titles/descriptions
- ⚠️ **WARN**: Commit messages that don't follow conventions
- ✅ **APPROVE**: Feature branches, descriptive commits with context

## Common Patterns & Conventions

### Database Connection
```python
from src.db import get_connection

# Always use context managers or try/finally
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT ...")
    conn.commit()
finally:
    conn.close()
```

### Type Conversion (CRITICAL for PostgreSQL)
```python
from src.utils.type_conversion import convert_numpy_types

# Convert ALL values before database insertion
values = convert_numpy_types({
    "score": np.float64(0.95),  # → 0.95
    "count": np.int64(42),      # → 42
})
```

### Statistical Tests
```python
from src.utils.statistics import (
    wilson_confidence_interval,
    binomial_test_synergy,
    bonferroni_correction,
)

# Always include confidence intervals
ci_lower, ci_upper = wilson_confidence_interval(wins=60, total=100)

# Always test significance
result = binomial_test_synergy(wins=60, total=100, expected_wr=0.5)

# Always apply multiple comparison correction
synergies = bonferroni_correction(synergies, alpha=0.05)
```

### API Client
```python
from src.api.client import MarvelRivalsClient
from src.api.rate_limiter import RateLimiter

rate_limiter = RateLimiter(requests_per_second=0.116)  # ~8.6s delay
client = MarvelRivalsClient(api_key=api_key, rate_limiter=rate_limiter)
```

## Performance Expectations

### Test Execution Time
- Unit tests: < 5 seconds total
- Integration tests: < 2 minutes (includes DB setup)
- CI pipeline total: < 3 minutes (parallel jobs)

### Database Operations
- Use connection pooling (already configured)
- Batch inserts for large datasets
- Proper indexes on frequently queried columns

## Documentation Standards

### Docstrings (Google Style)
```python
def analyze_synergy(wins: int, total: int, expected_wr: float) -> Dict[str, Any]:
    """Calculate synergy statistics for a hero pairing.

    Uses binomial test to determine if actual win rate differs significantly
    from expected win rate based on individual hero performance.

    Args:
        wins: Number of wins when paired together
        total: Total games played together
        expected_wr: Expected win rate from baseline model

    Returns:
        Dictionary containing:
            - actual_wr: Actual win rate (float)
            - synergy_score: Difference from expected (float)
            - p_value: Statistical significance (float)
            - significant: Whether p < 0.05 (bool)

    Raises:
        ValueError: If total < 1 or expected_wr not in [0, 1]
    """
```

### Code Comments
- Explain **why**, not **what**
- Document non-obvious statistical choices
- Reference research papers for complex algorithms
- Explain database schema decisions

## CI/CD Pipeline

### Required Checks (All Must Pass)
1. **Code Quality Checks** (~30 seconds)
   - black --check
   - ruff check
   - mypy src/

2. **Unit Tests** (~30 seconds)
   - 42 tests, no database required
   - Fast execution, mocked dependencies

3. **Integration Tests** (~2 minutes)
   - 17 tests with PostgreSQL service container
   - Migrations applied automatically
   - Real database operations

### Workflow Triggers
- Push to `main` branch
- Pull requests targeting `main`

## Local Development Quick Start

```bash
# Format code
black src/ scripts/ tests/

# Lint
ruff check src/ scripts/ tests/

# Type check
mypy src/

# Run unit tests
pytest tests/ -v --ignore=tests/test_integration/

# Run integration tests (requires Docker)
docker compose up -d
pytest tests/test_integration/ -v

# Run all checks (like CI)
black --check src/ scripts/ tests/ && \
ruff check src/ scripts/ tests/ && \
mypy src/ && \
pytest tests/ -v --ignore=tests/test_integration/
```

## Common Issues & Solutions

### 1. Numpy Serialization Errors
**Error**: `schema "np" does not exist`
**Solution**: Use `convert_numpy_types()` before database insertion

### 2. Migration Order Issues
**Error**: Migrations running in wrong order
**Solution**: Ensure zero-padded filenames (001, 002, not 1, 2)

### 3. Test Isolation Issues
**Error**: Tests pass individually but fail together
**Solution**: Check fixtures for proper cleanup, use transaction rollback

### 4. Type Checking Failures
**Error**: `Cannot find implementation or library stub`
**Solution**: Add to ignore_missing_imports in pyproject.toml or install type stubs

## Questions or Issues?

For Claude reviewers:
- If something is unclear, ask for clarification in the PR review
- Flag potential issues with severity: ❌ BLOCK, ⚠️ WARN, 💡 SUGGEST
- Always explain **why** something is an issue, not just **what** is wrong

For developers:
- Check existing tests for patterns and examples
- Review closed PRs for review examples
- Run full CI suite locally before pushing: `black && ruff && mypy && pytest`

---

**Last Updated**: 2025-10-15
**Project Status**: Active Development
**Maintainer**: Primary development via Claude Code with human oversight
