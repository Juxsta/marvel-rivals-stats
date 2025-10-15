# Marvel Rivals Stats - Implementation Plan

## Architecture Overview

**Language**: Python 3.10+
**Storage**: SQLite (local caching) + JSON (results export)
**Interface**: CLI scripts (no web UI)
**API**: marvelrivalsapi.com

## Core Principles

1. **Idempotent**: Scripts can be run multiple times safely
2. **Resumable**: Track progress, continue after failures
3. **Cached**: Never re-fetch data we already have
4. **Modular**: Separate scripts for discovery, collection, analysis

---

## Database Schema

### Tables

```sql
-- Track all discovered players
CREATE TABLE players (
    username TEXT PRIMARY KEY,
    rank_tier TEXT,
    rank_score INTEGER,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    match_history_fetched BOOLEAN DEFAULT FALSE
);

-- Store unique matches (deduplicated)
CREATE TABLE matches (
    match_id TEXT PRIMARY KEY,
    mode TEXT,
    season INTEGER,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track who played what in each match
CREATE TABLE match_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT,
    username TEXT,
    hero_id INTEGER,
    hero_name TEXT,
    role TEXT,  -- vanguard, duelist, strategist
    team INTEGER,  -- 0 or 1
    won BOOLEAN,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    damage REAL,
    healing REAL,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (username) REFERENCES players(username),
    UNIQUE(match_id, username)  -- Each player appears once per match
);

-- Cache analysis results
CREATE TABLE character_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_name TEXT,
    rank_tier TEXT,  -- NULL = all ranks
    total_games INTEGER,
    wins INTEGER,
    losses INTEGER,
    win_rate REAL,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hero_name, rank_tier)
);

-- Track character synergies
CREATE TABLE synergy_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_a TEXT,
    hero_b TEXT,
    rank_tier TEXT,  -- NULL = all ranks
    games_together INTEGER,
    wins_together INTEGER,
    win_rate REAL,
    expected_win_rate REAL,  -- Based on individual win rates
    synergy_score REAL,  -- Difference from expected
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hero_a, hero_b, rank_tier),
    CHECK(hero_a < hero_b)  -- Enforce alphabetical order to avoid duplicates
);

-- Track collection progress
CREATE TABLE collection_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Scripts Architecture

### 1. `scripts/discover_players.py`
**Purpose**: Find players to sample

**Process**:
```python
1. Query player leaderboard API
2. Query hero leaderboards (for diversity)
3. Insert discovered players into DB
4. Apply stratified sampling based on rank quotas
5. Mark players as "to be collected"
```

**Output**: Populated `players` table with target sample

**CLI**:
```bash
python scripts/discover_players.py --target 500 --quota config/rank_quotas.json
```

---

### 2. `scripts/collect_matches.py`
**Purpose**: Fetch match histories for all discovered players

**Process**:
```python
1. Load players where match_history_fetched = FALSE
2. For each player:
   a. Check API rate limit
   b. Fetch match history (paginated)
   c. For each match:
      - Check if match_id exists (deduplicate)
      - Insert match into matches table
      - Insert all participants into match_participants
   d. Mark player as fetched
   e. Sleep to respect rate limits
3. Handle errors (network, API limits) gracefully
4. Save progress checkpoint every N players
```

**Features**:
- Rate limiting (10k requests/day = ~416/hour = ~7/min)
- Progress tracking
- Resume capability
- Deduplication

**CLI**:
```bash
python scripts/collect_matches.py --limit 100 --delay 1000
# --limit: Max players to process this run
# --delay: MS between requests
```

---

### 3. `scripts/analyze_character.py`
**Purpose**: Calculate character win rates

**Process**:
```python
1. Query match_participants for target character
2. Group by rank_tier
3. Calculate:
   - Total games
   - Wins/losses
   - Win rate
   - Confidence intervals
   - Percentile rankings
4. Store in character_stats table
5. Export to JSON for reporting
```

**CLI**:
```bash
python scripts/analyze_character.py --hero "Spider-Man"
python scripts/analyze_character.py --hero "all"  # Analyze all characters
```

**Output**:
```json
{
  "hero": "Spider-Man",
  "overall": {
    "games": 1247,
    "wins": 689,
    "win_rate": 0.552,
    "confidence_95": [0.524, 0.580]
  },
  "by_rank": {
    "Bronze": { "games": 89, "wins": 45, "win_rate": 0.506 },
    "Silver": { "games": 156, "wins": 82, "win_rate": 0.526 },
    ...
  }
}
```

---

### 4. `scripts/analyze_synergy.py`
**Purpose**: Find character synergies (which heroes win more together)

**Process**:
```python
1. For each match, get all hero pairs on same team
2. Track: (hero_a, hero_b) -> games together, wins together
3. Calculate expected win rate:
   expected = (hero_a_win_rate + hero_b_win_rate) / 2
4. Calculate synergy score:
   synergy = actual_win_rate - expected_win_rate
5. Filter for statistical significance (min 30 games)
6. Store top synergies in synergy_stats
```

**CLI**:
```bash
python scripts/analyze_synergy.py --hero "Spider-Man"
python scripts/analyze_synergy.py --min-games 50
```

**Output**:
```json
{
  "hero": "Spider-Man",
  "best_synergies": [
    {
      "teammate": "Luna Snow",
      "games": 87,
      "win_rate": 0.678,
      "expected": 0.542,
      "synergy": +0.136,
      "significance": "p < 0.01"
    },
    ...
  ],
  "worst_synergies": [...]
}
```

---

### 5. `scripts/reset_db.py`
**Purpose**: Clear database for fresh start

**CLI**:
```bash
python scripts/reset_db.py --confirm
```

---

## Project Structure

```
marvel-rivals-stats/
├── src/
│   ├── api/
│   │   ├── client.py           # Marvel Rivals API wrapper
│   │   └── rate_limiter.py     # Rate limiting logic
│   ├── db/
│   │   ├── schema.sql          # Database schema
│   │   ├── connection.py       # DB connection manager
│   │   └── models.py           # ORM or query helpers
│   ├── collectors/
│   │   ├── player_discovery.py # Player discovery logic
│   │   └── match_collector.py  # Match fetching logic
│   ├── analyzers/
│   │   ├── character_winrate.py
│   │   └── team_synergy.py
│   └── utils/
│       ├── sampling.py         # Stratified sampling helpers
│       └── stats.py            # Statistical calculations
├── scripts/
│   ├── discover_players.py
│   ├── collect_matches.py
│   ├── analyze_character.py
│   ├── analyze_synergy.py
│   └── reset_db.py
├── config/
│   ├── rank_quotas.json
│   └── heroes.json             # Hero ID -> Name mapping
├── data/
│   └── rivals.db               # SQLite database
├── output/
│   ├── character_stats/
│   └── synergy_stats/
├── requirements.txt
├── .env.example
├── PLAN.md                     # This file
└── README.md
```

---

## Data Collection Strategy

### Phase 1: Player Discovery
**Goal**: Get 500 diverse players

**Method**:
1. Fetch player leaderboard (top 1000)
2. Fetch hero leaderboards (50 per hero, top 10 heroes)
3. Deduplicate
4. Stratify by rank tier
5. Random sample to meet quotas

**Expected result**: ~500 players with known ranks

### Phase 2: Match Collection
**Goal**: Get match histories for all players

**Method**:
1. Fetch 100-150 recent matches per player
2. Deduplicate by match_id
3. Extract all participants

**Expected result**: 50k-75k unique matches, ~600k player-match records

### Phase 3: Snowball (Optional)
**Goal**: Expand sample size

**Method**:
1. Extract all unique players from collected matches
2. Add to discovery pool
3. Fetch their match histories

**Expected result**: 2000+ players, 200k+ matches

---

## Statistical Approach

### Character Win Rate
- **Metric**: Win rate = Wins / Total Games
- **Confidence Interval**: Wilson score interval (95%)
- **Minimum Sample**: 30 games per rank tier
- **Filters**: Current season only, competitive mode

### Synergy Score
- **Metric**: Actual Win Rate - Expected Win Rate
- **Expected WR**: `(hero_a_wr + hero_b_wr) / 2`
- **Significance**: Chi-squared test (p < 0.05)
- **Minimum Sample**: 30 games together

### Rank Stratification
- Calculate stats separately for each rank
- Aggregate for overall stats
- Weight by sample size when needed

---

## Implementation Phases

### MVP (Week 1)
- [ ] Database schema and setup
- [ ] API client with rate limiting
- [ ] Player discovery script (leaderboard only)
- [ ] Match collection script
- [ ] Basic character win rate analysis
- [ ] Test with 50 players, 1 character

### Phase 2 (Week 2)
- [ ] Full 500 player collection
- [ ] All character analysis
- [ ] Rank-stratified statistics
- [ ] JSON export for results

### Phase 3 (Week 3)
- [ ] Team synergy analysis
- [ ] Pair-wise synergies
- [ ] Role-based analysis (best tank for each support, etc.)
- [ ] Statistical significance testing

### Future Enhancements
- [ ] Time-series tracking (meta changes over time)
- [ ] Counter-pick analysis (which heroes win against others)
- [ ] Team composition templates (2-2-2 variants)
- [ ] Web dashboard for visualization

---

## Risk Mitigation

**API Rate Limits**:
- Solution: Respect limits, implement backoff, cache aggressively

**API Changes**:
- Solution: Version client, handle errors gracefully, fallback to cached data

**Data Staleness**:
- Solution: Track last_updated, re-fetch periodically

**Sample Bias**:
- Solution: Stratified sampling, validate distributions

**Statistical Significance**:
- Solution: Require minimum samples, calculate confidence intervals

---

## Success Criteria

**MVP Success**:
- Collect 50 players successfully
- Calculate accurate win rate for 1 character
- Match win rates roughly align with community knowledge

**Phase 2 Success**:
- 500 players across all ranks
- Win rates for all 40+ characters
- Results exportable to JSON

**Phase 3 Success**:
- Identify top 10 synergies per character
- Statistical significance p < 0.05
- Results match or reveal new insights vs community wisdom
