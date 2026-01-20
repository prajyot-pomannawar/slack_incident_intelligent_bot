"""
Slack Incident Intelligence Bot (main entrypoint).

This file wires Slack events/commands/actions to the bot's incident-tracking logic,
updates in-memory state, and keeps a pinned incident summary refreshed in the channel.
"""

import os
import re
import time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import incident_state

from utils.owner_detection import extract_owner, detect_owner_question
from utils.action_detection import extract_action
from utils.eta_detection import extract_eta
from utils.status_detection import extract_status
from utils.jira_detection import extract_jira_id
from summary_renderer import render_summary, render_summary_blocks, render_summary_text
from utils.incident_classifier import classify_incident_intent
from utils.confirmation import ask_incident_confirmation
from utils.link_detection import extract_links
from utils.abstract_detection import extract_abstract
from utils.action_items import (
    add_action_item,
    infer_owner_from_text,
    normalize_actions,
    split_actions,
    update_action_item,
)


app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Track pinned summary per channel
PINNED_MESSAGES = {}
# channel_id -> detected message line (for MEDIUM confirmation flows)
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
                pending_confirmations[channel] = line

            return  # ⛔ stop further processing

    # If incident is still not active, ignore message
    if not incident_state.is_active(channel):
        return

    # -----------------------------
    # STEP 2: Normal incident processing
    # -----------------------------
    state = incident_state.get_state(channel)
    normalize_actions(state)
    updated = False

    for line in lines:
        l = line.lower()

        # -----------------------------
        # Abstract (short one-liner) detection
        # -----------------------------
        if (not state.get("abstract")) or state.get("abstract") == "TBD":
            abstract = extract_abstract(line)
            if abstract:
                state["abstract"] = abstract
                incident_state.add_timeline_event(channel, f"Abstract set to {abstract}")
                updated = True

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
        if action:
            # Create a structured action item; infer owner/due from text if possible.
            # NOTE: Don't default owner to the sender. If the message doesn't explicitly
            # assign someone, keep owner as None (can be set later via modal).
            owner = infer_owner_from_text(action)
            due = extract_eta(line)  # lightweight reuse; ok if None

            # De-dupe by text among OPEN actions
            open_items, _done_items = split_actions(state)
            if any((a.get("text") or "") == action for a in open_items):
                continue

            item = add_action_item(state, action, created_by=sender, owner=owner, due=due)
            incident_state.add_timeline_event(channel, f"Action added: #{item['id']}")
            updated = True
            continue

    # -----------------------------
    # FINAL: Render / update summary
    # -----------------------------
    if updated or incident_started:
        summary_text = render_summary_text(state)
        summary_blocks = render_summary_blocks(state, channel_id=channel)

        if channel in PINNED_MESSAGES:
            client.chat_update(
                channel=channel,
                ts=PINNED_MESSAGES[channel],
                text=summary_text,
                blocks=summary_blocks,
            )
        else:
            msg = client.chat_postMessage(
                channel=channel,
                text=summary_text,
                blocks=summary_blocks,
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
                text=render_summary_text(state),
                blocks=render_summary_blocks(state, channel_id=channel),
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

    detected_line = pending_confirmations.pop(channel, None)

    state = incident_state.get_state(channel)
    normalize_actions(state)

    # Try to set abstract from the originally detected line (MEDIUM flow)
    if detected_line and ((not state.get("abstract")) or state.get("abstract") == "TBD"):
        abstract = extract_abstract(detected_line)
        if abstract:
            state["abstract"] = abstract
            incident_state.add_timeline_event(channel, f"Abstract set to {abstract}")

    summary = render_summary_text(state)
    summary_blocks = render_summary_blocks(state, channel_id=channel)

    msg = client.chat_postMessage(channel=channel, text=summary, blocks=summary_blocks)
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
# Manage Actions (Modal)
# -----------------------------
@app.action("manage_actions")
def manage_actions(ack, body, client, logger):
    ack()

    try:
        channel = body["channel"]["id"]
        trigger_id = body.get("trigger_id")
        if not trigger_id:
            return

        if not incident_state.is_active(channel):
            client.chat_postEphemeral(
                channel=channel,
                user=body["user"]["id"],
                text="⚠️ No active incident in this channel.",
            )
            return

        state = incident_state.get_state(channel)
        normalize_actions(state)

        # Build options for existing actions
        options = []
        for a in state.get("actions", [])[-100:]:
            try:
                aid = a.get("id")
                status = a.get("status", "open")
                text = (a.get("text") or "").strip()
                label = f"#{aid} [{status}] {text}"[:75]
                options.append(
                    {
                        "text": {"type": "plain_text", "text": label},
                        "value": str(aid),
                    }
                )
            except Exception:
                continue

        view = {
            "type": "modal",
            "callback_id": "manage_actions_modal",
            "private_metadata": channel,
            "title": {"type": "plain_text", "text": "Manage Actions"},
            "submit": {"type": "plain_text", "text": "Save"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Add a new action item, or edit an existing one (owner, due date, status).",
                    },
                },
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "edit_select",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Select action to edit"},
                    "element": {
                        "type": "static_select",
                        "action_id": "selected_action",
                        "placeholder": {"type": "plain_text", "text": "Choose an action"},
                        "options": options or [
                            {
                                "text": {"type": "plain_text", "text": "No actions yet"},
                                "value": "0",
                            }
                        ],
                    },
                },
                {
                    "type": "input",
                    "block_id": "edit_owner",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Edit owner"},
                    "element": {"type": "users_select", "action_id": "owner"},
                },
                {
                    "type": "input",
                    "block_id": "edit_due",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Edit due date"},
                    "element": {"type": "datepicker", "action_id": "due"},
                },
                {
                    "type": "input",
                    "block_id": "edit_status",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Edit status"},
                    "element": {
                        "type": "static_select",
                        "action_id": "status",
                        "placeholder": {"type": "plain_text", "text": "Open or Done"},
                        "options": [
                            {"text": {"type": "plain_text", "text": "Open"}, "value": "open"},
                            {"text": {"type": "plain_text", "text": "Done"}, "value": "done"},
                        ],
                    },
                },
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "new_text",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Add new action item"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "text",
                        "placeholder": {"type": "plain_text", "text": "e.g. Investigate WebUI bug in login flow"},
                    },
                },
                {
                    "type": "input",
                    "block_id": "new_owner",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "New action owner (optional)"},
                    "element": {"type": "users_select", "action_id": "owner"},
                },
                {
                    "type": "input",
                    "block_id": "new_due",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "New action due date (optional)"},
                    "element": {"type": "datepicker", "action_id": "due"},
                },
            ],
        }

        # Network/proxy environments can cause transient TLS EOFs. Retry quickly
        # within the trigger_id validity window.
        last_err = None
        for attempt in range(3):
            try:
                client.views_open(trigger_id=trigger_id, view=view)
                last_err = None
                break
            except Exception as e:
                last_err = e
                # Short backoff; keep under trigger_id expiry.
                time.sleep(0.25 * (attempt + 1))

        if last_err is not None:
            raise last_err

    except Exception:
        logger.exception("Failed to open Manage Actions modal")


@app.view("manage_actions_modal")
def manage_actions_submit(ack, body, client, logger, view):
    ack()

    try:
        channel = (view.get("private_metadata") or "").strip()
        if not channel:
            return

        if not incident_state.is_active(channel):
            return

        state = incident_state.get_state(channel)
        normalize_actions(state)

        values = (view.get("state") or {}).get("values") or {}

        def _val(block_id: str, action_id: str):
            b = values.get(block_id) or {}
            a = b.get(action_id) or {}
            return a

        # Add new action (if provided)
        new_text = (_val("new_text", "text").get("value") or "").strip()
        new_owner_id = _val("new_owner", "owner").get("selected_user")
        new_due = _val("new_due", "due").get("selected_date")
        created_by = f"<@{body['user']['id']}>"

        if new_text:
            new_owner = f"<@{new_owner_id}>" if new_owner_id else None
            item = add_action_item(state, new_text, created_by=created_by, owner=new_owner, due=new_due)
            incident_state.add_timeline_event(channel, f"Action added via modal: #{item['id']}")

        # Edit existing action (if selected)
        selected = _val("edit_select", "selected_action").get("selected_option")
        if selected and selected.get("value") and selected.get("value") != "0":
            action_id = int(selected["value"])
            owner_id = _val("edit_owner", "owner").get("selected_user")
            due = _val("edit_due", "due").get("selected_date")
            status_opt = _val("edit_status", "status").get("selected_option")
            status = status_opt.get("value") if status_opt else None

            owner = f"<@{owner_id}>" if owner_id else None
            updated_item = update_action_item(
                state,
                action_id,
                owner=owner,
                due=due,
                status=status,
                done_by=created_by,
            )
            if updated_item:
                incident_state.add_timeline_event(channel, f"Action updated via modal: #{action_id}")

        # Update pinned summary message
        if channel in PINNED_MESSAGES:
            summary_text = render_summary_text(state)
            client.chat_update(
                channel=channel,
                ts=PINNED_MESSAGES[channel],
                text=summary_text,
                blocks=render_summary_blocks(state, channel_id=channel),
            )

    except Exception:
        logger.exception("Failed to submit Manage Actions modal")

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