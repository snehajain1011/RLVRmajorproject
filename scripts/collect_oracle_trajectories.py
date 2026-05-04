from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluate_browsergym_rlvr import OPTIMAL_STEPS, TASK_IDS, run_episode
from social_rlvr_web.oracle_policy import DynamicOraclePolicy
from social_rlvr_web.variants import iter_variant_ids, normalize_variant_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits", default="train")
    parser.add_argument("--train-count", type=int, default=50)
    parser.add_argument("--val-count", type=int, default=20)
    parser.add_argument("--test-count", type=int, default=20)
    parser.add_argument("--tasks", default=",".join(TASK_IDS))
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "rollouts" / "oracle_trajectories.jsonl")
    args = parser.parse_args()

    counts = {"train": args.train_count, "val": args.val_count, "test": args.test_count}
    task_ids = [item.strip() for item in args.tasks.split(",") if item.strip()]
    rows = []
    for split in [item.strip() for item in args.splits.split(",") if item.strip()]:
        for variant_id in iter_variant_ids(split, counts[split]):
            for task_id in task_ids:
                max_steps = max(OPTIMAL_STEPS[task_id], 12)
                episode = run_episode(
                    task_id,
                    DynamicOraclePolicy(),
                    max_steps,
                    variant_id=normalize_variant_id(variant_id),
                )
                rows.append(episode)
                print(
                    f'{task_id} | {variant_id} | success={episode["success"]} '
                    f'steps={episode["steps"]} | {episode["verifier_message"]}'
                )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"Wrote {len(rows)} oracle trajectories to {args.out.resolve()}")


if __name__ == "__main__":
    main()
