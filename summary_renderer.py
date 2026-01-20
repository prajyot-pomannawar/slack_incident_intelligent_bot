"""
Incident summary rendering utilities.

This module formats incident state into a pinned Slack summary (text + Block Kit blocks),
including top-level fields, open/done action items, timeline, and reference links.
"""

def render_timeline(timeline):
    if not timeline:
        return "None"

    # Show last 6 events to keep summary readable
    return "\n".join(f"• {t}" for t in timeline[-6:])


def _format_action_line(a: dict) -> str:
    """
    Action item formatter for summary text.
    """

    action_id = a.get("id", "?")
    text = a.get("text") or ""
    owner = a.get("owner")
    due = a.get("due")

    meta = []
    # Avoid repeating owner if it's already mentioned in the action text.
    if owner:
        owner_s = str(owner)
        if owner_s and owner_s not in text:
            meta.append(owner_s)
    if due:
        meta.append(f"due {due}")

    meta_part = f" ({', '.join(meta)})" if meta else ""
    return f"• #{action_id}: {text}{meta_part}"


def render_summary_text(state):
    lines = [
        "📌 *INCIDENT SUMMARY*",
        f"*Abstract:* {state.get('abstract') or 'TBD'}",
        f"*Severity:* {state.get('severity', 'P1')}",
        f"*Status:* {state.get('status', 'Investigating')}",
        f"*Owner:* {state.get('owner') or 'TBD'}",
        f"*ETA:* {state.get('eta') or 'TBD'}",
        f"*Jira:* {state.get('jira_id') or 'Not linked'}",
        "",
        "*Action Items:*"
    ]

    # Backward compatible rendering: actions may be list[str] or list[dict].
    actions = state.get("actions") or []
    open_actions = []
    done_actions = []

    for a in actions:
        if isinstance(a, dict):
            if a.get("status") == "done":
                done_actions.append(a)
            else:
                open_actions.append(a)
        else:
            open_actions.append({"id": "?", "text": str(a), "owner": None, "due": None})

    if open_actions:
        for a in open_actions[:10]:
            lines.append(_format_action_line(a))
        if len(open_actions) > 10:
            lines.append(f"_... {len(open_actions) - 10} more open action(s)_")
    else:
        lines.append("None")

    lines.append("")
    lines.append("*Done Actions:*")
    if done_actions:
        for a in done_actions[-10:]:
            lines.append(_format_action_line(a))
    else:
        lines.append("None")

    lines.append("")
    lines.append("*Timeline:*")
    lines.append(render_timeline(state.get("timeline", [])))

    # Links section
    lines.append("")
    lines.append("*Links / References:*")

    if state.get("links"):
        for link in state["links"]:
            lines.append(f"• {link}")
    else:
        lines.append("None")

    return "\n".join(lines)


def render_summary_blocks(state, *, channel_id: str = ""):
    """
    Slack Block Kit blocks for the pinned summary message.
    Includes a Manage Actions button.
    """

    text = render_summary_text(state)
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Manage Action Items"},
                    "action_id": "manage_actions",
                    "value": channel_id or "",
                }
            ],
        },
    ]
    return blocks


# Backward compatibility for existing imports
def render_summary(state):
    return render_summary_text(state)