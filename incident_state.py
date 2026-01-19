# -----------------------------
# In-memory incident store
# -----------------------------
from datetime import datetime
_INCIDENTS = {}

def start_incident(channel):
    if channel in _INCIDENTS:
        return False

    _INCIDENTS[channel] = {
        "severity": "P1",
        "status": "Investigating",
        "owner": "TBD",
        "eta": "TBD",
        "jira_id": None,
        "actions": [],
        "links": [],  # ✅ NEW
        "timeline": [],
        "pending_owner_request": None,
        "just_started": True
    }

    add_timeline_event(channel, "Incident detected")
    return True

def add_timeline_event(channel, message):
    if channel in _INCIDENTS:
        timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
        _INCIDENTS[channel]["timeline"].append(
            f"{timestamp} – {message}"
        )

def get_state(channel):
    return _INCIDENTS.get(channel)


def is_active(channel):
    return channel in _INCIDENTS


def clear(channel):
    _INCIDENTS.pop(channel, None)


def set_owner(channel, owner):
    if channel in _INCIDENTS:
        _INCIDENTS[channel]["owner"] = owner


def set_eta(channel, eta):
    if channel in _INCIDENTS:
        _INCIDENTS[channel]["eta"] = eta


def add_action(channel, action):
    if channel in _INCIDENTS:
        _INCIDENTS[channel]["actions"].append(action)
