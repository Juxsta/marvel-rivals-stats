# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-15

### Changed - BREAKING

**Synergy Analysis Methodology Fixed**

This version fixes a fundamental mathematical error in the synergy baseline calculation that affected all previous synergy analysis results.

- **Replaced multiplicative baseline with average baseline**
  - Old (flawed): `expected_wr = hero_a_wr × hero_b_wr`
  - New (correct): `expected_wr = (hero_a_wr + hero_b_wr) / 2`

- **Impact**: Synergy scores are now realistic (±3-7%) instead of artificially inflated (±25-30%)

- **Why the change**: The multiplicative baseline calculated the probability that two independent events both occur, which is only valid for separate games. Since teammates are on the same team in the same game, the average baseline correctly reflects their combined performance.

- **Example**: Hulk (52%) + Luna Snow (55%)
  - Old expected: 28.6% (unrealistic)
  - New expected: 53.5% (realistic)
  - Old synergy: +31.3% (inflated)
  - New synergy: +6.4% (realistic)

### Added

**Statistical Rigor Enhancements**

- **Confidence intervals**: 95% Wilson score intervals for actual win rates
- **Statistical significance testing**: Binomial tests with p-values for each synergy
- **Bonferroni correction**: Controls false positives when testing multiple hero pairs
- **Sample size warnings**: Flags results with insufficient data
  - High confidence: ≥500 games together
  - Medium confidence: 100-499 games
  - Low confidence: <100 games (excluded by default)
- **Power analysis**: Calculates required sample sizes to detect 3%, 5%, and 10% synergies
- **New CLI flags**:
  - `--baseline [average|additive]`: Choose baseline model (default: average)
  - `--alpha FLOAT`: Significance level (default: 0.05)
  - `--min-sample-size INT`: Minimum games to report (default: 50)

**New Statistical Functions** (`src/utils/statistics.py`)

- `expected_wr_average()`: Average baseline model
- `binomial_test_synergy()`: Statistical significance testing
- `bonferroni_correction()`: Multiple comparisons correction
- `power_analysis_sample_size()`: Required sample size calculation
- `confidence_level_label()`: Sample size classification

**Database Schema Updates**

- Added 5 new columns to `synergy_stats` table:
  - `confidence_lower` (REAL): Lower bound of 95% CI
  - `confidence_upper` (REAL): Upper bound of 95% CI
  - `p_value` (REAL): Statistical significance
  - `sample_size_warning` (TEXT): Insufficient data warning
  - `baseline_model` (TEXT): Methodology version tracking

**JSON Export Enhancements**

- New root-level metadata fields:
  - `methodology_version: "2.0"`
  - `baseline_model: "average"`
  - `analysis_date`: ISO 8601 timestamp
- New per-synergy fields:
  - `p_value`, `significant`, `significant_bonferroni`, `bonferroni_alpha`
  - `confidence_level` ("high", "medium", "low")
  - `warning` (sample size warning message)
- New per-hero section:
  - `power_analysis` with required sample sizes for 3%, 5%, 10% effects

### Documentation

- **[MIGRATION_SYNERGY_V2.md](docs/MIGRATION_SYNERGY_V2.md)**: Comprehensive migration guide
  - Before/after comparison tables
  - Visual examples of methodology impact
  - FAQ addressing common questions
  - Technical details and formulas

- **[STATISTICS.md](docs/STATISTICS.md)**: Updated statistical methodology
  - Detailed explanation of average baseline model
  - Why multiplicative baseline was flawed
  - Sample size requirements and power analysis
  - Confidence level interpretation

- **[troubleshooting.md](docs/troubleshooting.md)**: Added 3 new synergy troubleshooting entries
  - Why synergy scores decreased after updating
  - What insufficient sample size warnings mean
  - Why no synergies are statistically significant

- **[README.md](README.md)**: Updated synergy analysis section with v2.0 methodology note

### Migration Guide

**Action Required**: None - analysis automatically uses new methodology.

**What Changed**: All previous synergy results were mathematically incorrect and have been replaced with statistically defensible values.

**Rankings**: Relative ordering of hero pairs is similar, but effect magnitudes are now realistic.

**Interpretation**:
- Old results showed ±25-30% synergies (inflated due to flawed baseline)
- New results show ±3-7% synergies (realistic for team-based games)
- Most synergies are not statistically significant with current sample sizes (100-300 games)
- Detecting realistic 3-5% synergies requires 600-1,700 games per pair

See [MIGRATION_SYNERGY_V2.md](docs/MIGRATION_SYNERGY_V2.md) for complete migration guide.

### Deprecated

- Multiplicative baseline model removed (fundamentally flawed)
- Old v1.0 synergy results should be discarded

---

## [1.0.0] - 2025-10-14

### Added

**Initial Release**

- Docker Compose setup with PostgreSQL 16 and Python 3.10
- Marvel Rivals API client with rate limiting (7 req/minute)
- Player discovery with stratified sampling across 8 rank tiers
- Match history collection (resumable, rate-limited)
- Character win rate analysis with Wilson confidence intervals
- Teammate synergy analysis (v1.0 - later found to be flawed)
- JSON export functionality
- Database schema with 7 tables and indexes
- Comprehensive test suite (pytest)
- Documentation: README, STATISTICS, development workflow

**Scripts**

- `init_db.py`: Initialize database schema
- `test_api.py`: Test API connection
- `seed_sample_data.py`: Seed test data
- `discover_players.py`: Player discovery pipeline
- `collect_matches.py`: Match history collection
- `analyze_characters.py`: Character win rate analysis
- `analyze_synergies.py`: Teammate synergy analysis

**Core Features**

- Wilson score confidence intervals for win rates
- Stratified sampling by rank tier
- Match deduplication by match_id
- Rank-stratified win rate analysis
- Minimum sample size requirements (30/100/50 games)
- PostgreSQL caching for fast retrieval
- JSON export with confidence intervals

[2.0.0]: https://github.com/YOUR_USERNAME/marvel-rivals-stats/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/YOUR_USERNAME/marvel-rivals-stats/releases/tag/v1.0.0
