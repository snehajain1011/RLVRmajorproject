from __future__ import annotations

import argparse
import json
from pathlib import Path

from social_rlvr_web.serializer import BrowserStateSerializer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--augment-factor", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "sft" / "browser_sft.jsonl")
    args = parser.parse_args()

    serializer = BrowserStateSerializer()
    rows = []
    with args.trajectories.open("r", encoding="utf-8") as handle:
        for line in handle:
            episode = json.loads(line)
            history: list[str] = []
            for step in episode.get("trajectory", []):
                action = step["action"]
                # Stored eval artifacts do not keep full observations yet; this dataset is a schema bridge.
                # Full HPC collection should store obs snapshots and use serializer.prompt(obs, history).
                prompt = (
                    f"Goal task: {episode['task_id']}\n"
                    f"Variant: {episode.get('variant_id', 'train_000')}\n"
                    f"History: {history or '(none)'}\n"
                    "Return the next BrowserGym action."
                )
                for aug_idx in range(args.augment_factor):
                    rows.append(
                        {
                            "prompt": prompt,
                            "completion": action,
                            "task_id": episode["task_id"],
                            "variant_id": episode.get("variant_id", "train_000"),
                            "split": episode.get("split", "train"),
                            "source_policy": episode["policy"],
                            "augmentation_id": aug_idx,
                        }
                    )
                history.append(action)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"Wrote {len(rows)} SFT samples to {args.out.resolve()}")
    del serializer


if __name__ == "__main__":
    main()
