"""Tests for MarvelRivalsClient initialization and structure."""

import pytest
from src.api import MarvelRivalsClient, RateLimiter


def test_client_initializes_with_api_key():
    """Test that client can be initialized with an API key."""
    api_key = "test_api_key_123"
    client = MarvelRivalsClient(api_key=api_key)

    assert client is not None
    assert client.api_key == api_key


def test_rate_limiter_initializes():
    """Test that rate limiter is initialized when client is created."""
    api_key = "test_api_key_123"
    client = MarvelRivalsClient(api_key=api_key)

    assert client.rate_limiter is not None
    assert isinstance(client.rate_limiter, RateLimiter)


def test_client_has_expected_methods():
    """Test that client has the expected method signatures."""
    api_key = "test_api_key_123"
    client = MarvelRivalsClient(api_key=api_key)

    assert hasattr(client, "get_player_profile")
    assert hasattr(client, "get_player_matches")
    assert hasattr(client, "get_match_details")
    assert callable(client.get_player_profile)
    assert callable(client.get_player_matches)
    assert callable(client.get_match_details)
