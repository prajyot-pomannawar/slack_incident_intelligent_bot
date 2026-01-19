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