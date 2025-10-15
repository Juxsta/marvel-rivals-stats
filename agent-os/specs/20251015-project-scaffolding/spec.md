# SPEC-004: Project Scaffolding & Docker Setup

**Status**: Draft
**Author**: Development Team
**Created**: 2025-10-15
**Updated**: 2025-10-15

---

## Problem Statement

The Marvel Rivals Stats Analyzer requires a robust, production-ready development environment that can:
1. Run locally for development with hot-reload capabilities
2. Deploy to the Odin server with consistent behavior between environments
3. Manage PostgreSQL database with proper persistence on Odin's storage infrastructure
4. Support the complete data collection and analysis pipeline with proper dependency management
5. Enable easy onboarding for new developers with minimal setup friction

Currently, the project has basic scaffolding but lacks Docker orchestration, production-ready database configuration, and deployment infrastructure for the Odin server.

---

## Goals

1. Create a complete Docker Compose setup for both development and production environments
2. Configure PostgreSQL 16+ with proper volume mounts on Odin server storage (`/mnt/user/appdata/marvel-rivals-stats/`)
3. Set up Python 3.10+ development environment with hot-reload support
4. Initialize GitHub repository with proper structure and push to remote
5. Implement database migration system with schema versioning
6. Provide clear documentation for development workflow and deployment
7. Ensure seamless integration with existing Odin server infrastructure (Caddy network, storage conventions)

---

## Non-Goals

- FastAPI web backend implementation (Phase 2)
- Next.js frontend development (Phase 3)
- Caddy reverse proxy configuration (future spec)
- Redis caching layer (Phase 4)
- Monitoring stack setup (Phase 4)
- Actual data collection logic implementation (separate specs: SPEC-001, SPEC-002, SPEC-003)

---

## User Stories

1. **As a developer**, I want to run `docker compose up` and have a complete development environment with PostgreSQL and Python ready, so that I can start coding immediately without manual setup.

2. **As a developer**, I want changes to my Python code to be reflected immediately without rebuilding containers, so that I can iterate quickly during development.

3. **As a DevOps engineer**, I want to deploy the same Docker Compose configuration to the Odin server with minimal changes, so that development and production environments remain consistent.

---

## Proposed Solution

### Overview

We will create a Docker Compose configuration that:
- Runs PostgreSQL 16 in a container with persistent volumes on `/mnt/user/appdata/marvel-rivals-stats/postgres/data`
- Provides a Python 3.10 development container with source code mounted as a volume
- Uses Docker networks for inter-container communication
- Manages environment variables through `.env` files
- Includes initialization scripts for database schema setup
- Follows Odin server storage and networking conventions

The project will be initialized as a GitHub repository using `gh` CLI and pushed after completion.

---

## Technical Design

### Directory Structure

```
marvel-rivals-stats/
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Python application container
├── .env.example                 # Environment variable template
├── .env                         # Local environment (gitignored)
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml              # Tool configuration (black, ruff, mypy)
├── README.md                    # Quick start guide
├── PLAN.md                      # Implementation plan
│
├── src/                         # Application source code
│   ├── __init__.py
│   ├── api/                     # Marvel Rivals API client
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── rate_limiter.py
│   ├── db/                      # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py        # Connection pool management
│   │   └── queries.py           # Query helpers
│   ├── collectors/              # Data collection modules
│   │   ├── __init__.py
│   │   ├── player_discovery.py
│   │   └── match_collector.py
│   ├── analyzers/               # Statistical analysis
│   │   ├── __init__.py
│   │   ├── character_winrate.py
│   │   └── team_synergy.py
│   └── utils/                   # Helper utilities
│       ├── __init__.py
│       ├── sampling.py
│       └── stats.py
│
├── scripts/                     # CLI entry points
│   ├── init_db.py              # Database initialization
│   ├── test_api.py             # API client test
│   ├── seed_sample_data.py     # Sample data seeder
│   ├── discover_players.py     # Player discovery (Phase 1)
│   ├── collect_matches.py      # Match collection (Phase 1)
│   └── analyze_character.py    # Character analysis (Phase 1)
│
├── migrations/                  # Database migrations
│   ├── 001_initial_schema.sql  # Core tables
│   ├── 002_add_indexes.sql     # Performance indexes
│   └── schema_version.txt      # Current version tracker
│
├── config/                      # Configuration files
│   ├── rank_quotas.json        # Sampling quotas
│   └── heroes.json             # Hero metadata
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_api/
│   ├── test_db/
│   ├── test_collectors/
│   └── test_analyzers/
│
├── data/                        # Local development data (gitignored)
│   └── .gitkeep
│
├── output/                      # Analysis results (gitignored)
│   ├── character_stats/
│   └── synergy_stats/
│
├── docs/                        # Documentation
│   ├── README.md
│   └── PRODUCT.md
│
└── agent-os/                    # Agent OS framework
    ├── config.yml
    ├── product/
    │   ├── mission.md
    │   ├── roadmap.md
    │   └── tech-stack.md
    ├── specs/
    │   └── 20251015-project-scaffolding/
    │       ├── planning/
    │       │   └── requirements.md
    │       └── spec.md          # This document
    └── standards/
        ├── backend/
        ├── frontend/
        ├── global/
        └── testing/
```

---

### Docker Compose Configuration

**File: `docker-compose.yml`**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: marvel-rivals-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DATABASE_NAME:-marvel_rivals}
      POSTGRES_USER: ${DATABASE_USER:-marvel_stats}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:?Database password required}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      # Production: Use Odin server path
      # Development: Use local ./data/postgres
      - ${DATA_DIR:-./data}/postgres:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d:ro
    ports:
      - "${DATABASE_PORT:-5432}:5432"
    networks:
      - marvel-rivals-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DATABASE_USER:-marvel_stats}"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: ${PYTHON_VERSION:-3.10}
    container_name: marvel-rivals-app
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      # Database connection
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: ${DATABASE_NAME:-marvel_rivals}
      DATABASE_USER: ${DATABASE_USER:-marvel_stats}
      DATABASE_PASSWORD: ${DATABASE_PASSWORD}
      DATABASE_URL: postgresql://${DATABASE_USER:-marvel_stats}:${DATABASE_PASSWORD}@postgres:5432/${DATABASE_NAME:-marvel_rivals}

      # Application config
      MARVEL_RIVALS_API_KEY: ${MARVEL_RIVALS_API_KEY}
      RATE_LIMIT_REQUESTS_PER_MINUTE: ${RATE_LIMIT_REQUESTS_PER_MINUTE:-7}
      CURRENT_SEASON: ${CURRENT_SEASON:-9}
      APP_ENV: ${APP_ENV:-development}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}

      # Python environment
      PYTHONUNBUFFERED: 1
      PYTHONDONTWRITEBYTECODE: 1
    volumes:
      # Mount source code for hot-reload during development
      - ./src:/app/src:ro
      - ./scripts:/app/scripts:ro
      - ./config:/app/config:ro
      - ./migrations:/app/migrations:ro

      # Mount output directories (read-write)
      - ${DATA_DIR:-./data}/output:/app/output
      - ${DATA_DIR:-./data}/logs:/app/logs
    networks:
      - marvel-rivals-net
    # Keep container running for interactive use
    command: tail -f /dev/null
    # Alternative: Run a specific script
    # command: python scripts/collect_matches.py

networks:
  marvel-rivals-net:
    name: marvel-rivals-network
    driver: bridge
    # For Odin server, connect to existing Caddy network:
    # external: true
    # name: caddy

volumes:
  postgres-data:
    driver: local
```

**Notes:**
- Uses health checks to ensure PostgreSQL is ready before starting app
- Volumes are configurable via `DATA_DIR` environment variable
- For Odin deployment, set `DATA_DIR=/mnt/user/appdata/marvel-rivals-stats`
- Development mode mounts source code as read-only volumes for hot-reload
- Network can be switched to external `caddy` network for Phase 2 (web API)

---

### Dockerfile

**File: `Dockerfile`**

```dockerfile
ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY migrations/ ./migrations/

# Create output directories
RUN mkdir -p /app/output /app/logs

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "--version"]
```

**Features:**
- Multi-stage friendly (requirements cached separately)
- Includes PostgreSQL client for debugging
- Creates necessary directories
- Installs both production and dev dependencies

---

### Database Schema

**File: `migrations/001_initial_schema.sql`**

```sql
-- Marvel Rivals Stats Analyzer
-- Initial Database Schema
-- Version: 1.0.0
-- Created: 2025-10-15

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track all discovered players
CREATE TABLE IF NOT EXISTS players (
    username TEXT PRIMARY KEY,
    rank_tier TEXT,
    rank_score INTEGER,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    match_history_fetched BOOLEAN DEFAULT FALSE
);

-- Store unique matches (deduplicated)
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    mode TEXT,
    season INTEGER,
    match_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track who played what in each match
CREATE TABLE IF NOT EXISTS match_participants (
    id SERIAL PRIMARY KEY,
    match_id TEXT NOT NULL,
    username TEXT NOT NULL,
    hero_id INTEGER,
    hero_name TEXT NOT NULL,
    role TEXT CHECK (role IN ('vanguard', 'duelist', 'strategist')),
    team INTEGER CHECK (team IN (0, 1)),
    won BOOLEAN NOT NULL,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    damage DECIMAL(12, 2) DEFAULT 0,
    healing DECIMAL(12, 2) DEFAULT 0,
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE,
    FOREIGN KEY (username) REFERENCES players(username) ON DELETE CASCADE,
    UNIQUE(match_id, username)
);

-- Cache character analysis results
CREATE TABLE IF NOT EXISTS character_stats (
    id SERIAL PRIMARY KEY,
    hero_name TEXT NOT NULL,
    rank_tier TEXT,  -- NULL = all ranks
    total_games INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate DECIMAL(5, 4) NOT NULL,
    confidence_interval_lower DECIMAL(5, 4),
    confidence_interval_upper DECIMAL(5, 4),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hero_name, COALESCE(rank_tier, ''))
);

-- Track character synergies
CREATE TABLE IF NOT EXISTS synergy_stats (
    id SERIAL PRIMARY KEY,
    hero_a TEXT NOT NULL,
    hero_b TEXT NOT NULL,
    rank_tier TEXT,  -- NULL = all ranks
    games_together INTEGER NOT NULL,
    wins_together INTEGER NOT NULL,
    win_rate DECIMAL(5, 4) NOT NULL,
    expected_win_rate DECIMAL(5, 4),
    synergy_score DECIMAL(6, 4),
    statistical_significance DECIMAL(5, 4),  -- p-value
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hero_a, hero_b, COALESCE(rank_tier, '')),
    CHECK(hero_a < hero_b)  -- Enforce alphabetical order
);

-- Track collection progress and metadata
CREATE TABLE IF NOT EXISTS collection_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert schema version
INSERT INTO schema_migrations (version, description)
VALUES (1, 'Initial schema with players, matches, stats tables')
ON CONFLICT (version) DO NOTHING;

-- Insert default metadata
INSERT INTO collection_metadata (key, value) VALUES
    ('schema_version', '1'),
    ('last_collection_run', NULL),
    ('total_players_discovered', '0'),
    ('total_matches_collected', '0')
ON CONFLICT (key) DO NOTHING;
```

**File: `migrations/002_add_indexes.sql`**

```sql
-- Performance Indexes
-- Version: 1.1.0
-- Created: 2025-10-15

-- Indexes for match_participants (most queried table)
CREATE INDEX IF NOT EXISTS idx_match_participants_match_id
    ON match_participants(match_id);

CREATE INDEX IF NOT EXISTS idx_match_participants_username
    ON match_participants(username);

CREATE INDEX IF NOT EXISTS idx_match_participants_hero_name
    ON match_participants(hero_name);

CREATE INDEX IF NOT EXISTS idx_match_participants_won
    ON match_participants(won);

CREATE INDEX IF NOT EXISTS idx_match_participants_hero_won
    ON match_participants(hero_name, won);

-- Composite index for synergy analysis
CREATE INDEX IF NOT EXISTS idx_match_participants_match_team
    ON match_participants(match_id, team);

-- Indexes for matches
CREATE INDEX IF NOT EXISTS idx_matches_season
    ON matches(season);

CREATE INDEX IF NOT EXISTS idx_matches_timestamp
    ON matches(match_timestamp DESC);

-- Indexes for players
CREATE INDEX IF NOT EXISTS idx_players_rank_tier
    ON players(rank_tier);

CREATE INDEX IF NOT EXISTS idx_players_fetched
    ON players(match_history_fetched);

-- Indexes for cached stats
CREATE INDEX IF NOT EXISTS idx_character_stats_hero
    ON character_stats(hero_name);

CREATE INDEX IF NOT EXISTS idx_character_stats_analyzed
    ON character_stats(analyzed_at DESC);

-- Update schema version
INSERT INTO schema_migrations (version, description)
VALUES (2, 'Add performance indexes for queries')
ON CONFLICT (version) DO NOTHING;

UPDATE collection_metadata
SET value = '2', updated_at = CURRENT_TIMESTAMP
WHERE key = 'schema_version';
```

---

### Python Project Setup

**File: `src/__init__.py`**

```python
"""Marvel Rivals Stats Analyzer

A data collection and analysis tool for Marvel Rivals competitive statistics.
"""

__version__ = "0.1.0"
__author__ = "Eric Reyes"
```

**File: `src/db/__init__.py`**

```python
"""Database connection and query utilities."""

from .connection import get_connection, get_connection_pool, close_pool

__all__ = ["get_connection", "get_connection_pool", "close_pool"]
```

**File: `src/api/__init__.py`**

```python
"""Marvel Rivals API client."""

from .client import MarvelRivalsClient
from .rate_limiter import RateLimiter

__all__ = ["MarvelRivalsClient", "RateLimiter"]
```

**File: `src/collectors/__init__.py`**

```python
"""Data collection modules."""

# Will be populated in Phase 1
```

**File: `src/analyzers/__init__.py`**

```python
"""Statistical analysis modules."""

# Will be populated in Phase 1
```

**File: `src/utils/__init__.py`**

```python
"""Utility functions."""

# Will be populated as needed
```

---

### Configuration Management

**File: `.env.example`**

```bash
# Marvel Rivals API Configuration
MARVEL_RIVALS_API_KEY=your_api_key_here
RATE_LIMIT_REQUESTS_PER_MINUTE=7
CURRENT_SEASON=9

# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=marvel_rivals
DATABASE_USER=marvel_stats
DATABASE_PASSWORD=secure_password_here
DATABASE_URL=postgresql://marvel_stats:secure_password_here@localhost:5432/marvel_rivals

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
PYTHON_VERSION=3.10

# Storage Configuration
# For local development:
DATA_DIR=./data
# For Odin server deployment:
# DATA_DIR=/mnt/user/appdata/marvel-rivals-stats
```

**File: `pyproject.toml`**

```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | venv
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 100
target-version = "py310"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "D",   # pydocstyle
]
ignore = [
    "D100", # Missing docstring in public module
    "D104", # Missing docstring in public package
]

[tool.ruff.pydocstyle]
convention = "google"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

**File: `requirements.txt`**

```
# Core dependencies for production
requests>=2.31.0
python-dotenv>=1.0.0
scipy>=1.11.0
psycopg2-binary>=2.9.9
```

**File: `requirements-dev.txt`**

```
# Development dependencies
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.5.0
```

---

### Implementation Details

#### 1. Repository Initialization

The repository will be initialized and pushed to GitHub using the `gh` CLI:

```bash
# Initialize git repository (if not already initialized)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Project scaffolding with Docker setup

- Docker Compose configuration with PostgreSQL 16
- Complete Python project structure
- Database schema with migrations
- Development environment setup
- Documentation and standards"

# Create GitHub repository and push
gh repo create marvel-rivals-stats --public --source=. --remote=origin --push

# Set up branch protection (optional)
gh repo edit --enable-issues --enable-wiki=false
```

**Validation:**
- Repository exists on GitHub
- All files pushed successfully
- `.gitignore` excludes sensitive files (.env, data/, output/)

---

#### 2. Docker Setup

**Development Workflow:**

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add API key
# Set DATA_DIR=./data for local development

# 3. Start services
docker compose up -d

# 4. Verify PostgreSQL is running
docker compose ps
docker compose logs postgres

# 5. Initialize database (if not auto-initialized)
docker compose exec app python scripts/init_db.py

# 6. Test API connection
docker compose exec app python scripts/test_api.py

# 7. Run a script interactively
docker compose exec app python scripts/seed_sample_data.py

# 8. Stop services
docker compose down
```

**Production Deployment (Odin Server):**

```bash
# 1. SSH to Odin server
ssh odin

# 2. Clone repository
cd /home/ericreyes/github
git clone https://github.com/username/marvel-rivals-stats.git
cd marvel-rivals-stats

# 3. Configure environment for production
cp .env.example .env
nano .env
# Set:
#   DATA_DIR=/mnt/user/appdata/marvel-rivals-stats
#   APP_ENV=production
#   DATABASE_PASSWORD=<strong-password>
#   MARVEL_RIVALS_API_KEY=<actual-key>

# 4. Create data directories
mkdir -p /mnt/user/appdata/marvel-rivals-stats/{postgres,output,logs}

# 5. Start services
docker compose up -d

# 6. Verify services are running
docker compose ps
docker compose logs -f

# 7. Initialize database
docker compose exec app python scripts/init_db.py

# 8. Test API connection
docker compose exec app python scripts/test_api.py
```

**Volume Management:**
- PostgreSQL data persists in `/mnt/user/appdata/marvel-rivals-stats/postgres/`
- Application outputs in `/mnt/user/appdata/marvel-rivals-stats/output/`
- Logs in `/mnt/user/appdata/marvel-rivals-stats/logs/`
- Proper permissions: `chown -R ericreyes:ericreyes /mnt/user/appdata/marvel-rivals-stats/`

---

#### 3. Database Migrations

**Manual Migration System:**

The project uses a simple manual migration system with SQL files:

1. **Creating Migrations:**
   - Create numbered SQL files in `migrations/` directory
   - Format: `NNN_description.sql` (e.g., `001_initial_schema.sql`)
   - Track version in `schema_migrations` table

2. **Applying Migrations:**
   - Automatic: Migrations in `migrations/` are run on container initialization
   - Manual: Execute via psql or Python script

3. **Migration Script Template:**

**File: `scripts/run_migration.py`**

```python
#!/usr/bin/env python3
"""Apply database migration."""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def run_migration(migration_file: str) -> None:
    """Execute a migration SQL file."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))

    try:
        with conn.cursor() as cur:
            sql = Path(migration_file).read_text()
            cur.execute(sql)
            conn.commit()
            print(f"✓ Migration applied: {migration_file}")
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        sys.exit(1)

    run_migration(sys.argv[1])
```

**Checking Schema Version:**

```bash
# Connect to database
docker compose exec postgres psql -U marvel_stats -d marvel_rivals

# Check current version
SELECT * FROM schema_migrations ORDER BY version;

# Check metadata
SELECT * FROM collection_metadata;
```

---

#### 4. Development Workflow

**Daily Development:**

```bash
# Start environment
docker compose up -d

# Make code changes in src/ or scripts/
# Changes are automatically available in container (volume mount)

# Run tests
docker compose exec app pytest tests/ -v

# Format code
docker compose exec app black src/ scripts/ tests/

# Lint code
docker compose exec app ruff check src/ scripts/ tests/

# Type check
docker compose exec app mypy src/ scripts/

# Run a specific script
docker compose exec app python scripts/test_api.py

# View logs
docker compose logs -f app

# Stop environment
docker compose down
```

**Testing Database Queries:**

```bash
# Interactive psql session
docker compose exec postgres psql -U marvel_stats -d marvel_rivals

# Run queries
SELECT COUNT(*) FROM players;
SELECT * FROM schema_migrations;
```

**Rebuilding After Dependency Changes:**

```bash
# Rebuild app container
docker compose build app

# Restart with new image
docker compose up -d app
```

---

### Alternative Approaches Considered

#### 1. SQLite vs PostgreSQL
**Rejected**: SQLite
**Reason**:
- PostgreSQL provides better concurrent access for future web API
- JSONB support for flexible data
- Production-grade performance and reliability
- Easier to scale if needed
- Already planning self-hosted deployment on Odin

#### 2. Virtual Environment vs Docker
**Rejected**: Virtual environment only
**Reason**:
- Docker ensures consistency between dev and production
- Easier database setup (no manual PostgreSQL installation)
- Better isolation and reproducibility
- Aligns with Odin server infrastructure (Docker Compose for all services)

#### 3. Alembic/SQLAlchemy vs Manual Migrations
**Rejected**: Alembic migration tool
**Reason**:
- Overhead not justified for small project
- Direct SQL is more transparent and easier to debug
- No ORM benefits (using raw SQL queries)
- Simple version tracking is sufficient

#### 4. Separate Database Container Config
**Rejected**: Using external database config file
**Reason**:
- docker-compose.yml is sufficient for configuration
- Environment variables provide flexibility
- Less files to manage
- Standard Docker Compose pattern

---

## Dependencies

### Required Before Implementation
- ✅ Project directory exists at `/home/ericreyes/github/marvel-rivals-stats/`
- ✅ Basic Python project structure (src/, scripts/, docs/)
- ✅ Database schema designed (PLAN.md)
- ✅ Tech stack documented (tech-stack.md)
- ✅ Development standards defined (agent-os/standards/)

### Required for Deployment
- Docker 20.10+ installed on development machine
- Docker Compose 2.0+ installed
- GitHub account and `gh` CLI configured
- Access to Odin server via SSH
- Docker installed on Odin server
- Write permissions to `/mnt/user/appdata/` on Odin
- Marvel Rivals API key

### External Dependencies
- PostgreSQL 16+ Docker image (postgres:16-alpine)
- Python 3.10+ Docker image (python:3.10-slim)
- Docker Hub availability for pulling images

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **PostgreSQL data loss** | High | Low | Use proper volumes on `/mnt/user/appdata/`, implement backup strategy to NFS mount |
| **Docker image pull failures** | Medium | Low | Cache images locally, document manual image building |
| **Permission issues on Odin** | Medium | Medium | Document proper chown commands, use consistent UID/GID (1000:1000) |
| **Environment variable mistakes** | Medium | Medium | Provide comprehensive `.env.example`, validate on startup |
| **Port conflicts on Odin** | Low | Low | Use standard ports (5432), document how to change if needed |
| **Network configuration issues** | Medium | Low | Start with isolated network, document Caddy integration for Phase 2 |
| **Migration order issues** | Low | Low | Use numbered migrations, track in schema_migrations table |
| **Hot-reload not working** | Low | Medium | Document volume mount requirements, verify file permissions |

---

## Success Criteria

### Core Functionality
- ✅ `docker compose up` starts PostgreSQL and app containers without errors
- ✅ PostgreSQL data persists after `docker compose down` and restart
- ✅ Database schema created successfully with all tables and indexes
- ✅ Python container can connect to PostgreSQL
- ✅ Environment variables loaded correctly from `.env`
- ✅ Source code changes reflected in container without rebuild

### Database Verification
- ✅ All 7 tables created (players, matches, match_participants, character_stats, synergy_stats, collection_metadata, schema_migrations)
- ✅ All indexes created (11 total)
- ✅ Foreign key constraints working
- ✅ Sample data can be inserted and queried

### Development Workflow
- ✅ `scripts/init_db.py` runs successfully
- ✅ `scripts/test_api.py` demonstrates API client works (with mock/test key)
- ✅ `scripts/seed_sample_data.py` populates test data
- ✅ Code formatting, linting, and type checking commands work
- ✅ pytest runs successfully (even if no tests yet)

### Deployment
- ✅ Repository created on GitHub
- ✅ All code pushed to main branch
- ✅ `.gitignore` excludes sensitive files (.env, data/, output/)
- ✅ README provides clear quick start instructions
- ✅ Docker Compose runs on Odin server with production configuration

### Documentation
- ✅ README.md updated with Docker setup instructions
- ✅ Environment variables documented in `.env.example`
- ✅ Development workflow documented
- ✅ Deployment process documented for Odin server

---

## Testing Plan

### Manual Testing Checklist

**Local Development:**
```bash
# 1. Environment Setup
[ ] Copy .env.example to .env
[ ] Set DATA_DIR=./data
[ ] Add placeholder API key

# 2. Docker Compose
[ ] Run: docker compose up -d
[ ] Verify: docker compose ps shows both services "Up"
[ ] Check logs: docker compose logs postgres
[ ] Check logs: docker compose logs app

# 3. Database Connectivity
[ ] Connect: docker compose exec postgres psql -U marvel_stats -d marvel_rivals
[ ] List tables: \dt
[ ] Verify 7 tables exist
[ ] Check schema version: SELECT * FROM schema_migrations;
[ ] Exit: \q

# 4. Python Scripts
[ ] Run init_db: docker compose exec app python scripts/init_db.py
[ ] Run test_api: docker compose exec app python scripts/test_api.py
[ ] Run seed_data: docker compose exec app python scripts/seed_sample_data.py

# 5. Code Quality Tools
[ ] Format: docker compose exec app black --check src/ scripts/
[ ] Lint: docker compose exec app ruff check src/ scripts/
[ ] Type check: docker compose exec app mypy src/ scripts/
[ ] Test: docker compose exec app pytest tests/ -v

# 6. Hot Reload Test
[ ] Edit src/__init__.py (add a comment)
[ ] Verify change visible: docker compose exec app cat src/__init__.py
[ ] Edit scripts/test_api.py (add a print statement)
[ ] Run script: docker compose exec app python scripts/test_api.py
[ ] Confirm print statement appears

# 7. Persistence Test
[ ] Insert test data via psql or script
[ ] Stop: docker compose down
[ ] Start: docker compose up -d
[ ] Verify data still exists

# 8. Cleanup
[ ] Stop services: docker compose down
[ ] Remove volumes: docker compose down -v (optional, for clean slate)
```

**Odin Server Deployment:**
```bash
# 1. Initial Setup
[ ] SSH to Odin: ssh odin
[ ] Clone repo: git clone <repo-url>
[ ] cd marvel-rivals-stats

# 2. Environment Configuration
[ ] Copy: cp .env.example .env
[ ] Edit .env with production values
[ ] Set DATA_DIR=/mnt/user/appdata/marvel-rivals-stats
[ ] Set strong DATABASE_PASSWORD
[ ] Add real MARVEL_RIVALS_API_KEY

# 3. Storage Preparation
[ ] Create: mkdir -p /mnt/user/appdata/marvel-rivals-stats/{postgres,output,logs}
[ ] Set permissions: chown -R ericreyes:ericreyes /mnt/user/appdata/marvel-rivals-stats/

# 4. Docker Deployment
[ ] Start: docker compose up -d
[ ] Verify: docker compose ps
[ ] Check logs: docker compose logs -f

# 5. Database Initialization
[ ] Run: docker compose exec app python scripts/init_db.py
[ ] Verify tables: docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\dt"

# 6. API Test
[ ] Run: docker compose exec app python scripts/test_api.py
[ ] Verify successful API connection

# 7. Monitoring
[ ] Check disk usage: du -sh /mnt/user/appdata/marvel-rivals-stats/*
[ ] Check container stats: docker stats marvel-rivals-postgres marvel-rivals-app

# 8. Restart Test
[ ] Restart: docker compose restart
[ ] Verify services come back up healthy
```

### Automated Tests

**Unit Tests (tests/test_db/test_connection.py):**
```python
"""Test database connection."""

import os
import pytest
from src.db import get_connection


def test_database_connection():
    """Test that we can connect to PostgreSQL."""
    conn = get_connection()
    assert conn is not None

    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1

    conn.close()


def test_schema_version():
    """Test that schema migrations were applied."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1")
        result = cur.fetchone()
        assert result is not None
        assert result[0] >= 1

    conn.close()
```

---

## Implementation Tasks

### Phase 1: Local Development Setup (Week 1, Days 1-2)
1. Create `docker-compose.yml` with PostgreSQL and app services
2. Create `Dockerfile` for Python application
3. Create database migration files (001, 002)
4. Update `requirements.txt` and `requirements-dev.txt`
5. Create `pyproject.toml` for tool configuration
6. Update `.env.example` with all required variables
7. Create Python package `__init__.py` files
8. Update `.gitignore` for Docker and Python

### Phase 2: Scripts & Initialization (Week 1, Days 2-3)
1. Enhance `scripts/init_db.py` with connection pooling
2. Enhance `scripts/test_api.py` with Docker environment
3. Update `scripts/seed_sample_data.py` for PostgreSQL
4. Create `scripts/run_migration.py` for manual migrations
5. Add database connection module (`src/db/connection.py`)
6. Add basic query helpers (`src/db/queries.py`)

### Phase 3: Documentation (Week 1, Day 3)
1. Update README.md with Docker setup instructions
2. Document development workflow
3. Document deployment process for Odin
4. Create troubleshooting guide
5. Update PLAN.md with Docker architecture

### Phase 4: Testing & Validation (Week 1, Day 4)
1. Write database connection tests
2. Write schema validation tests
3. Test hot-reload functionality
4. Test data persistence
5. Run full local testing checklist
6. Fix any issues found

### Phase 5: Repository & Deployment (Week 1, Day 4)
1. Initialize Git repository (if needed)
2. Create GitHub repository using `gh` CLI
3. Push all code to GitHub
4. Deploy to Odin server
5. Run Odin deployment checklist
6. Verify production deployment

---

## Timeline

**Estimated Effort**: 4 days (32 hours)

**Breakdown:**
- Docker Configuration: 8 hours
  - docker-compose.yml: 2 hours
  - Dockerfile: 2 hours
  - Environment setup: 2 hours
  - Network configuration: 2 hours

- Database Setup: 6 hours
  - Migration files: 3 hours
  - Connection pooling: 2 hours
  - Testing: 1 hour

- Scripts & Tooling: 4 hours
  - Update existing scripts: 2 hours
  - Create migration runner: 1 hour
  - Code quality setup: 1 hour

- Documentation: 4 hours
  - README updates: 2 hours
  - Deployment guide: 2 hours

- Testing: 6 hours
  - Write tests: 3 hours
  - Manual testing: 2 hours
  - Debugging: 1 hour

- Deployment: 4 hours
  - GitHub setup: 1 hour
  - Odin deployment: 2 hours
  - Validation: 1 hour

**Target Completion**: End of Week 1 (Oct 18, 2025)

---

## Open Questions

1. **Network Configuration**: Should we connect to the existing Caddy network immediately, or wait until Phase 2 when we build the web API?
   - **Recommendation**: Start with isolated network, document Caddy integration for Phase 2

2. **Backup Strategy**: Should we implement automated PostgreSQL backups to the NFS mount now, or defer to Phase 4?
   - **Recommendation**: Defer to Phase 4, document manual backup procedure for now

3. **Container Restart Policy**: Should containers restart automatically on boot (`restart: always`) or only on failure (`restart: unless-stopped`)?
   - **Recommendation**: Use `unless-stopped` for development flexibility

4. **Development vs Production Compose**: Should we maintain separate `docker-compose.yml` and `docker-compose.prod.yml` files?
   - **Recommendation**: Single file with environment variable overrides is sufficient

5. **Logging Strategy**: Should we implement structured logging (JSON) immediately, or use simple text logs?
   - **Recommendation**: Start with simple text logs, enhance in Phase 4 with monitoring

---

## References

### Internal Documentation
- `/home/ericreyes/github/marvel-rivals-stats/PLAN.md` - Database schema and architecture
- `/home/ericreyes/github/marvel-rivals-stats/agent-os/product/tech-stack.md` - Technology decisions
- `/home/ericreyes/github/marvel-rivals-stats/agent-os/product/roadmap.md` - Project phases
- `/home/ericreyes/github/marvel-rivals-stats/agent-os/standards/` - Development standards

### External Resources
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Python Docker Image](https://hub.docker.com/_/python)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [Marvel Rivals API Documentation](https://marvelrivalsapi.com/docs)

### Odin Server Context
- Server storage conventions: `/mnt/user/appdata/<service>/`
- Docker network: `caddy` (for Phase 2 integration)
- Reverse proxy: Caddy with automatic SSL
- Authentication: Discord OAuth via Caddy (future)

---

**Last Updated**: 2025-10-15
**Next Review**: After Phase 1 MVP completion
