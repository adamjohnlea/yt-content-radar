"""yt-content-radar scraper library (YouTube-only).

Small, testable modules behind the scraper CLI:

- log       — stderr progress (keeps stdout clean for JSON)
- dates     — date parsing/normalization helpers
- youtube   — YouTube fetchers via the local yt-dlp binary (channel videos,
              single video, comments, transcript) — no API key, no quota
- platforms — builds the fetcher registries from the per-platform modules
- scoring   — weighted engagement score
- relevance — token-overlap relevance against content pillars
- analyze   — per-account baselines + outlier flags
- urls      — YouTube URL detection + handle extraction
- env       — persistent-storage path resolution (content_home)
- pipeline  — orchestration (scrape_all, filter_since, fetch_urls)
"""
