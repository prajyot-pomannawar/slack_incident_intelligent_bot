from vocabulary.incident_vocabulary import STRONG_ACTION_PHRASES, SOFT_PHRASES

def extract_action(text: str, sender_name: str):
    lowered = text.lower()

    if any(soft in lowered for soft in SOFT_PHRASES):
        return None

    for phrase in STRONG_ACTION_PHRASES:
        if phrase in lowered:
            return text.replace("I ", f"{sender_name} ", 1)

    return None