-- Players table
CREATE TABLE IF NOT EXISTS players (
    username TEXT PRIMARY KEY,
    rank_tier TEXT,
    rank_score INTEGER,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP,
    match_history_fetched BOOLEAN DEFAULT FALSE
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    mode TEXT,
    season INTEGER,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match participants
CREATE TABLE IF NOT EXISTS match_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    username TEXT NOT NULL,
    hero_id INTEGER,
    hero_name TEXT NOT NULL,
    role TEXT,  -- vanguard, duelist, strategist
    team INTEGER NOT NULL,  -- 0 or 1
    won BOOLEAN NOT NULL,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    damage REAL DEFAULT 0,
    healing REAL DEFAULT 0,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (username) REFERENCES players(username),
    UNIQUE(match_id, username)  -- Each player appears once per match
);

-- Character statistics cache
CREATE TABLE IF NOT EXISTS character_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_name TEXT NOT NULL,
    rank_tier TEXT DEFAULT '_all',  -- '_all' = all ranks combined
    total_games INTEGER NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hero_name, rank_tier)
);

-- Synergy statistics cache
CREATE TABLE IF NOT EXISTS synergy_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_a TEXT NOT NULL,
    hero_b TEXT NOT NULL,
    rank_tier TEXT DEFAULT '_all',  -- '_all' = all ranks combined
    games_together INTEGER NOT NULL,
    wins_together INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    expected_win_rate REAL,  -- Based on individual win rates
    synergy_score REAL,  -- Difference from expected
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hero_a, hero_b, rank_tier),
    CHECK(hero_a < hero_b)  -- Enforce alphabetical order to avoid duplicates
);

-- Collection metadata
CREATE TABLE IF NOT EXISTS collection_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_match_participants_match ON match_participants(match_id);
CREATE INDEX IF NOT EXISTS idx_match_participants_hero ON match_participants(hero_name);
CREATE INDEX IF NOT EXISTS idx_match_participants_team_won ON match_participants(team, won);
CREATE INDEX IF NOT EXISTS idx_players_rank ON players(rank_tier);
CREATE INDEX IF NOT EXISTS idx_players_fetched ON players(match_history_fetched);
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season);
