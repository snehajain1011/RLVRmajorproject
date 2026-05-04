from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import requests


Verifier = Callable[[dict], tuple[bool, str]]


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    start_path: str
    instruction: str
    max_steps: int
    verifier: Verifier


def verify_messages(state: dict) -> tuple[bool, str]:
    expected = state.get("expected", {})
    expected_recipients = expected.get("recipients", ["Kabir", "Meera", "Riya", "Vivaan", "Zara"])
    expected_text = expected.get("text", "Happy New Year")
    messages = state.get("messages", [])
    good = [
        msg
        for msg in messages
        if msg.get("recipient") in expected_recipients
        and msg.get("text", "").strip().lower() == expected_text.lower()
    ]
    recipients = {msg["recipient"] for msg in good}
    if recipients == set(expected_recipients):
        return True, "all five target recipients received the exact greeting"
    return False, f"sent valid greeting to {len(recipients)}/5 required recipients"


def verify_gallery(state: dict) -> tuple[bool, str]:
    expected = state.get("expected", {})
    expected_image = expected.get("image_id", "img_travel")
    expected_recipient = expected.get("recipient", "Meera")
    shares = state.get("shared_images", [])
    for share in shares:
        if share.get("image_id") == expected_image and share.get("recipient") == expected_recipient:
            return True, f"expected image shared with {expected_recipient}"
    return False, "expected image/recipient pair not found"


def verify_report(state: dict) -> tuple[bool, str]:
    expected_code = state.get("expected", {}).get("tracking_code", "TRV-8429-IN")
    reports = state.get("reports", [])
    for report in reports:
        if report.get("tracking_code") == expected_code:
            return True, "tracking code submitted correctly"
    return False, "correct tracking code not submitted"


def verify_priority_followup(state: dict) -> tuple[bool, str]:
    expected = state.get("expected", {})
    expected_recipient = expected.get("recipient", "Meera")
    expected_reference = expected.get("reference", "REF-MEERA-774")
    expected_note = expected.get("note", "Priority follow-up")
    followups = state.get("followups", [])
    for followup in followups:
        if (
            followup.get("recipient") == expected_recipient
            and followup.get("reference") == expected_reference
            and followup.get("note", "").strip().lower() == expected_note.lower()
        ):
            return True, f"high priority {expected_recipient} order follow-up created correctly"
    return False, "expected priority follow-up not found"


def verify_team_sync(state: dict) -> tuple[bool, str]:
    expected = state.get("expected", {})
    expected_title = expected.get("title", "Design review")
    expected_slot = expected.get("slot", "Fri 14:00")
    expected_attendees = set(expected.get("attendees", ["Kabir", "Zara"]))
    meetings = state.get("meetings", [])
    for meeting in meetings:
        attendees = set(meeting.get("attendees", []))
        if (
            meeting.get("title", "").strip().lower() == expected_title.lower()
            and meeting.get("slot") == expected_slot
            and attendees == expected_attendees
        ):
            return True, "design review scheduled with expected attendees in the shared slot"
    return False, "expected design review meeting not found"


TASKS = {
    "messages.last_five_new_year": TaskSpec(
        task_id="messages.last_five_new_year",
        start_path="/messages",
        instruction='Send "Happy New Year" to the last five friends.',
        max_steps=25,
        verifier=verify_messages,
    ),
    "gallery.aesthetic_travel_to_meera": TaskSpec(
        task_id="gallery.aesthetic_travel_to_meera",
        start_path="/gallery",
        instruction="Find an aesthetic travel image and send it to Meera.",
        max_steps=8,
        verifier=verify_gallery,
    ),
    "report.extract_tracking_code": TaskSpec(
        task_id="report.extract_tracking_code",
        start_path="/report",
        instruction="Extract the shipment tracking code into the report form.",
        max_steps=8,
        verifier=verify_report,
    ),
    "orders.priority_followup": TaskSpec(
        task_id="orders.priority_followup",
        start_path="/orders",
        instruction=(
            'Find the high priority order, then create a follow-up for that owner with the '
            'exact reference code and note "Priority follow-up".'
        ),
        max_steps=10,
        verifier=verify_priority_followup,
    ),
    "schedule.design_review_shared_slot": TaskSpec(
        task_id="schedule.design_review_shared_slot",
        start_path="/schedule",
        instruction=(
            "Schedule a design review with Kabir and Zara in the only shared open slot."
        ),
        max_steps=12,
        verifier=verify_team_sync,
    ),
}


def fetch_state(base_url: str) -> dict:
    response = requests.get(f"{base_url}/api/state", timeout=5)
    response.raise_for_status()
    return response.json()


def reset_state(base_url: str, task_id: str | None = None, variant_id: str | None = None) -> None:
    payload = {}
    if task_id:
        payload["task_id"] = task_id
    if variant_id:
        payload["variant_id"] = variant_id
    response = requests.post(f"{base_url}/api/reset", json=payload, timeout=5)
    response.raise_for_status()
