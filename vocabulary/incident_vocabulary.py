"""
Incident bot vocabulary (keywords + phrase lists).

This file contains the phrase dictionaries and keyword lists used by the bot's rule-based detectors
(incident intent, urgency, status, owner assignment, action items, ETA parsing, etc.).
"""

# Incident detection vocabulary
INCIDENT_KEYWORDS = [
    "bug", "issue", "defect", "regression",
    "escalation", "problem", "failure"
]

# Words that indicate urgency / severity
URGENCY_KEYWORDS = [
    "p0",
    "p1",
    "sev0",
    "sev1",
    "critical",
    "urgent",
    "immediately",
    "asap",
    "high priority",
    "impacting customers",
    "prod down",
    "blocker"
]

STRONG_ACTION_PHRASES = [
    # First-person commitments / ownership
    "i will",
    "i'll",
    "i will take",
    "i'll take",
    "i can take",
    "i will handle",
    "i'll handle",
    "i can handle",
    "i will own",
    "i'll own",
    "i can own",
    "i am taking",
    "i'm taking",
    "taking this",
    "taking it",
    "taking ownership",
    "owning this",
    "on it",
    "i am on it",
    "i'm on it",
    "i am looking into",
    "i'm looking into",
    "looking into this",
    "looking into it",
    "i will look into",
    "i'll look into",
    "taking a look",
    "i will take a look",
    "i'll take a look",
    "i can take a look",
    "investigating",
    "triaging",
    "debugging",
    "root causing",
    "rca in progress",

    # Fix / mitigation actions
    "working on",
    "working on it",
    "working on fix",
    "fix in progress",
    "fix underway",
    "building a fix",
    "coding a fix",
    "preparing a fix",
    "will fix",
    "i will fix",
    "i'll fix",
    "fixing",
    "pushing a fix",
    "deploying a fix",
    "hotfix",
    "patch",
    "deploying",
    "rolling out",
    "rollout",
    "rolling back",
    "rollback",
    "reverting",
    "revert",
    "mitigating",
    "mitigation",
    "applying workaround",
    "workaround in place",
    "restarting",
    "restart",

    # Direct requests that usually imply an action item
    "please check",
    "pls check",
    "please review",
    "pls review",
    "please investigate",
    "pls investigate",
    "please look into",
    "pls look into",
    "please verify",
    "pls verify",
    "please confirm",
    "pls confirm",
    "please share",
    "pls share",
    "please send",
    "pls send",
    "please update",
    "pls update",
    "please take a look",
    "pls take a look",
    "could you please",
    "can you please",
    "can you",
    "could you",

    # Assignment language
    "assigned to",
    "assigning to",
    "assign to",
    "owner:",
    "action:",
    "todo:",
    "next step:",

    # Priority nudges (often used as calls-to-action)
    "expedite",
]

SOFT_PHRASES = [
    "maybe", "i think", "looks like",
    "we should", "let's see", "can we", "could we",
    "might be", "probably", "it seems"
]

# Ownership intent
OWNER_ASSIGNMENT_PHRASES = [
    "will work on", "is taking", "assigned to",
    "will handle", "owns this", "looking into this", "have a look"
]

ETA_PHRASES = [
    "by",
    "complete by",
    "will complete by",
    "target to complete by",
    "expected by",
    "Finish it by"
]

EOD_KEYWORDS = [
    "eod",
    "end of day"
]

ASSIGNMENT_QUESTION_PHRASES = [
    "can you take this",
    "can you handle this",
    "can you look into this",
    "can you take this up",
]

STATUS_PHRASES = {
    "investigating": [
        "investigating",
        "looking into",
        "analyzing"
    ],
    "rca done": [
        "rca done",
        "root cause identified",
        "root cause found"
    ],
    "working on fix": [
        "working on fix",
        "fix in progress",
        "fix underway"
    ],
    "pr raised": [
        "pr raised",
        "pull request raised",
        "pr created"
    ],
    "monitoring": [
        "monitoring",
        "observing"
    ],
    "resolved": [
        "resolved",
        "fixed",
        "issue closed"
    ]
}