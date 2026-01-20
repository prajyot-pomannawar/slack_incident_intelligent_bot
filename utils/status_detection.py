"""
Status detection from free-form messages.

This module matches common status phrases (investigating, monitoring, resolved, etc.)
and converts them into a normalized incident status shown in the pinned summary.
"""

from vocabulary.incident_vocabulary import STATUS_PHRASES

def extract_status(text: str):
    lower = text.lower()

    for status, phrases in STATUS_PHRASES.items():
        for phrase in phrases:
            if phrase in lower:
                return status.title()

    return None