# SPEC-003: Character Win Rate Analysis

**Status**: Approved
**Author**: Development Team
**Created**: 2025-10-15
**Updated**: 2025-10-15

---

## Problem Statement

With match data collected (SPEC-002), we need to analyze character performance by calculating win rates stratified by rank tier. The analysis must be:
- Statistically rigorous (minimum sample sizes, confidence intervals)
- Rank-stratified (separate stats for Bronze, Silver, Gold, etc.)
- Exportable (JSON format for sharing/integration)
- Reproducible (cacheable results)

## Goals

1. Calculate win rates for all 40+ heroes
2. Stratify results by rank tier
3. Calculate confidence intervals (Wilson score, 95%)
4. Filter for minimum sample size (30 games per tier)
5. Export results to JSON
6. Cache results in database for fast retrieval

## Non-Goals

- Real-time/live win rate tracking
- Player-specific performance analysis
- Hero matchup analysis (counter-picks)
- Build/loadout recommendations

## User Stories

**As a competitive player, I want to see which heroes have the highest win rates at my rank so I can make informed picks.**

**As a content creator, I want exportable win rate data so I can create tier lists and guides.**

## Proposed Solution

### Overview

Build an analysis script that:
1. Queries match_participants table for each hero
2. Groups by rank tier (using player rank from matches)
3. Calculates wins, losses, win rate
4. Computes 95% confidence intervals
5. Filters out low-sample-size results
6. Caches in character_stats table
7. Exports to JSON

### Technical Design

#### Statistical Methodology

**Win Rate Calculation**:
```python
win_rate = wins / (wins + losses)
```

**Confidence Interval** (Wilson Score):
```python
from scipy.stats import norm

def wilson_confidence_interval(wins, total, confidence=0.95):
    """
    Calculate Wilson score confidence interval

    More accurate than normal approximation for small samples
    """
    if total == 0:
        return (0, 0)

    p = wins / total
    z = norm.ppf(1 - (1 - confidence) / 2)  # 1.96 for 95%
    denominator = 1 + z**2 / total

    center = (p + z**2 / (2*total)) / denominator
    margin = z * ((p * (1 - p) / total + z**2 / (4 * total**2)) ** 0.5) / denominator

    return (max(0, center - margin), min(1, center + margin))
```

**Sample Size Filter**:
- Minimum 30 games per rank tier to report
- Overall stats require 100+ games across all ranks

#### Algorithm

```python
def analyze_character_win_rates(hero_name=None, min_games=30):
    """
    Analyze win rates for one or all characters

    Args:
        hero_name: Specific hero (None = all heroes)
        min_games: Minimum games required per rank

    Returns:
        dict: Analysis results
    """

    heroes = [hero_name] if hero_name else get_all_heroes()

    results = {}

    for hero in heroes:
        # Query: Get all matches for this hero
        query = """
            SELECT
                mp.won,
                p.rank_tier
            FROM match_participants mp
            JOIN players p ON mp.username = p.username
            WHERE mp.hero_name = ?
              AND p.rank_tier IS NOT NULL
        """
        rows = db.conn.execute(query, (hero,)).fetchall()

        if len(rows) < min_games:
            continue  # Skip low-sample heroes

        # Group by rank
        by_rank = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for row in rows:
            won = row['won']
            rank = row['rank_tier']

            if won:
                by_rank[rank]['wins'] += 1
            else:
                by_rank[rank]['losses'] += 1

        # Calculate stats per rank
        rank_stats = {}
        for rank, data in by_rank.items():
            total = data['wins'] + data['losses']

            if total < min_games:
                continue  # Skip low-sample ranks

            win_rate = data['wins'] / total
            ci_low, ci_high = wilson_confidence_interval(data['wins'], total)

            rank_stats[rank] = {
                'total_games': total,
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': round(win_rate, 4),
                'confidence_interval_95': [round(ci_low, 4), round(ci_high, 4)]
            }

            # Cache in DB
            db.cache_character_stat(
                hero_name=hero,
                rank_tier=rank,
                total_games=total,
                wins=data['wins'],
                losses=data['losses'],
                win_rate=win_rate
            )

        # Calculate overall (all ranks)
        total_wins = sum(d['wins'] for d in by_rank.values())
        total_losses = sum(d['losses'] for d in by_rank.values())
        total_games = total_wins + total_losses

        if total_games >= 100:  # Higher bar for overall
            overall_wr = total_wins / total_games
            ci_low, ci_high = wilson_confidence_interval(total_wins, total_games)

            overall_stats = {
                'total_games': total_games,
                'wins': total_wins,
                'losses': total_losses,
                'win_rate': round(overall_wr, 4),
                'confidence_interval_95': [round(ci_low, 4), round(ci_high, 4)]
            }

            # Cache overall
            db.cache_character_stat(
                hero_name=hero,
                rank_tier='_all',
                total_games=total_games,
                wins=total_wins,
                losses=total_losses,
                win_rate=overall_wr
            )
        else:
            overall_stats = None

        results[hero] = {
            'hero': hero,
            'overall': overall_stats,
            'by_rank': rank_stats,
            'analyzed_at': datetime.now().isoformat()
        }

    return results
```

#### JSON Export Format

```json
{
  "Spider-Man": {
    "hero": "Spider-Man",
    "overall": {
      "total_games": 1247,
      "wins": 689,
      "losses": 558,
      "win_rate": 0.5524,
      "confidence_interval_95": [0.5245, 0.5801]
    },
    "by_rank": {
      "Bronze": {
        "total_games": 89,
        "wins": 45,
        "losses": 44,
        "win_rate": 0.5056,
        "confidence_interval_95": [0.4021, 0.6088]
      },
      "Gold": {
        "total_games": 234,
        "wins": 135,
        "losses": 99,
        "win_rate": 0.5769,
        "confidence_interval_95": [0.5129, 0.6389]
      }
      // ... other ranks
    },
    "analyzed_at": "2025-10-15T14:30:00Z"
  }
  // ... other heroes
}
```

### Alternative Approaches Considered

**Approach 1: Simple win/loss counts without confidence intervals**
- ❌ Rejected: Not statistically rigorous, misleading for small samples

**Approach 2: Use normal approximation for CI**
- ❌ Rejected: Inaccurate for small samples, Wilson score is better

**Approach 3: Weight ranks by player population**
- ❌ Rejected: Don't have population data, stratification is clearer

## Dependencies

- Match collection (SPEC-002) completed
- `scipy` for statistical functions
- Players table with rank_tier populated

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient sample sizes for rare heroes | Medium | Document sample sizes, filter out low-confidence results |
| Player rank data missing/stale | Medium | Filter WHERE rank_tier IS NOT NULL, document data quality |
| Confidence interval calculation errors | High | Use well-tested scipy library, add unit tests |
| Results misinterpreted by users | Medium | Include confidence intervals, document methodology |

## Success Criteria

- [ ] All heroes with 100+ games analyzed
- [ ] Win rates calculated for all rank tiers with 30+ games
- [ ] Confidence intervals calculated correctly
- [ ] Results cached in database
- [ ] JSON export created
- [ ] Results match manual calculations (spot check)

## Testing Plan

### Unit Tests
- Test Wilson confidence interval calculation
- Test rank grouping logic
- Test minimum sample filtering

### Integration Tests
- Run analysis on seed data
- Verify database caching
- Check JSON export format

### Manual Verification
- Calculate win rate manually for 1 hero
- Compare with script output
- Verify confidence intervals make sense

## Implementation Tasks

- [ ] Install scipy dependency
  - [ ] Add to `requirements.txt`
- [ ] Create `src/analyzers/character_winrate.py` module
  - [ ] Implement `wilson_confidence_interval()`
  - [ ] Implement `analyze_character_win_rates()`
  - [ ] Implement `get_all_heroes()` helper
  - [ ] Implement JSON export function
- [ ] Create `src/db/connection.py` query helpers
  - [ ] Add `get_hero_matches_by_rank()`
  - [ ] Add `cache_character_stat()`
- [ ] Create `scripts/analyze_character.py` CLI
  - [ ] Add argparse for hero selection
  - [ ] Add --min-games option
  - [ ] Add --export-json option
  - [ ] Add progress reporting
- [ ] Write tests
  - [ ] Unit tests for statistics
  - [ ] Integration test with sample data
- [ ] Documentation
  - [ ] Update README with analysis usage
  - [ ] Document statistical methodology

## Timeline

- **Effort**: 4-6 hours
- **Target completion**: 2025-10-18

## Open Questions

1. ✅ Should we weight recent matches more heavily?
   - **Answer**: No for MVP, all matches equal weight
2. ✅ How do we handle heroes with < 30 games?
   - **Answer**: Exclude from results, note in documentation
3. ✅ Should we show percentile rankings (vs other heroes)?
   - **Answer**: Not in MVP, just raw win rates

## References

- SPEC-002: Match Collection (prerequisite)
- `PLAN.md` - Statistical approach section
- [Wilson Score Confidence Interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval)
- `src/db/schema.sql` - character_stats table
