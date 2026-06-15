"""Fetcher registries.

This build is YouTube-only: every fetcher is backed by the local yt-dlp binary
(see youtube.py). The registries are kept as a layer of indirection so the
pipeline stays platform-agnostic and a platform could be re-added later by
dropping a module in and registering it here.
"""

from . import youtube

# Recent posts for a handle: fetch_profile(handle) -> [post]
PROFILE_FETCHERS = {
    "youtube": youtube.fetch_profile,
}

# A single post by URL: fetch_post(url) -> post | None
POST_FETCHERS = {
    "youtube": youtube.fetch_post,
}

# Top comments for a post URL: fetch_comments(url) -> [comment]
COMMENT_FETCHERS = {
    "youtube": youtube.fetch_comments,
}

# Spoken transcript for a post URL: fetch_transcript(url) -> str | None
TRANSCRIPT_FETCHERS = {
    "youtube": youtube.fetch_transcript,
}
