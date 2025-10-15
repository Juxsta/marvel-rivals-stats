# SPEC-001: Player Discovery System

**Status**: Approved
**Author**: Development Team
**Created**: 2025-10-15
**Updated**: 2025-10-15

---

## Problem Statement

To analyze character win rates and team compositions, we need a representative sample of players across all rank tiers. Manually collecting player usernames is not scalable, and we need an automated way to discover players that:
- Covers all rank tiers (Bronze → Celestial)
- Avoids sampling bias
- Respects API rate limits
- Is reproducible

## Goals

1. Discover 500+ players across all rank tiers using stratified sampling
2. Store discovered players in database with rank information
3. Track discovery progress and avoid duplicates
4. Enable quota-based sampling (e.g., 100 Gold players, 50 Master players)
5. Support multiple discovery methods (leaderboards, hero-specific, snowball)

## Non-Goals

- Real-time player tracking (one-time discovery is sufficient)
- Player skill assessment beyond rank tier
- Player profile details (focus on match history)
- Social graph analysis

## User Stories

**As a data analyst, I want to discover a diverse set of players so that my analysis represents the full player population.**

**As a developer, I want the discovery process to be resumable so that API failures don't require starting over.**

## Proposed Solution

### Overview

Build a player discovery script that:
1. Queries player leaderboard API for top players
2. Queries hero leaderboards for hero-specific top players
3. Applies stratified random sampling to meet rank quotas
4. Stores discovered players in database
5. Marks players for match history collection

### Technical Design

#### Data Model

```python
# Already exists in schema:
# players table (username, rank_tier, rank_score, discovered_at, match_history_fetched)

# Add to collection_metadata:
# - 'discovery_status': 'in_progress' | 'completed'
# - 'last_discovery_run': timestamp
# - 'target_player_count': number
```

#### API Endpoints Used

```python
api.get_player_leaderboard(limit=1000)
# Returns: [{"username": str, "rank": str, "rank_score": int}, ...]

api.get_hero_leaderboard(hero_id, limit=50)
# Returns: [{"username": str, "hero": str, "rank": str}, ...]
```

#### Algorithm

```python
def discover_players(target_count=500, rank_quotas=None):
    """
    Discover players using stratified sampling

    Args:
        target_count: Total players to discover
        rank_quotas: Dict[rank_tier, count] - players per rank

    Returns:
        int: Number of new players discovered
    """

    # 1. Fetch player leaderboard
    leaderboard_players = api.get_player_leaderboard(limit=1000)

    # 2. Fetch hero leaderboards for diversity
    hero_players = []
    for hero_id in TOP_10_HEROES:
        hero_players.extend(api.get_hero_leaderboard(hero_id, limit=50))

    # 3. Combine and deduplicate
    all_players = deduplicate_by_username(leaderboard_players + hero_players)

    # 4. Group by rank tier
    players_by_rank = group_by_rank(all_players)

    # 5. Apply quotas (stratified sampling)
    selected_players = []
    for rank, quota in rank_quotas.items():
        rank_pool = players_by_rank.get(rank, [])
        sampled = random.sample(rank_pool, min(quota, len(rank_pool)))
        selected_players.extend(sampled)

    # 6. Store in database
    for player in selected_players:
        db.insert_player(
            username=player['username'],
            rank_tier=player['rank'],
            rank_score=player['rank_score']
        )

    # 7. Update metadata
    db.set_metadata('discovery_status', 'completed')
    db.set_metadata('players_discovered', len(selected_players))

    return len(selected_players)
```

### Default Rank Quotas

```python
DEFAULT_RANK_QUOTAS = {
    'Bronze': 50,
    'Silver': 75,
    'Gold': 100,
    'Platinum': 100,
    'Diamond': 75,
    'Master': 50,
    'Grandmaster': 25,
    'Celestial': 25
}
# Total: 500 players
```

### Alternative Approaches Considered

**Approach 1: Random sampling from leaderboard only**
- ❌ Rejected: Would bias toward high-rank players

**Approach 2: Snowball sampling from match histories first**
- ❌ Rejected: Can't stratify by rank until after collection

**Approach 3: Equal quotas for all ranks**
- ❌ Rejected: Doesn't match player population distribution

## Dependencies

- Marvel Rivals API client (`src/api/client.py`) ✅
- Database connection (`src/db/connection.py`) ✅
- `players` table schema ✅

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API returns insufficient players for some ranks | Medium | Lower quotas for rare ranks, document sample sizes |
| API leaderboard data is stale | Low | Filter out inactive players in match collection phase |
| Duplicate players across methods | Low | Deduplicate by username before insertion |
| Rate limits during discovery | Medium | Add delays, make resumable, cache API responses |

## Success Criteria

- [ ] Script discovers 400+ players (80% of target)
- [ ] At least 5 players per rank tier (minimum sample)
- [ ] All players have rank_tier populated
- [ ] No duplicate players in database
- [ ] Process completes within API rate limits
- [ ] Progress is tracked and resumable

## Testing Plan

### Unit Tests
- Test deduplication logic
- Test rank grouping
- Test quota sampling (with mock data)

### Integration Tests
- Test with real API (10 player sample)
- Verify database insertion
- Check metadata tracking

### Manual Verification
- Run discovery with limit=50
- Verify rank distribution
- Check database state

## Implementation Tasks

- [ ] Create `src/collectors/player_discovery.py` module
  - [ ] Implement `fetch_leaderboard_players()`
  - [ ] Implement `fetch_hero_leaderboard_players()`
  - [ ] Implement `deduplicate_players()`
  - [ ] Implement `group_by_rank()`
  - [ ] Implement `stratified_sample()`
- [ ] Create `src/utils/sampling.py` helper
  - [ ] Implement rank quota configuration
  - [ ] Implement random sampling utilities
- [ ] Create `scripts/discover_players.py` CLI
  - [ ] Add argparse for quotas, limits
  - [ ] Add progress reporting
  - [ ] Add metadata tracking
  - [ ] Add error handling and resume logic
- [ ] Update database with metadata columns
  - [ ] Add discovery tracking to `collection_metadata`
- [ ] Write tests
  - [ ] Unit tests for sampling logic
  - [ ] Integration test with 10 players
- [ ] Documentation
  - [ ] Update README with discovery usage
  - [ ] Document rank quotas rationale

## Timeline

- **Effort**: 4-6 hours
- **Target completion**: 2025-10-16

## Open Questions

1. ✅ How do we handle players with no rank (unranked)?
   - **Answer**: Skip unranked players, focus on competitive only
2. ✅ Should we re-run discovery to refresh player pool?
   - **Answer**: Not in MVP, but design for it (add last_discovery_run tracking)
3. ✅ What if leaderboard API doesn't return rank_score?
   - **Answer**: Store NULL, can infer from rank_tier if needed

## References

- `PLAN.md` - Overall project plan
- `src/db/schema.sql` - Database schema
- `src/api/client.py` - API client implementation
- [Marvel Rivals API Docs](https://docs.marvelrivalsapi.com)
