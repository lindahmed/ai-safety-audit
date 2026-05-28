"""
Sliding-window rate limiter for the Google Gemini API.

Tracks every outgoing request in a 60-second window and blocks before
sending the next one if the per-minute cap would be exceeded.  This
prevents 429 ResourceExhausted errors without relying solely on
post-error retry logic.

Usage:
    from utils.rate_limiter import RateLimiter

    limiter = RateLimiter(max_requests_per_minute=12)

    limiter.wait_if_needed()   # call immediately before every API call
    response = model.generate_content(...)
"""

import time

from rich.console import Console

console = Console()

# Stepped retry delays (seconds) for when a 429 slips through anyway.
# Chosen to give the quota window time to fully reset.
RETRY_DELAYS = [15, 30, 60, 120]


class RateLimiter:
    """
    Sliding-window rate limiter.

    Keeps a list of timestamps for recent API calls and sleeps whenever
    the next call would push the per-minute count over the configured cap.

    Parameters
    ----------
    max_requests_per_minute : int
        Hard cap on requests per 60-second window.  Default is 12 to
        stay safely under the Gemini free-tier limit of 15 RPM.
    """

    def __init__(self, max_requests_per_minute: int = 12) -> None:
        self.max_rpm = max_requests_per_minute
        # Timestamps (float seconds since epoch) of recent API calls
        self.requests: list[float] = []

    # ── public API ────────────────────────────────────────────────────────────

    def wait_if_needed(self) -> None:
        """
        Block until it is safe to send another request.

        Purges timestamps older than 60 s, then checks whether the window
        is full.  If it is, sleeps until the oldest request ages out.
        """
        now = time.time()

        # Drop calls that have aged out of the 60-second window
        self.requests = [r for r in self.requests if now - r < 60]

        if len(self.requests) >= self.max_rpm:
            # Oldest request in window; sleep until it turns 60 s old (+1 s buffer)
            oldest = self.requests[0]
            sleep_time = 60 - (now - oldest) + 1.0
            sleep_time = max(sleep_time, 0.0)

            console.print(
                f"[bold yellow]⏳  Rate limit protection — "
                f"{len(self.requests)}/{self.max_rpm} requests in last 60s.  "
                f"Waiting {sleep_time:.1f}s before next call...[/bold yellow]"
            )
            time.sleep(sleep_time)

        # Record this call's timestamp
        self.requests.append(time.time())

    @property
    def requests_in_window(self) -> int:
        """Number of requests made in the current 60-second window."""
        now = time.time()
        return sum(1 for r in self.requests if now - r < 60)
