"""Marvel Rivals API client for data collection.

This module provides a client for interacting with the Marvel Rivals API.
Includes rate limiting and error handling for API requests.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Exception raised for API errors."""

    pass


class MarvelRivalsClient:
    """Client for Marvel Rivals API with rate limiting.

    Provides methods for fetching player profiles, match history, and match details.
    Integrates rate limiting to respect API usage constraints.
    """

    BASE_URL_V1 = "https://marvelrivalsapi.com/api/v1"
    BASE_URL_V2 = "https://marvelrivalsapi.com/api/v2"

    def __init__(
        self,
        api_key: Optional[str] = None,
        requests_per_minute: Optional[int] = None,
    ) -> None:
        """Initialize Marvel Rivals API client.

        Args:
            api_key: API key for authentication. If not provided, reads from
                     MARVEL_RIVALS_API_KEY environment variable.
            requests_per_minute: Rate limit for API requests. If not provided,
                                reads from RATE_LIMIT_REQUESTS_PER_MINUTE
                                environment variable, defaulting to 7.

        Raises:
            ValueError: If API key is not provided and not in environment.
        """
        self.api_key = api_key or os.getenv("MARVEL_RIVALS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set in MARVEL_RIVALS_API_KEY environment variable"
            )

        rate_limit = requests_per_minute or int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "7"))
        self.rate_limiter = RateLimiter(requests_per_minute=rate_limit)

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request with rate limiting and error handling.

        Args:
            url: Full URL to request
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            APIException: If request fails
        """
        self.rate_limiter.wait_if_needed()

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 429:
                raise APIException("Rate limit exceeded (429)")
            elif response.status_code == 404:
                raise APIException(f"Resource not found (404): {url}")
            elif response.status_code >= 500:
                raise APIException(f"Server error ({response.status_code})")
            elif response.status_code != 200:
                raise APIException(f"API error ({response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.Timeout:
            raise APIException("Request timeout")
        except requests.exceptions.ConnectionError:
            raise APIException("Connection error")
        except requests.exceptions.RequestException as e:
            raise APIException(f"Request failed: {e}")

    def get_leaderboard(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch players from general leaderboard.

        Args:
            limit: Maximum number of players to retrieve

        Returns:
            List of player dictionaries with username, rank_tier, rank_score

        Raises:
            APIException: If API request fails
        """
        url = f"{self.BASE_URL_V1}/leaderboard"
        params = {"limit": limit}

        logger.debug(f"Fetching leaderboard (limit={limit})")

        try:
            data = self._make_request(url, params)
            # Expected response format: {"players": [...]}
            players = data.get("players", [])
            logger.info(f"Fetched {len(players)} players from leaderboard")
            return players
        except APIException as e:
            logger.error(f"Failed to fetch leaderboard: {e}")
            raise

    def get_hero_leaderboard(self, hero_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch players from hero-specific leaderboard.

        Args:
            hero_id: Hero identifier
            limit: Maximum number of players to retrieve

        Returns:
            List of player dictionaries

        Raises:
            APIException: If API request fails
        """
        url = f"{self.BASE_URL_V1}/leaderboard/hero/{hero_id}"
        params = {"limit": limit}

        logger.debug(f"Fetching hero leaderboard (hero_id={hero_id}, limit={limit})")

        try:
            data = self._make_request(url, params)
            players = data.get("players", [])
            logger.info(f"Fetched {len(players)} players for hero_id={hero_id}")
            return players
        except APIException as e:
            logger.error(f"Failed to fetch hero leaderboard for hero_id={hero_id}: {e}")
            raise

    def get_player_profile(self, username: str) -> Dict[str, Any]:
        """Fetch player profile data.

        Args:
            username: Player username to fetch.

        Returns:
            Dictionary containing player profile data.

        Raises:
            NotImplementedError: Method will be implemented in Phase 1.
        """
        raise NotImplementedError(
            "get_player_profile will be implemented in Phase 1 (data collection)"
        )

    def get_player_matches(self, username: str, limit: int = 150) -> List[Dict[str, Any]]:
        """Fetch match history for a player.

        Args:
            username: Player username to fetch matches for.
            limit: Maximum number of matches to retrieve.

        Returns:
            List of match dictionaries.

        Raises:
            APIException: If API request fails
        """
        url = f"{self.BASE_URL_V1}/players/{username}/matches"
        params = {"limit": limit}

        logger.debug(f"Fetching match history for {username} (limit={limit})")

        try:
            data = self._make_request(url, params)
            matches = data.get("matches", [])
            logger.info(f"Fetched {len(matches)} matches for {username}")
            return matches
        except APIException as e:
            logger.error(f"Failed to fetch matches for {username}: {e}")
            raise

    def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed information for a specific match.

        Args:
            match_id: Unique identifier for the match.

        Returns:
            Dictionary containing match details.

        Raises:
            NotImplementedError: Method will be implemented in Phase 1.
        """
        raise NotImplementedError(
            "get_match_details will be implemented in Phase 1 (data collection)"
        )
