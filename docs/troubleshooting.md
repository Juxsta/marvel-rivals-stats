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

---

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
