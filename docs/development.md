# Development Workflow

This guide covers the daily development workflow for the Marvel Rivals Stats Analyzer project.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/marvel-rivals-stats.git
cd marvel-rivals-stats
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

Required environment variables for development:
- `MARVEL_RIVALS_API_KEY` - Your API key from Marvel Rivals API
- `DATABASE_PASSWORD` - Local database password (any secure string)
- `DATA_DIR=./data` - Use local data directory for development

### 3. Start Development Environment

```bash
# Start all services (PostgreSQL + app container)
docker compose up -d

# Verify services are running
docker compose ps
```

Expected output:
```
NAME                     STATUS              PORTS
marvel-rivals-app        Up
marvel-rivals-postgres   Up (healthy)        0.0.0.0:5432->5432/tcp
```

### 4. Initialize Database

```bash
# Run database initialization script
docker compose exec app python scripts/init_db.py
```

This will:
- Create all database tables
- Apply migrations
- Verify schema version

## Daily Development

### Starting/Stopping Services

```bash
# Start services
docker compose up -d

# Stop services (preserves data)
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Restart services
docker compose restart

# Restart specific service
docker compose restart app
```

### Viewing Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f app
docker compose logs -f postgres

# View last 100 lines
docker compose logs --tail=100 app
```

### Running Python Scripts

All Python scripts should be run inside the app container:

```bash
# General pattern
docker compose exec app python scripts/<script_name>.py

# Examples
docker compose exec app python scripts/init_db.py
docker compose exec app python scripts/test_api.py
docker compose exec app python scripts/seed_sample_data.py

# Run with environment variables
docker compose exec app python scripts/discover_players.py
```

### Making Code Changes

Python code is mounted as a volume, so changes are immediately available:

1. Edit files in `src/` or `scripts/` on your host machine
2. Changes are instantly reflected in the container
3. Run scripts to test changes
4. No container rebuild needed

Example workflow:
```bash
# 1. Edit a file
nano src/db/connection.py

# 2. Immediately test changes
docker compose exec app python -c "from src.db import get_connection; print('Works!')"

# 3. Or run a script that uses it
docker compose exec app python scripts/init_db.py
```

### Running Tests

```bash
# Run all tests
docker compose exec app pytest tests/ -v

# Run specific test file
docker compose exec app pytest tests/test_db/test_connection.py -v

# Run tests with coverage
docker compose exec app pytest tests/ -v --cov=src --cov-report=html

# Run tests matching pattern
docker compose exec app pytest tests/ -v -k "test_connection"

# Run tests and stop on first failure
docker compose exec app pytest tests/ -v -x
```

### Code Formatting and Linting

```bash
# Format code with Black
docker compose exec app black src/ scripts/ tests/

# Check formatting without making changes
docker compose exec app black --check src/ scripts/ tests/

# Lint with Ruff
docker compose exec app ruff check src/ scripts/ tests/

# Auto-fix Ruff issues
docker compose exec app ruff check --fix src/ scripts/ tests/

# Type checking with MyPy
docker compose exec app mypy src/ scripts/
```

Run before committing:
```bash
docker compose exec app black src/ scripts/ tests/ && \
docker compose exec app ruff check src/ scripts/ tests/ && \
docker compose exec app mypy src/ scripts/
```

### Database Access

#### Using psql

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U marvel_stats -d marvel_rivals

# Common psql commands:
\dt              # List tables
\di              # List indexes
\d table_name    # Describe table
\q               # Quit

# Run single query
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM players;"

# Run query from file
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -f migrations/001_initial_schema.sql
```

#### Using Python

```bash
# Interactive Python shell with database access
docker compose exec app python -c "
from src.db import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM players')
print(cur.fetchone())
conn.close()
"
```

### Rebuilding Containers

Rebuild when you modify:
- `Dockerfile`
- `requirements.txt`
- `requirements-dev.txt`

```bash
# Rebuild app container
docker compose build app

# Rebuild and restart
docker compose up -d --build app

# Force rebuild (no cache)
docker compose build --no-cache app
```

### Database Migrations

#### Migration File Naming Convention

**CRITICAL**: Migration files MUST follow this naming pattern:
```
NNN_descriptive_name.sql
```

Where:
- `NNN` is a zero-padded three-digit number (001, 002, 003, etc.)
- `descriptive_name` describes what the migration does
- Files are applied in **alphabetical order** (which equals numerical order with this convention)

Examples:
- ✅ `001_initial_schema.sql`
- ✅ `002_add_synergy_stats.sql`
- ✅ `010_add_indexes.sql`
- ❌ `1_initial.sql` (not zero-padded)
- ❌ `add_users.sql` (no number prefix)

#### Why Alphabetical Ordering Matters

The CI pipeline applies migrations using:
```bash
for migration in $(ls migrations/*.sql | sort); do
  psql -f "$migration"
done
```

This means:
- Migrations are applied in **alphabetical order**
- No database tracking table is used in CI
- Incorrect ordering will cause schema inconsistencies
- Always use zero-padded numbers to ensure correct sort order

#### Creating a New Migration

1. **Determine the next number**:
   ```bash
   ls migrations/ | sort | tail -1
   # If last is 002_add_synergy_stats.sql, use 003
   ```

2. **Create the migration file**:
   ```bash
   nano migrations/003_add_user_profiles.sql
   ```

3. **Write idempotent SQL** (safe to run multiple times):
   ```sql
   -- Good: Uses IF NOT EXISTS
   CREATE TABLE IF NOT EXISTS user_profiles (
       id SERIAL PRIMARY KEY,
       username VARCHAR(255) NOT NULL
   );

   -- Good: Checks existence before adding column
   DO $$
   BEGIN
       IF NOT EXISTS (
           SELECT 1 FROM information_schema.columns
           WHERE table_name='users' AND column_name='email'
       ) THEN
           ALTER TABLE users ADD COLUMN email VARCHAR(255);
       END IF;
   END $$;
   ```

4. **Test locally**:
   ```bash
   # Apply migration
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
       -f /docker-entrypoint-initdb.d/003_add_user_profiles.sql

   # Verify schema
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
       -c "\d user_profiles"
   ```

5. **Commit the migration**:
   ```bash
   git add migrations/003_add_user_profiles.sql
   git commit -m "Add user profiles migration"
   ```

#### Best Practices for Migrations

1. **Never modify existing migrations** after they've been merged
   - Create a new migration to fix issues instead
   - Existing migrations may have already run in production

2. **Make migrations idempotent**
   - Use `IF NOT EXISTS` for CREATE statements
   - Use `IF EXISTS` for DROP statements
   - Check for existence before ALTER TABLE operations

3. **Test rollback scenarios**
   - Ensure you can recover if migration fails
   - Consider creating a separate rollback script for complex changes

4. **Keep migrations focused**
   - One logical change per migration file
   - Easier to debug and rollback if needed

5. **Document breaking changes**
   - Add SQL comments explaining why the change is necessary
   - Note any required data migrations or cleanup

#### Applying Migrations Manually

```bash
# Apply specific migration
docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
    -f /docker-entrypoint-initdb.d/003_new_feature.sql

# Apply all pending migrations in order
for migration in migrations/*.sql; do
    echo "Applying: $migration"
    docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
        -f /docker-entrypoint-initdb.d/$(basename $migration)
done

# Check schema version (if using schema_migrations table)
docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
    -c "SELECT * FROM schema_migrations ORDER BY version;"
```

#### Troubleshooting Migrations

**Migration fails in CI but works locally**:
- Check if migration is idempotent (safe to run multiple times)
- Verify dependencies on previous migrations
- Ensure no hard-coded data that may differ between environments

**Migration order is wrong**:
- Rename files to use correct zero-padded numbers
- Run `ls migrations/ | sort` to verify alphabetical order matches intended order

**Need to rollback a migration**:
- Create a new migration that reverses the changes
- Don't modify or delete the original migration file

### Seeding Test Data

```bash
# Seed sample data
docker compose exec app python scripts/seed_sample_data.py

# Verify data
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM players;"
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM matches;"
```

## Hot Reload Behavior

The development environment supports hot reload for code changes:

### What Triggers Automatic Reload
- Changes to `src/` Python modules
- Changes to `scripts/` files
- Changes to `config/` JSON files

### What Requires Container Restart
- Changes to `.env` file
- Changes to `docker-compose.yml`
- Changes to environment variables

```bash
# After changing .env or docker-compose.yml
docker compose restart app
```

### What Requires Container Rebuild
- Changes to `Dockerfile`
- Changes to `requirements.txt` or `requirements-dev.txt`
- Changes to system dependencies

```bash
# After changing dependencies
docker compose build app
docker compose up -d app
```

## Debugging

### Check Service Health

```bash
# Check if containers are running
docker compose ps

# Check container logs for errors
docker compose logs app --tail=50
docker compose logs postgres --tail=50

# Check database connectivity
docker compose exec app python -c "from src.db import get_connection; get_connection(); print('Connected!')"

# Check environment variables
docker compose exec app env | grep DATABASE
docker compose exec app env | grep MARVEL
```

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 5432
sudo netstat -tlnp | grep 5432

# Stop conflicting service
sudo systemctl stop postgresql

# Or change port in .env
DATABASE_PORT=5433
```

#### Database Connection Refused
```bash
# Wait for PostgreSQL health check
docker compose exec postgres pg_isready -U marvel_stats

# Check PostgreSQL logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

#### Permission Denied on Volumes
```bash
# Fix ownership of data directory
sudo chown -R $USER:$USER ./data

# Or remove and recreate
docker compose down -v
docker compose up -d
```

## Best Practices

### Before Committing
1. Format code: `docker compose exec app black src/ scripts/ tests/`
2. Lint code: `docker compose exec app ruff check src/ scripts/ tests/`
3. Type check: `docker compose exec app mypy src/ scripts/`
4. Run tests: `docker compose exec app pytest tests/ -v`
5. Check no .env in staging: `git status`

### Before Pushing
1. Ensure all tests pass
2. Update documentation if needed
3. Review commit message follows conventions

### Regular Maintenance
```bash
# Clean up stopped containers
docker compose down

# Clean up Docker system (careful!)
docker system prune -a

# Backup database (development)
docker compose exec postgres pg_dump -U marvel_stats marvel_rivals > backup.sql

# Restore database
docker compose exec -T postgres psql -U marvel_stats -d marvel_rivals < backup.sql
```

## Useful Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias dc='docker compose'
alias dcup='docker compose up -d'
alias dcdown='docker compose down'
alias dclogs='docker compose logs -f'
alias dcps='docker compose ps'
alias dcapp='docker compose exec app'
alias dcdb='docker compose exec postgres psql -U marvel_stats -d marvel_rivals'

# Usage:
# dcapp python scripts/test_api.py
# dcdb -c "SELECT COUNT(*) FROM players;"
```

## Running the Data Collection Pipeline

### Complete Pipeline (All Steps)

```bash
# Step 1: Discover players (stratified sampling)
docker compose exec app python scripts/discover_players.py --target-count 500

# Step 2: Collect match histories (rate limited, ~70 minutes for 100 players)
docker compose exec app python scripts/collect_matches.py --batch-size 100

# Step 3: Analyze character win rates
docker compose exec app python scripts/analyze_characters.py

# Step 4: Analyze teammate synergies
docker compose exec app python scripts/analyze_synergies.py
```

### Development/Testing with Small Datasets

```bash
# Discover just 50 players for testing
docker compose exec app python scripts/discover_players.py --target-count 50

# Collect matches for 10 players only
docker compose exec app python scripts/collect_matches.py --batch-size 10

# Analyze with lower thresholds
docker compose exec app python scripts/analyze_characters.py --min-games-overall 20
docker compose exec app python scripts/analyze_synergies.py --min-games 10
```

### Dry Run Mode (Preview Without Changes)

All scripts support `--dry-run` to preview without database changes:

```bash
docker compose exec app python scripts/discover_players.py --dry-run
docker compose exec app python scripts/collect_matches.py --dry-run --batch-size 5
```

### Resuming Interrupted Collection

Match collection is resumable - it tracks which players have been processed:

```bash
# Start collection
docker compose exec app python scripts/collect_matches.py --batch-size 100

# Press Ctrl+C to stop (partial progress is saved)

# Resume later - picks up where it left off
docker compose exec app python scripts/collect_matches.py --batch-size 100
```

### Inspecting Output

```bash
# View JSON exports
cat output/character_win_rates.json | jq '."Spider-Man"'
cat output/synergies.json | jq '."Spider-Man".synergies[0:3]'

# Query database directly
dcdb -c "SELECT hero_name, win_rate, total_games FROM character_stats WHERE rank_tier IS NULL ORDER BY win_rate DESC LIMIT 10;"
dcdb -c "SELECT COUNT(*) FROM matches;"
dcdb -c "SELECT COUNT(*) FROM match_participants;"
```

### Common Development Workflows

**Add new hero analysis**:
1. Ensure matches collected: `dcdb -c "SELECT COUNT(*) FROM matches;"`
2. Run character analysis: `docker compose exec app python scripts/analyze_characters.py`
3. Check output: `cat output/character_win_rates.json | jq keys`

**Update synergy calculations**:
1. Modify `src/analyzers/teammate_synergy.py`
2. Run tests: `docker compose exec app pytest tests/test_analyzers/test_teammate_synergy.py -v`
3. Re-run analysis: `docker compose exec app python scripts/analyze_synergies.py`

**Debug data collection issues**:
1. Check logs: `docker compose logs -f app`
2. Inspect database: `dcdb -c "SELECT * FROM collection_metadata;"`
3. View API rate limit status: Check logs for "Rate limit" warnings

## Continuous Integration Pipeline

### Overview

The project uses GitHub Actions for automated testing on every push and pull request.

### Workflow Structure

The CI workflow (`.github/workflows/ci.yml`) consists of three parallel jobs:

1. **lint**: Code quality checks
   - black --check (code formatting)
   - ruff check (linting)
   - mypy (type checking)

2. **unit-tests**: Business logic tests
   - Runs ~42 unit tests
   - Tests: statistics, analyzers, collectors, utilities
   - Fast execution (~30 seconds)

3. **integration-tests**: End-to-end tests
   - Runs ~17 integration tests
   - Uses PostgreSQL service container
   - Runs database migrations automatically
   - Tests: pipeline, workflow, synergy analysis
   - Execution time: ~2 minutes

### Service Containers

Integration tests use a PostgreSQL 16 service container:
- Database: `marvel_rivals_test`
- User: `marvel_stats`
- Password: `test_password`
- Health checks ensure database is ready before tests run
- Migrations run automatically before tests

### Local Testing

To test locally before pushing:

```bash
# Run all checks that CI will run
docker compose exec app black --check src/ scripts/ tests/
docker compose exec app ruff check src/ scripts/ tests/
docker compose exec app mypy src/ scripts/
docker compose exec app pytest tests/ -v
```

### Debugging CI Failures

1. **View logs**: Go to GitHub Actions tab → Click failing workflow → Click failing job
2. **Reproduce locally**: Use the same commands that CI runs
3. **Test locally with act** (optional):
   ```bash
   # Install act tool
   brew install act  # macOS

   # Test workflow locally
   act push
   ```

### Execution Time

Target: Under 5 minutes total
- Lint job: ~30 seconds
- Unit tests job: ~30 seconds
- Integration tests job: ~2 minutes
- Total (parallel): ~2-3 minutes

### Status Checks

All PRs show status checks:
- Green checkmark: All checks passed
- Red X: One or more checks failed
- Yellow dot: Checks in progress

PRs cannot be merged until all checks pass.

## Next Steps

- Review [Deployment Guide](deployment.md) for production deployment
- Check [Troubleshooting Guide](troubleshooting.md) for common issues
- See [Product Documentation](PRODUCT.md) for feature requirements
