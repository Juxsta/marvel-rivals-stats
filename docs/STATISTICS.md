# Statistical Methodology

This document explains the statistical methods used in the Marvel Rivals Stats Analyzer to ensure rigorous and reliable results.

---

## Overview

The analyzer uses industry-standard statistical techniques to calculate win rates and identify hero synergies with proper confidence intervals and minimum sample size requirements.

---

## Win Rate Confidence Intervals

### Wilson Score Interval

We use the **Wilson score confidence interval** to calculate confidence bounds for win rates. This method is superior to the normal approximation for binomial proportions, especially with small sample sizes or extreme probabilities (close to 0% or 100%).

#### Formula

```
For a hero with w wins out of n total games at confidence level α (default: 95%):

p = w / n  (observed win rate)
z = 1.96   (z-score for 95% confidence)

center = (p + z²/2n) / (1 + z²/n)

margin = z × √[p(1-p)/n + z²/4n²] / (1 + z²/n)

lower_bound = center - margin
upper_bound = center + margin
```

#### Why Wilson Score?

- **Normal approximation fails** when sample sizes are small (<30 games) or win rates are extreme (>90% or <10%)
- **Wilson score is robust** across all sample sizes and win rates
- **Recommended by statisticians** for binomial proportions (Agresti & Coull, 1998)

#### Example

For a hero with **50 wins out of 100 games**:
- Observed win rate: 50%
- 95% CI: [39.8%, 60.2%]

This means we're 95% confident the true win rate is between 39.8% and 60.2%.

---

## Stratified Sampling

### Purpose

To ensure our player sample is representative of the entire player base across all skill levels, we use **stratified sampling** by rank tier.

### Method

1. **Define Strata**: 8 rank tiers (Bronze, Silver, Gold, Platinum, Diamond, Master, Grandmaster, Celestial)
2. **Allocate Quotas**: Assign a target number of players per rank tier
3. **Sample Within Strata**: Randomly sample players from each rank's leaderboard
4. **Combine Samples**: Merge all strata to form the final sample

### Default Quotas

| Rank Tier    | Quota | Rationale                          |
|--------------|-------|------------------------------------|
| Bronze       | 50    | Lower population, less variance    |
| Silver       | 75    | Growing population                 |
| Gold         | 100   | High population peak               |
| Platinum     | 100   | High population peak               |
| Diamond      | 75    | Declining population               |
| Master       | 50    | Lower population                   |
| Grandmaster  | 25    | Very small population              |
| Celestial    | 25    | Elite players, small population    |
| **Total**    | **500** |                                  |

### Benefits

- **Representative**: Captures skill variation across all ranks
- **Prevents Bias**: Avoids over-sampling high-population ranks
- **Enables Rank Stratification**: Allows rank-specific analysis

---

## Synergy Analysis Methodology (v2.0)

### Average Baseline Model

**Version 2.0** (October 2025) uses an **average baseline model** to calculate expected win rates for hero pairs:

```
Expected Win Rate = (Hero A's Win Rate + Hero B's Win Rate) / 2
```

**Rationale**: When two heroes are on the same team, their combined performance should reflect the average of their individual capabilities. This is theoretically sound because both heroes contribute to the same outcome (team victory).

### Why Not Multiplicative? (v1.0 Flaw)

Previous versions used a **multiplicative model** that was fundamentally flawed:

```
Expected Win Rate = Hero A's Win Rate × Hero B's Win Rate  [INCORRECT]
```

**The Problem**: This formula calculates the probability that **two independent events both occur**, which is only valid for separate games. Since teammates are in the **same game**, this produces unrealistic baselines:

- Hulk (52%) × Luna Snow (55%) = **28.6% expected** ❌ Too low!
- Average baseline: (52% + 55%) / 2 = **53.5% expected** ✅ Realistic

The multiplicative model artificially inflated synergy scores to ±25-30% when true effects are ±3-7%.

### Synergy Score Calculation

```
Synergy Score = Actual Win Rate - Expected Win Rate
```

**Interpretation**:
- **Positive score** (+0.05): Pair wins 5% more often than expected → **Positive synergy**
- **Zero score** (0.00): Pair wins exactly as expected → **No synergy**
- **Negative score** (-0.05): Pair wins 5% less often than expected → **Negative synergy (anti-synergy)**

### Example (v2.0 Methodology)

**Hulk** (52% solo win rate) and **Luna Snow** (55% solo win rate) play 207 games together with 124 wins:

- **Expected win rate**: (0.52 + 0.55) / 2 = **0.535** (53.5%)
- **Actual win rate**: 124 / 207 = **0.599** (59.9%)
- **Synergy score**: 0.599 - 0.535 = **+0.064** (+6.4% synergy)
- **95% Confidence Interval**: [52.5%, 67.0%]
- **P-value**: 0.142 (not statistically significant at α=0.05)

This suggests a modest positive synergy, but with current sample size (207 games), we cannot claim statistical significance.

### Statistical Enhancements (v2.0)

Beyond fixing the baseline model, v2.0 adds rigorous statistical testing:

1. **Wilson Confidence Intervals**: 95% CIs for actual win rates
2. **Binomial Significance Tests**: P-values for each synergy vs. expected baseline
3. **Bonferroni Correction**: Controls false positives when testing multiple pairs
4. **Sample Size Warnings**: Flags results with insufficient data (<100, 100-500, ≥500 games)
5. **Power Analysis**: Calculates required sample sizes to detect 3%, 5%, 10% synergies

### Sample Size Requirements

To achieve **80% statistical power** at α=0.05:

| True Synergy Effect | Games Required | Current Feasibility |
|---------------------|----------------|---------------------|
| ±3% | 1,692 games | ❌ Need 8× more data |
| ±5% | 606 games | ❌ Need 3× more data |
| ±10% | 149 games | ✅ Can detect with current data |

With typical datasets (100-300 games per pair), we can only reliably detect large synergies (≥10%). Realistic synergies (3-7%) require massive data collection.

### Confidence Levels

Results are labeled by confidence level based on sample size:

- **High Confidence**: ≥500 games together (narrow CIs, reliable)
- **Medium Confidence**: 100-499 games (moderate CIs, cautious interpretation)
- **Low Confidence**: <100 games (wide CIs, unreliable - excluded by default)

### Limitations

- **True synergies are small**: Even strong pairs show only ±5-10% effects
- **Large samples needed**: Detecting 3-5% synergies requires 1,000+ games
- **No causality**: Positive synergy doesn't prove hero abilities interact (could be playstyle correlation)
- **Multiple comparisons**: Testing 10+ pairs per hero increases false positive risk (addressed by Bonferroni correction)

---

## Minimum Sample Size Requirements

We enforce minimum sample sizes to avoid reporting unreliable statistics:

| Analysis Type          | Minimum Games | Rationale                              |
|------------------------|---------------|----------------------------------------|
| Per-rank win rate      | 30 games      | Statistical power for 95% CI           |
| Overall win rate       | 100 games     | Higher bar for aggregate statistics    |
| Synergy pair           | 50 games      | Sufficient to detect meaningful effects|

### Rationale

- **Statistical Power**: With <30 games, confidence intervals are too wide to be useful
- **False Positives**: Small samples produce unreliable extremes (e.g., 5-0 record = 100% win rate)
- **Practical Utility**: Users care about heroes they'll encounter frequently, not rare picks

### Exclusion Handling

- Heroes below the threshold are **excluded from results**
- JSON exports **do not include** low-sample heroes
- Database still **caches all data** for future re-analysis

---

## Rank Stratification

### Purpose

Win rates vary significantly by rank tier. A hero strong in Bronze may be weak in Grandmaster. Rank stratification provides skill-level-specific insights.

### Method

For each hero, we calculate **separate win rates** for each rank tier where the hero has ≥30 games.

### Example Output

```json
{
  "Spider-Man": {
    "overall": {
      "win_rate": 0.5524,
      "total_games": 1247
    },
    "by_rank": {
      "Bronze": {"win_rate": 0.4856, "total_games": 89},
      "Gold": {"win_rate": 0.5769, "total_games": 234},
      "Diamond": {"win_rate": 0.5912, "total_games": 156}
    }
  }
}
```

This shows Spider-Man's win rate increases with rank (48.6% → 59.1%).

---

## Data Quality Considerations

### Rank Staleness

- **Issue**: Player ranks may become stale if they stop playing
- **Mitigation**: We use the rank at discovery time, which is recent
- **Future**: Could re-fetch ranks periodically

### Match Deduplication

- **Issue**: Each match appears in multiple players' histories
- **Solution**: Store matches once by `match_id`
- **Verification**: Foreign key constraints prevent orphaned participants

### Outlier Detection

We do **not** currently filter outliers, but future enhancements could:
- Remove matches with suspicious K/D ratios (e.g., 100/0)
- Flag heroes with abnormal win rate swings
- Detect and exclude smurfs or boosted accounts

---

## References

### Academic Sources

- **Agresti, A., & Coull, B. A. (1998)**. "Approximate is better than 'exact' for interval estimation of binomial proportions." *The American Statistician*, 52(2), 119-126.
  - Recommends Wilson score interval for binomial proportions

- **Wilson, E. B. (1927)**. "Probable inference, the law of succession, and statistical inference." *Journal of the American Statistical Association*, 22(158), 209-212.
  - Original Wilson score interval paper

- **Brown, L. D., Cai, T. T., & DasGupta, A. (2001)**. "Interval estimation for a binomial proportion." *Statistical Science*, 16(2), 101-133.
  - Comprehensive comparison of confidence interval methods

### Implementation

- **scipy.stats.norm.ppf**: Used for z-score calculation (1.96 for 95% confidence)
- **PostgreSQL**: Database caching for fast retrieval
- **Python**: All statistical calculations in `src/utils/statistics.py`

---

## Changelog

- **2025-10-15 (v2.0)**: Fixed fundamental flaw in synergy baseline model. Replaced multiplicative with average baseline. Added confidence intervals, p-values, Bonferroni correction, sample size warnings, and power analysis.
- **2025-10-15 (v1.0)**: Initial statistical methodology documentation with Wilson score confidence intervals for character win rates and multiplicative baseline for synergies (later found to be flawed).
- **Future**: Plan to add Bayesian win rate estimation for low-sample heroes

---

## Questions?

For questions about the statistical methodology, see:
- Source code: `src/utils/statistics.py`
- Tests: `tests/test_analyzers/test_character_winrate.py`
- Specification: `docs/specs/SPEC-005-character-analysis.md`
