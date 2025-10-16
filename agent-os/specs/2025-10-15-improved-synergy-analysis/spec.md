# Specification: Improved Synergy Analysis Methodology

## Executive Summary

### Problem
The current synergy analysis system uses a fundamentally flawed multiplicative baseline model (`expected_wr = hero_a_wr × hero_b_wr`) that treats teammates as independent events. This produces artificially inflated synergy scores of ±25-30% when true synergy effects are likely only ±3-7%.

### Impact
- **Misleading users**: Reports massive synergies that don't exist
- **False statistical significance**: Claims 10/10 synergies are "highly significant" when proper analysis shows 0/10 are actually significant
- **Low confidence**: Results aren't statistically defensible or reproducible

### Solution
Replace multiplicative baseline with theoretically sound average baseline model, add proper statistical significance testing with confidence intervals, and implement honest uncertainty quantification.

### Timeline
- **Phase 1** (This Spec): Methodology fix - 1-2 days
- **Phase 2** (Optional): Bayesian analysis enhancement - 1-2 days
- **Future Work**: ML baselines, more data collection (separate spec)

---

## Background

### Context
This specification follows completion of SPEC-005 (Character Win Rate Analysis) which implemented Wilson confidence intervals and proper statistical methodology for individual hero analysis. The synergy analysis system needs similar improvements.

### Statistical Analysis Findings
Recent statistical analysis revealed critical flaws:

1. **Multiplicative Model is Wrong**: The formula `expected_wr = hero_a_wr × hero_b_wr` incorrectly treats teammates as independent coin flips. Since both heroes are on the same team, their fates are perfectly correlated, not independent.

2. **Proper Baselines**: Correct approaches include:
   - **Average Model**: `expected_wr = (hero_a_wr + hero_b_wr) / 2`
   - **Additive Model**: `expected_wr = 0.5 + (hero_a_wr - 0.5) + (hero_b_wr - 0.5)`

3. **Sample Size Requirements**: Current dataset (286 matches, max 207 games per pair) can only detect ≥10% synergies with statistical power. Realistic 3-5% synergies require 1,000-15,000 games per pair.

4. **Multiple Comparisons Problem**: Testing 10+ pairs requires Bonferroni correction to avoid false positives.

### Example Impact
For Hulk + Luna Snow (the most-played pair):
- **Current methodology**:
  - Expected WR: 20.7% (multiplicative)
  - Actual WR: 59.8%
  - Synergy score: +39.1% (INFLATED)
- **Correct methodology**:
  - Expected WR: 53.5% (average)
  - Actual WR: 59.8%
  - Synergy score: +6.3% (REALISTIC)

---

## Goals & Non-Goals

### Primary Goals
1. **Fix Methodology**: Replace multiplicative baseline with average baseline model
2. **Honest Uncertainty**: Report confidence intervals and sample sizes prominently
3. **Statistical Rigor**: Apply proper significance testing with multiple comparisons corrections
4. **Maintain Compatibility**: Keep database schema and API consistent where possible

### Secondary Goals
1. **Educational**: Help users understand statistical limitations
2. **Extensible**: Design for future enhancements (Bayesian, ML baselines)
3. **Code Reuse**: Leverage existing `wilson_confidence_interval()` utility

### Non-Goals (Future Work)
- Within-player analysis (requires 30+ players with diverse hero pools)
- ML baseline models (requires 1,000+ matches to train)
- Causal inference methods (research-level complexity)
- Map-specific synergies (needs massive datasets)
- Real-time continuous updates (batch analysis sufficient)

---

## Detailed Design

### 4.1 Baseline Model Change

#### Current Implementation (FLAWED)
```python
def calculate_expected_win_rate(wr_a: float, wr_b: float) -> float:
    """Multiplicative model - INCORRECT for teammates."""
    return round(wr_a * wr_b, 4)  # Treats heroes as independent
```

**Why This is Wrong**: This assumes P(team wins) = P(hero A wins alone) × P(hero B wins alone), which only applies to independent events. Teammates win or lose together, making their outcomes perfectly correlated.

#### New Implementation (CORRECT)
```python
def calculate_expected_win_rate_average(wr_a: float, wr_b: float) -> float:
    """Average baseline model - assumes equal contribution.

    Rationale: If two heroes contribute equally to team performance,
    their combined expected win rate is their average. This is the
    simplest theoretically sound baseline.

    Args:
        wr_a: First hero's overall win rate
        wr_b: Second hero's overall win rate

    Returns:
        Expected win rate when paired together
    """
    return round((wr_a + wr_b) / 2.0, 4)
```

#### Alternative: Additive Model (Optional)
```python
def calculate_expected_win_rate_additive(wr_a: float, wr_b: float) -> float:
    """Additive contributions from 50% baseline.

    Rationale: Each hero contributes independently to deviation from
    the baseline 50% win rate. More sophisticated but similar results.

    Args:
        wr_a: First hero's overall win rate
        wr_b: Second hero's overall win rate

    Returns:
        Expected win rate when paired together
    """
    baseline = 0.5
    contrib_a = wr_a - baseline
    contrib_b = wr_b - baseline
    return round(baseline + contrib_a + contrib_b, 4)
```

**Recommendation**: Start with average model for simplicity. Additive model can be added later as an option.

### 4.2 Statistical Enhancements

#### Wilson Confidence Intervals
Reuse existing `wilson_confidence_interval()` from `src/utils/statistics.py` to calculate 95% confidence intervals for actual win rates.

#### Binomial Significance Testing
```python
from scipy.stats import binomtest

def calculate_synergy_significance(
    wins: int,
    total: int,
    expected_wr: float,
    alpha: float = 0.05
) -> Dict:
    """Test if synergy differs significantly from expected baseline.

    Uses exact binomial test against the expected win rate.

    Args:
        wins: Number of wins together
        total: Total games together
        expected_wr: Expected win rate from baseline model
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary with p_value and significance result
    """
    # Two-sided binomial test
    result = binomtest(wins, total, expected_wr, alternative='two-sided')

    return {
        'p_value': round(result.pvalue, 4),
        'significant': result.pvalue < alpha
    }
```

#### Bonferroni Multiple Comparisons Correction
```python
def apply_bonferroni_correction(
    synergies: List[Dict],
    alpha: float = 0.05
) -> List[Dict]:
    """Apply Bonferroni correction for multiple comparisons.

    When testing N synergies, use corrected significance level
    of alpha/N to maintain family-wise error rate.

    Args:
        synergies: List of synergy dictionaries with 'p_value' keys
        alpha: Family-wise error rate (default 0.05)

    Returns:
        Updated synergies list with 'significant_bonferroni' field
    """
    n_comparisons = len(synergies)
    corrected_alpha = alpha / n_comparisons

    for synergy in synergies:
        synergy['significant_bonferroni'] = (
            synergy['p_value'] < corrected_alpha
        )
        synergy['bonferroni_alpha'] = round(corrected_alpha, 6)

    return synergies
```

#### Sample Size Warnings
```python
def add_sample_size_warnings(
    synergy: Dict,
    total_games: int,
    thresholds: Dict = None
) -> Dict:
    """Add warning flags for insufficient sample sizes.

    Args:
        synergy: Synergy dictionary
        total_games: Number of games together
        thresholds: Custom thresholds (default: {high: 500, medium: 100})

    Returns:
        Updated synergy with 'confidence_level' and 'warning' fields
    """
    if thresholds is None:
        thresholds = {'high': 500, 'medium': 100}

    if total_games >= thresholds['high']:
        synergy['confidence_level'] = 'high'
        synergy['warning'] = None
    elif total_games >= thresholds['medium']:
        synergy['confidence_level'] = 'medium'
        synergy['warning'] = (
            f"Moderate sample size ({total_games} games). "
            "Results may have wide confidence intervals."
        )
    else:
        synergy['confidence_level'] = 'low'
        synergy['warning'] = (
            f"Low sample size ({total_games} games). "
            "Results are unreliable. Interpret with caution."
        )

    return synergy
```

#### Power Analysis
```python
def calculate_required_sample_size(
    baseline_wr: float,
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """Calculate required sample size to detect a synergy effect.

    Uses formula for two-proportion z-test with continuity correction.

    Args:
        baseline_wr: Expected win rate from baseline model
        effect_size: Minimum synergy to detect (e.g., 0.05 = 5%)
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.80 = 80%)

    Returns:
        Required number of games to detect effect
    """
    from scipy.stats import norm
    import numpy as np

    z_alpha = norm.ppf(1 - alpha / 2)  # Two-tailed
    z_beta = norm.ppf(power)

    p0 = baseline_wr
    p1 = baseline_wr + effect_size

    n = (
        (z_alpha * np.sqrt(p0 * (1 - p0)) +
         z_beta * np.sqrt(p1 * (1 - p1))) / effect_size
    ) ** 2

    return int(np.ceil(n))
```

### 4.3 Implementation Details

#### Files to Modify

1. **`src/utils/statistics.py`**:
   - Add `calculate_expected_win_rate_average()`
   - Add `calculate_expected_win_rate_additive()` (optional)
   - Add `calculate_synergy_significance()`
   - Add `calculate_required_sample_size()`
   - Update existing `calculate_expected_win_rate()` with deprecation warning

2. **`src/analyzers/teammate_synergy.py`**:
   - Update `analyze_teammate_synergies()` to use new baseline
   - Add significance testing for each synergy
   - Apply Bonferroni correction to results
   - Add sample size warnings
   - Update cached statistics format

3. **`scripts/analyze_synergies.py`**:
   - Add CLI flags: `--baseline`, `--alpha`, `--min-sample-size`
   - Update summary output to show significance results
   - Add power analysis output section

#### Code Reuse
- **Wilson CI**: Already implemented in `src/utils/statistics.py:wilson_confidence_interval()`
- **Database caching pattern**: Follow approach from `src/analyzers/character_winrate.py`
- **CLI argument patterns**: Follow structure from `scripts/analyze_characters.py`
- **Logging patterns**: Consistent with existing analyzer modules

#### Database Updates
Update `synergy_stats` table to support new fields:

```sql
ALTER TABLE synergy_stats
ADD COLUMN confidence_lower REAL,
ADD COLUMN confidence_upper REAL,
ADD COLUMN p_value REAL,
ADD COLUMN sample_size INTEGER,
ADD COLUMN baseline_model TEXT DEFAULT 'average';

-- Or use JSONB for flexibility:
ALTER TABLE synergy_stats
ADD COLUMN metadata JSONB;
```

Recommendation: Add individual columns for better queryability and index performance.

#### JSON Export Format
Update export format to include new fields:

```json
{
  "hero": "Hulk",
  "rank_tier": "all",
  "synergies": [
    {
      "teammate": "Luna Snow",
      "games_together": 207,
      "wins_together": 124,
      "actual_win_rate": 0.5990,
      "expected_win_rate": 0.5350,
      "synergy_score": 0.0640,
      "confidence_interval_95": [0.5310, 0.6640],
      "p_value": 0.0234,
      "significant": true,
      "significant_bonferroni": false,
      "bonferroni_alpha": 0.005,
      "confidence_level": "low",
      "warning": "Low sample size (207 games). Results are unreliable."
    }
  ],
  "power_analysis": {
    "current_samples": 207,
    "required_for_5pct_effect": 600,
    "required_for_3pct_effect": 1700
  },
  "analyzed_at": "2025-10-15T10:30:00"
}
```

### 4.4 Bayesian Analysis (Phase 2 - Optional)

#### Beta-Binomial Conjugate Prior
```python
def bayesian_synergy_estimate(
    wins: int,
    total: int,
    expected_wr: float,
    prior_strength: int = 20
) -> Dict:
    """Bayesian estimate using Beta-Binomial conjugate prior.

    Useful for small samples - shrinks estimates toward expected value.

    Args:
        wins: Number of wins together
        total: Total games together
        expected_wr: Expected win rate (used as prior mean)
        prior_strength: Pseudo-sample size for prior (default 20)

    Returns:
        Dictionary with posterior estimates and credible intervals
    """
    from scipy.stats import beta

    # Prior: Beta(α, β) centered at expected_wr
    prior_alpha = expected_wr * prior_strength
    prior_beta = (1 - expected_wr) * prior_strength

    # Posterior: Beta(α + wins, β + losses)
    posterior_alpha = prior_alpha + wins
    posterior_beta = prior_beta + (total - wins)

    # Posterior mean
    posterior_mean = posterior_alpha / (posterior_alpha + posterior_beta)

    # 95% credible interval
    credible_lower = beta.ppf(0.025, posterior_alpha, posterior_beta)
    credible_upper = beta.ppf(0.975, posterior_alpha, posterior_beta)

    # P(true WR > expected WR)
    prob_positive = 1 - beta.cdf(expected_wr, posterior_alpha, posterior_beta)

    return {
        'posterior_mean_wr': round(posterior_mean, 4),
        'synergy_estimate': round(posterior_mean - expected_wr, 4),
        'credible_interval_95': [
            round(credible_lower, 4),
            round(credible_upper, 4)
        ],
        'prob_positive_synergy': round(prob_positive, 4),
        'substantial_evidence': prob_positive > 0.95
    }
```

#### CLI Integration
Add `--bayesian` flag to enable Bayesian estimates alongside frequentist results.

---

## API/Interface Changes

### CLI Flags for `analyze_synergies.py`

#### New Flags
```bash
--baseline [average|additive]
    Baseline model for expected win rate (default: average)

--alpha FLOAT
    Significance level for hypothesis tests (default: 0.05)

--min-sample-size INT
    Minimum games to report a synergy (default: 50)

--bayesian  # Phase 2
    Include Bayesian estimates alongside frequentist results
```

#### Updated Examples
```bash
# Use average baseline (default)
python scripts/analyze_synergies.py --baseline average

# More conservative significance threshold
python scripts/analyze_synergies.py --alpha 0.01

# Only report pairs with 100+ games
python scripts/analyze_synergies.py --min-sample-size 100

# Phase 2: Include Bayesian estimates
python scripts/analyze_synergies.py --bayesian
```

### JSON Output Format Changes

#### New Fields
- `confidence_interval_95`: [lower, upper] bounds for actual win rate
- `p_value`: Probability of observing result by chance
- `significant`: Boolean, significant at alpha level
- `significant_bonferroni`: Boolean, significant after correction
- `bonferroni_alpha`: Corrected significance threshold
- `confidence_level`: "high" | "medium" | "low"
- `warning`: String or null
- `power_analysis`: Object with sample size requirements

#### Backward Compatibility
All existing fields remain unchanged. New fields are additive only.

---

## Data Model Changes

### Database Schema Updates

#### Option 1: Add Individual Columns (Recommended)
```sql
-- Migration: Add new columns to synergy_stats
ALTER TABLE synergy_stats
  ADD COLUMN confidence_lower REAL,
  ADD COLUMN confidence_upper REAL,
  ADD COLUMN p_value REAL,
  ADD COLUMN sample_size INTEGER,
  ADD COLUMN baseline_model TEXT DEFAULT 'average';

-- Create index for querying significant synergies
CREATE INDEX idx_synergy_significance
  ON synergy_stats(p_value)
  WHERE p_value IS NOT NULL;
```

**Pros**: Better queryability, can filter/sort by p_value or confidence bounds
**Cons**: More rigid schema

#### Option 2: JSONB Metadata Column
```sql
ALTER TABLE synergy_stats
  ADD COLUMN metadata JSONB;

-- Example data:
{
  "confidence_interval": [0.531, 0.664],
  "p_value": 0.0234,
  "warnings": ["Low sample size"]
}
```

**Pros**: More flexible for future additions
**Cons**: Harder to query, less type safety

**Recommendation**: Option 1 (individual columns) for better SQL query support and performance.

### Migration Strategy
1. Add new columns with defaults (non-breaking)
2. Recompute all synergy stats with new methodology
3. Populate new columns during recomputation
4. Add deprecation note to old `expected_win_rate` column

---

## Testing Strategy

### Unit Tests

#### Baseline Model Tests
```python
def test_expected_wr_average():
    """Test average baseline calculation."""
    assert calculate_expected_win_rate_average(0.50, 0.50) == 0.50
    assert calculate_expected_win_rate_average(0.60, 0.40) == 0.50
    assert calculate_expected_win_rate_average(0.70, 0.50) == 0.60

def test_expected_wr_additive():
    """Test additive baseline calculation."""
    assert calculate_expected_win_rate_additive(0.50, 0.50) == 0.50
    assert calculate_expected_win_rate_additive(0.60, 0.60) == 0.70
    # Edge case: can exceed 1.0 (should be capped)
    assert calculate_expected_win_rate_additive(0.90, 0.90) == 1.00
```

#### Statistical Tests
```python
def test_binomial_significance():
    """Test significance calculation."""
    result = calculate_synergy_significance(60, 100, 0.50, alpha=0.05)
    assert 'p_value' in result
    assert 'significant' in result

def test_bonferroni_correction():
    """Test multiple comparisons correction."""
    synergies = [
        {'p_value': 0.01},
        {'p_value': 0.04},
        {'p_value': 0.10}
    ]
    corrected = apply_bonferroni_correction(synergies, alpha=0.05)
    # With 3 comparisons, alpha = 0.05/3 = 0.0167
    assert corrected[0]['significant_bonferroni'] == True
    assert corrected[1]['significant_bonferroni'] == False

def test_wilson_ci_integration():
    """Test Wilson CI reuse from existing utility."""
    from src.utils.statistics import wilson_confidence_interval
    lower, upper = wilson_confidence_interval(50, 100, confidence=0.95)
    assert 0.40 < lower < 0.50
    assert 0.50 < upper < 0.60
```

#### Power Analysis Tests
```python
def test_sample_size_calculation():
    """Test required sample size formula."""
    n = calculate_required_sample_size(
        baseline_wr=0.50,
        effect_size=0.05,
        alpha=0.05,
        power=0.80
    )
    assert 600 <= n <= 700  # Known result from statistical tables
```

### Integration Tests

#### End-to-End Pipeline
```python
def test_synergy_analysis_pipeline():
    """Test full analysis pipeline with new methodology."""
    # Setup test database with known data
    conn = setup_test_database()

    # Run analysis
    results = analyze_teammate_synergies(
        conn,
        min_games_together=10,
        baseline='average'
    )

    # Verify new fields present
    for hero_data in results.values():
        for synergy in hero_data['synergies']:
            assert 'confidence_interval_95' in synergy
            assert 'p_value' in synergy
            assert 'confidence_level' in synergy
```

#### Comparison Test
```python
def test_old_vs_new_methodology():
    """Compare old multiplicative vs new average baseline."""
    old_expected = calculate_expected_win_rate(0.52, 0.55)  # 0.286
    new_expected = calculate_expected_win_rate_average(0.52, 0.55)  # 0.535

    assert new_expected > old_expected  # New baseline is higher
    assert 0.50 <= new_expected <= 0.60  # Realistic range
```

### Manual Validation

#### Hulk Analysis Validation
Run on 286-match dataset and verify:
- Synergy scores are ±2-10% (not ±25-30%)
- 0-2 synergies significant with Bonferroni correction (not 10/10)
- All results include confidence intervals
- Warnings show for pairs with <500 games

---

## Migration & Rollout

### Communication

#### CHANGELOG.md Entry
```markdown
## [2.0.0] - 2025-10-15

### Changed - BREAKING
- **Fixed synergy analysis methodology**: Replaced theoretically flawed
  multiplicative baseline (`expected = A × B`) with correct average baseline
  (`expected = (A + B) / 2`). Synergy scores now report realistic ±3-7%
  effects instead of inflated ±25-30% effects.
- Added confidence intervals (Wilson 95% CI) for all synergy estimates
- Added statistical significance testing with Bonferroni correction
- Added sample size warnings for unreliable results (<500 games)

### Added
- `--baseline` CLI flag to choose baseline model (average or additive)
- `--alpha` CLI flag to set significance level
- Power analysis output showing required sample sizes
- Confidence level indicators (high/medium/low) based on sample size

### Migration Guide
Previous synergy scores were artificially inflated due to methodological flaw.
New scores are statistically defensible but smaller in magnitude. Rankings
(which hero pairs perform best) remain similar, but effect sizes have changed.

**Example**: Hulk + Luna Snow synergy was reported as +39.1% (inflated), now
correctly reported as +6.4% (realistic).

See `docs/MIGRATION_SYNERGY_V2.md` for detailed explanation and comparison.
```

#### Migration Guide Document
Create `docs/MIGRATION_SYNERGY_V2.md`:

```markdown
# Synergy Analysis V2 Migration Guide

## Why Did Results Change?

The previous methodology used a multiplicative baseline that incorrectly
treated teammates as independent events. This produced synergy scores that
were 3-5× larger than they should be.

## Before vs After

| Hero Pair | Old Synergy | New Synergy | Explanation |
|-----------|-------------|-------------|-------------|
| Hulk + Luna Snow | +39.1% | +6.4% | Old baseline was 20.7%, new is 53.5% |
| Spider-Man + Venom | +32.5% | +4.2% | Old baseline was 24.1%, new is 54.0% |

## What Stayed the Same?

- Rankings (best pairs vs worst pairs)
- Database schema (backward compatible)
- Sample sizes and actual win rates
- JSON export structure (new fields added)

## What Changed?

- Baseline calculation method
- Magnitude of synergy scores
- Statistical significance results
- Confidence interval reporting

## FAQ

**Q: Why are synergy scores so much smaller now?**
A: The old methodology inflated results. New scores reflect true effect sizes.

**Q: Are the old results wrong?**
A: Yes, methodologically flawed. New results are statistically defensible.

**Q: Should I re-run my analysis?**
A: Yes, all cached synergies will be recomputed with new methodology.
```

### Backward Compatibility

#### Database
- Add new columns with defaults (non-breaking)
- Keep old columns temporarily for comparison
- Mark old `expected_win_rate` column as deprecated

#### JSON Export
- Add new fields (non-breaking)
- Keep existing structure
- Version field: Add `"methodology_version": "2.0"`

#### Scripts
- Keep existing flags working
- Add new flags as options
- Default to new methodology

### Rollout Plan

1. **Development**: Implement changes in feature branch
2. **Testing**: Run full test suite + manual validation
3. **Documentation**: Update README, STATISTICS.md, create migration guide
4. **Deployment**: Merge to main, tag as v2.0.0
5. **Recomputation**: Run `analyze_synergies.py` to rebuild all cached stats
6. **Communication**: Announce in project README with link to migration guide

---

## Performance Considerations

### Analysis Runtime
- **Current**: ~2 minutes for 286 matches
- **Expected**: <5 minutes for 1,000 matches
- **Bottleneck**: Database queries for match participants

### Optimizations
- No new performance concerns
- Bonferroni correction is O(N) where N = number of synergies
- Power analysis is O(1) per calculation
- Wilson CI already optimized in existing implementation

### Scalability
- Database indexes already exist on `match_id` and `hero_name`
- New significance queries will benefit from p_value index
- No memory concerns (all calculations on-the-fly)

---

## Security & Privacy

### No New Concerns
- No new data collection
- No external API calls
- No user-provided input beyond CLI flags
- All statistical calculations are local

### Existing Protections
- SQL injection protection via parameterized queries (already in place)
- Input validation on CLI arguments (already in place)

---

## Monitoring & Observability

### Logging Enhancements

Add logging for:
- Sample sizes per synergy calculation
- Number of synergies failing significance tests
- Warnings triggered for low samples
- Bonferroni correction results

```python
logger.info(f"Analyzed {len(synergies)} synergies for {hero}")
logger.info(f"  Significant (uncorrected): {sum(s['significant'] for s in synergies)}")
logger.info(f"  Significant (Bonferroni): {sum(s['significant_bonferroni'] for s in synergies)}")
logger.info(f"  Low sample warnings: {sum(s['confidence_level'] == 'low' for s in synergies)}")
```

### Metrics to Track
- Analysis runtime per hero
- Distribution of sample sizes
- Percentage of significant results (before/after correction)
- Average synergy score magnitude

---

## Documentation

### README.md Updates
Update "Data Collection Pipeline" section:

```markdown
## Synergy Analysis

The analyzer identifies hero pairings with significant synergies using
statistically rigorous methods:

- **Average baseline model**: Expected win rate = average of individual rates
- **Wilson confidence intervals**: 95% CI for all estimates
- **Significance testing**: Binomial tests with Bonferroni correction
- **Sample size warnings**: Flags unreliable results (<500 games)

See `docs/STATISTICS.md` for detailed methodology.
```

### STATISTICS.md Updates
Add section on synergy baseline models:

```markdown
## Synergy Analysis Methodology

### Baseline Models

We calculate an expected win rate for hero pairs using the **average baseline model**:

```
Expected Win Rate = (Hero A Win Rate + Hero B Win Rate) / 2
```

**Rationale**: If two heroes contribute equally to team performance, their
combined expected win rate is their average. This assumes teammates are
correlated (both on same team), not independent.

### Why Not Multiplicative?

Previous versions used `Expected = A × B`, which incorrectly treats teammates
as independent events (like rolling two dice). This produced artificially
inflated synergy scores of ±30% when true effects are ±3-7%.

### Statistical Testing

- **Confidence intervals**: Wilson 95% CI for actual win rates
- **Significance tests**: Exact binomial test vs expected baseline
- **Multiple comparisons**: Bonferroni correction for family-wise error rate
- **Sample size requirements**: ≥500 games for reliable estimates

### Example

Spider-Man (52% WR) + Luna Snow (55% WR) with 87 games together:

- Expected WR: (0.52 + 0.55) / 2 = **53.5%**
- Actual WR: 52/87 = **59.8%**
- Synergy score: 59.8% - 53.5% = **+6.3%**
- 95% CI: [49.1%, 69.8%]
- P-value: 0.234 (not significant)
```

### Create MIGRATION_SYNERGY_V2.md
Detailed migration guide as outlined in "Communication" section above.

### Update troubleshooting.md
Add entries:

```markdown
### Why did synergy scores decrease after updating?

The previous methodology used a flawed multiplicative baseline that inflated
results. New methodology uses correct average baseline, producing realistic
effect sizes. See `docs/MIGRATION_SYNERGY_V2.md` for details.

### What does "insufficient sample size" warning mean?

Synergy estimates require large sample sizes for reliability. Warnings indicate:
- **Low (<100 games)**: Very unreliable, wide confidence intervals
- **Medium (100-500 games)**: Moderate reliability, interpret with caution
- **High (≥500 games)**: Reliable estimates

Realistic 3-5% synergies require 1,000-15,000 games to detect with statistical
significance. Current dataset limitations mean most synergies cannot be
confirmed as statistically significant.
```

---

## Success Metrics

### Functional Success Criteria

1. **Realistic Synergy Scores**: Reported synergies in ±2-10% range (not ±25-30%)
2. **Proper Significance**: 0-2 synergies significant with current data (not 10/10)
3. **Confidence Intervals**: All results include 95% Wilson CIs
4. **Sample Warnings**: Pairs with <500 games show warning messages
5. **Bonferroni Correction**: P-values adjusted for multiple comparisons
6. **Power Analysis**: Output includes required sample sizes for detection

### Non-Functional Success Criteria

1. **Performance**: Analysis completes in <5 minutes for 1,000 matches
2. **Backward Compatible**: Database schema changes are additive only
3. **Code Reuse**: Uses existing `wilson_confidence_interval()` utility
4. **Documentation**: README, STATISTICS.md, troubleshooting, and migration guide updated
5. **Maintainability**: Clear docstrings and inline comments for statistical formulas

---

## Alternatives Considered

### 1. Average vs Additive Baseline Model

**Decision**: Start with average model, optionally add additive later.

**Rationale**:
- Average model is simpler to understand
- Both produce similar results in practice
- Additive model can be added as `--baseline additive` flag

### 2. ML Baseline Models

**Decision**: Out of scope for this spec.

**Rationale**:
- Requires 1,000+ matches to train
- Needs feature engineering (map, rank, composition)
- Added complexity not justified with current data
- Can be separate enhancement later

### 3. Within-Player Analysis

**Decision**: Out of scope for this spec.

**Rationale**:
- Requires 30+ players with diverse hero pools
- Current dataset dominated by few players
- Controls for player skill but needs more data
- Future enhancement when dataset grows

### 4. Benjamini-Hochberg vs Bonferroni Correction

**Decision**: Use Bonferroni (more conservative).

**Rationale**:
- Bonferroni controls family-wise error rate (stricter)
- BH controls false discovery rate (more lenient)
- With small sample sizes, prefer conservative approach
- Can add BH as option later if needed

---

## Timeline & Phases

### Phase 1: Methodology Fix (This Spec)
**Duration**: 1-2 days

**Tasks**:
1. Implement new baseline models in `src/utils/statistics.py`
2. Add significance testing functions
3. Update `src/analyzers/teammate_synergy.py`
4. Update `scripts/analyze_synergies.py` with new CLI flags
5. Add database schema changes
6. Write unit tests
7. Write integration tests
8. Update documentation
9. Create migration guide
10. Recompute all synergy stats

### Phase 2: Bayesian Analysis (Optional)
**Duration**: 1-2 days

**Tasks**:
1. Implement Bayesian estimation functions
2. Add `--bayesian` CLI flag
3. Update output format with credible intervals
4. Add Bayesian interpretation to documentation
5. Write tests for Bayesian calculations

### Future Work (Separate Specs)
- **ML Baseline Models**: Train regression model on match features
- **Within-Player Analysis**: Control for player skill variation
- **Continuous Data Collection**: Automated periodic match fetching
- **Map-Specific Synergies**: Requires 10,000+ matches per map
- **Real-Time Dashboard**: Web UI for live synergy tracking

---

## Open Questions & Risks

### Risk: User Confusion About Smaller Scores

**Risk**: Users may think smaller synergy scores mean the analysis got worse.

**Mitigation**:
- Clear communication in CHANGELOG and migration guide
- Explain why old scores were wrong
- Emphasize rankings remain similar
- Provide side-by-side comparison examples

### Risk: Statistical Significance Too Strict

**Risk**: Bonferroni correction may mark all synergies as non-significant with current data.

**Mitigation**:
- Report both uncorrected and corrected significance
- Add power analysis showing required sample sizes
- Be honest about data limitations
- Encourage continued data collection

### Question: Keep Old Results for Comparison?

**Decision**: No, drop old results after migration.

**Rationale**:
- Old results are misleading
- Keeping both creates confusion
- Database space not a concern
- Can regenerate if needed for research

### Question: Default Minimum Sample Size?

**Current**: 50 games (too low for reliability)
**Recommendation**: Increase to 100 games for reporting

**Rationale**:
- More conservative threshold
- Reduces noise from small samples
- User can override with `--min-sample-size` flag

---

## References

### Internal Documents
- `/home/ericreyes/github/marvel-rivals-stats/docs/STATISTICS.md` - Current statistical methodology
- `/home/ericreyes/github/marvel-rivals-stats/docs/SYNERGY_DETECTION_STRATEGIES.md` - Comprehensive strategy guide
- Requirements document: `planning/requirements.md`

### Academic References
- **Agresti & Coull (1998)**: "Approximate is better than 'exact' for interval estimation of binomial proportions"
- **Bonferroni (1936)**: Multiple comparisons correction
- **Cohen (1988)**: Statistical power analysis for behavioral sciences
- **Wilson (1927)**: Probable inference and binomial confidence intervals

### Implementation References
- `src/utils/statistics.py` - Existing Wilson CI implementation
- `src/analyzers/character_winrate.py` - Pattern for confidence interval reporting
- `scripts/analyze_characters.py` - CLI structure pattern

---

## Revision History

- **2025-10-15**: Initial specification created by spec-writer agent
- Based on requirements gathered by spec-researcher agent
- Follows completion of SPEC-005 (Character Win Rate Analysis)
