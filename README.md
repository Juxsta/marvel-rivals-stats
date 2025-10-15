# Marvel Rivals Stats Analyzer

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
│   ├── discover_players.py  # (Coming) Player discovery
│   ├── collect_matches.py   # (Coming) Match collection
│   ├── analyze_character.py # (Coming) Character win rates
│   └── analyze_synergy.py   # (Coming) Team synergies
├── data/                 # PostgreSQL data (Docker volume)
├── output/               # Analysis results (JSON)
├── config/               # Configuration files
├── PLAN.md              # Detailed implementation plan
└── README.md            # This file
```

## Documentation

- [Development Workflow](docs/development.md) - Daily development commands and practices
- [Deployment Guide](docs/deployment.md) - Deploying to Odin server
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
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

### Phase 1: MVP (Current)
- [x] Project scaffolding
- [x] Database schema
- [x] API client with rate limiting
- [x] Test scripts
- [ ] Player discovery script
- [ ] Match collection script
- [ ] Basic character win rate analysis

### Phase 2: Full Collection
- [ ] Collect 500 players across all ranks
- [ ] All character analysis
- [ ] Rank-stratified statistics
- [ ] JSON export

### Phase 3: Team Synergies
- [ ] Pair-wise synergy analysis
- [ ] Role-based analysis
- [ ] Statistical significance testing

## Testing

```bash
# Run all tests
docker compose exec app pytest tests/ -v

# Run with coverage
docker compose exec app pytest tests/ -v --cov=src

# Run specific test file
docker compose exec app pytest tests/test_db/test_connection.py -v
```

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
