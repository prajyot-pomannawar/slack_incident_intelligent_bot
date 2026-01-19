import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import incident_state

from utils.owner_detection import extract_owner, detect_owner_question
from utils.action_detection import extract_action
from utils.eta_detection import extract_eta
from utils.status_detection import extract_status
from utils.jira_detection import extract_jira_id
from summary_renderer import render_summary
from utils.incident_classifier import classify_incident_intent
from utils.confirmation import ask_incident_confirmation
from utils.link_detection import extract_links


app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Track pinned summary per channel
PINNED_MESSAGES = {}
pending_confirmations = {}

# -----------------------------
# Message Handler
# -----------------------------
@app.event("message")
def handle_message(event, client):
    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")

    # Ignore bot / empty messages
    if not text or user is None:
        return

    sender = f"<@{user}>"
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # -----------------------------
    # STEP 1: Incident detection (Rule-based)
    # -----------------------------
    incident_started = False

    for line in lines:
        intent = classify_incident_intent(line)

        # 🔥 HIGH confidence → auto start
        if intent == "HIGH":
            incident_started = incident_state.start_incident(channel)
            break

        # ⚠️ MEDIUM confidence → ask confirmation (rule-based)
        elif intent == "MEDIUM":
            if (
                not incident_state.is_active(channel)
                and channel not in pending_confirmations
            ):
                ask_incident_confirmation(client, channel, line)
                pending_confirmations[channel] = True

            return  # ⛔ stop further processing

    # If incident is still not active, ignore message
    if not incident_state.is_active(channel):
        return

    # -----------------------------
    # STEP 2: Normal incident processing
    # -----------------------------
    state = incident_state.get_state(channel)
    updated = False

    for line in lines:
        l = line.lower()

        # -----------------------------
        # Owner QUESTION detection
        # -----------------------------
        if detect_owner_question(line):
            mentions = re.findall(r"<@([A-Z0-9]+)>", line)
            if mentions:
                state["pending_owner_request"] = mentions[0]
            continue

        # -----------------------------
        # Owner CONFIRMATION detection
        # -----------------------------
        if state.get("pending_owner_request"):
            if l in ["yes", "ok", "okay", "sure", "i will"] and user == state["pending_owner_request"]:
                state["owner"] = sender
                state["pending_owner_request"] = None

                incident_state.add_timeline_event(
                    channel, f"Owner assigned to {sender}"
                )

                updated = True
                continue

        # -----------------------------
        # Status detection
        # -----------------------------
        status = extract_status(line)
        if status and status != state.get("status"):
            state["status"] = status

            incident_state.add_timeline_event(
                channel, f"Status updated to {status}"
            )

            updated = True
            continue

        # -----------------------------
        # Jira detection
        # -----------------------------
        jira_id = extract_jira_id(line)
        if jira_id and jira_id != state.get("jira_id"):
            state["jira_id"] = jira_id

            incident_state.add_timeline_event(
                channel, f"Jira linked: {jira_id}"
            )

            updated = True
            continue

        # -----------------------------
        # Link / Reference detection
        # -----------------------------
        links = extract_links(line)
        for link in links:
            if link not in state["links"]:
                state["links"].append(link)

                incident_state.add_timeline_event(
                    channel, f"Reference added: {link}"
                )

                updated = True

        # -----------------------------
        # Explicit / implicit owner detection
        # -----------------------------
        owner = extract_owner(line, sender)
        if owner and owner != state.get("owner"):
            state["owner"] = owner

            incident_state.add_timeline_event(
                channel, f"Owner assigned to {owner}"
            )

            updated = True
            continue

        # -----------------------------
        # ETA detection
        # -----------------------------
        eta = extract_eta(line)
        if eta and eta != state.get("eta"):
            state["eta"] = eta

            incident_state.add_timeline_event(
                channel, f"ETA set to {eta}"
            )

            updated = True
            continue

        # -----------------------------
        # Action detection
        # -----------------------------
        action = extract_action(line, sender)
        if action and action not in state["actions"]:
            state["actions"].append(action)

            incident_state.add_timeline_event(
                channel, f"Action added: {action}"
            )

            updated = True
            continue

    # -----------------------------
    # FINAL: Render / update summary
    # -----------------------------
    if updated or incident_started:
        summary_text = render_summary(state)

        if channel in PINNED_MESSAGES:
            client.chat_update(
                channel=channel,
                ts=PINNED_MESSAGES[channel],
                text=summary_text
            )
        else:
            msg = client.chat_postMessage(
                channel=channel,
                text=summary_text
            )
            client.pins_add(channel=channel, timestamp=msg["ts"])
            PINNED_MESSAGES[channel] = msg["ts"]

        state["just_started"] = False


# -----------------------------
# Resolve Incident Command
# -----------------------------
@app.command("/resolve-incident")
def resolve_incident(ack, body, client, logger):
    # ACK IMMEDIATELY
    ack()

    try:
        channel = body["channel_id"]

        if not incident_state.is_active(channel):
            client.chat_postEphemeral(
                channel=channel,
                user=body["user_id"],
                text="⚠️ No active incident found in this channel."
            )
            return

        state = incident_state.get_state(channel)

        # Update status
        state["status"] = "Resolved"
        incident_state.add_timeline_event(channel, "Incident resolved")

        # Update pinned summary
        if channel in PINNED_MESSAGES:
            client.chat_update(
                channel=channel,
                ts=PINNED_MESSAGES[channel],
                text=render_summary(state)
            )

            # Unpin
            client.pins_remove(
                channel=channel,
                timestamp=PINNED_MESSAGES[channel]
            )

            del PINNED_MESSAGES[channel]

        # Clear state LAST
        incident_state.clear(channel)

        # Confirmation message
        client.chat_postMessage(
            channel=channel,
            text="✅ Incident has been marked as *Resolved* and tracking has stopped."
        )

    except Exception as e:
        logger.exception("Resolve incident failed")
        client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text=f"❌ Failed to resolve incident: `{str(e)}`"
        )

@app.action("confirm_incident")
def confirm_incident(ack, body, client):
    ack()
    channel = body["channel"]["id"]

    if not incident_state.is_active(channel):
        incident_state.start_incident(channel)
        incident_state.add_timeline_event(
            channel, "Incident confirmed by user"
        )

    pending_confirmations.pop(channel, None)

    state = incident_state.get_state(channel)
    summary = render_summary(state)

    msg = client.chat_postMessage(channel=channel, text=summary)
    client.pins_add(channel=channel, timestamp=msg["ts"])
    PINNED_MESSAGES[channel] = msg["ts"]

    client.chat_postMessage(
        channel=channel,
        text="🚨 Incident tracking has started."
    )


@app.action("ignore_incident")
def ignore_incident(ack, body):
    ack()
    channel = body["channel"]["id"]
    pending_confirmations.pop(channel, None)

# -----------------------------
# App mention
# -----------------------------
@app.event("app_mention")
def mention_handler(event, say):
    say("👀 I am tracking this incident.")


# -----------------------------
# Start App
# -----------------------------
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()