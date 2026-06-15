"""Date helpers for the scraper's recency window."""

from datetime import datetime, timedelta, timezone


def days_ago(n):
    """Return the UTC date `n` days before today as a YYYY-MM-DD string."""
    return (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y-%m-%d")
