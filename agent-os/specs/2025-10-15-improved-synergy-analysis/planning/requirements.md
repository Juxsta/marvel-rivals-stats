# Requirements: Improved Synergy Analysis

**Date:** 2025-10-15
**Status:** Draft
**Priority:** High (fixes critical methodological flaw)

---

## Problem Statement

The current synergy analysis in Marvel Rivals Stats Analyzer has a fundamental methodological flaw:

### Current Issues

1. **Flawed Multiplicative Model**: Uses `expected_wr = hero_a_wr × hero_b_wr`, which treats teammates as independent events. This is theoretically unsound because both heroes are on the same team.

2. **Artificially Inflated Synergies**: Reports synergy scores of ±25-30% when true effects are likely ±3-7%.

3. **False Statistical Significance**: Shows 10/10 synergies as "highly significant" (p < 0.001) when proper analysis shows 0/10 are significant (p > 0.05).

4. **No Uncertainty Quantification**: Doesn't report confidence intervals, power analysis, or sample size requirements.

5. **Insufficient Sample Sizes**: Current dataset (286 matches, max 207 games per pair) can only detect ≥10% synergies. Realistic 3-5% synergies require 1,000-15,000 games per pair.

### Impact

- **Misleading Users**: Current output claims huge synergies that don't exist
- **Low Confidence**: Results aren't statistically defensible
- **Poor Prioritization**: Can't distinguish real synergies from noise

---

## Goals

### Primary Goals

1. **Fix Methodology**: Replace multiplicative model with theoretically sound baseline (average or additive model)

2. **Honest Uncertainty**: Report confidence intervals and sample sizes prominently

3. **Statistical Rigor**: Apply proper significance testing with multiple comparisons corrections

4. **Phased Improvement**: Start with simple fixes, build toward advanced methods

### Secondary Goals

1. **Maintain Compatibility**: Keep database schema and API consistent
2. **Educational**: Help users understand statistical limitations
3. **Extensible**: Design for future enhancements (Bayesian, ML baselines)

---

## Scope

### In Scope

#### Phase 1: Fix Methodology (This Spec)
- ✅ Replace multiplicative baseline with average model: `expected_wr = (hero_a_wr + hero_b_wr) / 2`
- ✅ Add Wilson confidence intervals for synergy estimates
- ✅ Implement proper binomial significance tests
- ✅ Add Bonferroni correction for multiple comparisons
- ✅ Report sample sizes and power analysis
- ✅ Add warnings for insufficient sample sizes (<500 games)
- ✅ Update documentation explaining the fix
- ✅ Update existing `analyze_synergies.py` script
- ✅ Update `src/analyzers/teammate_synergy.py` module

#### Phase 2: Bayesian Analysis (Optional Enhancement)
- ✅ Add optional Bayesian estimates alongside frequentist results
- ✅ Use Beta-Binomial conjugate priors
- ✅ Report credible intervals and posterior probabilities
- ✅ Add flag `--bayesian` to enable

### Out of Scope

- ❌ **Within-player analysis**: Requires 30+ players with diverse hero pools (future enhancement)
- ❌ **ML baseline models**: Requires 1,000+ matches to train (separate spec)
- ❌ **Causal inference methods**: Research-level complexity (propensity scoring, DiD)
- ❌ **Map-specific synergies**: Needs massive datasets
- ❌ **Rank-specific synergies**: Already partially implemented, but needs more data
- ❌ **Real-time continuous updates**: Batch analysis is sufficient
- ❌ **Automated data collection**: Manual periodic runs for now

---

## User Stories

### As a User
- I want to see **realistic synergy estimates** (±3-7%) instead of inflated values (±30%)
- I want to know **how confident** the analysis is (confidence intervals)
- I want to see **sample sizes** so I can judge reliability
- I want **warnings** when data is insufficient
- I want to understand **why the methodology changed** (migration notes)

### As a Developer
- I want to **reuse existing utilities** (Wilson CI from `src/utils/statistics.py`)
- I want **consistent patterns** with character analysis
- I want **well-documented** statistical methods
- I want **extensible design** for future enhancements

### As a Data Scientist
- I want **defensible statistics** that pass peer review
- I want **multiple comparison corrections** to avoid false positives
- I want **power analysis** to understand limitations
- I want **Bayesian options** for small samples

---

## Technical Requirements

### 1. New Baseline Models

#### Primary: Average Model
```python
def expected_wr_average(hero_a_wr: float, hero_b_wr: float) -> float:
    """Simple average of individual win rates.

    Rationale: If heroes contribute equally to team performance,
    their combined expected win rate is their average.
    """
    return (hero_a_wr + hero_b_wr) / 2.0
```

#### Alternative: Additive Model (Optional)
```python
def expected_wr_additive(hero_a_wr: float, hero_b_wr: float) -> float:
    """Additive contributions from baseline.

    Rationale: Each hero contributes independently to deviation from 50%.
    """
    baseline = 0.5
    contrib_a = hero_a_wr - baseline
    contrib_b = hero_b_wr - baseline
    return baseline + contrib_a + contrib_b
```

### 2. Synergy Score Calculation

```python
def calculate_synergy_with_ci(
    wins: int,
    total: int,
    hero_a_wr: float,
    hero_b_wr: float,
    confidence: float = 0.95
) -> Dict:
    """Calculate synergy with confidence interval.

    Returns:
        {
            'actual_wr': float,
            'expected_wr': float,
            'synergy_score': float,
            'confidence_interval': (lower, upper),
            'p_value': float,
            'significant': bool,
            'sample_size': int,
            'warning': Optional[str]
        }
    """
    actual_wr = wins / total
    expected_wr = expected_wr_average(hero_a_wr, hero_b_wr)
    synergy_score = actual_wr - expected_wr

    # Wilson CI for actual_wr
    ci_lower, ci_upper = wilson_confidence_interval(wins, total, confidence)

    # Binomial test
    p_value = binomtest(wins, total, expected_wr, alternative='two-sided').pvalue

    # Bonferroni correction (adjust in caller based on n_comparisons)
    # significant = p_value < (alpha / n_comparisons)

    # Warning for small samples
    warning = None
    if total < 500:
        warning = f"Low sample size ({total} games). Results may be unreliable."

    return {
        'actual_wr': actual_wr,
        'expected_wr': expected_wr,
        'synergy_score': synergy_score,
        'confidence_interval': (ci_lower, ci_upper),
        'p_value': p_value,
        'sample_size': total,
        'warning': warning
    }
```

### 3. Multiple Comparisons Correction

```python
def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """Apply Bonferroni correction for multiple comparisons.

    Args:
        p_values: List of p-values from individual tests
        alpha: Family-wise error rate (default 0.05)

    Returns:
        List of booleans indicating significance after correction
    """
    n_comparisons = len(p_values)
    corrected_alpha = alpha / n_comparisons
    return [p < corrected_alpha for p in p_values]
```

### 4. Power Analysis

```python
def calculate_required_sample_size(
    baseline_wr: float,
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """Calculate required sample size to detect effect.

    Uses formula for binomial proportions with continuity correction.
    """
    from scipy.stats import norm
    import numpy as np

    z_alpha = norm.ppf(1 - alpha / 2)  # Two-tailed
    z_beta = norm.ppf(power)

    p0 = baseline_wr
    p1 = baseline_wr + effect_size

    n = ((z_alpha * np.sqrt(p0 * (1 - p0)) + z_beta * np.sqrt(p1 * (1 - p1))) / effect_size) ** 2

    return int(np.ceil(n))
```

### 5. Bayesian Analysis (Phase 2)

```python
def bayesian_synergy_estimate(
    wins: int,
    total: int,
    expected_wr: float,
    prior_strength: int = 20
) -> Dict:
    """Bayesian estimate using Beta-Binomial conjugate prior.

    Prior: Beta(α, β) centered at expected_wr
    Posterior: Beta(α + wins, β + losses)
    """
    from scipy.stats import beta

    prior_alpha = expected_wr * prior_strength
    prior_beta = (1 - expected_wr) * prior_strength

    posterior_alpha = prior_alpha + wins
    posterior_beta = prior_beta + (total - wins)

    posterior_mean = posterior_alpha / (posterior_alpha + posterior_beta)
    credible_lower = beta.ppf(0.025, posterior_alpha, posterior_beta)
    credible_upper = beta.ppf(0.975, posterior_alpha, posterior_beta)

    prob_positive = 1 - beta.cdf(expected_wr, posterior_alpha, posterior_beta)

    return {
        'posterior_mean': posterior_mean,
        'credible_interval': (credible_lower, credible_upper),
        'synergy_estimate': posterior_mean - expected_wr,
        'prob_positive_synergy': prob_positive,
        'substantial_evidence': prob_positive > 0.95
    }
```

---

## Data Requirements

### Current State
- **Total matches**: 286
- **Max games per pair**: 207 (Hulk + Luna Snow)
- **Average games per pair**: ~80

### Target State (Long-term)
- **Total matches**: 10,000+ (35× increase)
- **Games per major pair**: 1,000+ (5× increase)
- **Timeline**: 3-6 months of continuous collection

### Phase 1 Requirements
- **No new data needed**: Fix methodology with existing data
- **Honest reporting**: Show uncertainty with current sample sizes
- **Data collection guidance**: Document how much data is needed for significance

---

## Success Criteria

### Functional

1. ✅ **Correct Baseline**: Average model produces expected WR of 50-65% (not 20-30%)

2. ✅ **Realistic Synergies**: Reported synergy scores are ±2-10% (not ±25-30%)

3. ✅ **Proper Significance**: With current data, 0-2 synergies significant (not 10/10)

4. ✅ **Confidence Intervals**: All estimates include 95% Wilson CIs

5. ✅ **Sample Size Warnings**: Results with <500 games show warnings

6. ✅ **Bonferroni Correction**: P-values adjusted for number of comparisons

7. ✅ **Power Analysis**: Output includes required sample sizes for detection

### Non-Functional

1. ✅ **Performance**: Analysis completes in <5 minutes for 1,000 matches

2. ✅ **Backward Compatible**: Database schema unchanged

3. ✅ **Code Reuse**: Uses existing `wilson_confidence_interval()` utility

4. ✅ **Documentation**: Updated README, STATISTICS.md, troubleshooting guide

5. ✅ **Migration Guide**: Explains why results changed

6. ✅ **Maintainability**: Clear, well-commented code

---

## Acceptance Criteria

### Phase 1: Methodology Fix

- [ ] `src/analyzers/teammate_synergy.py` uses average baseline model
- [ ] Synergy results include confidence intervals
- [ ] P-values computed with binomial test vs average baseline
- [ ] Bonferroni correction applied for multiple comparisons
- [ ] Warnings displayed for samples <500 games
- [ ] Power analysis output shows required sample sizes
- [ ] JSON export format updated with new fields
- [ ] Database `synergy_stats` table schema supports new fields (or uses JSON)
- [ ] `scripts/analyze_synergies.py` updated with new flags:
  - `--baseline [average|additive]` (default: average)
  - `--alpha 0.05` (significance level)
  - `--min-sample-size 50` (minimum games to report)
- [ ] Documentation updated:
  - README.md mentions methodology improvement
  - STATISTICS.md explains average baseline model
  - CHANGELOG.md documents the fix
  - Migration guide created
- [ ] Existing tests updated to reflect new methodology
- [ ] New tests added for:
  - Average baseline calculation
  - Confidence interval calculation
  - Bonferroni correction
  - Power analysis

### Phase 2: Bayesian Analysis (Optional)

- [ ] `--bayesian` flag added to `analyze_synergies.py`
- [ ] Bayesian estimates calculated alongside frequentist
- [ ] Output includes credible intervals and P(positive synergy)
- [ ] Documentation explains Bayesian interpretation
- [ ] Tests cover Bayesian calculations

---

## Dependencies

### Existing Code to Reuse

1. **`src/utils/statistics.py`**:
   - `wilson_confidence_interval()` - Already implemented
   - Can add new functions: `expected_wr_average()`, `binomial_test_synergy()`

2. **`src/analyzers/character_winrate.py`**:
   - Pattern for confidence interval reporting
   - Database caching approach

3. **`scripts/analyze_characters.py`**:
   - Script structure and CLI argument patterns
   - Output formatting style

4. **Database Schema**:
   - `synergy_stats` table already exists
   - May need to add columns: `confidence_lower`, `confidence_upper`, `p_value`, `sample_size`
   - Or use JSONB field for flexibility

### External Libraries

- `scipy.stats` - Already in requirements.txt
- `numpy` - Already in requirements.txt
- No new dependencies needed

---

## Constraints

### Statistical Constraints

1. **Sample Size**: Can only detect ≥10% synergies with current 200-300 games per pair
2. **Power**: 80% power requires 600+ games for 5% effects, 1,700+ for 3% effects
3. **Multiple Comparisons**: Testing 10+ pairs requires Bonferroni correction (α = 0.005)

### Technical Constraints

1. **API Rate Limits**: 7 requests/min limits data collection speed
2. **Storage**: Not a constraint (PostgreSQL handles it)
3. **Compute**: Not a constraint (analysis is fast)

### Timeline Constraints

1. **Phase 1**: Can implement in 1-2 days (primarily refactoring)
2. **Phase 2**: Additional 1-2 days for Bayesian methods
3. **Data Collection**: Months to reach adequate sample sizes (out of scope for this spec)

---

## Migration Plan

### Communication

1. **CHANGELOG.md Entry**:
   ```markdown
   ## [2.0.0] - 2025-10-15
   ### Changed - BREAKING
   - **Fixed synergy analysis methodology**: Replaced flawed multiplicative
     baseline with average baseline model. Synergy scores now report realistic
     ±3-7% effects instead of inflated ±30% effects.
   - Added confidence intervals and statistical significance testing
   - Added sample size warnings for unreliable results

   ### Migration
   Previous synergy scores were artificially inflated due to methodological
   flaw. New scores are statistically defensible but smaller in magnitude.
   Rankings (which hero pairs are best) remain similar, but effect sizes
   have changed.

   See docs/STATISTICS.md for detailed explanation.
   ```

2. **Migration Guide** (`docs/MIGRATION_SYNERGY_V2.md`):
   - Explain the flaw in multiplicative model
   - Show before/after comparison
   - Clarify that rankings are still valid
   - Explain new uncertainty quantification

### Backward Compatibility

- **Database**: Add new columns with defaults, don't drop old data
- **JSON Export**: Add new fields, keep old format structure
- **Scripts**: Keep existing flags working, add new ones

---

## Testing Strategy

### Unit Tests

1. **Baseline model tests**:
   - `test_expected_wr_average()` - Verify average calculation
   - `test_expected_wr_additive()` - Verify additive calculation
   - Edge cases: 0% WR, 100% WR, 50% WR

2. **Statistical tests**:
   - `test_confidence_interval_synergy()` - Verify CI calculation
   - `test_binomial_test()` - Verify p-value calculation
   - `test_bonferroni_correction()` - Verify multiple comparisons

3. **Power analysis tests**:
   - `test_sample_size_calculation()` - Verify formula
   - Known examples from literature

4. **Bayesian tests** (Phase 2):
   - `test_bayesian_estimate()` - Verify posterior calculation
   - `test_credible_interval()` - Verify Bayesian CI

### Integration Tests

1. **End-to-end pipeline**:
   - Run analysis on test dataset
   - Verify new fields in output
   - Verify warnings trigger correctly

2. **Comparison test**:
   - Compare old vs new methodology on same data
   - Document differences

### Manual Testing

1. **Hulk analysis validation**:
   - Re-run on 286-match dataset
   - Verify realistic synergy scores (±3-7%)
   - Verify 0-2 synergies significant (not 10/10)

---

## Documentation Requirements

### User Documentation

1. **README.md**:
   - Update "Data Collection Pipeline" section
   - Mention methodology improvement
   - Link to STATISTICS.md for details

2. **docs/STATISTICS.md**:
   - Add section on synergy baseline models
   - Explain average vs multiplicative vs additive
   - Show mathematical formulas
   - Provide examples with Hulk data

3. **docs/MIGRATION_SYNERGY_V2.md**:
   - New document explaining the change
   - Before/after comparison
   - FAQ section

4. **docs/troubleshooting.md**:
   - Add entry for "Why did synergy scores decrease?"
   - Add entry for "What does 'insufficient sample size' warning mean?"

### Developer Documentation

1. **Code comments**:
   - Docstrings for all new functions
   - Inline comments explaining statistical formulas

2. **docs/development.md**:
   - Update with new analysis flags
   - Add power analysis examples

---

## Open Questions

1. **Should we keep old synergy results in database for comparison?**
   - Recommendation: No, they're misleading. Drop and recompute.

2. **Should we add a "confidence level" field to filter results?**
   - Example: Only show pairs with >100 games
   - Recommendation: Yes, add `--min-sample-size` flag

3. **Should we automatically flag "high confidence" vs "low confidence" synergies?**
   - Recommendation: Yes, use sample size thresholds (>500 = high, 100-500 = medium, <100 = low)

---

## References

### Internal Documents
- `docs/STATISTICS.md` - Current statistical methodology
- `docs/SYNERGY_DETECTION_STRATEGIES.md` - Comprehensive strategy guide
- `scripts/statistical_significance_analysis.py` - Baseline model comparison
- `scripts/power_analysis_synergies.py` - Sample size calculations

### Academic References
- Agresti & Coull (1998) - Wilson confidence intervals
- Bonferroni (1936) - Multiple comparisons correction
- Cohen (1988) - Statistical power analysis

---

## Revision History

- **2025-10-15**: Initial requirements draft based on statistical analysis findings
