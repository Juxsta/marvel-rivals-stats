-- Rollback: Remove Statistical Fields from Synergy Stats
-- Version: 2.0.0
-- Created: 2025-10-15
-- Purpose: Rollback migration 003 if needed

-- Drop the significance index
DROP INDEX IF EXISTS idx_synergy_significance;

-- Remove the new columns
ALTER TABLE synergy_stats
    DROP COLUMN IF EXISTS confidence_lower,
    DROP COLUMN IF EXISTS confidence_upper,
    DROP COLUMN IF EXISTS p_value,
    DROP COLUMN IF EXISTS sample_size_warning,
    DROP COLUMN IF EXISTS baseline_model;

-- Revert schema version
DELETE FROM schema_migrations WHERE version = 3;

UPDATE collection_metadata
SET value = '2', updated_at = CURRENT_TIMESTAMP
WHERE key = 'schema_version';
