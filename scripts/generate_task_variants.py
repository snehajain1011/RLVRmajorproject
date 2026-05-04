from __future__ import annotations

import argparse
import json
from pathlib import Path

from social_rlvr_web.variants import get_task_variant, iter_variant_ids


TASK_IDS = [
    "report.extract_tracking_code",
    "gallery.aesthetic_travel_to_meera",
    "messages.last_five_new_year",
    "orders.priority_followup",
    "schedule.design_review_shared_slot",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-count", type=int, default=50)
    parser.add_argument("--val-count", type=int, default=20)
    parser.add_argument("--test-count", type=int, default=20)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "variants" / "local_variants.json")
    args = parser.parse_args()

    rows = []
    for split, count in [("train", args.train_count), ("val", args.val_count), ("test", args.test_count)]:
        for variant_id in iter_variant_ids(split, count):
            for task_id in TASK_IDS:
                variant = get_task_variant(task_id, variant_id)
                rows.append(
                    {
                        "task_id": task_id,
                        "browsergym_task_id": f"browsergym/social_rlvr.{task_id}",
                        "variant_id": variant.variant_id,
                        "split": variant.split,
                        "instruction": variant.instruction,
                        "expected": variant.expected,
                        "page_data": variant.page_data,
                    }
                )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} variants to {args.out.resolve()}")


if __name__ == "__main__":
    main()
