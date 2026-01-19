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
    "i will", "i'll", "i am taking",
    "assigned to", "taking this",
    "working on", "please check",
    "can you", "will fix", "Could you please", "please review", "expedite", "verify"
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