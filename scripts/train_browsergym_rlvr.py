from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from evaluate_browsergym_rlvr import (
    TASK_IDS,
    VerifierSelectedPolicy,
    OllamaVisionPolicy,
    run_episode,
)


def safe_policy_name(name: str) -> str:
    return name.replace(":", "_").replace(".", "_").replace("-", "_")


def select_successful_trajectory(episodes: list[dict]) -> dict | None:
    successful = [episode for episode in episodes if episode["success"]]
    if not successful:
        return None
    return sorted(successful, key=lambda episode: (-episode["reward"], episode["steps"]))[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a lightweight verifier-guided RLVR policy artifact."
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--model-steps", type=int, default=4)
    parser.add_argument("--ollama-model", default=os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b"))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--model-no-images", action="store_true")
    parser.add_argument(
        "--tasks",
        default=",".join(TASK_IDS),
        help="Comma-separated BrowserGym task ids to train on.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts") / "rlvr_training" / "learned_policy.json",
    )
    parser.add_argument(
        "--include-scripted-teacher",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Add verifier-selected successful trajectories when model rollouts do not solve a task.",
    )
    args = parser.parse_args()

    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path(".playwright").resolve()))

    task_ids = [item.strip() for item in args.tasks.split(",") if item.strip()]
    unknown_tasks = set(task_ids) - set(TASK_IDS)
    if unknown_tasks:
        raise SystemExit(f"Unknown task ids: {sorted(unknown_tasks)}")

    base_policy_name = safe_policy_name(args.ollama_model)
    all_episodes: list[dict] = []
    task_policies: dict[str, dict] = {}

    for task_id in task_ids:
        task_episodes: list[dict] = []
        for _ in range(args.repeats):
            qwen_policy = OllamaVisionPolicy(
                model=args.ollama_model,
                host=args.ollama_host,
                use_images=not args.model_no_images,
            )
            episode = run_episode(task_id, qwen_policy, args.model_steps)
            task_episodes.append(episode)
            all_episodes.append(episode)
            print(
                f'{episode["policy"]} | {task_id} | success={episode["success"]} '
                f'reward={episode["reward"]} | {episode["verifier_message"]}'
            )

        selected = select_successful_trajectory(task_episodes)
        if selected is None and args.include_scripted_teacher:
            teacher_episode = run_episode(task_id, VerifierSelectedPolicy(), max_eval_steps=25)
            teacher_episode["policy"] = "verifier_guided_teacher"
            task_episodes.append(teacher_episode)
            all_episodes.append(teacher_episode)
            selected = select_successful_trajectory(task_episodes)
            print(
                f'{teacher_episode["policy"]} | {task_id} | success={teacher_episode["success"]} '
                f'reward={teacher_episode["reward"]} | {teacher_episode["verifier_message"]}'
            )

        if selected is None:
            print(f"No successful trajectory selected for {task_id}; skipping learned policy entry.")
            continue

        task_policies[task_id] = {
            "source_policy": selected["policy"],
            "reward": selected["reward"],
            "success": selected["success"],
            "steps": selected["steps"],
            "verifier_message": selected["verifier_message"],
            "actions": [step["action"] for step in selected["trajectory"]],
        }

    artifact = {
        "format_version": 1,
        "method": "verifier_guided_trajectory_distillation",
        "base_policy": base_policy_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "training_config": {
            "repeats": args.repeats,
            "model_steps": args.model_steps,
            "ollama_model": args.ollama_model,
            "model_no_images": args.model_no_images,
            "include_scripted_teacher": args.include_scripted_teacher,
            "tasks": task_ids,
        },
        "task_policies": task_policies,
        "episodes": all_episodes,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print()
    print(f"Wrote learned RLVR policy to {args.out.resolve()}")
    print(f"Learned task policies: {len(task_policies)}/{len(task_ids)}")


if __name__ == "__main__":
    main()
