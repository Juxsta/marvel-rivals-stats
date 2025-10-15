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
