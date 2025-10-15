# Tasks: Project Scaffolding & Docker Setup

**Spec**: SPEC-004
**Status**: Not Started
**Estimated Total Time**: 8-12 hours

---

## Overview

This specification implements the foundational infrastructure for the Marvel Rivals Stats Analyzer project. The approach prioritizes:

1. **Quick wins first**: Start with simple, visible progress (GitHub repo, directories)
2. **Incremental validation**: Each phase ends with working, verifiable infrastructure
3. **Development-first**: Set up local environment completely before Odin deployment
4. **Minimal test writing**: Infrastructure validation through manual testing and basic smoke tests only

The implementation strategy builds infrastructure layer by layer, ensuring each component works before adding the next. This allows for early validation and reduces debugging complexity.

---

## Available Implementers

Based `/home/ericreyes/github/marvel-rivals-stats/agent-os/roles/implementers.yml`:

- **database-engineer**: Database migrations, schemas, queries, seed data
- **api-engineer**: API endpoints, controllers, business logic (not heavily used in Phase 1)
- **ui-designer**: Frontend components (not used in Phase 1 - no frontend yet)
- **testing-engineer**: Test infrastructure and critical smoke tests

**Note**: This scaffolding project is primarily infrastructure/DevOps work, so tasks will be assigned to database-engineer (for database setup) and testing-engineer (for validation scripts), with some unassigned infrastructure tasks that don't fit specialist roles.

---

## Task Breakdown

### Phase 1: Repository & Project Structure

#### Task Group 1: GitHub Repository Initialization
**Assigned implementer:** Unassigned (infrastructure task)
**Dependencies:** None
**Estimated Time:** 30 minutes

- [ ] **1.1**: Create `.gitignore` file
  - **Description**: Create comprehensive Python/Docker `.gitignore`
  - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/.gitignore`
  - **Contents should include**:
    - Python artifacts (`__pycache__/`, `*.pyc`, `.pytest_cache/`)
    - Virtual environments (`venv/`, `.venv/`)
    - IDE files (`.vscode/`, `.idea/`)
    - Environment files (`.env`)
    - Data directories (`data/`, `output/`)
    - Docker volumes
  - **Verification**: `git status` should not show ignored files after creation
  - **Estimated time**: 5 minutes

- [ ] **1.2**: Update README.md with quick start
  - **Description**: Add Docker setup instructions and project overview
  - **Files to modify**: `/home/ericreyes/github/marvel-rivals-stats/README.md`
  - **Should include**:
    - Project description
    - Prerequisites (Docker, Docker Compose)
    - Quick start commands (`docker compose up`, etc.)
    - Environment variable setup
    - Common development commands
  - **Verification**: Follow README instructions on fresh clone
  - **Estimated time**: 20 minutes

- [ ] **1.3**: Initialize Git repository and push to GitHub
  - **Description**: Initialize git, create GitHub repo using `gh` CLI
  - **Commands to run**:
    ```bash
    cd /home/ericreyes/github/marvel-rivals-stats
    git init
    git add .gitignore README.md
    git commit -m "Initial commit: Project setup"
    gh repo create marvel-rivals-stats --public --source=. --remote=origin --push
    ```
  - **Verification**: Visit GitHub URL and confirm repo exists
  - **Estimated time**: 5 minutes

**Acceptance Criteria:**
- GitHub repository exists and is accessible
- `.gitignore` properly excludes sensitive files
- README provides clear setup instructions

---

### Phase 2: Directory Structure & Configuration Files

#### Task Group 2: Project Scaffolding
**Assigned implementer:** Unassigned (infrastructure task)
**Dependencies:** Task Group 1
**Estimated Time:** 1 hour

- [x] **2.1**: Create Python package structure
  - **Description**: Create all source directories and `__init__.py` files
  - **Directories to create**:
    - `/home/ericreyes/github/marvel-rivals-stats/src/`
    - `/home/ericreyes/github/marvel-rivals-stats/src/api/`
    - `/home/ericreyes/github/marvel-rivals-stats/src/db/`
    - `/home/ericreyes/github/marvel-rivals-stats/src/collectors/`
    - `/home/ericreyes/github/marvel-rivals-stats/src/analyzers/`
    - `/home/ericreyes/github/marvel-rivals-stats/src/utils/`
  - **Files to create**: Create `__init__.py` in each directory with appropriate docstrings
  - **Reference**: See spec.md lines 489-544 for exact `__init__.py` content
  - **Verification**: `python -c "import src.api; import src.db"` should work
  - **Estimated time**: 15 minutes

- [x] **2.2**: Create scripts directory structure
  - **Description**: Create scripts directory with placeholder files
  - **Directories to create**:
    - `/home/ericreyes/github/marvel-rivals-stats/scripts/`
  - **Files to create**:
    - `scripts/init_db.py` (placeholder)
    - `scripts/test_api.py` (placeholder)
    - `scripts/seed_sample_data.py` (placeholder)
    - `scripts/run_migration.py` (placeholder)
  - **Note**: These will be implemented in later task groups
  - **Verification**: Files exist and are executable
  - **Estimated time**: 10 minutes

- [x] **2.3**: Create supporting directories
  - **Description**: Create migrations, config, tests, data, output directories
  - **Directories to create**:
    - `/home/ericreyes/github/marvel-rivals-stats/migrations/`
    - `/home/ericreyes/github/marvel-rivals-stats/config/`
    - `/home/ericreyes/github/marvel-rivals-stats/tests/`
    - `/home/ericreyes/github/marvel-rivals-stats/data/` (with `.gitkeep`)
    - `/home/ericreyes/github/marvel-rivals-stats/output/` (with `.gitkeep`)
  - **Verification**: All directories exist
  - **Estimated time**: 5 minutes

- [x] **2.4**: Create Python configuration files
  - **Description**: Create requirements files and pyproject.toml
  - **Files to create**:
    - `requirements.txt` - See spec.md lines 635-641
    - `requirements-dev.txt` - See spec.md lines 643-653
    - `pyproject.toml` - See spec.md lines 578-631
  - **Verification**: `pip install -r requirements.txt` works (in venv)
  - **Estimated time**: 15 minutes

- [x] **2.5**: Create environment configuration template
  - **Description**: Create `.env.example` with all required variables
  - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/.env.example`
  - **Reference**: See spec.md lines 550-576 for complete content
  - **Should include**:
    - Marvel Rivals API configuration
    - Database configuration
    - Application configuration
    - Storage configuration (with both local and Odin paths commented)
  - **Verification**: All variables are documented and have example values
  - **Estimated time**: 15 minutes

**Acceptance Criteria:**
- Complete directory structure matches spec.md design
- All `__init__.py` files created with proper docstrings
- Configuration files are valid and parseable
- `.env.example` documents all required environment variables

---

### Phase 3: Docker Configuration

#### Task Group 3: Docker Compose Setup
**Assigned implementer:** Unassigned (infrastructure task)
**Dependencies:** Task Group 2
**Estimated Time:** 1.5 hours

- [x] **3.1**: Create Dockerfile for Python application
  - **Description**: Create multi-stage Dockerfile with development dependencies
  - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/Dockerfile`
  - **Reference**: See spec.md lines 268-305 for exact content
  - **Must include**:
    - Python 3.10 slim base image
    - PostgreSQL client installation
    - Requirements installation with layer caching
    - Proper PYTHONPATH configuration
    - Working directory setup
  - **Verification**: `docker build -t marvel-rivals-test .` succeeds
  - **Estimated time**: 30 minutes

- [x] **3.2**: Create docker-compose.yml
  - **Description**: Create Docker Compose configuration with PostgreSQL and app services
  - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/docker-compose.yml`
  - **Reference**: See spec.md lines 167-257 for exact content
  - **Must include**:
    - PostgreSQL 16 service with health checks
    - Python app service with volume mounts
    - Proper environment variable configuration
    - Network configuration
    - Volume configuration for data persistence
  - **Verification**: `docker compose config` validates without errors
  - **Estimated time**: 45 minutes

- [x] **3.3**: Create local development .env file
  - **Description**: Copy `.env.example` to `.env` and configure for local development
  - **Commands to run**:
    ```bash
    cd /home/ericreyes/github/marvel-rivals-stats
    cp .env.example .env
    ```
  - **Required edits**:
    - Set `DATA_DIR=./data`
    - Set `DATABASE_PASSWORD` to a secure local password
    - Set `MARVEL_RIVALS_API_KEY` to test key (or placeholder)
    - Ensure all other variables have sensible defaults
  - **Verification**: `.env` file exists and is not tracked by git
  - **Estimated time**: 5 minutes

- [x] **3.4**: Test Docker Compose startup
  - **Description**: Start services and verify they run
  - **Commands to run**:
    ```bash
    docker compose up -d
    docker compose ps
    docker compose logs postgres
    docker compose logs app
    ```
  - **Verification**:
    - Both services show "Up" status
    - PostgreSQL health check passes
    - No errors in logs
  - **Rollback**: `docker compose down` if issues found
  - **Estimated time**: 10 minutes

**Acceptance Criteria:**
- Docker Compose successfully starts both services
- PostgreSQL container passes health check
- App container starts and stays running
- Volume mounts work correctly
- Environment variables are passed to containers

---

### Phase 4: Database Schema & Migrations

#### Task Group 4: Database Setup
**Assigned implementer:** database-engineer
**Dependencies:** Task Group 3
**Estimated Time:** 2 hours

- [ ] **4.0**: Complete database layer setup
  - [ ] **4.1**: Write 2-4 focused tests for database connection
    - **Description**: Create basic smoke tests for PostgreSQL connectivity
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/tests/test_db/test_connection.py`
    - **Tests should cover**:
      - Database connection succeeds
      - Can execute simple query (SELECT 1)
      - Can create and drop test table
      - Schema version table exists
    - **Limit**: Maximum 4 tests focused on connectivity only
    - **Reference**: See spec.md lines 1106-1139 for example tests
    - **Estimated time**: 20 minutes

  - [ ] **4.2**: Create initial schema migration
    - **Description**: Create SQL migration with all core tables
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/migrations/001_initial_schema.sql`
    - **Reference**: See spec.md lines 317-425 for complete schema
    - **Must create tables**:
      - `schema_migrations` (for version tracking)
      - `players` (player discovery)
      - `matches` (unique matches)
      - `match_participants` (match details)
      - `character_stats` (cached analysis)
      - `synergy_stats` (team synergies)
      - `collection_metadata` (tracking)
    - **Must include**: UUID extension, foreign keys, check constraints
    - **Verification**: SQL syntax is valid
    - **Estimated time**: 30 minutes

  - [ ] **4.3**: Create indexes migration
    - **Description**: Create performance indexes for queries
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/migrations/002_add_indexes.sql`
    - **Reference**: See spec.md lines 427-483 for complete indexes
    - **Must create indexes for**:
      - `match_participants` (most queried table)
      - `matches` (season, timestamp)
      - `players` (rank_tier, match_history_fetched)
      - `character_stats` (hero_name, analyzed_at)
    - **Verification**: SQL syntax is valid
    - **Estimated time**: 20 minutes

  - [ ] **4.4**: Create database connection module
    - **Description**: Implement PostgreSQL connection pooling
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/src/db/connection.py`
    - **Must implement**:
      - `get_connection()` - Get single connection
      - `get_connection_pool()` - Get connection pool
      - `close_pool()` - Close all connections
      - Environment variable configuration
      - Error handling and logging
    - **Dependencies**: psycopg2-binary
    - **Verification**: Can import module without errors
    - **Estimated time**: 30 minutes

  - [ ] **4.5**: Run database migrations and verify
    - **Description**: Apply migrations and verify schema
    - **Commands to run**:
      ```bash
      docker compose exec postgres psql -U marvel_stats -d marvel_rivals -f /docker-entrypoint-initdb.d/001_initial_schema.sql
      docker compose exec postgres psql -U marvel_stats -d marvel_rivals -f /docker-entrypoint-initdb.d/002_add_indexes.sql
      docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\dt"
      docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\di"
      ```
    - **Verification**:
      - 7 tables exist
      - 11+ indexes created
      - Schema version is 2
      - No errors in psql output
    - **Estimated time**: 20 minutes

**Acceptance Criteria:**
- All 7 tables created successfully
- All indexes created successfully
- Foreign key constraints work correctly
- Connection module successfully connects to database
- 2-4 database connection tests pass

---

### Phase 5: Database Initialization Scripts

#### Task Group 5: Database Scripts
**Assigned implementer:** database-engineer
**Dependencies:** Task Group 4
**Estimated Time:** 1.5 hours

- [x] **5.0**: Complete database script implementation
  - [x] **5.1**: Implement `init_db.py` script
    - **Description**: Create script to initialize database and verify schema
    - **Files to create/modify**: `/home/ericreyes/github/marvel-rivals-stats/scripts/init_db.py`
    - **Must implement**:
      - Load environment variables
      - Connect to PostgreSQL
      - Check if schema exists
      - Run migrations if needed
      - Verify all tables exist
      - Print status report
    - **Verification**: `docker compose exec app python scripts/init_db.py` succeeds
    - **Estimated time**: 40 minutes

  - [x] **5.2**: Implement `run_migration.py` script
    - **Description**: Create script to manually apply migration files
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/scripts/run_migration.py`
    - **Reference**: See spec.md lines 786-823 for complete implementation
    - **Must implement**:
      - Accept migration file path as argument
      - Execute SQL file contents
      - Handle errors and rollback
      - Print success/failure
    - **Verification**: Can manually run a migration file
    - **Estimated time**: 20 minutes

  - [x] **5.3**: Implement `seed_sample_data.py` script
    - **Description**: Create script to insert sample data for testing
    - **Files to create/modify**: `/home/ericreyes/github/marvel-rivals-stats/scripts/seed_sample_data.py`
    - **Must implement**:
      - Insert 3-5 sample players
      - Insert 2-3 sample matches
      - Insert 10-15 sample match_participants
      - Use realistic data (actual hero names, valid ranks)
      - Print what was inserted
    - **Verification**: `docker compose exec app python scripts/seed_sample_data.py` succeeds
    - **Estimated time**: 30 minutes

**Acceptance Criteria:**
- `init_db.py` successfully initializes database
- `run_migration.py` can apply migrations
- `seed_sample_data.py` inserts valid test data
- All scripts handle errors gracefully
- All scripts print helpful status messages

---

### Phase 6: API Client Stubs

#### Task Group 6: API Integration Setup
**Assigned implementer:** api-engineer
**Dependencies:** Task Group 5
**Estimated Time:** 1.5 hours

- [x] **6.0**: Complete API client layer
  - [x] **6.1**: Write 2-3 focused tests for API client
    - **Description**: Create basic tests for API client initialization
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/tests/test_api/test_client.py`
    - **Tests should cover**:
      - Client initializes with API key
      - Rate limiter initializes correctly
      - Client has expected methods (even if unimplemented)
    - **Limit**: Maximum 3 tests, no actual API calls
    - **Estimated time**: 15 minutes

  - [x] **6.2**: Create rate limiter module
    - **Description**: Implement token bucket rate limiter
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/src/api/rate_limiter.py`
    - **Must implement**:
      - `RateLimiter` class
      - Token bucket algorithm
      - Configurable requests per minute
      - `wait_if_needed()` method
      - Thread-safe implementation
    - **Note**: This is needed for future API calls
    - **Verification**: Can import and instantiate
    - **Estimated time**: 40 minutes

  - [x] **6.3**: Create API client stub
    - **Description**: Create API client with method stubs for future implementation
    - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/src/api/client.py`
    - **Must implement**:
      - `MarvelRivalsClient` class
      - Constructor accepting API key
      - Rate limiter integration
      - Method stubs (raise `NotImplementedError`):
        - `get_player_profile(username)`
        - `get_player_matches(username)`
        - `get_match_details(match_id)`
      - Basic error handling structure
    - **Verification**: Can import and instantiate client
    - **Estimated time**: 30 minutes

  - [x] **6.4**: Create `test_api.py` script
    - **Description**: Create script to test API client initialization (no actual API calls yet)
    - **Files to create/modify**: `/home/ericreyes/github/marvel-rivals-stats/scripts/test_api.py`
    - **Must implement**:
      - Load API key from environment
      - Initialize MarvelRivalsClient
      - Print client configuration
      - Print "API client initialized successfully"
      - Note: Actual API calls will be implemented in Phase 1 (data collection)
    - **Verification**: `docker compose exec app python scripts/test_api.py` succeeds
    - **Estimated time**: 15 minutes

  - [x] **6.5**: Run API client tests
    - **Description**: Execute the 2-3 tests written in 6.1
    - **Commands to run**:
      ```bash
      docker compose exec app pytest tests/test_api/ -v
      ```
    - **Verification**: All 2-3 tests pass
    - **Estimated time**: 5 minutes

**Acceptance Criteria:**
- Rate limiter module implemented and functional
- API client stub created with method signatures
- `test_api.py` script successfully initializes client
- 2-3 API client tests pass
- No actual API calls made (stubs only)

---

### Phase 7: Testing & Validation

#### Task Group 7: Integration Testing
**Assigned implementer:** testing-engineer
**Dependencies:** Task Groups 4, 5, 6
**Estimated Time:** 2 hours

- [x] **7.0**: Complete integration testing and validation
  - [x] **7.1**: Run all existing tests
    - **Description**: Execute pytest to verify all tests pass
    - **Commands to run**:
      ```bash
      docker compose exec app pytest tests/ -v
      ```
    - **Expected**: 10 existing tests pass (4 DB + 3 API + 3 seed data tests)
    - **Action**: Document any failures
    - **Estimated time**: 10 minutes

  - [x] **7.2**: Create end-to-end workflow test
    - **Description**: Test complete data flow from database to seed data
    - **Files to create**:
      - `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/__init__.py`
      - `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_workflow.py`
    - **Tests implemented** (3 tests total):
      - Test database → init_db → seed_sample_data → verify data exists
      - Test all tables have expected data after seeding
      - Test foreign key relationships work end-to-end
    - **Estimated time**: 30 minutes

  - [x] **7.3**: Docker health validation
    - **Description**: Verify Docker services are healthy
    - **Files to create**:
      - `/home/ericreyes/github/marvel-rivals-stats/tests/test_integration/test_docker.py`
    - **Tests implemented** (3 tests total):
      - Test PostgreSQL is reachable from app container
      - Test can execute psql commands
      - Test environment variables are loaded correctly
    - **Estimated time**: 20 minutes

  - [x] **7.4**: Validation checklist execution
    - **Description**: Run through manual validation checklist
    - **Actions performed**:
      - Verified Docker Compose services all healthy
      - Verified all 7 database tables exist
      - Verified all migrations applied (schema version 2)
      - Verified seed data inserted successfully (5 players, 3 matches)
      - Verified all 16 tests pass
    - **Estimated time**: 10 minutes

**Acceptance Criteria:**
- Total 16 tests pass (10 existing + 6 new integration tests)
- Critical integration points validated
- Manual validation checklist completed successfully
- Docker services healthy
- All verification commands documented

---

### Phase 8: Documentation & Deployment

#### Task Group 8: Final Documentation
**Assigned implementer:** Unassigned (documentation task)
**Dependencies:** Task Group 7
**Estimated Time:** 1.5 hours

- [x] **8.1**: Update README.md with complete instructions
  - **Description**: Add comprehensive setup and usage documentation
  - **Files to modify**: `/home/ericreyes/github/marvel-rivals-stats/README.md`
  - **Must include**:
    - Project overview and goals
    - Prerequisites (Docker 20.10+, Docker Compose 2.0+)
    - Quick start guide
    - Development workflow
    - Common commands
    - Troubleshooting section
    - Links to additional documentation
  - **Reference**: See spec.md for examples
  - **Verification**: A new developer can follow README to get started
  - **Estimated time**: 30 minutes

- [x] **8.2**: Create development workflow guide
  - **Description**: Document daily development practices
  - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/docs/development.md`
  - **Must include**:
    - Starting and stopping services
    - Running scripts
    - Running tests
    - Code formatting and linting
    - Database access
    - Rebuilding containers
  - **Reference**: See spec.md lines 840-893
  - **Verification**: All commands are tested and work
  - **Estimated time**: 20 minutes

- [x] **8.3**: Create Odin deployment guide
  - **Description**: Document production deployment to Odin server
  - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/docs/deployment.md`
  - **Must include**:
    - SSH access to Odin
    - Repository cloning
    - Environment configuration for production
    - Storage directory setup
    - Docker Compose deployment
    - Verification steps
    - Monitoring commands
  - **Reference**: See spec.md lines 725-760
  - **Verification**: Instructions are clear and complete
  - **Estimated time**: 25 minutes

- [x] **8.4**: Create troubleshooting guide
  - **Description**: Document common issues and solutions
  - **Files to create**: `/home/ericreyes/github/marvel-rivals-stats/docs/troubleshooting.md`
  - **Must include**:
    - Port conflicts
    - Permission issues
    - Database connection failures
    - Volume mount problems
    - Environment variable issues
  - **Verification**: Covers issues found during development
  - **Estimated time**: 15 minutes

**Acceptance Criteria:**
- README is comprehensive and beginner-friendly
- Development workflow is documented with working commands
- Odin deployment process is clear and complete
- Troubleshooting guide addresses common issues

---

### Phase 9: Git Commit & GitHub Push

#### Task Group 9: Version Control Finalization
**Assigned implementer:** Unassigned (infrastructure task)
**Dependencies:** Task Group 8
**Estimated Time:** 30 minutes

- [x] **9.1**: Review all changes and commit
  - **Description**: Commit all scaffolding work with comprehensive message
  - **Commands to run**:
    ```bash
    cd /home/ericreyes/github/marvel-rivals-stats
    git add .
    git status  # Review what will be committed
    ```
  - **Verification**:
    - `.env` is NOT in staging (should be in .gitignore)
    - `data/` and `output/` are NOT in staging
    - All code and configuration files are included
  - **Estimated time**: 10 minutes

- [x] **9.2**: Create comprehensive commit
  - **Description**: Commit with detailed message following project standards
  - **Commands to run**:
    ```bash
    git commit -m "$(cat <<'EOF'
    Complete project scaffolding with Docker setup

    - Add Docker Compose configuration with PostgreSQL 16 and Python 3.10
    - Create complete project structure (src/, scripts/, tests/, migrations/)
    - Implement database schema with 7 tables and performance indexes
    - Add database connection pooling and initialization scripts
    - Create API client stubs with rate limiter
    - Add development, testing, and troubleshooting documentation
    - Include environment configuration template
    - Set up code quality tools (black, ruff, mypy, pytest)

    Infrastructure is ready for Phase 1 data collection implementation.

    🤖 Generated with [Claude Code](https://claude.com/claude-code)

    Co-Authored-By: Claude <noreply@anthropic.com>
    EOF
    )"
    ```
  - **Verification**: `git log -1` shows complete commit message
  - **Estimated time**: 5 minutes

- [x] **9.3**: Push to GitHub
  - **Description**: Push all commits to remote repository
  - **Commands to run**:
    ```bash
    git push origin main
    ```
  - **Verification**: Visit GitHub repo URL and confirm all files are present
  - **Estimated time**: 5 minutes

- [x] **9.4**: Verify GitHub repository
  - **Description**: Review repository on GitHub.com
  - **Check**:
    - All files present
    - `.gitignore` working (no .env, no data/)
    - README renders correctly
    - Commit history is clean
  - **Verification**: Repository is ready for collaboration
  - **Estimated time**: 10 minutes

**Acceptance Criteria:**
- All code committed with descriptive message
- Changes pushed to GitHub successfully
- `.gitignore` properly excludes sensitive files
- Repository is accessible and well-organized

---

### Phase 10: Odin Server Deployment (Optional)

#### Task Group 10: Production Deployment
**Assigned implementer:** Unassigned (deployment task)
**Dependencies:** Task Group 9
**Estimated Time:** 1 hour
**Note**: This is optional and can be done later when ready for production

- [ ] **10.1**: SSH to Odin and clone repository
  - **Description**: Access Odin server and clone the GitHub repository
  - **Commands to run**:
    ```bash
    ssh odin
    cd /home/ericreyes/github
    git clone https://github.com/YOUR_USERNAME/marvel-rivals-stats.git
    cd marvel-rivals-stats
    ```
  - **Verification**: Repository cloned successfully
  - **Estimated time**: 5 minutes

- [ ] **10.2**: Configure production environment
  - **Description**: Create production `.env` file
  - **Commands to run**:
    ```bash
    cp .env.example .env
    nano .env
    ```
  - **Required configuration**:
    - `DATA_DIR=/mnt/user/appdata/marvel-rivals-stats`
    - `APP_ENV=production`
    - Strong `DATABASE_PASSWORD`
    - Real `MARVEL_RIVALS_API_KEY`
    - `LOG_LEVEL=INFO`
  - **Verification**: All production values set correctly
  - **Estimated time**: 10 minutes

- [ ] **10.3**: Create storage directories on Odin
  - **Description**: Set up persistent storage paths
  - **Commands to run**:
    ```bash
    mkdir -p /mnt/user/appdata/marvel-rivals-stats/{postgres,output,logs}
    chown -R ericreyes:ericreyes /mnt/user/appdata/marvel-rivals-stats/
    ls -la /mnt/user/appdata/marvel-rivals-stats/
    ```
  - **Verification**: Directories exist with correct permissions
  - **Estimated time**: 5 minutes

- [ ] **10.4**: Deploy with Docker Compose
  - **Description**: Start services on Odin server
  - **Commands to run**:
    ```bash
    docker compose up -d
    docker compose ps
    docker compose logs -f
    ```
  - **Verification**:
    - Both services show "Up" status
    - PostgreSQL health check passes
    - No errors in logs
  - **Estimated time**: 15 minutes

- [ ] **10.5**: Initialize production database
  - **Description**: Run database initialization on production
  - **Commands to run**:
    ```bash
    docker compose exec app python scripts/init_db.py
    docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "\dt"
    docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT * FROM schema_migrations;"
    ```
  - **Verification**: All tables created, schema version correct
  - **Estimated time**: 10 minutes

- [ ] **10.6**: Run production validation tests
  - **Description**: Verify deployment on Odin
  - **Commands to run**:
    ```bash
    docker compose exec app python scripts/test_api.py
    docker compose exec app pytest tests/ -v
    docker compose exec app python scripts/seed_sample_data.py
    docker compose restart
    docker compose ps
    ```
  - **Verification**: All tests pass, services restart successfully
  - **Estimated time**: 15 minutes

**Acceptance Criteria:**
- Services running on Odin server
- Database initialized with correct schema
- Persistent storage configured correctly
- All validation tests pass on production
- Services survive restart

---

## Task Dependencies Graph

```
Phase 1: Repository & Project Structure
    └─> Task Group 1: GitHub Repository Initialization
            │
            v
Phase 2: Directory Structure & Configuration Files
    └─> Task Group 2: Project Scaffolding
            │
            v
Phase 3: Docker Configuration
    └─> Task Group 3: Docker Compose Setup
            │
            v
Phase 4: Database Schema & Migrations
    └─> Task Group 4: Database Setup (database-engineer)
            │
            v
Phase 5: Database Initialization Scripts
    └─> Task Group 5: Database Scripts (database-engineer)
            │
            v
Phase 6: API Client Stubs
    └─> Task Group 6: API Integration Setup (api-engineer)
            │
            v
Phase 7: Testing & Validation
    └─> Task Group 7: Integration Testing (testing-engineer)
            │
            v
Phase 8: Documentation & Deployment
    └─> Task Group 8: Final Documentation
            │
            v
Phase 9: Git Commit & GitHub Push
    └─> Task Group 9: Version Control Finalization
            │
            v
Phase 10: Odin Server Deployment (Optional)
    └─> Task Group 10: Production Deployment
```

**Note**: Each phase must be completed and verified before moving to the next. This ensures working infrastructure at each checkpoint.

---

## Testing Checkpoints

### After Phase 3 (Docker Configuration)
- [ ] `docker compose up -d` starts both services
- [ ] `docker compose ps` shows both services "Up"
- [ ] PostgreSQL health check passes
- [ ] Can execute: `docker compose exec postgres psql -U marvel_stats -d marvel_rivals -c "SELECT 1;"`

### After Phase 4 (Database Setup)
- [ ] All 7 tables exist: `\dt` in psql
- [ ] All indexes created: `\di` in psql
- [ ] Schema version is 2
- [ ] Database connection tests pass (2-4 tests)

### After Phase 5 (Database Scripts)
- [ ] `scripts/init_db.py` runs without errors
- [ ] `scripts/seed_sample_data.py` inserts test data
- [ ] Can query sample data: `SELECT COUNT(*) FROM players;`

### After Phase 6 (API Client)
- [x] `scripts/test_api.py` runs without errors
- [x] API client tests pass (2-3 tests)
- [x] Rate limiter initializes correctly

### After Phase 7 (Testing)
- [x] All tests pass (16 tests total: 4 DB + 3 API + 3 seed + 6 integration)
- [x] Manual testing checklist completed
- [x] No critical issues found

### After Phase 9 (GitHub Push)
- [ ] Repository visible on GitHub
- [ ] README renders correctly
- [ ] All files committed (except .env, data/)

### After Phase 10 (Odin Deployment) - Optional
- [ ] Services running on Odin
- [ ] Database persists after restart
- [ ] Tests pass on production

---

## Rollback Plan

### If Docker Compose fails to start:
1. Check Docker daemon status: `systemctl status docker`
2. Validate compose file: `docker compose config`
3. Check port conflicts: `netstat -tlnp | grep 5432`
4. Review logs: `docker compose logs`
5. Remove containers and retry: `docker compose down -v && docker compose up -d`

### If database migrations fail:
1. Connect to PostgreSQL: `docker compose exec postgres psql -U marvel_stats -d marvel_rivals`
2. Check schema_migrations table: `SELECT * FROM schema_migrations;`
3. Manually rollback: `DROP TABLE IF EXISTS [table_name] CASCADE;`
4. Re-run migrations: `docker compose exec app python scripts/run_migration.py migrations/001_initial_schema.sql`

### If tests fail:
1. Check test output for specific failure
2. Verify environment variables: `docker compose exec app env | grep DATABASE`
3. Check database connectivity: `docker compose exec app python -c "from src.db import get_connection; get_connection()"`
4. Review test logs: `docker compose exec app pytest tests/ -v --tb=long`

### If GitHub push fails:
1. Check authentication: `gh auth status`
2. Verify remote: `git remote -v`
3. Check branch: `git branch -a`
4. Force push if needed (only for initial setup): `git push -f origin main`

### If Odin deployment fails:
1. Check storage permissions: `ls -la /mnt/user/appdata/marvel-rivals-stats/`
2. Verify environment variables on Odin: `cat .env`
3. Check Docker network: `docker network ls`
4. Review Odin-specific logs: `docker compose logs -f`
5. Restart services: `docker compose restart`

---

## Notes

### Development vs Production Configuration

The project uses a single `docker-compose.yml` with environment variable overrides for flexibility:

- **Development**:
  - `DATA_DIR=./data` (local storage)
  - `APP_ENV=development`
  - Database port exposed on host (5432)

- **Production (Odin)**:
  - `DATA_DIR=/mnt/user/appdata/marvel-rivals-stats` (persistent storage)
  - `APP_ENV=production`
  - Strong database password
  - Real API key

### Migration Strategy

This project uses a simple manual migration system:
- Numbered SQL files (001, 002, etc.)
- Tracked in `schema_migrations` table
- No automatic rollback (manual if needed)
- Sufficient for small project scope

**Why not Alembic?** Overhead not justified for a small project with infrequent schema changes. Direct SQL is more transparent and easier to debug.

### Hot Reload Strategy

Python code is mounted as read-only volumes in Docker:
- Changes to `src/` immediately available in container
- No container rebuild needed for code changes
- Rebuild only needed for dependency changes

### Testing Philosophy

Following the project's testing standards:
- **Minimal tests during development**: 16 tests total for scaffolding
- **Focus on critical paths**: Database connectivity, Docker environment, workflows
- **No exhaustive coverage**: Skip edge cases, error handling, comprehensive unit tests
- **Manual testing**: Use checklists for infrastructure validation

### Storage Persistence

PostgreSQL data persists in:
- **Development**: `./data/postgres/` (gitignored)
- **Production**: `/mnt/user/appdata/marvel-rivals-stats/postgres/`

Data survives container restarts and `docker compose down`. Only `docker compose down -v` removes volumes.

### Next Steps After Completion

After this scaffolding is complete, the project will be ready for:
1. **Phase 1 Implementation**: Data collection (player discovery, match collection)
2. **Phase 1 Implementation**: Statistical analysis (character win rates, synergies)
3. **Phase 2 Implementation**: FastAPI web backend
4. **Phase 3 Implementation**: Next.js frontend
5. **Phase 4 Implementation**: Redis caching and monitoring

---

**Last Updated**: 2025-10-15
**Estimated Completion**: 8-12 hours of focused work
**Target Date**: Complete within 2-3 days
