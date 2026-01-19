import re

JIRA_KEY_REGEX = r"\b[A-Z]{2,10}-\d+\b"
JIRA_URL_REGEX = r"https?://[^\s]+/browse/([A-Z]{2,10}-\d+)"

def extract_jira_id(text: str):
    url_match = re.search(JIRA_URL_REGEX, text)
    if url_match:
        return url_match.group(1)

    key_match = re.search(JIRA_KEY_REGEX, text)
    if key_match:
        return key_match.group(0)

    return None