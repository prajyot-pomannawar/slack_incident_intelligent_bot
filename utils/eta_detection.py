"""
ETA extraction from chat messages.

This module extracts simple ETAs such as EOD or explicit dates when users mention "by <date>",
and stores them in incident state so the pinned summary shows expected timelines.
"""

import re
from datetime import datetime
from vocabulary.incident_vocabulary import ETA_PHRASES, EOD_KEYWORDS

DATE_REGEX = r"(\d{1,2}(st|nd|rd|th)?\s+[A-Za-z]+)"

def extract_eta(text: str):
    lower = text.lower()

    # --- Case 1: EOD ---
    if any(eod in lower for eod in EOD_KEYWORDS):
        today = datetime.now().strftime("%d %b %Y")
        return f"EOD ({today})"

    # --- Case 2: Explicit date ---
    if any(p in lower for p in ETA_PHRASES):
        match = re.search(DATE_REGEX, text)
        if match:
            return match.group(1)

    return None