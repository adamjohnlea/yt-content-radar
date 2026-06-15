"""Persistent-storage paths.

The persistent base dir (brand/ + research/) is resolved by `content_home()`.
"""

import os
from pathlib import Path

CONTENT_HOME_VAR = "CONTENT_HOME"
DEFAULT_CONTENT_HOME = Path.home() / "Documents" / "Content"


def content_home():
    """Resolve the persistent base dir holding brand/ and research/.

    Honors the CONTENT_HOME env var; defaults to ~/Documents/Content. This is
    deliberately NOT the current working directory: the skill is invoked from
    anywhere and runs daily, so brand/ (the user's identity) and research/ (the
    dated history that feeds taste memory) must be found again on the next run
    regardless of where the terminal happens to be.
    """
    override = os.environ.get(CONTENT_HOME_VAR, "").strip()
    return Path(override).expanduser() if override else DEFAULT_CONTENT_HOME
