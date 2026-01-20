"""
Owner detection and ownership-question detection.

This module recognizes when someone assigns/accepts ownership of an incident (or asks someone to take it),
so the incident state can track the current owner and prompt for confirmation when needed.
"""

import re
from vocabulary.incident_vocabulary import OWNER_ASSIGNMENT_PHRASES, ASSIGNMENT_QUESTION_PHRASES

MENTION_REGEX = r"<@([A-Z0-9]+)>"

def detect_owner_question(text: str):
    lower = text.lower()
    for phrase in ASSIGNMENT_QUESTION_PHRASES:
        if phrase in lower:
            return True
    return False

def extract_owner(text: str, sender_name: str):
    lowered = text.lower()

    for phrase in OWNER_ASSIGNMENT_PHRASES:
        if phrase in lowered:
            mentions = re.findall(MENTION_REGEX, text)
            if mentions:
                return f"<@{mentions[0]}>"
            return sender_name

    if "owner" in lowered:
        mentions = re.findall(MENTION_REGEX, text)
        if mentions:
            return f"<@{mentions[0]}>"

    return None