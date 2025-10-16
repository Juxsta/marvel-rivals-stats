# How to Achieve Statistical Significance in Synergy Detection

**Date:** 2025-10-15
**Analysis of:** Hulk synergies with current dataset (286 matches)

---

## Executive Summary

**Current Status:** ❌ No synergies reach statistical significance with proper methodology

**Why:**
- Sample sizes too small (50-200 games per pair)
- True effect sizes likely small (2-5%)
- Multiple comparisons problem (testing 10+ pairs)

**Solution:** Multiple strategies available depending on goals and constraints

---

## The Power Analysis Results

### Sample Sizes Needed to Detect Synergies (80% power, α=0.05)

| True Effect Size | Games Needed Per Pair | Current Max | Feasible? |
|------------------|----------------------|-------------|-----------|
| **±1%** | **15,279 games** | 207 | ❌ |
| **±2%** | **3,813 games** | 207 | ❌ |
| **±3%** | **1,692 games** | 207 | ❌ |
| **±5%** | **606 games** | 207 | ❌ |
| **±10%** | **149 games** | 207 | ✅ |

**Reality Check:** We can currently only detect unrealistically large synergies (≥10%).

---

## Strategy 1: Collect Massively More Data 📊

**Goal:** Detect 3-5% synergies reliably

### What You Need

- **10,000-50,000 total matches** (vs current 286)
- **1,000-2,000 games per hero pair** (vs current 50-200)
- **Continuous data collection** over 3-6 months

### Implementation

```python
# Scale up data collection
def continuous_collection():
    while True:
        # Discover 500 new players daily
        discover_players(target=500)

        # Collect matches (rate-limited)
        collect_matches(batch_size=500)

        # Re-analyze weekly
        if days % 7 == 0:
            analyze_characters()
            analyze_synergies()

        sleep(86400)  # Run daily
```

### Pros & Cons

✅ **Pros:**
- Gold standard approach
- Detects small real effects
- Enables subgroup analysis (by rank, map, etc.)

❌ **Cons:**
- Requires months of data collection
- API rate limits slow process
- Storage/compute costs increase

### Expected Results

With 10,000 matches:
- **Hulk+Star-Lord:** ~800 games together → Can detect ±4% synergy
- **Hulk+Doctor Strange:** ~1,500 games → Can detect ±3% synergy
- **Hulk+Luna Snow:** ~1,800 games → Can detect ±3% synergy

---

## Strategy 2: Within-Player Paired Analysis 🎯

**Goal:** Control for player skill, reduce variance

### Current Promising Results

From our analysis (n=3 players):

| Pairing | Difference | P-value | Significant? |
|---------|-----------|---------|--------------|
| Hulk + Star-Lord | **+18.3%** | 0.183 | Not yet |
| Hulk + Black Widow | **+11.7%** | 0.129 | Not yet |
| Hulk + Doctor Strange | **+8.6%** | 0.135 | Not yet |

**These are HUGE effects!** But with only 3 players, we lack power.

### What You Need

- **30-50 players** who play Hulk with multiple heroes
- Each player needs 10+ games with target hero and 10+ with comparison heroes

### Implementation

```python
def within_player_synergy(hero_a, hero_b, min_games=10):
    """
    For each player who plays hero_a:
    1. Calculate their WR when paired with hero_b
    2. Calculate their WR when paired with other heroes
    3. Paired t-test on the differences
    """
    players = get_players_with_both(hero_a, hero_b, min_games)

    if len(players) >= 30:
        # Adequate power for paired t-test
        differences = []
        for player in players:
            wr_with_b = player.wr_with(hero_a, hero_b)
            wr_with_others = player.wr_with(hero_a, exclude=hero_b)
            differences.append(wr_with_b - wr_with_others)

        t, p = ttest_rel(differences, [0] * len(differences))
        return {"effect": mean(differences), "p_value": p}
```

### Pros & Cons

✅ **Pros:**
- Controls for player skill (biggest confounder)
- More power with fewer total games
- Strong causal inference

❌ **Cons:**
- Requires diverse player pool
- Not all players play multiple heroes
- Still needs 300-500 games per hero pair

### Expected Results

With 30 players:
- **Hulk+Star-Lord:** If true effect is +10%, would reach p<0.05
- **Hulk+Doctor Strange:** If true effect is +8%, would reach p<0.05

---

## Strategy 3: Bayesian Hierarchical Modeling 📈

**Goal:** Share information across hero pairs, increase power

### Current Results

Bayesian analysis with weakly informative priors:

| Pairing | P(Positive Synergy) | Substantial? |
|---------|---------------------|--------------|
| Hulk + Star-Lord | 85.9% | No (need >95%) |
| Hulk + Black Widow | 79.1% | No |
| Hulk + Doctor Strange | 80.2% | No |

**Close, but not quite there.**

### What You Need

- **Stronger priors** based on:
  - Expected synergies for role combinations (Tank+Healer, DPS+DPS, etc.)
  - Historical data from previous patches
  - Expert knowledge about hero abilities

- **Hierarchical model:**
  ```
  synergy_ij ~ Normal(μ_role_combination, σ_synergy)
  μ_vanguard_strategist ~ Normal(0.05, 0.02)  # Tanks+Healers typically synergize
  μ_duelist_duelist ~ Normal(0.00, 0.02)     # DPS+DPS less synergy
  ```

### Implementation

```python
# PyMC3 or Stan model
with pm.Model() as hierarchical_model:
    # Hyperpriors for role combinations
    mu_vanguard_strategist = pm.Normal('mu_v_s', 0.05, 0.02)
    mu_duelist_duelist = pm.Normal('mu_d_d', 0.00, 0.02)

    # Hero pair synergies drawn from role prior
    synergy_hulk_luna = pm.Normal('hulk_luna',
                                   mu_vanguard_strategist,
                                   sigma_synergy)

    # Likelihood
    wins_observed = pm.Binomial('wins',
                                 n=games_together,
                                 p=expected_wr + synergy_hulk_luna,
                                 observed=wins_data)

    trace = pm.sample(2000)
```

### Pros & Cons

✅ **Pros:**
- Uses all available data efficiently
- Regularizes extreme estimates
- Provides full uncertainty quantification

❌ **Cons:**
- Complex to implement and explain
- Requires domain expertise for priors
- Computationally intensive

### Expected Results

- Credible intervals narrow by ~20-30%
- P(positive synergy) increases to ~90-95% for top pairs
- Better rankings, still uncertain magnitudes

---

## Strategy 4: Focus on Large, Obvious Synergies 🎖️

**Goal:** Only claim significance for undeniable synergies

### Approach

1. **Use conservative thresholds:**
   - Require p < 0.005 (Bonferroni corrected for 10 tests)
   - Require effect size > 5%
   - Require confidence interval fully above 0%

2. **Focus on mechanistic synergies:**
   - Tank + Healer (obvious synergy)
   - Dive DPS + Dive Tank (coordinated engages)
   - AOE damage + CC (combos)

3. **Test fewer hypotheses:**
   - Pre-specify 3-5 expected synergies
   - Don't test all possible pairs
   - Reduces multiple comparisons problem

### Implementation

```python
# Pre-specify expected strong synergies
HYPOTHESIZED_SYNERGIES = [
    ('Hulk', 'Luna Snow', 'Tank+Healer'),
    ('Hulk', 'Doctor Strange', 'Tank+Healer'),
    ('Spider-Man', 'Luna Snow', 'Dive+Healer'),
]

# Test only these (α = 0.05/3 = 0.017)
for hero_a, hero_b, reason in HYPOTHESIZED_SYNERGIES:
    result = test_synergy(hero_a, hero_b, alpha=0.017)
    if result.significant and result.effect_size > 0.05:
        print(f"CONFIRMED: {hero_a} + {hero_b} synergize ({reason})")
```

### Pros & Cons

✅ **Pros:**
- Fewer false positives
- Higher confidence in reported synergies
- Aligned with game mechanics

❌ **Cons:**
- Misses unexpected synergies
- Only detects large effects
- Less discovery-oriented

### Expected Results

- 0-2 synergies reach strict significance threshold
- High confidence in those that do
- Clear, defensible claims

---

## Strategy 5: Machine Learning Baseline 🤖

**Goal:** Better expected win rate predictions

### Current Problem

Our expected WR models are too simple:
- **Multiplicative:** Expected = 0.32 (way too low)
- **Additive:** Expected = 0.64 (okay but simplistic)
- **Average:** Expected = 0.57 (reasonable)

None account for:
- Full team composition (other 4 heroes)
- Enemy team composition
- Map
- Player skill beyond rank tier

### Better Baseline

Train an ML model:

```python
from sklearn.ensemble import GradientBoostingClassifier

# Features for each game
X = [
    team_hero_1_id, team_hero_2_id, ..., team_hero_6_id,
    enemy_hero_1_id, ..., enemy_hero_6_id,
    map_id,
    avg_team_rank_score,
    avg_enemy_rank_score
]

# Target
y = team_won  # Boolean

# Train model
model = GradientBoostingClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Predict synergy
def synergy_with_model(hero_a, hero_b, games_together):
    for game in games_together:
        baseline_pred = model.predict_proba(game.features)[0][1]
        actual = game.won
        synergy = actual - baseline_pred

    return mean(synergies)
```

### Pros & Cons

✅ **Pros:**
- Most accurate baseline
- Controls for confounders automatically
- Detects unexpected patterns

❌ **Cons:**
- Requires many features (full match data)
- Black box (hard to interpret)
- Needs 1,000+ matches to train

### Expected Results

- Reduces residual variance by 30-50%
- Increases power without more data
- May reveal synergies missed by simple baselines

---

## Recommended Path Forward

### Short Term (Current Dataset)

1. **Report descriptive statistics only:**
   - "Hulk + Star-Lord have 63.6% WR together (77 games)"
   - "This is 6.7 percentage points above their average solo WRs"
   - "More data needed to confirm statistical significance"

2. **Use Bayesian estimates with wide credible intervals:**
   - Report posterior means and 95% CIs
   - Note that intervals are wide due to limited data

3. **Focus on rankings, not magnitudes:**
   - "Star-Lord appears to be Hulk's best pairing"
   - "But the true synergy size is uncertain (±5-10%)"

### Medium Term (3-6 months)

1. **Implement continuous data collection**
   - Collect 10,000+ matches
   - Target 1,000+ games per major hero pair

2. **Add within-player analysis**
   - Track same players over time
   - Compare paired vs unpaired games

3. **Build ML baseline model**
   - Predict WR from full team comp
   - Use residuals as synergy estimates

### Long Term (6-12 months)

1. **Hierarchical Bayesian models**
   - Share information across role combinations
   - Narrow credible intervals

2. **Causal inference methods**
   - Propensity score matching
   - Difference-in-differences
   - Establish causality, not just correlation

3. **Subgroup analyses**
   - Synergies by rank tier
   - Synergies by map
   - Synergies by patch/meta

---

## Key Takeaways

### The Hard Truth

✅ **Current implementation works correctly** - No bugs in code
❌ **But methodology has fundamental issues:**
- Multiplicative model is theoretically unsound
- Sample sizes too small for reliable inference
- Multiple comparisons inflate false positive rate

### What We Know

1. **Rankings are probably valid:**
   - Hulk+Star-Lord likely is better than Hulk+Thor
   - Relative ordering seems reasonable

2. **Magnitudes are uncertain:**
   - "±30% synergy" is clearly wrong (multiplicative model)
   - "±5% synergy" might be right (additive/average model)
   - But could be anywhere from 0% to ±10%

3. **More data solves everything:**
   - With 10,000 matches, all uncertainty disappears
   - Can detect 3% synergies reliably
   - Can do subgroup analysis

### Pragmatic Recommendation

**For production:**
1. Switch to additive or average baseline model
2. Report point estimates with wide confidence intervals
3. Add disclaimer about statistical power
4. Focus on collecting more data over time

**Example output:**
```
Hulk's Top Synergies:
1. Star-Lord: 63.6% WR together (77 games)
   Estimated synergy: +6.7% (95% CI: -3%, +17%)
   ⚠️ More data needed for confirmation

2. Doctor Strange: 56.5% WR together (177 games)
   Estimated synergy: +3.3% (95% CI: -2%, +9%)
   ⚠️ Likely positive, but not yet statistically significant
```

This is honest, informative, and scientifically defensible.

---

## Conclusion

**Can we reach statistical significance?**

**YES, but you need to:**

1. ✅ **Collect 10-50× more data** (most important)
2. ✅ **Use better baseline models** (ML, team comp aware)
3. ✅ **Apply within-player analysis** (controls skill)
4. ✅ **Use Bayesian methods** (efficient use of data)
5. ✅ **Focus on large synergies** (easier to detect)

**With current data (286 matches):**
- Can detect ≥10% synergies ✅
- Cannot detect 2-5% synergies ❌
- Rankings probably valid ✅
- Magnitudes uncertain ⚠️

**With 10,000 matches:**
- Can detect ≥3% synergies ✅
- Narrow confidence intervals ✅
- Subgroup analysis possible ✅
- Production-ready results ✅

The path forward is clear: **collect more data**. Everything else is incremental improvement.
