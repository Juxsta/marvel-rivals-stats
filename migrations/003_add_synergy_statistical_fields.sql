-- Add Statistical Fields to Synergy Stats
-- Version: 2.0.0
-- Created: 2025-10-15
-- Purpose: Add confidence intervals, p-values, and metadata for improved synergy analysis

-- Add new columns for statistical significance and confidence intervals
ALTER TABLE synergy_stats
    ADD COLUMN IF NOT EXISTS confidence_lower REAL,
    ADD COLUMN IF NOT EXISTS confidence_upper REAL,
    ADD COLUMN IF NOT EXISTS p_value REAL,
    ADD COLUMN IF NOT EXISTS sample_size_warning TEXT,
    ADD COLUMN IF NOT EXISTS baseline_model TEXT DEFAULT 'average';

-- Create index for filtering by statistical significance
-- Partial index only includes rows where p_value is not null
CREATE INDEX IF NOT EXISTS idx_synergy_significance
    ON synergy_stats(p_value)
    WHERE p_value IS NOT NULL;

-- Update schema version
INSERT INTO schema_migrations (version, description)
VALUES (3, 'Add statistical fields (confidence intervals, p-values) to synergy_stats')
ON CONFLICT (version) DO NOTHING;

UPDATE collection_metadata
SET value = '3', updated_at = CURRENT_TIMESTAMP
WHERE key = 'schema_version';
