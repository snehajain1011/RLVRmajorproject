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
    expected_recipients = ["Kabir", "Meera", "Riya", "Vivaan", "Zara"]
    messages = state.get("messages", [])
    good = [
        msg
        for msg in messages
        if msg.get("recipient") in expected_recipients
        and msg.get("text", "").strip().lower() == "happy new year"
    ]
    recipients = {msg["recipient"] for msg in good}
    if recipients == set(expected_recipients):
        return True, "all five target recipients received the exact greeting"
    return False, f"sent valid greeting to {len(recipients)}/5 required recipients"


def verify_gallery(state: dict) -> tuple[bool, str]:
    shares = state.get("shared_images", [])
    for share in shares:
        if share.get("image_id") == "img_travel" and share.get("recipient") == "Meera":
            return True, "aesthetic travel image shared with Meera"
    return False, "expected image/recipient pair not found"


def verify_report(state: dict) -> tuple[bool, str]:
    reports = state.get("reports", [])
    for report in reports:
        if report.get("tracking_code") == "TRV-8429-IN":
            return True, "tracking code submitted correctly"
    return False, "correct tracking code not submitted"


def verify_priority_followup(state: dict) -> tuple[bool, str]:
    followups = state.get("followups", [])
    for followup in followups:
        if (
            followup.get("recipient") == "Meera"
            and followup.get("reference") == "REF-MEERA-774"
            and followup.get("note", "").strip().lower() == "priority follow-up"
        ):
            return True, "high priority Meera order follow-up created correctly"
    return False, "expected priority follow-up not found"


def verify_team_sync(state: dict) -> tuple[bool, str]:
    meetings = state.get("meetings", [])
    for meeting in meetings:
        attendees = set(meeting.get("attendees", []))
        if (
            meeting.get("title", "").strip().lower() == "design review"
            and meeting.get("slot") == "Fri 14:00"
            and attendees == {"Kabir", "Zara"}
        ):
            return True, "design review scheduled with Kabir and Zara in the shared slot"
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


def reset_state(base_url: str) -> None:
    response = requests.post(f"{base_url}/api/reset", timeout=5)
    response.raise_for_status()
