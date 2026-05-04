from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from social_rlvr_web.variants import iter_variant_ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policies", default="qwen,dynamic_oracle,trajectory_replay")
    parser.add_argument("--tasks", default="")
    parser.add_argument("--train-count", type=int, default=5)
    parser.add_argument("--val-count", type=int, default=5)
    parser.add_argument("--test-count", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "eval_generalization")
    args = parser.parse_args()

    variants = (
        iter_variant_ids("train", args.train_count)
        + iter_variant_ids("val", args.val_count)
        + iter_variant_ids("test", args.test_count)
    )
    command = [
        sys.executable,
        "scripts/evaluate_browsergym_rlvr.py",
        "--policies",
        args.policies,
        "--variants",
        ",".join(variants),
        "--out",
        str(args.out),
    ]
    if args.tasks:
        command.extend(["--tasks", args.tasks])
    subprocess.run(command, check=True)
    subprocess.run(
        [
            sys.executable,
            "scripts/bootstrap_metrics.py",
            "--episode-results",
            str(args.out / "episode_results.csv"),
            "--out",
            str(args.out / "bootstrap_ci.csv"),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
