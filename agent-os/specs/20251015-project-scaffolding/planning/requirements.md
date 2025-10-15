# Requirements: Project Scaffolding & Docker Setup

## Spec ID
20251015-project-scaffolding

## Overview
Set up the complete project scaffolding for Marvel Rivals Stats Analyzer with Docker Compose for development and deployment on self-hosted infrastructure (Odin server).

## User Request
"lets create the first spec - primary scaffolding. Lets use docker compose for setup. i believe we dont need next js right now. you can use the gh cli to initialize the repo and push after completion"

## Core Requirements

### 1. Project Initialization
- Initialize GitHub repository using `gh` CLI
- Set up proper `.gitignore` for Python projects
- Create README with quick start instructions
- Set up proper directory structure following the documented architecture

### 2. Docker Compose Setup
- **PostgreSQL 16+** container for database
- **Python 3.10+** development environment
- Volume mounts for:
  - Database data: `/mnt/user/appdata/marvel-rivals-stats/postgres/data`
  - Application data: `/mnt/user/appdata/marvel-rivals-stats/`
  - Project code for development
- Network configuration for container communication
- Environment variable management via `.env`

### 3. Database Setup
- PostgreSQL schema based on PLAN.md design:
  - `players` table
  - `matches` table
  - `match_participants` table
  - `character_stats` table (for caching)
  - `synergy_stats` table
  - `collection_metadata` table
  - `schema_migrations` table
- Migration system (manual SQL files)
- Database initialization script

### 4. Python Project Structure
- `src/` directory with modules:
  - `src/api/` - Marvel Rivals API client
  - `src/db/` - Database connection and queries
  - `src/collectors/` - Data collection logic
  - `src/analyzers/` - Statistical analysis
  - `src/utils/` - Helper functions
- `scripts/` directory for CLI tools:
  - `scripts/init_db.py` - Initialize database
  - `scripts/test_api.py` - Test API connection
  - `scripts/seed_sample_data.py` - Seed test data
- `tests/` directory for pytest
- `config/` directory for configuration files
- `migrations/` directory for SQL migrations

### 5. Dependencies & Configuration
- `requirements.txt` with production dependencies:
  - requests
  - python-dotenv
  - scipy
  - psycopg2-binary
- `requirements-dev.txt` with development dependencies:
  - pytest
  - pytest-cov
  - pytest-mock
  - black
  - ruff
  - mypy
- `.env.example` with all required environment variables
- `pyproject.toml` for tool configuration (black, ruff, mypy)

### 6. Development Workflow
- Docker Compose commands documented
- Database connection from host machine (for development)
- Hot reload support for Python code
- Scripts to run tests, linting, formatting

### 7. Integration with Existing Infrastructure
- Prepare for Caddy reverse proxy integration (future)
- Use existing Docker network naming conventions
- Follow Odin server storage conventions

## Out of Scope
- ❌ Next.js frontend (Phase 3)
- ❌ FastAPI backend (Phase 2)
- ❌ Actual data collection implementation (separate specs)
- ❌ Caddy configuration (future spec)
- ❌ Redis caching (Phase 4)
- ❌ Monitoring stack (Phase 4)

## Success Criteria
1. ✅ Repository created on GitHub
2. ✅ Docker Compose successfully starts PostgreSQL
3. ✅ Database schema created and verified
4. ✅ Python environment accessible in container
5. ✅ All dependencies installed correctly
6. ✅ `init_db.py` script runs successfully
7. ✅ `test_api.py` demonstrates API client works (with mock/test key)
8. ✅ Project structure matches documented architecture
9. ✅ README provides clear quick start instructions
10. ✅ Code pushed to GitHub repository

## Technical Context
- **Target Server**: Odin (Proxmox VM, Ubuntu, 225GB available)
- **Storage Path**: `/mnt/user/appdata/marvel-rivals-stats/`
- **Database**: PostgreSQL 16+ (Docker container)
- **Python Version**: 3.10+
- **Package Manager**: pip + requirements.txt

## Reference Documentation
- `/home/ericreyes/github/marvel-rivals-stats/PLAN.md` - Database schema
- `/home/ericreyes/github/marvel-rivals-stats/agent-os/product/tech-stack.md` - Tech stack decisions
- `/home/ericreyes/github/marvel-rivals-stats/agent-os/product/roadmap.md` - Phase 1 requirements
- `/home/ericreyes/github/marvel-rivals-stats/docs/PRODUCT.md` - Product vision

## Constraints
- Must use Docker Compose (not separate Docker commands)
- Must follow existing server conventions (volumes, networks)
- Must be PostgreSQL (not SQLite) for production readiness
- Python code must be mounted as volume for development hot-reload
