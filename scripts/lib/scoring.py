"""Weighted engagement scoring."""


def score_engagement(post):
    """Compute a weighted engagement score for a YouTube post.

    Views are abundant and cheap, so they're discounted heavily; likes count
    at face value and comments (the costliest signal of interest) are weighted up.
    """
    e = post.get("engagement", {})

    if post.get("platform") == "youtube":
        return (e.get("views", 0) * 0.1
                + e.get("likes", 0)
                + 3 * e.get("comments", 0))

    # Fallback: sum all numeric values
    return sum(v for v in e.values() if isinstance(v, (int, float)))
