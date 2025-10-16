"""Rate limiter implementation using token bucket algorithm."""

import threading
import time


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm.

    Ensures API requests don't exceed a configured rate limit by enforcing
    delays between requests.
    """

    def __init__(self, requests_per_minute: int = 7) -> None:
        """Initialize rate limiter with configured rate.

        Args:
            requests_per_minute: Maximum number of requests allowed per minute.
        """
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute
        self.last_request_time: float = 0
        self.lock = threading.Lock()

    def wait_if_needed(self) -> None:
        """Block if necessary to respect rate limit.

        Thread-safe method that ensures minimum delay between requests.
        If called too soon after the last request, this method will sleep
        until enough time has passed.
        """
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time

            if elapsed < self.min_delay:
                sleep_time = self.min_delay - elapsed
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def get_delay(self) -> float:
        """Get the minimum delay in seconds between requests.

        Returns:
            Minimum delay in seconds between requests.
        """
        return self.min_delay
