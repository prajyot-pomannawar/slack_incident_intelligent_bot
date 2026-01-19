def render_timeline(timeline):
    if not timeline:
        return "None"

    # Show last 6 events to keep summary readable
    return "\n".join(f"• {t}" for t in timeline[-6:])


def render_summary(state):
    lines = [
        "📌 *INCIDENT SUMMARY*",
        f"*Severity:* {state.get('severity', 'P1')}",
        f"*Status:* {state.get('status', 'Investigating')}",
        f"*Owner:* {state.get('owner') or 'TBD'}",
        f"*ETA:* {state.get('eta') or 'TBD'}",
        f"*Jira:* {state.get('jira_id') or 'Not linked'}",
        "",
        "*Open Actions:*"
    ]

    if state.get("actions"):
        for a in state["actions"]:
            lines.append(f"• {a}")
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