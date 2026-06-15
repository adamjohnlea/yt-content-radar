"""YouTube fetchers: channel videos, single video, comments, transcript.

Backed entirely by the local `yt-dlp` binary — no API key and no daily quota.

yt-dlp scrapes YouTube's public surface, so it can rate-limit on very large
runs and may need an occasional `brew upgrade yt-dlp` when YouTube changes
things. That maintenance burden is the tradeoff for paying nothing.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile

from .log import log
from .urls import extract_handle_from_url

MAX_COMMENTS = 10
MAX_VIDEOS = 15  # recent videos pulled per channel; the cost knob — each is a full extraction
TRANSCRIPT_WORD_CAP = 5000  # bound feed-data size on very long videos
CANARY_MIN_VIDEOS = 5  # only flag a date collapse once there are enough videos to be suspicious

SUBPROCESS_TIMEOUT = 120  # seconds per yt-dlp invocation
SUB_LANGS = "en.*"  # english + regional + auto-generated english captions
COMMENT_EXTRACTOR_ARGS = "youtube:comment_sort=top;max_comments=30,30,0,0"

# Resolve yt-dlp once. shutil.which honors PATH; the explicit fallbacks cover the
# common Homebrew locations in case the skill runs with a stripped PATH.
_YTDLP = (
    shutil.which("yt-dlp")
    or next((p for p in ("/opt/homebrew/bin/yt-dlp", "/usr/local/bin/yt-dlp") if os.path.exists(p)), None)
)


def _int(value):
    """Coerce a yt-dlp count (which may be None when hidden) to a plain int."""
    return int(value) if isinstance(value, (int, float)) else 0


def _run(args):
    """Run yt-dlp with the given args. Returns CompletedProcess or None on failure."""
    if not _YTDLP:
        log("  ✗ youtube: yt-dlp not found on PATH — install with `brew install yt-dlp`")
        return None
    try:
        return subprocess.run(
            [_YTDLP, "--no-warnings", "--ignore-config", "--no-progress", *args],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        log(f"  ✗ youtube: yt-dlp timed out after {SUBPROCESS_TIMEOUT}s")
        return None
    except OSError as e:
        log(f"  ✗ youtube: yt-dlp failed to launch — {e}")
        return None


def _ytdlp_json(args):
    """Run yt-dlp with `-J` and return the parsed JSON object, or None."""
    proc = _run(["-J", *args])
    if not proc or proc.returncode != 0 or not proc.stdout.strip():
        if proc and proc.stderr.strip():
            log(f"  ✗ youtube: {proc.stderr.strip().splitlines()[-1]}")
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def _channel_videos_url(handle):
    """Build a channel /videos URL from a stored handle, channel id, or full URL."""
    h = handle.strip()
    if h.startswith("http"):
        base = h.rstrip("/")
    elif h.startswith("UC") and len(h) == 24:
        base = f"https://www.youtube.com/channel/{h}"
    else:
        base = f"https://www.youtube.com/@{h.lstrip('@')}"
    return base if base.endswith("/videos") else f"{base}/videos"


def _date_of(info):
    """Return upload date as YYYY-MM-DD, or None. Prefers upload_date (YYYYMMDD)."""
    raw = info.get("upload_date")
    if raw and len(str(raw)) == 8:
        s = str(raw)
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return None


def _post_from_info(info, author):
    """Map a yt-dlp video info dict to a normalized post dict."""
    return {
        "text": info.get("title", "") or "",
        "url": info.get("webpage_url") or info.get("original_url") or "",
        "author": author,
        "date": _date_of(info),
        "platform": "youtube",
        "engagement": {
            "views": _int(info.get("view_count")),
            "likes": _int(info.get("like_count")),
            "comments": _int(info.get("comment_count")),
        },
        "duration": int(info["duration"]) if isinstance(info.get("duration"), (int, float)) else None,
        "description": info.get("description", "") or "",
    }


def fetch_profile(handle):
    """Recent videos for a channel handle via `yt-dlp -J <channel>/videos`."""
    data = _ytdlp_json(["--playlist-end", str(MAX_VIDEOS), _channel_videos_url(handle)])
    if not data:
        return []
    entries = data.get("entries") or []
    posts = [_post_from_info(e, handle) for e in entries if isinstance(e, dict)]
    _warn_on_date_collapse(handle, posts)
    return posts


def _warn_on_date_collapse(handle, posts):
    """Canary: warn when every dated video shares one identical date.

    yt-dlp reports real upload dates, so this should never fire — but if a future
    YouTube change ever corrupts them, this surfaces it loudly rather than letting
    a feed silently fill with stale-but-same-dated posts.
    """
    dated = [p["date"] for p in posts if p.get("date")]
    if len(dated) >= CANARY_MIN_VIDEOS and len(set(dated)) == 1:
        log(f"  ⚠ {handle}: all {len(dated)} videos share date {dated[0]} — dates may be unreliable.")


def fetch_post(url):
    """A single video by URL via `yt-dlp -J --no-playlist <url>`."""
    info = _ytdlp_json(["--no-playlist", url])
    if not info:
        return None
    author = (
        info.get("uploader")
        or info.get("channel")
        or extract_handle_from_url(url, "youtube")
        or ""
    )
    return _post_from_info(info, author)


def fetch_comments(post_url):
    """Top comments for a video via yt-dlp's comment extractor."""
    info = _ytdlp_json([
        "--no-playlist",
        "--write-comments",
        "--extractor-args", COMMENT_EXTRACTOR_ARGS,
        post_url,
    ])
    if not info:
        return []
    raw = info.get("comments") or []
    # Keep top-level comments only (replies have a non-'root' parent), best-liked first.
    top_level = [c for c in raw if isinstance(c, dict) and c.get("parent", "root") == "root"]
    top_level.sort(key=lambda c: _int(c.get("like_count")), reverse=True)
    return [
        {
            "author": (c.get("author") or "").lstrip("@"),
            "text": c.get("text", "") or "",
            "likes": _int(c.get("like_count")),
        }
        for c in top_level[:MAX_COMMENTS]
    ]


def fetch_transcript(post_url):
    """Plain-text transcript via yt-dlp subtitle download (manual or auto-captions).

    Downloads English VTT subtitles to a temp dir, strips the cue formatting to
    plain text, de-duplicates the rolling repeats auto-captions emit, and caps the
    result at TRANSCRIPT_WORD_CAP words.
    """
    if not _YTDLP:
        return None
    with tempfile.TemporaryDirectory() as td:
        proc = _run([
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs", SUB_LANGS,
            "--sub-format", "vtt/best",
            "--no-playlist",
            "-o", os.path.join(td, "%(id)s.%(ext)s"),
            post_url,
        ])
        if not proc:
            return None
        vtts = [f for f in os.listdir(td) if f.endswith(".vtt")]
        if not vtts:
            return None
        # Prefer a manual track (no '.auto.'/auto-style marker) when both exist.
        vtts.sort(key=lambda f: ("auto" in f.lower(), f))
        try:
            raw = open(os.path.join(td, vtts[0]), encoding="utf-8").read()
        except OSError:
            return None
    text = _vtt_to_text(raw)
    if not text:
        return None
    return " ".join(text.split()[:TRANSCRIPT_WORD_CAP])


_VTT_TAG = re.compile(r"<[^>]+>")  # inline timing tags like <00:00:01.000> and <c> spans


def _vtt_to_text(raw):
    """Strip a WEBVTT subtitle blob down to de-duplicated plain text."""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT" or "-->" in line:
            continue
        if line.startswith(("NOTE", "Kind:", "Language:")) or line.isdigit():
            continue
        cleaned = _VTT_TAG.sub("", line).strip()
        # Auto-captions repeat the previous cue's trailing line as the next cue's
        # first line; skip exact consecutive duplicates so the text reads cleanly.
        if cleaned and (not lines or lines[-1] != cleaned):
            lines.append(cleaned)
    return " ".join(lines).strip()
