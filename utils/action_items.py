"""
Structured action-item storage helpers.

This module defines how action items are represented in incident state (id/text/owner/due/status),
including backward-compatible migration from legacy string-based actions.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


MENTION_REGEX = re.compile(r"<@([A-Z0-9]+)>")


def _now_ts() -> str:
    return datetime.now().strftime("%d %b %Y, %I:%M %p")


def normalize_actions(state: Dict[str, Any]) -> None:
    """
    Ensure state['actions'] is a list of dict action-items and state has next_action_id.
    Backward compatible with earlier versions that stored actions as list[str].
    """

    actions = state.get("actions")
    if actions is None:
        state["actions"] = []
        state["next_action_id"] = state.get("next_action_id", 1) or 1
        return

    if not isinstance(actions, list):
        state["actions"] = []
        state["next_action_id"] = state.get("next_action_id", 1) or 1
        return

    next_id = state.get("next_action_id")
    if not isinstance(next_id, int) or next_id < 1:
        next_id = 1

    # If legacy list[str], migrate.
    if actions and isinstance(actions[0], str):
        migrated: List[Dict[str, Any]] = []
        for a in actions:
            if not isinstance(a, str):
                continue
            migrated.append(
                {
                    "id": next_id,
                    "text": a.strip(),
                    "owner": None,
                    "due": None,
                    "status": "open",
                    "created_at": _now_ts(),
                    "created_by": None,
                    "done_at": None,
                    "done_by": None,
                }
            )
            next_id += 1
        state["actions"] = migrated

    # Normalize dict items, and compute next id safely.
    max_id = 0
    normalized: List[Dict[str, Any]] = []
    for item in state.get("actions", []):
        if isinstance(item, str):
            # Mixed legacy content, migrate on the fly.
            item = {
                "id": next_id,
                "text": item.strip(),
                "owner": None,
                "due": None,
                "status": "open",
                "created_at": _now_ts(),
                "created_by": None,
                "done_at": None,
                "done_by": None,
            }
            next_id += 1

        if not isinstance(item, dict):
            continue

        item_id = item.get("id")
        if not isinstance(item_id, int):
            item_id = next_id
            next_id += 1

        status = item.get("status") if item.get("status") in {"open", "done"} else "open"

        normalized.append(
            {
                "id": item_id,
                "text": str(item.get("text") or "").strip(),
                "owner": item.get("owner"),
                "due": item.get("due"),
                "status": status,
                "created_at": item.get("created_at") or _now_ts(),
                "created_by": item.get("created_by"),
                "done_at": item.get("done_at"),
                "done_by": item.get("done_by"),
            }
        )
        max_id = max(max_id, item_id)

    state["actions"] = normalized
    state["next_action_id"] = max(max_id + 1, next_id, 1)


def split_actions(state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    normalize_actions(state)
    open_items: List[Dict[str, Any]] = []
    done_items: List[Dict[str, Any]] = []
    for a in state.get("actions", []):
        if a.get("status") == "done":
            done_items.append(a)
        else:
            open_items.append(a)
    return open_items, done_items


def infer_owner_from_text(text: str) -> Optional[str]:
    """
    If the text contains a Slack mention, treat the first mention as the action owner.
    Returns "<@USERID>" or None.
    """

    if not text:
        return None
    m = MENTION_REGEX.search(text)
    if not m:
        return None
    return f"<@{m.group(1)}>"


def add_action_item(
    state: Dict[str, Any],
    text: str,
    *,
    created_by: Optional[str] = None,
    owner: Optional[str] = None,
    due: Optional[str] = None,
) -> Dict[str, Any]:
    normalize_actions(state)

    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("action text is empty")

    item_id = int(state.get("next_action_id") or 1)
    state["next_action_id"] = item_id + 1

    item = {
        "id": item_id,
        "text": cleaned,
        "owner": owner,
        "due": due,
        "status": "open",
        "created_at": _now_ts(),
        "created_by": created_by,
        "done_at": None,
        "done_by": None,
    }
    state["actions"].append(item)
    return item


def update_action_item(
    state: Dict[str, Any],
    action_id: int,
    *,
    text: Optional[str] = None,
    owner: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None,
    done_by: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    normalize_actions(state)

    for item in state.get("actions", []):
        if item.get("id") == action_id:
            if text is not None and str(text).strip():
                item["text"] = str(text).strip()
            if owner is not None:
                item["owner"] = owner
            if due is not None:
                item["due"] = due
            if status in {"open", "done"}:
                item["status"] = status
                if status == "done":
                    item["done_at"] = _now_ts()
                    item["done_by"] = done_by
                else:
                    item["done_at"] = None
                    item["done_by"] = None
            return item
    return None

