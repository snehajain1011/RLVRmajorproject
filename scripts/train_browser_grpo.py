from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="GRPO entrypoint for the HPC browser-RL pipeline.")
    parser.add_argument("--sft-adapter", type=Path, required=True)
    parser.add_argument("--rollout-groups", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "checkpoints" / "grpo_qwen25_3b")
    parser.parse_args()

    missing = [name for name in ["torch", "trl", "peft", "transformers"] if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit(
            "Missing GRPO dependencies: "
            + ", ".join(missing)
            + "\nInstall the HPC extras before training: pip install -e .[hpc]"
        )
    raise SystemExit(
        "GRPO adapter updates require the HPC online rollout loop. "
        "Use train_browser_rloo.py first to validate terminal-continuation groups; "
        "then connect those groups to TRL GRPOTrainer/RLOOTrainer on the HPC node."
    )


if __name__ == "__main__":
    main()
