"""
Rule-based incident intent classifier.

This module maps a single message line to HIGH/MEDIUM/LOW using keyword heuristics.
It is used as the primary gate before starting incident tracking or asking for confirmation.
"""

# utils/incident_classifier.py

from vocabulary.incident_vocabulary import INCIDENT_KEYWORDS, URGENCY_KEYWORDS

def classify_incident_intent(line: str) -> str:
    """
    Returns:
      HIGH   -> Auto-create incident
      MEDIUM -> Ask confirmation
      LOW    -> Ignore

    Note: This is intentionally rule-based only.
    """
    text = line.lower()

    intent_score = sum(1 for k in INCIDENT_KEYWORDS if k in text)
    urgency_score = sum(1 for u in URGENCY_KEYWORDS if u in text)

    # Rule-based classification
    if intent_score >= 1 and urgency_score >= 1:
        return "HIGH"

    if intent_score >= 1 and urgency_score == 0:
        return "MEDIUM"

    return "LOW"