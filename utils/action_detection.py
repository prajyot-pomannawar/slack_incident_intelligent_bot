"""
Action-item detection from free-form chat messages.

This module detects strong "do this" / "I'm on it" style statements and converts
first-person actions into sender-attributed action text for incident tracking.
"""

import re

from vocabulary.incident_vocabulary import STRONG_ACTION_PHRASES, SOFT_PHRASES


_CURLY_APOSTROPHE = "\u2019"
_LEADING_ILL_RE = re.compile(r"^\s*i[’']ll\b", re.IGNORECASE)
_LEADING_I_RE = re.compile(r"^\s*i\b", re.IGNORECASE)

def extract_action(text: str, sender_name: str):
    # Normalize apostrophes (Slack sometimes uses curly apostrophes)
    normalized = (text or "").replace(_CURLY_APOSTROPHE, "'")
    lowered = normalized.lower()

    if any(soft in lowered for soft in SOFT_PHRASES):
        return None

    for phrase in STRONG_ACTION_PHRASES:
        if phrase in lowered:
            # Normalize first-person statements to attribute to sender.
            # Examples:
            #   "I will troubleshoot..." -> "<@U123> will troubleshoot..."
            #   "I'll troubleshoot..."   -> "<@U123> will troubleshoot..."
            if _LEADING_ILL_RE.search(normalized):
                return _LEADING_ILL_RE.sub(f"{sender_name} will", normalized, count=1)
            if _LEADING_I_RE.search(normalized):
                return _LEADING_I_RE.sub(sender_name, normalized, count=1)
            return normalized

    return None