from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from social_rlvr_web.checkpoints import ReplayCheckpoint
from social_rlvr_web.oracle_policy import DynamicOraclePolicy
from social_rlvr_web.rollout import group_relative_advantages, score_candidate_with_terminal_continuation


def require_hpc_deps() -> None:
    missing = [
        name
        for name in ["torch", "transformers", "peft", "trl", "accelerate"]
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise SystemExit(
            "Missing RL dependencies: "
            + ", ".join(missing)
            + "\nInstall the HPC extras before training: pip install -e .[hpc]"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Step-level sparse terminal-reward RLOO scaffold for BrowserGym."
    )
    parser.add_argument("--task", default="browsergym/social_rlvr.report.extract_tracking_code")
    parser.add_argument("--variant", default="train_000")
    parser.add_argument("--candidate-actions", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "rloo" / "step_groups.jsonl")
    parser.add_argument("--check-deps", action="store_true")
    args = parser.parse_args()

    if args.check_deps:
        require_hpc_deps()

    candidates = json.loads(args.candidate_actions.read_text(encoding="utf-8-sig"))
    if len(candidates) < 2:
        raise SystemExit("Need at least 2 candidate actions for group-relative scoring.")

    checkpoint = ReplayCheckpoint(task_id=args.task, variant_id=args.variant, history=[])
    continuation_policy = DynamicOraclePolicy()
    scores = [
        score_candidate_with_terminal_continuation(
            checkpoint=checkpoint,
            candidate_action=action,
            continuation_policy=continuation_policy,
            max_steps=args.max_steps,
        )
        for action in candidates
    ]
    advantages = group_relative_advantages([score.terminal_reward for score in scores])
    rows = []
    for score, advantage in zip(scores, advantages):
        rows.append(
            {
                "task_id": args.task,
                "variant_id": args.variant,
                "checkpoint_backend": checkpoint.backend,
                "candidate_action": score.candidate_action,
                "terminal_reward": score.terminal_reward,
                "advantage": advantage,
                "success": score.success,
                "valid": score.valid,
                "invalid_reason": score.invalid_reason,
                "continuation_trajectory": score.trajectory,
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    print(f"Wrote {len(rows)} RLOO candidate scores to {args.out.resolve()}")
    print("This script verifies terminal-continuation scoring; adapter-gradient updates run on the HPC path.")


if __name__ == "__main__":
    main()
