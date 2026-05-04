from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


CONTACTS = ["Aarav", "Diya", "Kabir", "Meera", "Riya", "Vivaan", "Zara"]
MESSAGE_TEXT = "Happy New Year"

IMAGE_LIBRARY = [
    {
        "id": "img_city",
        "title": "City lights",
        "tags": ["urban", "night", "architecture"],
        "gradient": "linear-gradient(135deg,#1d3557,#a8dadc)",
    },
    {
        "id": "img_travel",
        "title": "Aesthetic travel",
        "tags": ["travel", "aesthetic", "mountains"],
        "gradient": "linear-gradient(135deg,#2a9d8f,#f4a261)",
    },
    {
        "id": "img_food",
        "title": "Cafe dessert",
        "tags": ["food", "dessert", "indoor"],
        "gradient": "linear-gradient(135deg,#6d597a,#e56b6f)",
    },
    {
        "id": "img_garden",
        "title": "Quiet garden",
        "tags": ["nature", "calm", "outdoor"],
        "gradient": "linear-gradient(135deg,#386641,#a7c957)",
    },
]

SLOTS = ["Mon 09:00", "Wed 11:00", "Fri 14:00", "Thu 16:00"]


@dataclass(frozen=True)
class TaskVariant:
    task_id: str
    variant_id: str
    split: str
    instruction: str
    expected: dict[str, Any]
    page_data: dict[str, Any]


def normalize_variant_id(variant_id: str | None) -> str:
    if not variant_id or variant_id == "train":
        return "train_000"
    if variant_id == "val":
        return "val_000"
    if variant_id == "test":
        return "test_000"
    return variant_id


def split_for_variant(variant_id: str) -> str:
    variant_id = normalize_variant_id(variant_id)
    return variant_id.split("_", 1)[0]


def get_task_variant(task_id: str, variant_id: str | None = None) -> TaskVariant:
    variant_id = normalize_variant_id(variant_id)
    split, index_text = variant_id.split("_", 1)
    index = int(index_text)
    seed = {"train": 1000, "val": 2000, "test": 3000}.get(split, 4000) + index
    rng = random.Random(seed + sum(ord(char) for char in task_id))

    if task_id == "report.extract_tracking_code":
        return _report_variant(variant_id, split, rng, index)
    if task_id == "gallery.aesthetic_travel_to_meera":
        return _gallery_variant(variant_id, split, rng)
    if task_id == "messages.last_five_new_year":
        return _messages_variant(variant_id, split, rng)
    if task_id == "orders.priority_followup":
        return _orders_variant(variant_id, split, rng, index)
    if task_id == "schedule.design_review_shared_slot":
        return _schedule_variant(variant_id, split, rng)
    raise KeyError(f"Unknown task id {task_id!r}")


def iter_variant_ids(split: str, count: int) -> list[str]:
    return [f"{split}_{idx:03d}" for idx in range(count)]


def _report_variant(variant_id: str, split: str, rng: random.Random, index: int) -> TaskVariant:
    country = rng.choice(["IN", "US", "SG", "AE", "GB"])
    code = "TRV-8429-IN" if variant_id == "train_000" else f"TRV-{rng.randrange(1000, 9999)}-{country}"
    owner = rng.choice(CONTACTS)
    total = rng.randrange(1200, 9900)
    return TaskVariant(
        task_id="report.extract_tracking_code",
        variant_id=variant_id,
        split=split,
        instruction="Extract the shipment tracking code into the report form.",
        expected={"tracking_code": code},
        page_data={"owner": owner, "invoice_total": total, "tracking_code": code, "index": index},
    )


def _gallery_variant(variant_id: str, split: str, rng: random.Random) -> TaskVariant:
    image = IMAGE_LIBRARY[1] if variant_id == "train_000" else rng.choice(IMAGE_LIBRARY)
    recipient = "Meera" if variant_id == "train_000" else rng.choice(CONTACTS)
    descriptor = image["title"].lower()
    return TaskVariant(
        task_id="gallery.aesthetic_travel_to_meera",
        variant_id=variant_id,
        split=split,
        instruction=f"Find the {descriptor} image and send it to {recipient}.",
        expected={"image_id": image["id"], "recipient": recipient},
        page_data={"images": IMAGE_LIBRARY, "target_title": image["title"], "recipient": recipient},
    )


def _messages_variant(variant_id: str, split: str, rng: random.Random) -> TaskVariant:
    recipients = ["Kabir", "Meera", "Riya", "Vivaan", "Zara"]
    if variant_id != "train_000":
        recipients = rng.sample(CONTACTS, 5)
    return TaskVariant(
        task_id="messages.last_five_new_year",
        variant_id=variant_id,
        split=split,
        instruction=f'Send "{MESSAGE_TEXT}" to these five friends: {", ".join(recipients)}.',
        expected={"recipients": recipients, "text": MESSAGE_TEXT},
        page_data={"recipients": recipients},
    )


def _orders_variant(variant_id: str, split: str, rng: random.Random, index: int) -> TaskVariant:
    high_owner = "Meera" if variant_id == "train_000" else rng.choice(CONTACTS)
    owners = [high_owner] + [name for name in rng.sample(CONTACTS, 3) if name != high_owner]
    while len(owners) < 3:
        candidate = rng.choice(CONTACTS)
        if candidate not in owners:
            owners.append(candidate)
    rng.shuffle(owners)
    reference = "REF-MEERA-774" if variant_id == "train_000" else f"REF-{high_owner.upper()}-{rng.randrange(100, 999)}"
    orders = []
    for owner in owners[:3]:
        is_high = owner == high_owner
        orders.append(
            {
                "owner": owner,
                "priority": "High" if is_high else rng.choice(["Normal", "Low"]),
                "reference": reference if is_high else f"REF-{owner.upper()}-{rng.randrange(100, 999)}",
                "status": "Awaiting follow-up" if is_high else rng.choice(["Packed", "Queued"]),
            }
        )
    return TaskVariant(
        task_id="orders.priority_followup",
        variant_id=variant_id,
        split=split,
        instruction=(
            'Find the high priority order, then create a follow-up for that owner with the '
            'exact reference code and note "Priority follow-up".'
        ),
        expected={"recipient": high_owner, "reference": reference, "note": "Priority follow-up"},
        page_data={"orders": orders, "index": index},
    )


def _schedule_variant(variant_id: str, split: str, rng: random.Random) -> TaskVariant:
    attendees = ["Kabir", "Zara"] if variant_id == "train_000" else sorted(rng.sample(CONTACTS, 2))
    slot = "Fri 14:00" if variant_id == "train_000" else rng.choice(SLOTS)
    availability = []
    for contact in CONTACTS:
        row = {"person": contact}
        for candidate_slot in SLOTS:
            row[candidate_slot] = "Open" if contact in attendees and candidate_slot == slot else "Busy"
        if contact not in attendees:
            row[rng.choice([item for item in SLOTS if item != slot])] = "Open"
        availability.append(row)
    return TaskVariant(
        task_id="schedule.design_review_shared_slot",
        variant_id=variant_id,
        split=split,
        instruction=(
            f"Schedule a design review with {attendees[0]} and {attendees[1]} "
            "in their only shared open slot."
        ),
        expected={"title": "Design review", "slot": slot, "attendees": attendees},
        page_data={"slots": SLOTS, "attendees": attendees, "availability": availability},
    )
