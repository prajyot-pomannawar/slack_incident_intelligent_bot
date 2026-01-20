"""
Incident abstract (one-liner) detection.

This module infers a short, human-friendly summary label (e.g., "WebUI Bug") from chat text
using simple rule-based patterns, and is shown at the top of the pinned incident summary.
"""

import re
from typing import Optional


_WORD_UI = re.compile(r"\bui\b", re.IGNORECASE)


def extract_abstract(text: str) -> Optional[str]:
    """
    Return a short, one-line abstract for the incident (rule-based).

    Examples:
      - "WebUI Bug"
      - "Service Outage"
      - "Software Bug"

    Returns None if no confident abstract can be inferred from the text.
    """

    t = (text or "").strip()
    if not t:
        return None

    lower = t.lower()

    # Web / UI issues
    if (
        "webui" in lower
        or "web ui" in lower
        or "frontend" in lower
        or "front-end" in lower
        or "dashboard" in lower
        or "console" in lower
        or _WORD_UI.search(t) is not None
    ):
        return "WebUI Bug"

    # Service / availability issues
    if any(k in lower for k in ["outage", "downtime", "prod down", "service down"]):
        return "Service Outage"

    # Auth/login issues
    if any(k in lower for k in ["login", "sso", "auth", "authentication", "authorization", "token expired"]):
        return "Auth/Login Issue"

    # Generic software bug/issues
    if any(k in lower for k in ["bug", "issue", "defect", "regression", "failure", "error"]):
        return "Software Bug"

    return None

