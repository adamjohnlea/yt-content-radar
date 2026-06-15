"""Platform detection and handle extraction from post URLs (URL mode).

YouTube-only build: detect_platform recognizes YouTube URLs and rejects
everything else.
"""


def detect_platform(url):
    """Return 'youtube' for a YouTube URL, else None."""
    url_lower = url.lower()
    if "youtube.com/" in url_lower or "youtu.be/" in url_lower:
        return "youtube"
    return None


def extract_handle_from_url(url, platform="youtube"):
    """Best-effort channel handle from a YouTube URL. Returns handle or None.

    Handles https://www.youtube.com/@handle/... ; channel-ID URLs have no handle.
    """
    for part in url.split("/"):
        if part.startswith("@"):
            return part.lstrip("@")
    return None
