from vocabulary.incident_vocabulary import INCIDENT_KEYWORDS

def detect_incident(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in INCIDENT_KEYWORDS)