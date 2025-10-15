# Marvel Rivals API Documentation

This document describes the assumed structure of the Marvel Rivals API based on common patterns. **Note**: This is a hypothetical API structure used for development. The actual API may differ.

---

## Base URL

```
https://api.marvelrivals.com/v1
```

---

## Authentication

All requests require an API key in the header:

```
Authorization: Bearer YOUR_API_KEY
```

Set your API key in `.env`:
```bash
MARVEL_RIVALS_API_KEY=your_key_here
```

---

## Rate Limits

| Tier | Requests/Minute | Requests/Day |
|------|-----------------|--------------|
| Free | 7               | 10,000       |
| Pro  | 60              | 100,000      |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 7
X-RateLimit-Remaining: 5
X-RateLimit-Reset: 1634567890
```

**429 Response** (rate limit exceeded):
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Endpoints

### 1. General Leaderboard

Retrieve top players across all heroes.

**Endpoint**: `GET /leaderboard`

**Parameters**:
| Parameter | Type    | Required | Default | Description                    |
|-----------|---------|----------|---------|--------------------------------|
| limit     | integer | No       | 100     | Number of players to return    |
| offset    | integer | No       | 0       | Pagination offset              |

**Example Request**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://api.marvelrivals.com/v1/leaderboard?limit=500"
```

**Example Response**:
```json
{
  "players": [
    {
      "username": "player123",
      "rank_tier": "Diamond",
      "rank_score": 3250,
      "wins": 547,
      "losses": 423
    },
    ...
  ],
  "total": 50000,
  "limit": 500,
  "offset": 0
}
```

---

### 2. Hero-Specific Leaderboard

Retrieve top players for a specific hero.

**Endpoint**: `GET /leaderboard/hero/{hero_id}`

**Parameters**:
| Parameter | Type    | Required | Default | Description                    |
|-----------|---------|----------|---------|--------------------------------|
| hero_id   | integer | Yes      | -       | Unique hero identifier         |
| limit     | integer | No       | 50      | Number of players to return    |

**Example Request**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://api.marvelrivals.com/v1/leaderboard/hero/101?limit=50"
```

**Example Response**:
```json
{
  "hero_id": 101,
  "hero_name": "Spider-Man",
  "players": [
    {
      "username": "spidey_main",
      "rank_tier": "Grandmaster",
      "rank_score": 4100,
      "hero_games": 234,
      "hero_wins": 145,
      "hero_win_rate": 0.6197
    },
    ...
  ],
  "total": 15000,
  "limit": 50
}
```

---

### 3. Player Match History

Retrieve recent matches for a specific player.

**Endpoint**: `GET /players/{username}/matches`

**Parameters**:
| Parameter | Type    | Required | Default | Description                    |
|-----------|---------|----------|---------|--------------------------------|
| username  | string  | Yes      | -       | Player username                |
| limit     | integer | No       | 100     | Number of matches to return    |
| mode      | string  | No       | all     | Filter by mode (competitive, quick_play, all) |
| season    | integer | No       | current | Season number                  |

**Example Request**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://api.marvelrivals.com/v1/players/player123/matches?limit=150&mode=competitive"
```

**Example Response**:
```json
{
  "username": "player123",
  "matches": [
    {
      "match_id": "abc123",
      "mode": "competitive",
      "season": 1,
      "timestamp": "2025-10-15T10:30:00Z",
      "map_name": "Tokyo 2099",
      "teams": [
        {
          "team_id": 1,
          "won": true,
          "players": [
            {
              "username": "player123",
              "hero_id": 101,
              "hero_name": "Spider-Man",
              "role": "Duelist",
              "kills": 15,
              "deaths": 8,
              "assists": 12,
              "damage": 25000,
              "healing": 0
            },
            ...  // 5 more teammates
          ]
        },
        {
          "team_id": 2,
          "won": false,
          "players": [ ... ]  // 6 enemy players
        }
      ]
    },
    ...
  ],
  "total_matches": 547,
  "limit": 150
}
```

---

## Hero IDs

| Hero Name        | ID  | Role       |
|------------------|-----|------------|
| Spider-Man       | 101 | Duelist    |
| Iron Man         | 102 | Duelist    |
| Hulk             | 103 | Vanguard   |
| Captain America  | 104 | Vanguard   |
| Thor             | 105 | Vanguard   |
| Black Widow      | 106 | Duelist    |
| Scarlet Witch    | 107 | Duelist    |
| Doctor Strange   | 108 | Strategist |
| Groot            | 109 | Vanguard   |
| Rocket Raccoon   | 110 | Strategist |
| Star-Lord        | 111 | Duelist    |
| Mantis           | 112 | Strategist |
| Luna Snow        | 113 | Strategist |
| Magneto          | 114 | Vanguard   |
| Storm            | 115 | Duelist    |
| ...              | ... | ...        |

*(Full list: 40+ heroes)*

---

## Error Codes

| Code | Meaning                | Example Response                          |
|------|------------------------|-------------------------------------------|
| 200  | OK                     | Request successful                        |
| 400  | Bad Request            | `{"error": "Invalid parameter: limit"}` |
| 401  | Unauthorized           | `{"error": "Invalid API key"}`          |
| 404  | Not Found              | `{"error": "Player not found"}`         |
| 429  | Too Many Requests      | `{"error": "Rate limit exceeded", "retry_after": 60}` |
| 500  | Internal Server Error  | `{"error": "Server error"}`             |
| 503  | Service Unavailable    | `{"error": "API temporarily unavailable"}` |

---

## Rate Limiting Best Practices

Our implementation automatically handles rate limiting:

1. **Token Bucket Algorithm**: Enforces 7 requests/minute
2. **Automatic Delays**: 8.6 seconds between requests
3. **Exponential Backoff**: On 429 errors, wait 1s, 2s, 4s, 8s before retrying
4. **Graceful Degradation**: Logs errors but continues processing

See `src/api/rate_limiter.py` for implementation details.

---

## Client Usage

### Python Client

```python
from src.api.client import MarvelRivalsClient

client = MarvelRivalsClient()

# Get leaderboard
players = client.get_leaderboard(limit=500)

# Get hero leaderboard
spidey_mains = client.get_hero_leaderboard(hero_id=101, limit=50)

# Get player matches
matches = client.get_player_matches(username="player123", limit=150)
```

### CLI Scripts

All scripts automatically use the API client with rate limiting:

```bash
# Discover players (uses leaderboard endpoints)
docker compose exec app python scripts/discover_players.py

# Collect matches (uses match history endpoint)
docker compose exec app python scripts/collect_matches.py
```

---

## Notes

- **API Structure**: This is an assumed/hypothetical API based on common patterns
- **Actual Implementation**: May differ significantly from real Marvel Rivals API
- **Mock Mode**: For testing, use mock responses in `tests/fixtures/`
- **Updates**: If API structure changes, update `src/api/client.py`

---

## Future Enhancements

- **Webhook Support**: Real-time match notifications
- **Bulk Endpoints**: Fetch multiple players in one request
- **Historical Data**: Access past seasons' data
- **Player Stats**: Detailed performance metrics per hero

---

## Questions?

For API client implementation details, see:
- Source code: `src/api/client.py`
- Rate limiter: `src/api/rate_limiter.py`
- Tests: `tests/test_api/` (when implemented)
