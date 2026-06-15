# Credits

**yt-content-radar** is a YouTube-only fork of
[content-ideas](https://github.com/bradautomates/content-ideas) by
**Bradley Bonanno** (MIT licensed).

The original is a multi-platform competitor-research tool (X, Instagram, TikTok,
YouTube) that sourced all of its data through the paid ScrapeCreators API.
yt-content-radar keeps the engagement-scoring, outlier-detection, relevance,
idea-generation, and feed-rendering engine and re-points it at a single,
free, local data source:

- **Data source** — replaced ScrapeCreators with the local
  [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) binary. No API key, no quota, no
  account, no paid service.
- **Scope** — narrowed to YouTube only; the X / Instagram / TikTok modules and
  all cross-platform code, styling, and docs were removed.
- **Distribution** — standalone repo; usable as a Claude Code skill or directly
  from the command line.

Per the MIT license, the original copyright notice is retained in
[`LICENSE`](LICENSE). Modifications are © 2026 leaStudios, also under MIT.
