"""
Link/reference extraction from chat messages.

This module finds URLs in message text so they can be stored as references in the incident state
and displayed in the pinned incident summary for quick access.
"""

import re

URL_REGEX = re.compile(
    r"(https?://[^\s<>]+)",
    re.IGNORECASE
)

def extract_links(text):
    """
    Returns list of URLs found in text
    """
    return URL_REGEX.findall(text)