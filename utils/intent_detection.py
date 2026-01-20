"""
Basic incident keyword presence detector.

This module provides a simple boolean keyword check and is used for lightweight intent detection
in places where the full HIGH/MEDIUM/LOW classifier is not needed.
"""

from vocabulary.incident_vocabulary import INCIDENT_KEYWORDS

def detect_incident(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in INCIDENT_KEYWORDS)