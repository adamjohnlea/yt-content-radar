# yt-content-radar

**Your For You page for YouTube.** Track the top creators in any niche, see what's
actually performing, and turn it into original content ideas — backed by real
engagement data, not guesswork. Free, local, and no API key.

---

## What it is

You define the topics and industries you care about and point it at the top
YouTube channels in those spaces. Each run it:

1. **Scrapes** the recent videos from the channels you track (via `yt-dlp`).
2. **Scores** them — not just raw views, but what's *overperforming* relative to
   each channel's own baseline (statistical outlier detection).
3. **Generates** original content ideas off those signals — each with a short
   brief: the angle, why it's worth doing now, and a hook to open with.
4. **Renders** a single self-contained "For You" web page with two tabs: a
   sortable **Posts** feed and an **Ideas** tab. React to items (▲/▼/note) and
   it personalizes over time.

## What it isn't

**A plagiarism machine.** It doesn't copy, rewrite, or repost anyone's content.
It uses what's working as a *read on what an audience cares about right now*, then
helps you build an original take — your angle, your expertise, your spin. It even
checks each idea against what you've already published so you don't repeat
yourself. Think of it like scrolling what's trending in a space and deciding what
to make — just backed by real engagement data instead of a gut feel.

---

## How it works

```
tracked channels ──► scrape.py ──► scored posts + outliers (JSON)
                       (yt-dlp)            │
                                           ▼
                              ideas + briefs (LLM step)
                                           │
                                           ▼
                     generate_feed.py ──► For You page (HTML)
```

- **Scraping, scoring, outlier/relevance analysis, and rendering** are plain
  Python — they run anywhere, no LLM required.
- **Idea generation** (angles, briefs, hooks) is an LLM step. The richest
  experience is as a [Claude Code](https://claude.com/claude-code) skill, where
  Claude reads the scored data and writes the ideas automatically. Run standalone
  (see below) and you get the full scraping/scoring/rendering pipeline; the Ideas
  tab is whatever your own LLM step puts there.

Everything a creator's video exposes publicly — title, description, view/like/
comment counts, top comments, and captions/transcript — is fair game. Nothing is
behind a login or a paywall.

---

## Requirements

- **Python 3.9+** (standard library only — nothing to `pip install`)
- **[`yt-dlp`](https://github.com/yt-dlp/yt-dlp)** on your `PATH` — the one
  external dependency:
  ```bash
  brew install yt-dlp        # macOS
  # or: pipx install yt-dlp  # any platform
  ```
  Keep it current — `brew upgrade yt-dlp` — since YouTube changes its internals
  periodically and an outdated `yt-dlp` is the usual cause of empty results.

No API key, no account, no quota, no paid service.

---

## Install

### As a Claude Code skill (recommended)

Clone into your Claude Code skills directory and invoke it with a slash command:

```bash
git clone https://github.com/<you>/yt-content-radar.git ~/.claude/skills/yt-content-radar
```

Then in Claude Code:

```
/yt-content-radar
```

The first run walks you through setup (confirms `yt-dlp`, builds a profile for
your niche, and lets you pick channels to track), then builds your daily feed.

### Standalone CLI

Clone anywhere and run the scripts directly:

```bash
git clone https://github.com/<you>/yt-content-radar.git
cd yt-content-radar
```

---

## Usage (CLI)

### 1. Scrape tracked channels

```bash
python3 scripts/scrape.py \
  '{"youtube": ["@channel1", "@channel2", "@channel3"]}' \
  --pillars "indie game dev, godot, pixel art" \
  --days 7
```

- First arg: a JSON object mapping `youtube` to the channel handles/URLs to track.
- `--pillars` — comma-separated themes; drives the relevance score.
- `--days N` — recency window (default 7, max 90). Only videos from the last N
  days are kept.
- `--since YYYY-MM-DD` — incremental cursor; narrows the window (never widens it).

Fetch specific videos instead of whole channels:

```bash
python3 scripts/scrape.py urls \
  "https://www.youtube.com/watch?v=abc" "https://youtu.be/xyz" \
  --pillars "..."
```

Output is JSON on **stdout** (progress on stderr). Each post carries `title`,
`url`, `author`, `date`, `engagement` (`views`/`likes`/`comments`), a weighted
`score`, a `relevance` (0–1), a `baseline`, an `outlier` flag, and — for top
videos — `comments` and `transcript`.

### 2. Render the For You page

`generate_feed.py` reads a `feed-data.json` from a run directory and renders the
page. (See [`FILE-SCHEMAS.md`](FILE-SCHEMAS.md) for the `feed-data.json`
structure.)

```bash
# Serve it live on http://localhost:3119 (interactive — reactions save to feedback.json)
python3 scripts/generate_feed.py ~/Documents/Content/research/2026-06-14

# Or write a self-contained file you can reopen anytime
python3 scripts/generate_feed.py ~/Documents/Content/research/2026-06-14 --static
# → <run-dir>/for-you.html
```

Useful flags: `--port N` (default 3119), `--no-browser`, `--feed <path>` to point
at a specific `feed-data.json`.

---

## Tracking multiple niches

All state for a niche — the profile, tracked channels, and run history — lives
under one folder, **`$CONTENT_HOME`** (default `~/Documents/Content`). To run a
completely separate subject, point `CONTENT_HOME` at a different folder:

```bash
CONTENT_HOME=~/Documents/Radar-Fitness python3 scripts/scrape.py '{"youtube": ["@athleanx"]}' --pillars "strength training"
```

In Claude Code, launch the session with the env var set and the skill sets that
niche up from scratch — fully isolated from your other workspaces:

```bash
CONTENT_HOME=~/Documents/Radar-Fitness claude
# then: /yt-content-radar
```

---

## Configuration & data layout

Under `$CONTENT_HOME`:

```
brand/
  profile.md                  # niche, content pillars, search terms, goal, your channel
  tracked-accounts/youtube.md # the channels to track
  my-content.md               # rolling snapshot of your own performance (anti-cannibalization)
research/
  YYYY-MM-DD/
    feed-data.json            # the assembled feed (posts + ideas)
    for-you.html              # the rendered page (with --static)
    feedback.json             # your ▲/▼/note reactions
```

Full schemas for every file are in [`FILE-SCHEMAS.md`](FILE-SCHEMAS.md). Tuning
knobs (videos pulled per channel, comment/transcript caps) live at the top of
`scripts/lib/youtube.py`.

---

## Notes & limitations

- **Idea quality depends on the LLM step.** The Python pipeline gives you scored,
  outlier-flagged data and a renderer; the *ideas* are only as good as the model
  reading them. The Claude Code skill is the intended full experience.
- **`yt-dlp` is the maintenance surface.** It scrapes YouTube's public pages, so
  it can rate-limit on very large runs and occasionally needs updating when
  YouTube changes things. That's the trade-off for paying nothing.
- **Respect terms and copyright.** This tool reads publicly available data for
  research and inspiration. How you *use* what you collect — storing, republishing,
  etc. — is on you; check YouTube's Terms of Service and applicable copyright/
  privacy law for your use case.

---

## Credits

A YouTube-only fork of
[content-ideas](https://github.com/bradautomates/content-ideas) by Bradley
Bonanno (MIT). See [`CREDITS.md`](CREDITS.md) for what changed.

## License

[MIT](LICENSE) — © 2026 leaStudios, with the original copyright © 2026 Bradley
Bonanno retained per the license.
