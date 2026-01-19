# Slack Incident Bot (Incident Intelligence Bot)

A lightweight Slack bot that **detects probable incidents in Slack conversations**, starts tracking them, and keeps a **pinned incident summary** updated as new details arrive.

The bot uses **rule-based intent detection** (HIGH / MEDIUM / LOW):

- **HIGH**: Automatically starts incident tracking
- **MEDIUM**: Asks for confirmation (“Track Incident” / “Ignore”)
- **LOW**: Ignores the message

## What it does

- **Detects incidents** from messages using keyword + urgency vocab
- **Tracks incident state per Slack channel** (in memory)
- **Extracts key details** from messages:
  - **Owner**
  - **Status**
  - **ETA**
  - **Jira ID**
  - **Actions**
  - **Links / references**
- **Posts and pins an “Incident Summary”** message
- **Updates the pinned summary** as the incident evolves
- **Resolves incidents** via `/resolve-incident` (unpins summary + clears state)

## How detection works (HIGH / MEDIUM / LOW)

The rule-based classifier checks each message line for:

- **Incident keywords** (e.g. “bug”, “issue”, “failure”)
- **Urgency keywords** (e.g. “p1”, “sev1”, “critical”, “prod down”)

Behavior:

- **HIGH** = incident keyword + urgency keyword → auto-track
- **MEDIUM** = incident keyword only → implies possible incident → ask confirmation
- **LOW** = no incident keyword → ignore

Vocabulary lives in `vocabulary/incident_vocabulary.py`.

## Repository structure

- `app.py`: Slack Bolt app (Socket Mode) + message handling + summary pin/update
- `incident_state.py`: In-memory incident store per channel
- `summary_renderer.py`: Renders the pinned incident summary text
- `utils/`: Intent + field extraction helpers (owner/status/eta/jira/actions/links)
- `vocabulary/`: Keyword lists and phrase dictionaries

## Requirements

- **Python 3.10+** recommended
- A Slack app configured for **Socket Mode**

Python dependencies are in `requirements.txt`:

- `slack-bolt`
- `slack-sdk`
- `requests`

## Slack app setup (required)

In your Slack App configuration:

- **Socket Mode**: Enabled
  - Create an app-level token with the scope **`connections:write`**
- **Interactivity & Shortcuts**: Enabled (required for the confirmation buttons)
- **Event Subscriptions**: Enabled
  - Subscribe to relevant events (depending on where you’ll run the bot):
    - Public channels: `message.channels`
    - Private channels: `message.groups`
    - DMs: `message.im`
  - `app_mention` is optional (the bot responds to mentions)
- **Slash command**:
  - Create `/resolve-incident`
- **Bot Token Scopes** (typical minimum; add more only if needed):
  - `chat:write`
  - `channels:history` (for public channels)
  - `groups:history` (for private channels, if used)
  - `im:history` (for DMs, if used)
  - `pins:write` (to pin/unpin the summary)
  - `commands` (for slash commands)

After changing scopes/events, **reinstall the app** to your workspace.

## Getting started (clone + run)

### 1) Clone the repository

```bash
git clone <your-repo-url>
cd slack_incident_bot
```

### 2) Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Set environment variables

You must set:

- `SLACK_BOT_TOKEN` — starts with `xoxb-...`
- `SLACK_APP_TOKEN` — Socket Mode token, starts with `xapp-...`

**Windows PowerShell:**

```powershell
$env:SLACK_BOT_TOKEN="xoxb-..."
$env:SLACK_APP_TOKEN="xapp-..."
```

**macOS/Linux:**

```bash
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."
```

### 5) Run the bot

```bash
python app.py
```

Invite the bot to the channel you want to test.

## Testing scenarios (manual)

Send messages in a channel where the bot is present.

- **HIGH (auto-track)**: include an incident keyword + urgency keyword
  - Example: `prod down - critical issue`
  - Expected: tracking starts automatically; summary is posted + pinned

- **MEDIUM (confirmation)**: include incident keyword only
  - Example: `We observed a bug`
  - Expected: bot asks if it should track; click **Yes – Track Incident** to start

- **LOW (ignored)**: no incident keyword
  - Example: `good morning team`
  - Expected: no bot action

### Resolve

Run:

```text
/resolve-incident
```

Expected:

- incident status becomes **Resolved**
- pinned summary is **unpinned**
- incident state is cleared

## Notes / limitations

- **State is in-memory only**: restarting the process clears all active incidents.
- **Per-channel tracking**: each Slack channel can have its own incident state.
- **Keyword-based**: detection accuracy depends on `vocabulary/incident_vocabulary.py`.

## Troubleshooting

- **Bot doesn’t respond**:
  - Verify the app is running (`python app.py`)
  - Ensure the bot is invited to the channel
  - Check Event Subscriptions + scopes and reinstall the app

- **Buttons don’t work**:
  - Enable **Interactivity & Shortcuts**

- **Socket Mode not connecting**:
  - Confirm `SLACK_APP_TOKEN` (starts with `xapp-...`) and scope `connections:write`

