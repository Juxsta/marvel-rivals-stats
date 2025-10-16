# Marvel Rivals Stats Analyzer

[![CI](https://github.com/Juxsta/marvel-rivals-stats/actions/workflows/ci.yml/badge.svg)](https://github.com/Juxsta/marvel-rivals-stats/actions)

Analyzes Marvel Rivals character win rates and team composition synergies using the Marvel Rivals API.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/YOUR_USERNAME/marvel-rivals-stats.git
cd marvel-rivals-stats

# Create environment file
cp .env.example .env
# Edit .env and add your Marvel Rivals API key
nano .env
```

### 2. Start Services

```bash
# Start PostgreSQL and application containers
docker compose up -d

# Check service status
docker compose ps
```

### 3. Initialize Database

```bash
docker compose exec app python scripts/init_db.py
```

### 4. Test API Connection

```bash
docker compose exec app python scripts/test_api.py
```

### 5. Seed Sample Data (Optional)

```bash
docker compose exec app python scripts/seed_sample_data.py
```

## Data Collection Pipeline

The character analysis pipeline consists of 4 sequential steps:

### Step 1: Discover Players

Discover players from leaderboards using stratified sampling across rank tiers.

```bash
# Discover 500 players (default quotas)
docker compose exec app python scripts/discover_players.py

# Discover with custom target
docker compose exec app python scripts/discover_players.py --target-count 100

# Dry run (preview without database changes)
docker compose exec app python scripts/discover_players.py --dry-run
```

**Default Quotas**: Bronze (50), Silver (75), Gold (100), Platinum (100), Diamond (75), Master (50), Grandmaster (25), Celestial (25)

### Step 2: Collect Match Histories

Collect 100-150 matches per discovered player with automatic rate limiting.

```bash
# Collect matches for 100 players (rate limited: ~70 minutes)
docker compose exec app python scripts/collect_matches.py

# Collect with custom batch size
docker compose exec app python scripts/collect_matches.py --batch-size 50

# Dry run (preview without database changes)
docker compose exec app python scripts/collect_matches.py --dry-run
```

**Rate Limiting**: 8.6 seconds between requests (7 req/minute) to respect API limits.
**Resumable**: Can stop (Ctrl+C) and restart - already-collected players are skipped.

### Step 3: Analyze Character Win Rates

Calculate win rates for all heroes with Wilson confidence intervals.

```bash
# Analyze all heroes
docker compose exec app python scripts/analyze_characters.py

# Customize minimum sample sizes
docker compose exec app python scripts/analyze_characters.py --min-games-per-rank 50 --min-games-overall 200

# Database caching only (no JSON export)
docker compose exec app python scripts/analyze_characters.py --no-export
```

**Output**: `output/character_win_rates.json` with win rates stratified by rank tier.
**Filters**: Heroes with <30 games per rank or <100 games overall are excluded.

### Step 4: Analyze Teammate Synergies

Identify hero pairings with positive/negative synergies using statistically rigorous methodology.

```bash
# Analyze all hero pairings (v2.0 methodology)
docker compose exec app python scripts/analyze_synergies.py

# Use stricter significance level
docker compose exec app python scripts/analyze_synergies.py --alpha 0.01

# Require more games together
docker compose exec app python scripts/analyze_synergies.py --min-sample-size 100

# Database caching only (no JSON export)
docker compose exec app python scripts/analyze_synergies.py --no-export
```

**Output**: `output/synergies.json` with top 10 synergies per hero.
**Methodology** (v2.0): Uses average baseline model with confidence intervals, p-values, and Bonferroni correction for multiple comparisons.
**Formula**: `synergy_score = actual_win_rate - expected_win_rate` where `expected_win_rate = (hero_a_wr + hero_b_wr) / 2`

> **Note**: v2.0 methodology (Oct 2025) fixed a fundamental flaw in the baseline model. Previous versions used a multiplicative baseline that inflated synergy scores to ±25-30%. The new average baseline produces realistic ±3-7% synergies with proper statistical testing. See [STATISTICS.md](docs/STATISTICS.md) for details.

## Common Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after dependency changes
docker compose build

# Run tests
docker compose exec app pytest tests/ -v

# Access PostgreSQL directly
docker compose exec postgres psql -U marvel_stats -d marvel_rivals

# Run any Python script
docker compose exec app python scripts/your_script.py
```

## Project Structure

```
marvel-rivals-stats/
├── src/
│   ├── api/              # Marvel Rivals API client
│   ├── db/               # Database connection and schema
│   ├── collectors/       # Data collection logic
│   ├── analyzers/        # Statistical analysis
│   └── utils/            # Helper functions
├── scripts/              # Executable scripts
│   ├── init_db.py           # Initialize database
│   ├── test_api.py          # Test API connection
│   ├── seed_sample_data.py  # Seed test data
│   ├── discover_players.py  # Player discovery (stratified sampling)
│   ├── collect_matches.py   # Match history collection
│   ├── analyze_characters.py # Character win rate analysis
│   └── analyze_synergies.py  # Teammate synergy analysis
├── data/                 # PostgreSQL data (Docker volume)
├── output/               # Analysis results (JSON)
├── config/               # Configuration files
├── PLAN.md              # Detailed implementation plan
└── README.md            # This file
```

## Documentation

- [Development Workflow](docs/development.md) - Daily development commands and practices
- [Statistical Methodology](docs/STATISTICS.md) - Win rate confidence intervals and synergy analysis methodology
- [Deployment Guide](docs/deployment.md) - Deploying to Odin server
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Synergy Analysis Migration Guide](docs/MIGRATION_SYNERGY_V2.md) - Understanding the v2.0 methodology change
- [Product Documentation](docs/PRODUCT.md) - Product requirements and specifications

## Environment Variables

The following environment variables are required. Copy `.env.example` to `.env` and configure:

```bash
# Marvel Rivals API
MARVEL_RIVALS_API_KEY=your_api_key_here
RATE_LIMIT_REQUESTS_PER_MINUTE=7
CURRENT_SEASON=9

# Database
DATABASE_PASSWORD=secure_password_here
DATABASE_NAME=marvel_rivals
DATABASE_USER=marvel_stats

# Application
APP_ENV=development
LOG_LEVEL=INFO

# Storage (local dev uses ./data, production uses /mnt/user/appdata/marvel-rivals-stats)
DATA_DIR=./data
```

## Database Schema

- **players**: All discovered players with rank info
- **matches**: Unique matches (deduplicated)
- **match_participants**: Who played what hero in each match
- **character_stats**: Cached character win rate analysis
- **synergy_stats**: Cached team synergy analysis

See `migrations/` for complete schema with indexes.

## Roadmap

See `PLAN.md` for detailed implementation plan.

### Phase 1: MVP (✅ Complete)
- [x] Project scaffolding and Docker setup
- [x] Database schema with migrations
- [x] API client with rate limiting
- [x] Player discovery with stratified sampling
- [x] Match history collection (resumable)
- [x] Character win rate analysis (Wilson CIs)
- [x] Teammate synergy analysis
- [x] JSON export functionality

### Phase 2: Full Collection (Next)
- [ ] Collect 500 players across all ranks
- [ ] Generate complete character analysis
- [ ] Export comprehensive datasets
- [ ] Web API (FastAPI)

### Phase 3: Web Frontend
- [ ] Next.js dashboard
- [ ] Hero statistics visualization
- [ ] Synergy matrix display
- [ ] Rank tier filtering

## Testing

### Running Tests Locally

```bash
# Run all tests
docker compose exec app pytest tests/ -v

# Run unit tests only (faster)
docker compose exec app pytest tests/ -v --ignore=tests/test_integration/

# Run integration tests only
docker compose exec app pytest tests/test_integration/ -v

# Run with coverage
docker compose exec app pytest tests/ -v --cov=src
```

### Requirements for Integration Tests

Integration tests require:
- PostgreSQL database running (via `docker compose up`)
- Database migrations applied (`scripts/init_db.py`)
- `DATABASE_URL` environment variable set

### Continuous Integration

All pull requests must pass CI checks before merging:
- **Linting**: black, ruff, mypy
- **Unit Tests**: Business logic validation
- **Integration Tests**: End-to-end workflows with PostgreSQL

View CI history: [GitHub Actions](https://github.com/Juxsta/marvel-rivals-stats/actions)

## Contributing

### Before Submitting a Pull Request

1. **Run tests locally** to ensure they pass:
   ```bash
   docker compose exec app pytest tests/ -v
   ```

2. **Format your code** with black:
   ```bash
   docker compose exec app black src/ scripts/ tests/
   ```

3. **Lint your code** with ruff:
   ```bash
   docker compose exec app ruff check src/ scripts/ tests/ --fix
   ```

4. **Check types** with mypy:
   ```bash
   docker compose exec app mypy src/ scripts/
   ```

### CI Checks

All pull requests automatically run:
- Code formatting checks (black)
- Linting checks (ruff, mypy)
- Unit tests (~42 tests)
- Integration tests (~17 tests) with PostgreSQL

Pull requests cannot be merged until all CI checks pass.

For more details, see [Development Workflow](docs/development.md).

## Code Quality

```bash
# Format code
docker compose exec app black src/ scripts/ tests/

# Lint code
docker compose exec app ruff check src/ scripts/ tests/

# Type checking
docker compose exec app mypy src/ scripts/
```

## API Rate Limits

- Free tier: 10,000 requests/day
- Scripts automatically respect rate limits
- Default: 7 requests/minute (configurable in .env)

## License

MIT
