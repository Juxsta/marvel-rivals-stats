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
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create unique index for character_stats (handles NULL rank_tier)
CREATE UNIQUE INDEX IF NOT EXISTS idx_character_stats_unique
    ON character_stats(hero_name, COALESCE(rank_tier, ''));

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
    CHECK(hero_a < hero_b)  -- Enforce alphabetical order
);

-- Create unique index for synergy_stats (handles NULL rank_tier)
CREATE UNIQUE INDEX IF NOT EXISTS idx_synergy_stats_unique
    ON synergy_stats(hero_a, hero_b, COALESCE(rank_tier, ''));

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
