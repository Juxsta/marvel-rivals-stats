# SPEC-002: Match History Collection

**Status**: Approved
**Author**: Development Team
**Created**: 2025-10-15
**Updated**: 2025-10-15

---

## Problem Statement

After discovering players (SPEC-001), we need to collect their match histories to build our dataset. The match collection must:
- Handle API rate limits (10k requests/day)
- Deduplicate matches (same match seen from multiple players)
- Be resumable after failures/interruptions
- Extract detailed match participant data
- Filter for current season/competitive mode

## Goals

1. Collect 100-150 recent matches per discovered player
2. Store matches with full participant details (hero, role, stats)
3. Deduplicate matches by match_id
4. Track collection progress per player
5. Respect API rate limits with delays
6. Support pause/resume without data loss

## Non-Goals

- Historical match data (focus on current season)
- Match replay analysis
- Real-time match tracking
- Per-match detailed stats (focus on team composition and outcome)

## User Stories

**As a data analyst, I want to collect match data efficiently so that I can analyze team compositions without hitting rate limits.**

**As a developer, I want the collection process to be resumable so that I can stop and restart without losing progress.**

## Proposed Solution

### Overview

Build a match collection script that:
1. Loads all players where `match_history_fetched = FALSE`
2. For each player:
   - Fetch match history (paginated, 150 matches)
   - Extract match metadata (id, mode, season, timestamp)
   - Extract all participants (heroes, roles, stats, team, outcome)
   - Insert into database (with deduplication)
   - Mark player as collected
3. Rate limit between requests
4. Log progress and handle errors gracefully

### Technical Design

#### Data Flow

```
Player (username)
  → API.get_match_history()
  → List[Match]
  → For each match:
      → Check if match_id exists in DB
      → If new: Insert match + all participants
      → If exists: Skip (already collected from another player)
  → Mark player.match_history_fetched = TRUE
```

#### API Response Structure

```python
# API returns:
{
  "matches": [
    {
      "match_id": "abc123",
      "mode": "competitive",
      "season": 9,
      "timestamp": "2025-10-15T10:30:00Z",
      "teams": [
        {
          "team": 0,
          "won": True,
          "players": [
            {
              "username": "player1",
              "hero_id": 1014,
              "hero_name": "The Punisher",
              "role": "duelist",
              "kills": 15,
              "deaths": 3,
              "assists": 5,
              "damage": 25000,
              "healing": 0
            },
            # ... 5 more players
          ]
        },
        {
          "team": 1,
          "won": False,
          "players": [ ... ]
        }
      ]
    },
    # ... more matches
  ]
}
```

#### Algorithm

```python
def collect_matches(batch_size=100, delay_ms=1000):
    """
    Collect match histories for all pending players

    Args:
        batch_size: Max players to process in this run
        delay_ms: Milliseconds to wait between API requests

    Returns:
        dict: Collection statistics
    """

    # 1. Load pending players
    pending_players = db.get_players_where(match_history_fetched=False)
    pending_players = pending_players[:batch_size]

    stats = {
        'players_processed': 0,
        'matches_collected': 0,
        'matches_skipped': 0,  # Already in DB
        'errors': 0
    }

    # 2. Process each player
    for player in pending_players:
        try:
            # 3. Fetch match history
            matches = api.get_player_match_history(
                player.username,
                limit=150
            )

            # 4. Filter for current season + competitive
            matches = filter_matches(matches, season=CURRENT_SEASON, mode='competitive')

            # 5. Process each match
            for match in matches:
                if db.match_exists(match['match_id']):
                    stats['matches_skipped'] += 1
                    continue

                # 6. Insert match
                db.insert_match(
                    match_id=match['match_id'],
                    mode=match['mode'],
                    season=match['season'],
                    timestamp=match.get('timestamp')
                )

                # 7. Insert all participants
                for team_data in match['teams']:
                    team_num = team_data['team']
                    won = team_data['won']

                    for participant in team_data['players']:
                        db.insert_match_participant(
                            match_id=match['match_id'],
                            username=participant['username'],
                            hero_id=participant['hero_id'],
                            hero_name=participant['hero_name'],
                            role=participant['role'],
                            team=team_num,
                            won=won,
                            kills=participant.get('kills', 0),
                            deaths=participant.get('deaths', 0),
                            assists=participant.get('assists', 0),
                            damage=participant.get('damage', 0),
                            healing=participant.get('healing', 0)
                        )

                stats['matches_collected'] += 1

            # 8. Mark player as collected
            db.update_player(
                player.username,
                match_history_fetched=True,
                last_updated=datetime.now()
            )

            stats['players_processed'] += 1

            # 9. Rate limiting
            time.sleep(delay_ms / 1000.0)

        except Exception as e:
            log_error(f"Failed to collect matches for {player.username}: {e}")
            stats['errors'] += 1
            continue  # Don't mark as collected on error

    # 10. Update metadata
    db.set_metadata('last_collection_run', datetime.now())
    db.set_metadata('total_matches_collected',
        db.count('matches'))

    return stats
```

#### Database Queries

```python
# Check if match exists
def match_exists(match_id: str) -> bool:
    return db.conn.execute(
        "SELECT 1 FROM matches WHERE match_id = ?",
        (match_id,)
    ).fetchone() is not None

# Insert match
def insert_match(match_id, mode, season, timestamp):
    db.conn.execute("""
        INSERT OR IGNORE INTO matches (match_id, mode, season, timestamp)
        VALUES (?, ?, ?, ?)
    """, (match_id, mode, season, timestamp))

# Insert participant
def insert_match_participant(**kwargs):
    db.conn.execute("""
        INSERT OR IGNORE INTO match_participants
        (match_id, username, hero_id, hero_name, role, team, won,
         kills, deaths, assists, damage, healing)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(kwargs.values()))
```

### Alternative Approaches Considered

**Approach 1: Collect all players sequentially without batching**
- ❌ Rejected: No pause capability, long-running process

**Approach 2: Store raw API JSON and parse later**
- ❌ Rejected: Adds complexity, harder to deduplicate

**Approach 3: Parallel collection with threading**
- ❌ Rejected: Rate limiting would be complex, overkill for MVP

## Dependencies

- Marvel Rivals API client ✅
- Database with schema ✅
- Player discovery (SPEC-001) must run first
- Current season defined in config

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API returns incomplete match data | Medium | Validate required fields, skip invalid matches |
| Rate limit exceeded | High | Enforce delays, track request count, resume on error |
| Database transaction failures | Medium | Commit per match, handle duplicates with OR IGNORE |
| Player username changes | Low | Store by username as provided, accept some stale data |
| Large number of API failures | High | Log errors, mark players as failed, retry mechanism |

## Success Criteria

- [ ] Collect 50,000+ unique matches
- [ ] At least 80% of players have matches collected
- [ ] All matches have 12 participants (6v6)
- [ ] Deduplication works (no duplicate match_ids)
- [ ] Process respects rate limits
- [ ] Collection can be resumed after interruption
- [ ] Progress is logged and visible

## Testing Plan

### Unit Tests
- Test match deduplication logic
- Test participant extraction
- Test filtering (season, mode)

### Integration Tests
- Test with 5 players
- Verify matches inserted correctly
- Check participant counts
- Verify player marked as collected

### Manual Verification
- Run collection with batch_size=10
- Check database: `SELECT COUNT(*) FROM matches`
- Check participants: `SELECT COUNT(*) FROM match_participants`
- Verify no duplicates: `SELECT match_id, COUNT(*) FROM matches GROUP BY match_id HAVING COUNT(*) > 1`

## Implementation Tasks

- [ ] Create `src/collectors/match_collector.py` module
  - [ ] Implement `collect_matches()` main function
  - [ ] Implement `filter_matches()` for season/mode
  - [ ] Implement `extract_participants()` parser
  - [ ] Implement error handling and logging
- [ ] Create `src/db/connection.py` helper methods
  - [ ] Add `get_players_where()`
  - [ ] Add `match_exists()`
  - [ ] Add `insert_match()`
  - [ ] Add `insert_match_participant()`
  - [ ] Add `update_player()`
- [ ] Create `scripts/collect_matches.py` CLI
  - [ ] Add argparse for batch_size, delay
  - [ ] Add progress bar (optional)
  - [ ] Add stats reporting
  - [ ] Add resume capability
- [ ] Update `config/config.py`
  - [ ] Add CURRENT_SEASON constant
  - [ ] Add rate limit settings
- [ ] Write tests
  - [ ] Unit tests for filtering and parsing
  - [ ] Integration test with sample data
- [ ] Documentation
  - [ ] Update README with collection usage
  - [ ] Document rate limit recommendations

## Timeline

- **Effort**: 6-8 hours
- **Target completion**: 2025-10-17

## Open Questions

1. ✅ What if match history API pagination is broken?
   - **Answer**: Request all in one call (limit=150), if API supports it
2. ✅ Should we store private/casual matches too?
   - **Answer**: No, filter for competitive mode only
3. ✅ How do we handle players with private profiles?
   - **Answer**: API call will fail, log error, mark as failed
4. ❓ Should we re-collect match histories periodically?
   - **Answer**: Not in MVP, but add last_updated tracking for future

## References

- SPEC-001: Player Discovery (prerequisite)
- `PLAN.md` - Data collection strategy
- `src/db/schema.sql` - matches and match_participants tables
- [Marvel Rivals API Docs](https://docs.marvelrivalsapi.com)
