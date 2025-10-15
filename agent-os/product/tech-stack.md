# Marvel Rivals Stats Analyzer - Tech Stack

## Overview

This document defines the complete technical stack for the Marvel Rivals Stats Analyzer project. All development should adhere to these technology choices to maintain consistency and code quality.

---

## Core Technologies

### Language & Runtime
- **Language**: Python 3.10+
  - **Rationale**: Excellent data science ecosystem (scipy, pandas), simple scripting, great for CLI tools
  - **Version**: 3.10 minimum (for modern type hints and match statements)
- **Package Manager**: pip + requirements.txt
  - **Rationale**: Standard Python tooling, simple dependency management
- **Virtual Environment**: venv (built-in)

### Application Architecture
- **Interface**: CLI scripts
  - **Rationale**: Simple, reproducible, scriptable, no web server overhead
- **Entry Points**: `scripts/` directory with executable Python files
- **Module Structure**: `src/` directory with importable modules

---

## Data & Storage

### Database
- **Primary Database**: PostgreSQL 16+
  - **Rationale**:
    - Production-grade relational database
    - Concurrent read/write support (CLI + web)
    - Better query performance for complex analytics
    - JSONB support for flexible data
    - Self-hosted on Odin server
  - **Location**: Docker container on Odin
  - **Connection**: psycopg2 or asyncpg (Python)
  - **Schema Management**: SQL migrations in `migrations/`

- **Development Database**: SQLite 3 (optional)
  - For local development/testing without server access
  - Can mirror schema from PostgreSQL

### Data Export
- **Format**: JSON
  - **Rationale**:
    - Human-readable, widely supported
    - Easy integration with web tools, Discord bots
    - Native Python support with `json` module
  - **Location**: `output/` directory or web API responses

### Storage Locations
- **Database**: `/mnt/user/appdata/marvel-rivals-stats/postgres/data`
- **Application Data**: `/mnt/user/appdata/marvel-rivals-stats/`
- **Logs**: `/mnt/user/appdata/marvel-rivals-stats/logs/`
- **Exports**: `/mnt/user/appdata/marvel-rivals-stats/exports/`

---

## External APIs

### Marvel Rivals API
- **Provider**: marvelrivalsapi.com
- **Client**: Custom wrapper (`src/api/client.py`)
- **Features**:
  - Rate limiting (7 requests/minute)
  - Automatic retries with exponential backoff
  - Error handling and logging
- **Authentication**: API key via environment variable

---

## Libraries & Dependencies

### Core Dependencies

#### Data Analysis
- **scipy** (v1.11+): Statistical functions
  - Wilson confidence intervals
  - Significance testing
  - `pip install scipy`

#### HTTP Requests
- **requests** (v2.31+): API client
  - Simple, reliable HTTP library
  - `pip install requests`

#### Database
- **psycopg2-binary** (v2.9+): PostgreSQL adapter
  - Python to PostgreSQL connection
  - `pip install psycopg2-binary`
- **sqlalchemy** (v2.0+): SQL toolkit (optional)
  - If we want ORM features later
  - Currently using raw SQL

#### Environment Configuration
- **python-dotenv** (v1.0+): .env file parsing
  - Secure API key management
  - `pip install python-dotenv`

### Development Dependencies

#### Testing
- **pytest** (v7.4+): Test framework
  - **Rationale**: Modern, feature-rich, widely adopted
  - **Plugins**:
    - `pytest-cov`: Coverage reporting
    - `pytest-mock`: Mocking utilities
  - **Usage**: `pytest tests/`

#### Code Quality
- **black** (v23.0+): Code formatter
  - **Rationale**: Opinionated, consistent, reduces bike-shedding
  - **Config**: Line length 100 characters
  - **Usage**: `black src/ scripts/ tests/`

- **ruff** (v0.1+): Fast Python linter
  - **Rationale**: Replaces flake8, isort, pydocstyle - much faster
  - **Rules**: pycodestyle (E/W), pyflakes (F), isort (I), pydocstyle (D)
  - **Usage**: `ruff check src/ scripts/`

- **mypy** (v1.5+): Static type checker
  - **Rationale**: Catch type errors before runtime
  - **Config**: Strict mode enabled
  - **Usage**: `mypy src/ scripts/`

#### Utilities
- **tqdm** (v4.66+): Progress bars (optional)
  - For long-running collection scripts
  - `pip install tqdm`

---

## Database Schema

### ORM / Query Builder
- **Raw SQL with psycopg2**: Direct PostgreSQL queries
  - **Rationale**:
    - Small project, ORM overhead not justified
    - Direct SQL is more explicit and transparent
    - Easier to optimize queries
    - Full control over query performance
  - **Helpers**: Custom query functions in `src/db/connection.py`
  - **Connection Pooling**: SimpleConnectionPool for concurrent access

### Migration Strategy
- **Manual Migrations**: SQL files with version numbers
  - **Rationale**: Simple, explicit, no dependencies
  - **Process**:
    - Create `migrations/001_initial.sql`
    - Apply via `psql` or Python script
    - Track applied migrations in `schema_migrations` table

---

## Testing & Quality

### Test Framework
- **pytest**: All tests in `tests/` directory
- **Coverage Target**: 80%+ for core modules
- **Test Types**:
  - **Unit Tests**: Individual functions, mocked dependencies
  - **Integration Tests**: API calls, database operations (with test DB)
  - **Manual Tests**: Sample data validation

### Code Quality Tools
```bash
# Format code
black src/ scripts/ tests/

# Lint code
ruff check src/ scripts/ tests/

# Type check
mypy src/ scripts/

# Run tests with coverage
pytest --cov=src --cov-report=html
```

### Pre-commit Hooks (Future)
- **pre-commit framework**: Automated checks before git commit
  - Run black, ruff, mypy
  - Prevent committing broken code

---

## CI/CD

### Continuous Integration
- **Platform**: GitHub Actions
- **Triggers**: Push to main, pull requests
- **Jobs**:
  1. **Lint**: Run ruff and black --check
  2. **Type Check**: Run mypy
  3. **Test**: Run pytest with coverage
  4. **Report**: Upload coverage to Codecov (optional)

### Continuous Deployment
- **Platform**: Self-hosted on Odin server
- **Deployment Strategy**:
  - **Collection Scripts**: Cron jobs on server (daily data collection)
  - **Web Application**: Docker container with auto-restart
  - **Updates**: Git pull + Docker rebuild on server
- **Orchestration**: Docker Compose (integrates with existing server stack)
- **Reverse Proxy**: Caddy (existing) with subdomain `rivals.jinocenc.io`
- **Authentication**: Discord OAuth via Caddy (optional for admin features)

---

## Development Environment

### Required Tools
- Python 3.10+ (pyenv recommended for version management)
- Git
- SQLite3 (usually pre-installed)
- Text editor with Python support (VS Code, PyCharm, Vim, etc.)

### Recommended VS Code Extensions
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Ruff (charliermarsh.ruff)

### Environment Setup
```bash
# Clone repository
git clone <repo-url>
cd marvel-rivals-stats

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env and add API key
```

---

## Configuration Management

### Environment Variables (.env)
```bash
# Marvel Rivals API
MARVEL_RIVALS_API_KEY=your_key_here
RATE_LIMIT_REQUESTS_PER_MINUTE=7
CURRENT_SEASON=9

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/marvel_rivals
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=marvel_rivals
DATABASE_USER=marvel_stats
DATABASE_PASSWORD=secure_password

# Application
APP_ENV=production
LOG_LEVEL=INFO
DATA_DIR=/mnt/user/appdata/marvel-rivals-stats
```

### Configuration Files
- **config/rank_quotas.json**: Player sampling quotas by rank
- **config/heroes.json**: Hero ID to name mappings
- **.env**: Secrets and environment-specific settings
- **docker-compose.yml**: Service orchestration on Odin

---

## Logging

### Strategy
- **Module**: Python `logging` module
- **Format**: `[%(asctime)s] %(levelname)s: %(message)s`
- **Levels**:
  - **DEBUG**: Detailed diagnostic info
  - **INFO**: Progress and status updates
  - **WARNING**: Rate limit warnings, data quality issues
  - **ERROR**: API failures, database errors
- **Output**: Console (stdout) + optional log file

### Example Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/collector.log')
    ]
)
```

---

## Security

### API Key Management
- **Storage**: .env file (never commit)
- **Access**: python-dotenv loads into environment
- **Validation**: Check at startup, fail fast if missing

### Data Privacy
- **Player Data**: Store only username and rank (no personal info)
- **Match Data**: Public competitive matches only
- **Rate Limiting**: Respect API provider's limits

---

## Performance Considerations

### Database Optimization
- **Indexes**:
  - `match_participants(match_id)`
  - `match_participants(hero_name)`
  - `match_participants(username)`
- **Batch Inserts**: Use transactions for bulk operations
- **Query Optimization**: Avoid N+1 queries, use JOINs

### API Rate Limiting
- **Strategy**: Token bucket algorithm
- **Default**: 7 requests/minute (10k/day free tier)
- **Implementation**: Sleep between requests, track usage

### Memory Management
- **Streaming**: Process matches one at a time, don't load all into memory
- **Pagination**: Fetch match history in chunks
- **Cleanup**: Close database connections, clear caches

---

## Version Control

### Git Strategy
- **Branching**: main (production), feature/* (development)
- **Commits**: Conventional Commits format
  - `feat:` New features
  - `fix:` Bug fixes
  - `docs:` Documentation
  - `test:` Tests
  - `refactor:` Code refactoring

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Project
data/rivals.db
data/*.db
output/
.env
*.log

# IDEs
.vscode/
.idea/
*.swp
```

---

## Documentation

### Code Documentation
- **Docstrings**: Google style
  - Module docstrings: Purpose and usage
  - Function docstrings: Args, Returns, Raises
  - Class docstrings: Purpose and attributes

### Project Documentation
- **README.md**: Quick start, usage, structure
- **PLAN.md**: Implementation plan and architecture
- **docs/PRODUCT.md**: Product vision and strategy
- **docs/specs/**: Detailed feature specifications

---

## Web Application Stack (Phase 2+)

### Backend API
- **Framework**: FastAPI 0.104+
  - **Rationale**:
    - Modern async Python framework
    - Auto-generated OpenAPI docs
    - Fast performance (async/await)
    - Type hints + Pydantic validation
  - **ASGI Server**: Uvicorn
  - **Deployment**: Docker container on Odin

### Frontend
- **Framework**: Next.js 14+ (TypeScript)
  - **Rationale**:
    - Server-side rendering (SEO friendly)
    - React 18 with server components
    - Built-in API routes
    - Excellent developer experience
  - **Styling**: Tailwind CSS 3+
  - **Charts**: Recharts or Chart.js
  - **State**: React Context or Zustand (lightweight)

### Containerization
- **Runtime**: Docker 24+
- **Orchestration**: Docker Compose
- **Network**: Caddy Docker network (existing)
- **Volumes**:
  - `/mnt/user/appdata/marvel-rivals-stats` → container data
  - PostgreSQL data volume

### Infrastructure
- **Server**: Odin (Proxmox VM on Ubuntu)
- **Reverse Proxy**: Caddy (existing)
  - Subdomain: `rivals.jinocenc.io`
  - SSL: Auto via Caddy
  - Auth: Discord OAuth (optional)
- **Data Collection**: Systemd timers or cron for Python scripts
- **Backups**: Database dumps to `/mnt/user/media/` (NFS mount)

### Advanced Features (Phase 3+)

#### Caching Layer
- **Redis**: For web API response caching
  - Docker container on Odin
  - TTL: 1 hour for stats endpoints

#### Monitoring
- **Prometheus**: Metrics collection
  - Integrate with existing server monitoring
- **Grafana**: Visualization
  - Dashboard for collection stats, API usage

#### Search
- **PostgreSQL Full-Text Search**: For hero/player search
  - No additional dependencies needed

---

## Dependency Management

### requirements.txt (Production)
```
# Core dependencies
requests>=2.31.0
python-dotenv>=1.0.0
scipy>=1.11.0
psycopg2-binary>=2.9.9

# Web API (Phase 2+)
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# Optional
tqdm>=4.66.0
```

### requirements-dev.txt (Development)
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-asyncio>=0.21.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.5.0
httpx>=0.25.0  # For testing FastAPI
```

---

## Tech Stack Summary

### Phase 1: Data Collection & Analysis (Current)
| Category | Technology | Purpose |
|----------|-----------|---------|
| **Language** | Python 3.10+ | Core application |
| **Database** | PostgreSQL 16+ | Data storage & caching |
| **API Client** | requests | Marvel Rivals API |
| **Statistics** | scipy | Win rate analysis |
| **Testing** | pytest | Test framework |
| **Formatting** | black | Code formatting |
| **Linting** | ruff | Code quality |
| **Type Checking** | mypy | Static analysis |
| **CI/CD** | GitHub Actions | Testing automation |
| **Configuration** | python-dotenv | Environment management |
| **Logging** | logging (stdlib) | Diagnostics |

### Phase 2+: Web Application
| Category | Technology | Purpose |
|----------|-----------|---------|
| **Backend API** | FastAPI + Uvicorn | REST API endpoints |
| **Frontend** | Next.js 14 (TypeScript) | Web interface |
| **Styling** | Tailwind CSS | UI design |
| **Charts** | Recharts | Data visualization |
| **Containerization** | Docker + Compose | Service orchestration |
| **Reverse Proxy** | Caddy | SSL + routing |
| **Hosting** | Odin (self-hosted) | Infrastructure |
| **Caching** | Redis (optional) | API response cache |
| **Monitoring** | Prometheus + Grafana | Observability |

### Infrastructure Summary
- **Server**: Odin (Proxmox VM, Ubuntu, 225GB available)
- **URL**: `rivals.jinocenc.io` (via Caddy)
- **Storage**: `/mnt/user/appdata/marvel-rivals-stats/`
- **Backups**: NFS mount to 10.0.0.26
- **Network**: Caddy Docker network (existing)
- **Auth**: Discord OAuth (optional, via Caddy)

---

**Last Updated**: 2025-10-15
