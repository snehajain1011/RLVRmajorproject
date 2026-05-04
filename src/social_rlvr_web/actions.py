from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


ALLOWED_ACTION_TYPES = {"click", "fill", "select_option", "noop"}


@dataclass(frozen=True)
class ActionValidation:
    valid: bool
    action: str
    reason: str = ""


def action_dict_to_browsergym(action: dict[str, Any]) -> ActionValidation:
    action_type = action.get("type")
    if action_type not in ALLOWED_ACTION_TYPES:
        return ActionValidation(False, "noop(100)", f"unknown action type {action_type!r}")
    if action_type == "noop":
        return ActionValidation(True, "noop(100)")
    bid = str(action.get("bid", "")).strip()
    if not bid:
        return ActionValidation(False, "noop(100)", "missing bid")
    if action_type == "click":
        return ActionValidation(True, f'click("{bid}")')
    value = str(action.get("value", ""))
    escaped_value = json.dumps(value)
    if action_type == "fill":
        return ActionValidation(True, f'fill("{bid}", {escaped_value})')
    if action_type == "select_option":
        return ActionValidation(True, f'select_option("{bid}", {escaped_value})')
    return ActionValidation(False, "noop(100)", "unreachable action validation branch")


def browsergym_action_to_dict(action: str) -> dict[str, Any]:
    if action.startswith("noop"):
        return {"type": "noop"}
    for action_type in ("click", "fill", "select_option"):
        prefix = f"{action_type}("
        if not action.startswith(prefix) or not action.endswith(")"):
            continue
        args = json.loads(f"[{action[len(prefix):-1]}]")
        if action_type == "click":
            return {"type": "click", "bid": str(args[0])}
        return {"type": action_type, "bid": str(args[0]), "value": str(args[1])}
    raise ValueError(f"Unsupported BrowserGym action: {action}")


def valid_bid_set(axtree: Any) -> set[str]:
    if not isinstance(axtree, dict):
        return set()
    bids: set[str] = set()
    for node in axtree.get("nodes", []):
        if isinstance(node, dict) and "browsergym_id" in node:
            bids.add(str(node["browsergym_id"]))
    return bids


def validate_bid(action: str, obs: dict[str, Any]) -> ActionValidation:
    try:
        action_dict = browsergym_action_to_dict(action)
    except ValueError as exc:
        return ActionValidation(False, "noop(100)", str(exc))
    if action_dict["type"] == "noop":
        return ActionValidation(True, action)
    bid = action_dict.get("bid")
    if bid not in valid_bid_set(obs.get("axtree_object")):
        return ActionValidation(False, "noop(100)", f"bid {bid!r} is not valid in current observation")
    return ActionValidation(True, action)
