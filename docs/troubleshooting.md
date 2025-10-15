# Troubleshooting Guide

Common issues and solutions for the Marvel Rivals Stats Analyzer project.

## Table of Contents

- [Docker Issues](#docker-issues)
- [Database Issues](#database-issues)
- [Environment Variable Issues](#environment-variable-issues)
- [Permission Issues](#permission-issues)
- [Network Issues](#network-issues)
- [API Issues](#api-issues)
- [Test Issues](#test-issues)
- [Migration Issues](#migration-issues)

---

## Docker Issues

### Port 5432 Already in Use

**Problem**: PostgreSQL container fails to start with "port is already allocated" error.

**Symptoms**:
```
Error response from daemon: driver failed programming external connectivity:
Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

**Solutions**:

1. **Check what's using port 5432**:
   ```bash
   sudo netstat -tlnp | grep 5432
   # Or on Odin:
   ss -tlnp | grep 5432
   ```

2. **If system PostgreSQL is running**:
   ```bash
   sudo systemctl stop postgresql
   sudo systemctl disable postgresql  # Prevent auto-start
   ```

3. **Change port in .env** (alternative solution):
   ```bash
   nano .env
   # Change:
   DATABASE_PORT=5433

   # Update DATABASE_URL:
   DATABASE_URL=postgresql://marvel_stats:password@postgres:5432/marvel_rivals
   # Note: Internal port stays 5432, external changes to 5433
   ```

4. **Restart Docker Compose**:
   ```bash
   docker compose down
   docker compose up -d
   ```

### Container Won't Start

**Problem**: Container exits immediately or fails to start.

**Symptoms**:
```
docker compose ps
# Shows container as "Exited (1)"
```

**Solutions**:

1. **Check logs**:
   ```bash
   docker compose logs app
   docker compose logs postgres
   ```

2. **Verify Docker daemon is running**:
   ```bash
   sudo systemctl status docker
   # If not running:
   sudo systemctl start docker
   ```

3. **Check docker-compose.yml syntax**:
   ```bash
   docker compose config
   # Should show validated configuration
   ```

4. **Rebuild container**:
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

5. **Check disk space**:
   ```bash
   df -h
   # Ensure sufficient space on Docker partition
   ```

### Docker Compose Command Not Found

**Problem**: `docker compose` command doesn't work.

**Solutions**:

1. **Check Docker Compose version**:
   ```bash
   docker compose version
   # Should show 2.0+
   ```

2. **If using older Docker** (v1 syntax):
   ```bash
   docker-compose --version
   # Use docker-compose (with hyphen) instead
   ```

3. **Update Docker** (if needed):
   ```bash
   sudo apt update
   sudo apt install docker-compose-plugin
   ```

---

## Database Issues

### Database Connection Failed

**Problem**: Application can't connect to PostgreSQL.

**Symptoms**:
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions**:

1. **Check PostgreSQL is running**:
   ```bash
   docker compose ps
   # postgres should show "Up (healthy)"
   ```

2. **Check database health**:
   ```bash
   docker compose exec postgres pg_isready -U marvel_stats
   # Should return: accepting connections
   ```

3. **Verify environment variables**:
   ```bash
   docker compose exec app env | grep DATABASE
   # Check all DATABASE_* variables are set correctly
   ```

4. **Check password matches**:
   ```bash
   # In .env file, ensure DATABASE_PASSWORD in DATABASE_URL matches DATABASE_PASSWORD variable
   ```

5. **Wait for initialization**:
   ```bash
   # PostgreSQL may take 10-30 seconds to initialize
   docker compose logs postgres
   # Wait for: "database system is ready to accept connections"
   ```

6. **Test connection manually**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT 1;"
   ```

### Tables Don't Exist

**Problem**: Queries fail with "relation does not exist" error.

**Symptoms**:
```
psycopg2.errors.UndefinedTable: relation "players" does not exist
```

**Solutions**:

1. **Check if tables exist**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\dt"
   ```

2. **Run database initialization**:
   ```bash
   docker compose exec app python scripts/init_db.py
   ```

3. **Manually apply migrations**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
     -f /docker-entrypoint-initdb.d/001_initial_schema.sql

   docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
     -f /docker-entrypoint-initdb.d/002_add_indexes.sql
   ```

4. **Check schema version**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals \
     -c "SELECT * FROM schema_migrations;"
   ```

### Database Data Lost After Restart

**Problem**: Data disappears when restarting containers.

**Symptoms**: Tables exist but are empty after `docker compose down && docker compose up`.

**Solutions**:

1. **Check if volumes were removed**:
   ```bash
   # Don't use -v flag unless you want to delete data!
   docker compose down    # Good - preserves data
   docker compose down -v # BAD - deletes volumes!
   ```

2. **Verify volume configuration**:
   ```bash
   docker compose config | grep -A5 volumes
   # Should show DATA_DIR mapped to /var/lib/postgresql/data
   ```

3. **Check DATA_DIR in .env**:
   ```bash
   cat .env | grep DATA_DIR
   # Development: DATA_DIR=./data
   # Production: DATA_DIR=/mnt/user/appdata/marvel-rivals-stats
   ```

4. **Verify data directory exists**:
   ```bash
   ls -la ${DATA_DIR}/postgres/
   # Should contain PostgreSQL files
   ```

### Query Performance Issues

**Problem**: Queries are very slow.

**Solutions**:

1. **Check if indexes exist**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\di"
   # Should show 11+ indexes
   ```

2. **Run ANALYZE**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "ANALYZE;"
   ```

3. **Check table sizes**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "
   SELECT
     tablename,
     pg_size_pretty(pg_total_relation_size('public.'||tablename))
   FROM pg_tables
   WHERE schemaname = 'public';
   "
   ```

4. **Review slow queries**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;
   "
   ```

---

## Environment Variable Issues

### Environment Variables Not Loaded

**Problem**: Application uses wrong values or complains about missing variables.

**Symptoms**:
```
KeyError: 'DATABASE_PASSWORD'
# Or using default values instead of .env values
```

**Solutions**:

1. **Verify .env file exists**:
   ```bash
   ls -la .env
   # Should exist and not be empty
   ```

2. **Check .env syntax**:
   ```bash
   cat .env
   # Lines should be: KEY=value (no spaces around =)
   # No quotes needed unless value has spaces
   ```

3. **Restart containers after changing .env**:
   ```bash
   docker compose down
   docker compose up -d
   ```

4. **Check environment variables in container**:
   ```bash
   docker compose exec app env | grep DATABASE
   docker compose exec app env | grep MARVEL
   ```

5. **Test variable in Python**:
   ```bash
   docker compose exec app python -c "import os; print(os.getenv('DATABASE_PASSWORD'))"
   ```

### DATABASE_URL Format Issues

**Problem**: Database URL is incorrectly formatted.

**Correct format**:
```
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

**Example**:
```
DATABASE_URL=postgresql://marvel_stats:mypassword@postgres:5432/marvel_rivals
```

**Common mistakes**:
- Missing protocol: `marvel_stats:password@postgres...` (needs `postgresql://`)
- Wrong host: `localhost` (should be `postgres` inside Docker)
- Unescaped special characters in password
- Spaces in URL

---

## Permission Issues

### Permission Denied on ./data Directory

**Problem**: Can't write to local data directory.

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied: './data/postgres'
```

**Solutions**:

1. **Fix ownership**:
   ```bash
   sudo chown -R $USER:$USER ./data
   ```

2. **Fix permissions**:
   ```bash
   chmod -R 755 ./data
   ```

3. **If on Odin, check NFS mount permissions**:
   ```bash
   ls -la /mnt/user/appdata/marvel-rivals-stats/
   chown -R ericreyes:ericreyes /mnt/user/appdata/marvel-rivals-stats/
   ```

### Can't Create Files in /mnt/user/appdata (Odin)

**Problem**: Container can't write to Odin storage.

**Solutions**:

1. **Create directories first**:
   ```bash
   mkdir -p /mnt/user/appdata/marvel-rivals-stats/{postgres,output,logs}
   ```

2. **Set correct ownership**:
   ```bash
   chown -R ericreyes:ericreyes /mnt/user/appdata/marvel-rivals-stats/
   ```

3. **Check NFS mount**:
   ```bash
   df -h | grep /mnt/user
   # Ensure NFS is mounted
   ```

4. **Verify DATA_DIR in .env**:
   ```bash
   grep DATA_DIR .env
   # Should be: DATA_DIR=/mnt/user/appdata/marvel-rivals-stats
   ```

---

## Network Issues

### Can't Connect to PostgreSQL from App Container

**Problem**: App container can't reach PostgreSQL.

**Solutions**:

1. **Check both containers are on same network**:
   ```bash
   docker network ls
   docker network inspect marvel-rivals-network
   # Both containers should be listed
   ```

2. **Use service name, not localhost**:
   ```python
   # Correct:
   host = "postgres"

   # Wrong inside Docker:
   host = "localhost"
   ```

3. **Verify DATABASE_HOST in .env**:
   ```bash
   grep DATABASE_HOST .env
   # Should be: DATABASE_HOST=postgres
   ```

4. **Test network connectivity**:
   ```bash
   docker compose exec app ping postgres
   ```

### Can't Access PostgreSQL from Host Machine

**Problem**: Can't connect to PostgreSQL from host (e.g., using pgAdmin).

**Solutions**:

1. **Check port mapping in docker-compose.yml**:
   ```yaml
   ports:
     - "${DATABASE_PORT:-5432}:5432"
   ```

2. **Connect using localhost from host**:
   ```bash
   psql -h localhost -p 5432 -U marvel_stats -d marvel_rivals
   ```

3. **If port mapping is missing**, add to docker-compose.yml:
   ```yaml
   postgres:
     ports:
       - "5432:5432"  # Add this line
   ```

---

## API Issues

### API Key Invalid

**Problem**: Marvel Rivals API returns 401 Unauthorized.

**Solutions**:

1. **Check API key is set**:
   ```bash
   docker compose exec app env | grep MARVEL_RIVALS_API_KEY
   ```

2. **Verify API key format**:
   - Should be a long alphanumeric string
   - No quotes needed in .env
   - No spaces

3. **Test API key**:
   ```bash
   docker compose exec app python scripts/test_api.py
   ```

4. **Get new API key** if needed from Marvel Rivals API website.

### Rate Limit Exceeded

**Problem**: API returns 429 Too Many Requests.

**Solutions**:

1. **Check rate limit configuration**:
   ```bash
   grep RATE_LIMIT .env
   # Should be: RATE_LIMIT_REQUESTS_PER_MINUTE=7
   ```

2. **Reduce rate limit in .env**:
   ```bash
   RATE_LIMIT_REQUESTS_PER_MINUTE=5
   ```

3. **Wait before retrying**:
   - Free tier: 10,000 requests/day
   - Wait 24 hours for quota reset

4. **Check rate limiter is working**:
   ```bash
   docker compose exec app python -c "
   from src.api import RateLimiter
   limiter = RateLimiter(7)
   print('Rate limiter initialized')
   "
   ```

---

## Test Issues

### Tests Fail to Run

**Problem**: pytest command fails or tests don't run.

**Solutions**:

1. **Verify pytest is installed**:
   ```bash
   docker compose exec app pip list | grep pytest
   ```

2. **Reinstall dev dependencies**:
   ```bash
   docker compose exec app pip install -r requirements-dev.txt
   ```

3. **Check test file syntax**:
   ```bash
   docker compose exec app python -m py_compile tests/test_db/test_connection.py
   ```

4. **Run with verbose output**:
   ```bash
   docker compose exec app pytest tests/ -v --tb=long
   ```

### Database Tests Fail

**Problem**: Database connection tests fail.

**Solutions**:

1. **Ensure database is initialized**:
   ```bash
   docker compose exec app python scripts/init_db.py
   ```

2. **Check database is healthy**:
   ```bash
   docker compose exec postgres pg_isready -U marvel_stats
   ```

3. **Verify test database connection**:
   ```bash
   docker compose exec app python -c "from src.db import get_connection; get_connection()"
   ```

4. **Check test environment variables**:
   ```bash
   docker compose exec app pytest tests/test_db/ -v -s
   ```

### Import Errors in Tests

**Problem**: Tests can't import modules from src/.

**Symptoms**:
```
ImportError: No module named 'src'
```

**Solutions**:

1. **Check PYTHONPATH is set**:
   ```bash
   docker compose exec app env | grep PYTHONPATH
   # Should be: PYTHONPATH=/app
   ```

2. **Run pytest from correct directory**:
   ```bash
   docker compose exec app pytest tests/ -v
   # Not: pytest /app/tests/
   ```

3. **Verify __init__.py files exist**:
   ```bash
   find src/ -name "__init__.py"
   # Should list all package __init__.py files
   ```

### Fixture Isolation Issues

**Symptom**: Tests fail with "duplicate key value violates unique constraint"

**Cause**: Test data not properly cleaned between tests

**Solution**:
1. Check `clean_test_data` fixture includes all test data patterns
2. Ensure fixture uses proper cleanup patterns (LIKE '%test%', etc.)
3. Run tests individually to identify which test leaves data behind
4. Use unique IDs per test invocation

### Numpy Serialization Errors

**Symptom**: `psycopg2.errors.InvalidSchemaName: schema "np" does not exist`

**Cause**: Numpy types (numpy.float64, numpy.int64) being passed to PostgreSQL

**Solution**:
1. Use type conversion utilities from `tests/test_utils/type_conversion.py`
2. Convert numpy types before database INSERT:
   ```python
   from tests.test_utils.type_conversion import convert_numpy_types
   value = convert_numpy_types(some_numpy_value)
   ```
3. Check that statistical functions return Python types, not numpy types

### Database Connection Issues

**Symptom**: `psycopg2.OperationalError: could not connect to server`

**Cause**: PostgreSQL container not running or DATABASE_URL not set

**Solution**:
1. Ensure containers are running: `docker compose ps`
2. Start containers if needed: `docker compose up -d`
3. Check DATABASE_URL: `echo $DATABASE_URL`
4. Verify PostgreSQL health: `docker compose exec postgres pg_isready`

### Migration Failures

**Symptom**: Tests fail with "relation does not exist" errors

**Cause**: Database migrations not applied

**Solution**:
1. Run migrations: `docker compose exec app python scripts/init_db.py`
2. Check migration status:
   ```sql
   SELECT * FROM schema_migrations ORDER BY version;
   ```
3. Verify all tables exist:
   ```sql
   \dt
   ```

---

## CI Failures

### How to Read GitHub Actions Logs

1. Go to repository → **Actions** tab
2. Click on the failing workflow run
3. Click on the failing job (lint, unit-tests, or integration-tests)
4. Expand the failing step to see error output
5. Look for:
   - Test failures: `FAILED tests/...`
   - Linting errors: `src/file.py:line:col: error message`
   - Type errors: `src/file.py:line: error: ...`

### Common CI-Specific Issues

**Symptom**: Tests pass locally but fail in CI

**Possible Causes**:
1. **Environment differences**: CI uses fresh database each run
2. **Timing issues**: CI may be slower, exposing race conditions
3. **Missing environment variables**: Check workflow YAML for required vars
4. **File path differences**: CI runs in `/github/workspace/`, not your local path

**Solutions**:
1. Review CI logs for specific error messages
2. Ensure tests don't depend on local data or state
3. Check that all required environment variables are set in workflow
4. Use relative imports and paths

### Testing Workflow Locally with `act`

To test the GitHub Actions workflow on your machine:

```bash
# Install act
brew install act  # macOS
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Test lint job
act -j lint

# Test unit tests job
act -j unit-tests

# Test integration tests job (may require adjustments)
act -j integration-tests

# Run full workflow
act push
```

**Note**: `act` doesn't perfectly replicate GitHub Actions, especially for service containers. Use it for quick validation, but final verification should be on GitHub.

## Migration Issues

### Migration Already Applied

**Problem**: Trying to apply a migration that's already applied.

**Solutions**:

1. **Check applied migrations**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "
   SELECT * FROM schema_migrations ORDER BY version;
   "
   ```

2. **Skip if already applied** - migrations are idempotent.

3. **Force reapply** (careful!):
   ```bash
   # Drop and recreate
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "
   DROP TABLE IF EXISTS schema_migrations CASCADE;
   "
   # Then reapply all migrations
   ```

### Migration Failed Halfway

**Problem**: Migration failed, database in inconsistent state.

**Solutions**:

1. **Check what exists**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\dt"
   ```

2. **Rollback manually**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "
   DROP TABLE IF EXISTS [problematic_table] CASCADE;
   "
   ```

3. **Clean slate** (WARNING: deletes all data):
   ```bash
   docker compose down -v
   docker compose up -d
   docker compose exec app python scripts/init_db.py
   ```

4. **Check migration SQL syntax**:
   ```bash
   cat migrations/001_initial_schema.sql
   # Look for syntax errors
   ```

---

## General Debugging Steps

### Step 1: Check All Services Are Running

```bash
docker compose ps
# All should show "Up" or "Up (healthy)"
```

### Step 2: Check Logs

```bash
docker compose logs --tail=100 app
docker compose logs --tail=100 postgres
```

### Step 3: Verify Configuration

```bash
# Check .env exists and has correct values
cat .env

# Check environment in container
docker compose exec app env | sort
```

### Step 4: Test Database Connection

```bash
# From app container
docker compose exec app python -c "from src.db import get_connection; get_connection(); print('OK')"

# Direct psql
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT 1;"
```

### Step 5: Restart Services

```bash
docker compose restart
docker compose ps
```

### Step 6: Full Restart (Preserves Data)

```bash
docker compose down
docker compose up -d
docker compose logs -f
```

### Step 7: Nuclear Option (Deletes Data!)

```bash
docker compose down -v
rm -rf ./data/*
docker compose up -d
docker compose exec app python scripts/init_db.py
```

---

## Getting Help

If none of these solutions work:

1. **Check GitHub Issues**: Search for similar problems
2. **Review Docker logs**: `docker compose logs -f`
3. **Check Docker daemon**: `sudo systemctl status docker`
4. **Verify system resources**: `df -h` and `free -h`
5. **Check documentation**:
   - [Development Guide](development.md)
   - [Deployment Guide](deployment.md)
   - Project spec: `agent-os/specs/20251015-project-scaffolding/spec.md`

## Useful Debugging Commands

```bash
# Container info
docker compose ps
docker compose top
docker stats

# Network info
docker network ls
docker network inspect marvel-rivals-network

# Volume info
docker volume ls
docker volume inspect marvel-rivals-stats_postgres-data

# Container shell access
docker compose exec app bash
docker compose exec postgres bash

# Check Docker disk usage
docker system df

# Clean up (be careful!)
docker system prune
docker volume prune
```
## Data Collection Pipeline Issues

### Player Discovery Returns No Results

**Problem**:  runs but finds 0 players.

**Symptoms**:
```
Total players fetched from API: 0
New players added to database: 0
```

**Solutions**:

1. **Check API key configuration**:
   ```bash
   docker compose exec app python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('MARVEL_RIVALS_API_KEY'))"
   # Should print your API key, not None
   ```

2. **Test API connectivity**:
   ```bash
   docker compose exec app python scripts/test_api.py
   ```

3. **Check API response format** - API structure may have changed:
   - Review logs: `docker compose logs app | grep -i 'api'`
   - Update `src/api/client.py` if needed

4. **Verify database connection**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM players;"
   ```

---

### Match Collection Stuck at 0 Matches

**Problem**: Collection runs but no matches are inserted.

**Symptoms**:
```
Players processed: 10
Matches collected: 0 (new)
Matches skipped: 0 (duplicates)
```

**Solutions**:

1. **Check players have been discovered**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM players WHERE match_history_fetched = FALSE;"
   # Should show pending players
   ```

2. **Check match filtering** - Matches may be filtered out:
   ```bash
   # Check current season setting
   grep CURRENT_SEASON .env
   # Verify matches are competitive mode
   ```

3. **Review API responses** in logs:
   ```bash
   docker compose logs app | grep -A 5 'get_player_matches'
   ```

4. **Try with --dry-run** to see what would be collected:
   ```bash
   docker compose exec app python scripts/collect_matches.py --dry-run --batch-size 5
   ```

---

### Rate Limit Errors (429)

**Problem**: API returns "Rate limit exceeded" errors.

**Symptoms**:
```
API Error: 429 - Rate limit exceeded
```

**Solutions**:

1. **Verify rate limit delay** in collection:
   ```bash
   # Should be 8.6 seconds (7 requests/minute)
   docker compose exec app python scripts/collect_matches.py --rate-limit-delay 8.6
   ```

2. **Check if previous run is still executing**:
   ```bash
   docker compose exec app ps aux | grep python
   # Kill if duplicate processes found
   ```

3. **Wait for rate limit reset** (check API response):
   - Free tier: Resets every minute
   - Daily limit: Resets at midnight UTC

4. **Reduce batch size** to spread requests over longer period:
   ```bash
   docker compose exec app python scripts/collect_matches.py --batch-size 50
   ```

---

### Character Analysis Shows No Heroes

**Problem**: Analysis completes but no heroes in output.

**Symptoms**:
```
No heroes met minimum sample size requirements
```

**Solutions**:

1. **Check match data exists**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM matches;"
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM match_participants;"
   # Should show >0 for both
   ```

2. **Lower minimum thresholds** for testing:
   ```bash
   docker compose exec app python scripts/analyze_characters.py --min-games-overall 10
   ```

3. **Check hero distribution**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT hero_name, COUNT(*) FROM match_participants GROUP BY hero_name ORDER BY COUNT(*) DESC LIMIT 10;"
   ```

4. **Verify player rank data**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM players WHERE rank_tier IS NOT NULL;"
   # Should be >0
   ```

---

### JSON Export File Not Created

**Problem**: Analysis runs but no JSON file appears.

**Symptoms**:
```
Analysis complete\!
# But output/character_win_rates.json doesn't exist
```

**Solutions**:

1. **Check if --no-export flag was used**:
   ```bash
   # Run without --no-export
   docker compose exec app python scripts/analyze_characters.py
   ```

2. **Verify output directory exists and is writable**:
   ```bash
   ls -la output/
   # Should show directory exists
   # Create if missing:
   mkdir -p output
   ```

3. **Check Docker volume mounts**:
   ```bash
   docker compose exec app ls -la /app/output/
   # Verify directory exists in container
   ```

4. **Review logs for write errors**:
   ```bash
   docker compose logs app | grep -i 'export\|error'
   ```

---

### Synergy Analysis Runs Forever

**Problem**: Synergy analysis takes >30 minutes or never completes.

**Symptoms**:
- Script running for very long time
- High CPU usage

**Solutions**:

1. **Check dataset size** - Synergy is O(N×M×K) where N=heroes, M=matches, K=teammates:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(DISTINCT hero_name) FROM match_participants;"
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM matches;"
   # Large counts (>1000 heroes or >100k matches) = long runtime
   ```

2. **Increase minimum games threshold** to reduce processing:
   ```bash
   docker compose exec app python scripts/analyze_synergies.py --min-games 100
   ```

3. **Monitor progress** - Check logs for progress updates:
   ```bash
   docker compose logs -f app | grep 'Analyzing'
   ```

4. **Run with smaller sample** first:
   - Delete some data: `DELETE FROM matches WHERE match_id IN (SELECT match_id FROM matches LIMIT 5000);`
   - Or test with just a few heroes

---

### Duplicate Match IDs Error

**Problem**: Database constraint violation on match_id.

**Symptoms**:
```
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "matches_pkey"
```

**Solutions**:

1. **This should not happen** - collection has deduplication logic. If it does:
   ```bash
   # Check for duplicates
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT match_id, COUNT(*) FROM matches GROUP BY match_id HAVING COUNT(*) > 1;"
   ```

2. **Fix duplicates manually**:
   ```sql
   DELETE FROM match_participants WHERE match_id IN (
     SELECT match_id FROM (
       SELECT match_id, ROW_NUMBER() OVER(PARTITION BY match_id) as rn
       FROM matches
     ) t WHERE rn > 1
   );
   DELETE FROM matches WHERE ctid NOT IN (
     SELECT MIN(ctid) FROM matches GROUP BY match_id
   );
   ```

3. **Report bug** - This indicates a logic error in collection code

---

### Foreign Key Violation Errors

**Problem**: Cannot insert match_participants due to missing match or player.

**Symptoms**:
```
psycopg2.errors.ForeignKeyViolation: insert or update on table "match_participants" violates foreign key constraint
```

**Solutions**:

1. **Check insertion order** - Matches must exist before participants:
   - Review `src/collectors/match_collector.py` insert logic
   - Ensure `insert_match()` is called before `insert_match_participants()`

2. **Verify player exists**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT username FROM players LIMIT 10;"
   ```

3. **Check for transaction rollbacks**:
   - If match insert fails, participants shouldn't be inserted
   - Review error handling in collection code

---

## Performance Issues

### Slow Database Queries

**Problem**: Analysis scripts run very slowly.

**Solutions**:

1. **Check indexes exist**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\di"
   # Should show multiple indexes
   ```

2. **Apply index migration if missing**:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -f /docker-entrypoint-initdb.d/002_add_indexes.sql
   ```

3. **Vacuum database** to optimize:
   ```bash
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "VACUUM ANALYZE;"
   ```

4. **Check query plans** for slow queries:
   ```sql
   EXPLAIN ANALYZE SELECT mp.won, p.rank_tier FROM match_participants mp
   JOIN players p ON mp.username = p.username
   WHERE mp.hero_name = 'Spider-Man';
   ```

---

### Out of Disk Space

**Problem**: Database fills available disk space.

**Symptoms**:
```
ERROR: could not extend file "base/16384/12345": No space left on device
```

**Solutions**:

1. **Check disk usage**:
   ```bash
   df -h
   docker system df
   ```

2. **Clean old data**:
   ```bash
   # Truncate large tables (CAUTION: deletes data)
   docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "TRUNCATE TABLE match_participants, matches CASCADE;"
   ```

3. **Increase Docker disk allocation**:
   - Docker Desktop → Preferences → Resources → Disk image size

4. **Move data directory** to larger volume:
   - Update `docker-compose.yml` postgres volume mount
   - Restart containers

---

## Synergy Analysis Issues (v2.0)

### Why Did Synergy Scores Decrease After Updating?

**Problem**: Synergy scores dropped from ±25-30% to ±3-7% after upgrading to v2.0.

**Explanation**:

This is **expected and correct**. Version 2.0 fixed a fundamental methodological flaw in the baseline model.

**v1.0 (Old - Flawed)**:
- Used multiplicative baseline: `expected_wr = hero_a_wr × hero_b_wr`
- Produced unrealistic baselines (20-30% expected win rates)
- Artificially inflated synergy scores to ±25-30%

**v2.0 (New - Correct)**:
- Uses average baseline: `expected_wr = (hero_a_wr + hero_b_wr) / 2`
- Produces realistic baselines (50-60% expected win rates)
- Reports honest synergy scores of ±3-7%

**Example**: Hulk + Luna Snow
- Old expected: 28.6% → Synergy: +31.3% ❌
- New expected: 53.5% → Synergy: +6.4% ✅

**Action**: None required. The new scores are correct. Old v1.0 results were mathematically unsound and should be discarded.

**Reference**: See [MIGRATION_SYNERGY_V2.md](MIGRATION_SYNERGY_V2.md) for detailed explanation.

---

### What Does "Insufficient Sample Size" Warning Mean?

**Problem**: Synergy analysis shows warnings like "Low confidence - only 87 games together".

**Explanation**:

Statistical power depends on sample size. With small samples, confidence intervals are wide and results are uncertain.

**Confidence Levels**:
- **High Confidence**: ≥500 games together (narrow CIs, reliable estimates)
- **Medium Confidence**: 100-499 games (moderate CIs, cautious interpretation needed)
- **Low Confidence**: <100 games (wide CIs, results unreliable - excluded by default)

**Required Sample Sizes** (80% power to detect synergy):
- **3% synergy**: 1,692 games required
- **5% synergy**: 606 games required
- **10% synergy**: 149 games required

**Example**: With 200 games together, you can reliably detect ≥10% synergies but not realistic 3-5% synergies.

**Solutions**:

1. **Increase minimum sample size threshold**:
   ```bash
   docker compose exec app python scripts/analyze_synergies.py --min-sample-size 100
   ```

2. **Collect more data**:
   - Run `discover_players.py` with higher target count
   - Run `collect_matches.py` for more players
   - Target 10,000+ total matches for reliable 3-5% synergy detection

3. **Focus on high-confidence pairs**:
   - Filter JSON results to only `confidence_level: "high"`
   - Interpret medium/low confidence results with caution

**Remember**: Small synergies (3-7%) require massive datasets. With typical data (100-300 games per pair), only large synergies (≥10%) are detectable.

---

### No Synergies Are Statistically Significant

**Problem**: After upgrading to v2.0, all p-values > 0.05 and no synergies marked as significant.

**Explanation**:

This is **expected** with current sample sizes. v2.0 applies proper statistical testing that reveals the truth: with 100-300 games per pair, we lack power to detect realistic 3-7% synergies.

**Why v1.0 Showed Everything as Significant**:
- Flawed multiplicative baseline created artificially low expected win rates
- Made every pair appear to have massive +30% synergies
- All p-values < 0.001 (false positives due to wrong baseline)

**Why v2.0 Shows Nothing as Significant**:
- Correct average baseline produces realistic expected win rates
- True synergies are only ±3-7% (not ±30%)
- Current samples (100-300 games) insufficient to detect small effects
- P-values > 0.05 (honest assessment of uncertainty)

**Power Analysis**:
- With 200 games: 80% power to detect ±10% synergies
- With 200 games: 20% power to detect ±5% synergies (insufficient)
- Need 600+ games to reliably detect ±5% synergies

**Solutions**:

1. **Accept the reality**: True synergies are small and require massive data

2. **Use rankings, not significance**:
   - Hulk + Star-Lord likely better than Hulk + Mantis
   - Even if not statistically conclusive
   - Directional guidance is still valuable

3. **Collect 10× more data**:
   ```bash
   # Target 5,000 players instead of 500
   docker compose exec app python scripts/discover_players.py --target-count 5000
   ```

4. **Lower significance threshold (more liberal)**:
   ```bash
   docker compose exec app python scripts/analyze_synergies.py --alpha 0.10
   ```
   ⚠️ Warning: Increases false positive rate

5. **Focus on large effect sizes**:
   - Look for synergies with magnitude ≥10%
   - These are detectable with current data
   - Realistic synergies (3-7%) require more data collection

**Remember**: Honest uncertainty is better than false confidence. v2.0 tells the truth about what we can and cannot detect with current data.

---
