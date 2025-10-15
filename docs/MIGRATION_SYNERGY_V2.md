# Synergy Analysis v2.0 Migration Guide

**Date**: October 15, 2025
**Version**: 2.0.0
**Breaking Change**: Yes - Synergy scores and statistical methodology changed

---

## TL;DR

**What Changed**: Fixed fundamental flaw in synergy baseline model. Synergy scores are now realistic (±3-7%) instead of inflated (±25-30%).

**Why**: Old multiplicative baseline was theoretically wrong for teammates on the same team.

**Impact**: Rankings stay similar, but effect magnitudes decreased dramatically.

**Action Required**: None - analysis automatically uses new methodology. Old results were incorrect and have been replaced.

---

## Why Did Results Change?

###  The Flaw (v1.0)

Previous versions used a **multiplicative baseline** to calculate expected win rates:

```
Expected Win Rate = Hero A's Win Rate × Hero B's Win Rate
```

**Example**: Hulk (52%) × Luna Snow (55%) = **28.6% expected**

**The Problem**: This formula calculates the probability that two independent events **both occur**. It only makes sense for separate games:
- "What's the chance Hulk's team wins Game 1 AND Luna's team wins Game 2?"

But Hulk and Luna Snow are **on the same team** in the **same game**! Using multiplication produces an unrealistically low baseline (28.6%) that makes every pairing look like a huge synergy.

### The Fix (v2.0)

Version 2.0 uses an **average baseline** that reflects combined performance:

```
Expected Win Rate = (Hero A's Win Rate + Hero B's Win Rate) / 2
```

**Example**: (52% + 55%) / 2 = **53.5% expected**

**Why This Works**: If two heroes contribute independently to team performance, their combined expected win rate should be the average of their individual capabilities. This is theoretically sound for teammates.

---

## Before vs. After Comparison

### Example: Hulk + Luna Snow (207 games, 124 wins)

| Metric | v1.0 (Old - Flawed) | v2.0 (New - Correct) | Difference |
|--------|---------------------|----------------------|------------|
| **Expected Win Rate** | 28.6% | 53.5% | +24.9% |
| **Actual Win Rate** | 59.9% | 59.9% | (unchanged) |
| **Synergy Score** | **+31.3%** | **+6.4%** | -24.9% |
| **Interpretation** | "Massive synergy!" | "Modest positive synergy" | More realistic |
| **Statistical Significance** | p < 0.001 | p = 0.142 | Not significant |

### Visual Comparison

**v1.0 Results (Inflated)**:
```
Top 5 Hulk Synergies:
1. Star-Lord:      +31.4% synergy ★★★
2. Black Widow:    +30.9% synergy ★★★
3. Doctor Strange: +28.3% synergy ★★★
4. Iron Man:       +28.1% synergy ★★★
5. Hawkeye:        +27.3% synergy ★★★
```

**v2.0 Results (Realistic)**:
```
Top 5 Hulk Synergies:
1. Star-Lord:      +6.7% synergy [CI: -3%, +17%]
2. Black Widow:    +6.0% synergy [CI: -5%, +17%]
3. Doctor Strange: +3.3% synergy [CI: -2%, +9%]
4. Iron Man:       +3.0% synergy [CI: -8%, +14%]
5. Hawkeye:        +2.3% synergy [CI: -8%, +13%]

Note: None are statistically significant (p > 0.05)
⚠ Warning: Sample sizes insufficient for detecting <10% synergies
```

---

## What Stayed the Same?

### Rankings Are Similar ✅

The **relative ordering** of synergies hasn't changed much:

**v1.0 Top 3**: Star-Lord (#1), Black Widow (#2), Doctor Strange (#3)
**v2.0 Top 3**: Star-Lord (#1), Black Widow (#2), Doctor Strange (#3)

The best and worst pairings are still the best and worst - we just report honest effect sizes now.

### Database Schema ✅

No data was lost. The underlying match data is unchanged. Only the **calculated synergy scores** are different because we fixed the formula.

### Collection Pipeline ✅

Player discovery, match collection, and character analysis are unaffected. Only synergy analysis methodology changed.

---

## What Changed?

### 1. Expected Win Rate Baseline

- **Old**: Multiplicative (wrong for teammates)
- **New**: Average (theoretically sound)

### 2. Synergy Score Magnitude

- **Old**: ±25-30% (artificially inflated)
- **New**: ±3-7% (realistic for team games)

### 3. Statistical Significance

- **Old**: All pairs showed p < 0.001 (false positives)
- **New**: Most pairs show p > 0.05 (honest assessment)

### 4. New Information Added

v2.0 includes additional statistical enhancements:

- **Confidence Intervals**: 95% Wilson CIs for actual win rates
- **P-Values**: Statistical significance testing with Bonferroni correction
- **Sample Size Warnings**: High/Medium/Low confidence labels
- **Power Analysis**: Required sample sizes to detect 3%, 5%, 10% synergies

### 5. CLI Flags

New flags added to `analyze_synergies.py`:

```bash
--baseline average        # Choose baseline model (average or additive)
--alpha 0.05             # Significance level
--min-sample-size 50     # Minimum games to report
```

---

## FAQ

### Q: Are my old results wrong?

**Yes**. The v1.0 multiplicative baseline was mathematically unsound for teammates on the same team. It produced expected win rates of 20-30% when they should be 50-60%, making everything look like a massive synergy when true effects are ±3-7%.

### Q: Should I trust the new results?

**Yes**. The v2.0 average baseline is theoretically correct and produces defensible results. Effect sizes now match expectations for team-based games.

However, **statistical significance is low** with current sample sizes (100-300 games per pair). We can only reliably detect large synergies (≥10%). Detecting realistic 3-5% synergies requires 1,000+ games per pair.

### Q: Which hero pairs are *truly* synergistic?

**Hard to say** with current data. Most observed synergies are **not statistically significant** after applying proper testing and Bonferroni correction.

Example: Hulk + Star-Lord shows +6.7% synergy with 95% CI [-3%, +17%] and p=0.142. This *suggests* positive synergy, but we can't rule out random chance with only 77 games together.

To confidently detect 5% synergies, we need **600+ games per pair**. Current datasets have 100-300 games, which is only sufficient for detecting ≥10% effects.

### Q: Why can't I detect small synergies?

**Statistical power**. With 200 games together:
- **Can detect**: ±10% synergies (80% power)
- **Cannot detect**: ±5% synergies (need 600 games)
- **Cannot detect**: ±3% synergies (need 1,700 games)

True hero synergies are likely in the 3-7% range based on team game mechanics. Detecting them requires **massive data collection** (10,000+ matches, 1,000+ games per major pair).

### Q: So should I ignore synergy analysis?

**No**. The rankings are still useful:

1. **Relative ordering matters**: Hulk + Star-Lord likely is better than Hulk + Mantis, even if we can't quantify the exact magnitude.

2. **Large synergies are detectable**: If a pair truly has ≥10% synergy, current data can identify it.

3. **Directional guidance**: Positive scores suggest good pairings worth exploring, even if not statistically conclusive.

Just understand the **limitations**: Small samples mean wide confidence intervals and uncertain magnitudes.

### Q: Will synergies become significant with more data?

**Maybe**. Power analysis shows:
- With **600 games**: Can detect 5% synergies
- With **1,700 games**: Can detect 3% synergies
- With **10,000 games**: Can detect 1% synergies

If you collect 10,000+ total matches with diverse hero combinations, synergies will become statistically clear. With current data (100-300 games per pair), only large effects (≥10%) reach significance.

### Q: Can I still use the old methodology?

**No**. The multiplicative baseline is fundamentally flawed and has been removed. All analyses now use the average baseline.

If you have old v1.0 results saved, they should be discarded. They showed inflated synergy scores due to the methodological error.

### Q: How do I interpret the new output?

Look for:
- **Synergy score**: ±3-7% is realistic, ±10%+ is strong
- **Confidence interval**: Narrow = reliable, wide = uncertain
- **P-value**: <0.05 = statistically significant (after Bonferroni correction)
- **Sample size warning**: High confidence ≥500 games, Medium 100-499, Low <100
- **Power analysis**: Shows how much data needed for reliable detection

---

## Technical Details

### Baseline Model Formulas

**v1.0 (Multiplicative - Flawed)**:
```python
expected_wr = hero_a_wr * hero_b_wr
```

**v2.0 (Average - Correct)**:
```python
expected_wr = (hero_a_wr + hero_b_wr) / 2
```

**v2.0 Alternative (Additive)**:
```python
expected_wr = 0.5 + (hero_a_wr - 0.5) + (hero_b_wr - 0.5)
# Equivalent to additive contributions from baseline
```

### Statistical Testing (v2.0 Only)

Each synergy is tested with:

1. **Binomial test**: H₀: actual_wr = expected_wr, H₁: actual_wr ≠ expected_wr
2. **Bonferroni correction**: α_corrected = α / n_comparisons (controls family-wise error)
3. **Wilson confidence interval**: 95% CI for actual win rate
4. **Power analysis**: Required sample size for 80% power to detect 3%, 5%, 10% effects

### Database Schema Changes

New columns added to `synergy_stats` table:
- `confidence_lower` (REAL): Lower bound of 95% CI
- `confidence_upper` (REAL): Upper bound of 95% CI
- `p_value` (REAL): Statistical significance (two-tailed binomial test)
- `sample_size_warning` (TEXT): Warning message for insufficient data
- `baseline_model` (TEXT): "average" or "additive"

Existing columns unchanged (backward compatible).

### JSON Export Format (v2.0)

New root-level fields:
- `methodology_version: "2.0"`
- `baseline_model: "average"`
- `analysis_date: "2025-10-15T..."`

New per-synergy fields:
- `p_value`, `significant`, `significant_bonferroni`, `bonferroni_alpha`
- `confidence_level` ("high", "medium", "low")
- `warning` (sample size warning message)

New per-hero section:
- `power_analysis` with required sample sizes for 3%, 5%, 10% effects

---

## Migration Checklist

- ✅ **Update to v2.0** - Pull latest code and rebuild containers
- ✅ **Run database migration** - Schema update is automatic on next analysis
- ✅ **Re-run synergy analysis** - Old results are replaced with corrected values
- ✅ **Review new output format** - Familiarize with CIs, p-values, warnings
- ✅ **Discard old results** - v1.0 synergy scores were incorrect
- ✅ **Understand limitations** - Current data only detects ≥10% synergies
- ✅ **Plan data collection** - Need 10,000+ matches for 3-5% synergy detection

---

## Support

For questions or issues:
- Documentation: [STATISTICS.md](STATISTICS.md) - Detailed methodology
- Troubleshooting: [troubleshooting.md](troubleshooting.md) - Common issues
- Specification: `agent-os/specs/2025-10-15-improved-synergy-analysis/spec.md`

---

## Summary

The v2.0 synergy analysis methodology:

✅ **Fixes** fundamental mathematical error in baseline calculation
✅ **Reports** realistic synergy scores (±3-7% instead of ±25-30%)
✅ **Adds** rigorous statistical testing with confidence intervals and p-values
✅ **Educates** users about sample size requirements and limitations
✅ **Maintains** backward compatibility for collection and character analysis

The new methodology is statistically defensible and produces honest, interpretable results. Rankings remain similar to v1.0, but effect magnitudes are now realistic and supported by proper statistical inference.
