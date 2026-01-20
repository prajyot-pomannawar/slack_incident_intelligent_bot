"""
Slack confirmation UI for MEDIUM-confidence incidents.

This module posts an interactive message with buttons (Track / Ignore) to let humans confirm
whether the bot should start tracking a probable incident in the channel.
"""

# utils/confirmation.py


def ask_incident_confirmation(client, channel, line):
    client.chat_postMessage(
        channel=channel,
        text="⚠️ Possible incident detected",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Detected message:*\n>{line}"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Yes – Track Incident"},
                        "style": "danger",
                        "action_id": "confirm_incident",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Ignore"},
                        "action_id": "ignore_incident",
                    },
                ],
            },
        ],
    )
