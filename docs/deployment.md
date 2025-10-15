# Deployment Guide - Odin Server

This guide covers deploying the Marvel Rivals Stats Analyzer to the Odin server.

## Prerequisites

- SSH access to Odin server
- Docker and Docker Compose installed on Odin
- GitHub repository access
- Marvel Rivals API key

## Architecture Overview

The Odin server deployment follows these conventions:
- **Server Name**: Odin (Proxmox VM)
- **Platform**: Linux (Ubuntu)
- **Docker Network**: Isolated network (can connect to `caddy` network later for web API)
- **Storage Location**: `/mnt/user/appdata/marvel-rivals-stats/`
- **Repository Location**: `/home/ericreyes/github/marvel-rivals-stats/`
- **User**: `ericreyes` (UID/GID 1000)

## Deployment Steps

### 1. SSH to Odin Server

```bash
ssh ericreyes@odin
# Or if configured in SSH config:
ssh odin
```

### 2. Clone Repository

```bash
# Navigate to GitHub projects directory
cd /home/ericreyes/github

# Clone the repository
git clone https://github.com/YOUR_USERNAME/marvel-rivals-stats.git
cd marvel-rivals-stats
```

If the repository is private:
```bash
# Ensure GitHub authentication is configured
gh auth login
# Then clone
git clone https://github.com/YOUR_USERNAME/marvel-rivals-stats.git
```

### 3. Configure Production Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with production values
nano .env
```

**Required Production Configuration:**

```bash
# Marvel Rivals API Configuration
MARVEL_RIVALS_API_KEY=your_actual_api_key_here
RATE_LIMIT_REQUESTS_PER_MINUTE=7
CURRENT_SEASON=9

# Database Configuration
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=marvel_rivals
DATABASE_USER=marvel_stats
DATABASE_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD  # Use a strong password!
DATABASE_URL=postgresql://marvel_stats:YOUR_STRONG_PASSWORD@postgres:5432/marvel_rivals

# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
PYTHON_VERSION=3.10

# Storage Configuration - IMPORTANT for Odin!
DATA_DIR=/mnt/user/appdata/marvel-rivals-stats
```

**Security Notes:**
- Use a strong, unique password for `DATABASE_PASSWORD`
- Never commit `.env` file to git
- Keep API key secure

### 4. Create Storage Directories

```bash
# Create persistent storage directories on Odin
mkdir -p /mnt/user/appdata/marvel-rivals-stats/postgres
mkdir -p /mnt/user/appdata/marvel-rivals-stats/output
mkdir -p /mnt/user/appdata/marvel-rivals-stats/logs

# Set correct permissions
chown -R ericreyes:ericreyes /mnt/user/appdata/marvel-rivals-stats/

# Verify directories
ls -la /mnt/user/appdata/marvel-rivals-stats/
```

Expected output:
```
drwxr-xr-x  2 ericreyes ericreyes 4096 ... postgres/
drwxr-xr-x  2 ericreyes ericreyes 4096 ... output/
drwxr-xr-x  2 ericreyes ericreyes 4096 ... logs/
```

### 5. Deploy with Docker Compose

```bash
# From the project directory
cd /home/ericreyes/github/marvel-rivals-stats

# Pull Docker images
docker compose pull

# Build application container
docker compose build

# Start services in detached mode
docker compose up -d
```

### 6. Verify Services Are Running

```bash
# Check service status
docker compose ps

# Expected output:
# NAME                     STATUS              PORTS
# marvel-rivals-app        Up
# marvel-rivals-postgres   Up (healthy)        5432/tcp

# View logs
docker compose logs -f
```

Wait for PostgreSQL health check to pass (may take 10-30 seconds).

### 7. Initialize Database

```bash
# Run database initialization script
docker compose exec app python scripts/init_db.py
```

Expected output:
```
Connecting to database...
Running migrations...
✓ Migration 001_initial_schema.sql applied
✓ Migration 002_add_indexes.sql applied
Database initialized successfully!
Schema version: 2
Tables: 7
```

Verify database:
```bash
# Check tables exist
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\dt"

# Check schema version
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT * FROM schema_migrations;"
```

### 8. Test API Connection

```bash
# Test Marvel Rivals API client
docker compose exec app python scripts/test_api.py
```

Expected output:
```
Marvel Rivals API Client initialized
API Key: ****...
Rate Limit: 7 requests/minute
API client initialized successfully!
```

### 9. Seed Sample Data (Optional)

```bash
# Insert sample data for testing
docker compose exec app python scripts/seed_sample_data.py

# Verify data inserted
docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT COUNT(*) FROM players;"
```

## Verification Checklist

After deployment, verify:

- [ ] Services running: `docker compose ps`
- [ ] PostgreSQL healthy: `docker compose exec postgres pg_isready -U marvel_stats`
- [ ] Database tables exist: `docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\dt"`
- [ ] Schema version correct: Check `schema_migrations` table shows version 2
- [ ] API client works: `docker compose exec app python scripts/test_api.py`
- [ ] Data persists: `docker compose restart && docker compose ps`
- [ ] Logs accessible: `docker compose logs app --tail=50`
- [ ] Storage directories writable: `ls -la /mnt/user/appdata/marvel-rivals-stats/`

## Monitoring

### View Real-Time Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app
docker compose logs -f postgres

# Last N lines
docker compose logs --tail=100 app
```

### Check Service Status

```bash
# Service health
docker compose ps

# Container resource usage
docker stats marvel-rivals-app marvel-rivals-postgres

# Disk usage
du -sh /mnt/user/appdata/marvel-rivals-stats/*
```

### Database Monitoring

```bash
# Connect to database
docker compose exec postgres psql -U marvel_stats -d marvel_rivals

# Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check row counts
SELECT
    'players' AS table_name, COUNT(*) FROM players
UNION ALL
SELECT 'matches', COUNT(*) FROM matches
UNION ALL
SELECT 'match_participants', COUNT(*) FROM match_participants;
```

## Maintenance

### Updating the Application

```bash
# SSH to Odin
ssh odin
cd /home/ericreyes/github/marvel-rivals-stats

# Pull latest changes
git pull origin main

# Rebuild if dependencies changed
docker compose build

# Restart services
docker compose up -d

# Verify
docker compose ps
docker compose logs app --tail=50
```

### Restarting Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart app
docker compose restart postgres

# Full stop and start (preserves data)
docker compose down
docker compose up -d
```

### Database Backups

```bash
# Create backup
docker compose exec postgres pg_dump -U marvel_stats marvel_rivals > /mnt/user/appdata/marvel-rivals-stats/backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh /mnt/user/appdata/marvel-rivals-stats/backup_*.sql

# Restore from backup (if needed)
docker compose exec -T postgres psql -U marvel_stats -d marvel_rivals < /mnt/user/appdata/marvel-rivals-stats/backup_YYYYMMDD_HHMMSS.sql
```

Recommended: Set up automated backups with cron:
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /home/ericreyes/github/marvel-rivals-stats && docker compose exec -T postgres pg_dump -U marvel_stats marvel_rivals > /mnt/user/appdata/marvel-rivals-stats/backup_$(date +\%Y\%m\%d).sql
```

### Viewing Application Logs

```bash
# Application logs from Docker
docker compose logs app --tail=100 -f

# If writing to log files
tail -f /mnt/user/appdata/marvel-rivals-stats/logs/app.log
```

### Cleaning Up

```bash
# Remove stopped containers
docker compose down

# Remove containers and volumes (CAREFUL: deletes data!)
docker compose down -v

# Clean Docker system (prune unused images)
docker system prune -a
```

## Updating Environment Variables

If you need to change environment variables after deployment:

```bash
# Edit .env file
nano .env

# Restart services to apply changes
docker compose restart

# Or reload (down/up)
docker compose down
docker compose up -d
```

## Running Data Collection Scripts

Once deployed, run collection scripts:

```bash
# Player discovery (Phase 1)
docker compose exec app python scripts/discover_players.py

# Match collection (Phase 1)
docker compose exec app python scripts/collect_matches.py

# Character analysis (Phase 1)
docker compose exec app python scripts/analyze_character.py

# View output
ls -lh /mnt/user/appdata/marvel-rivals-stats/output/
```

## Connecting to Caddy Network (Future)

When adding web API (Phase 2), connect to existing Caddy network:

```bash
# Edit docker-compose.yml
nano docker-compose.yml
```

Change network configuration:
```yaml
networks:
  marvel-rivals-net:
    external: true
    name: caddy
```

Then restart:
```bash
docker compose down
docker compose up -d
```

## Security Considerations

1. **Database Password**: Use a strong, unique password
2. **API Key**: Keep secure, rotate periodically
3. **File Permissions**: Ensure `/mnt/user/appdata/marvel-rivals-stats/` owned by `ericreyes`
4. **Firewall**: PostgreSQL port (5432) should not be exposed externally
5. **Backups**: Store backups securely, consider encryption for sensitive data

## Performance Tuning

### PostgreSQL Configuration

For better performance with large datasets:

```bash
# Connect to database
docker compose exec postgres psql -U marvel_stats -d marvel_rivals

# Increase shared_buffers (adjust based on available RAM)
ALTER SYSTEM SET shared_buffers = '256MB';

# Increase work_mem for complex queries
ALTER SYSTEM SET work_mem = '16MB';

# Restart to apply
docker compose restart postgres
```

### Application Configuration

Adjust in `.env`:
```bash
# Increase rate limit if API allows
RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Adjust log level for production
LOG_LEVEL=WARNING
```

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.

Common deployment issues:
- Port conflicts: Check if another service is using port 5432
- Permission denied: Verify ownership of `/mnt/user/appdata/marvel-rivals-stats/`
- Container won't start: Check logs with `docker compose logs`
- Database connection failed: Verify `.env` configuration and PostgreSQL health

## Rollback Procedure

If deployment fails:

```bash
# Stop services
docker compose down

# Checkout previous version
git log --oneline  # Find last working commit
git checkout <commit-hash>

# Rebuild and restart
docker compose build
docker compose up -d

# Verify
docker compose ps
```

## Next Steps

After successful deployment:
1. Set up monitoring and alerting (Phase 4)
2. Configure automated backups
3. Implement data collection scripts (Phase 1)
4. Set up Caddy reverse proxy for web API (Phase 2)

## Support

For issues or questions:
- Check [Troubleshooting Guide](troubleshooting.md)
- Review [Development Workflow](development.md)
- Check Docker logs: `docker compose logs -f`
- Verify environment configuration: `.env` file
