from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import gymnasium as gym

import social_rlvr_web.browsergym_tasks  # noqa: F401
from social_rlvr_web.model_policy import ModelPolicyError, OllamaVisionPolicy
from social_rlvr_web.oracle_policy import DynamicOraclePolicy
from social_rlvr_web.rlvr_policy import TrajectoryReplayPolicy, RLVRPolicyError
from social_rlvr_web.variants import normalize_variant_id


TASK_IDS = [
    "browsergym/social_rlvr.report.extract_tracking_code",
    "browsergym/social_rlvr.gallery.aesthetic_travel_to_meera",
    "browsergym/social_rlvr.messages.last_five_new_year",
    "browsergym/social_rlvr.orders.priority_followup",
    "browsergym/social_rlvr.schedule.design_review_shared_slot",
]

OPTIMAL_STEPS = {
    "browsergym/social_rlvr.report.extract_tracking_code": 2,
    "browsergym/social_rlvr.gallery.aesthetic_travel_to_meera": 2,
    "browsergym/social_rlvr.messages.last_five_new_year": 15,
    "browsergym/social_rlvr.orders.priority_followup": 4,
    "browsergym/social_rlvr.schedule.design_review_shared_slot": 5,
}


def bid_for(page, selector: str, index: int = 0) -> str:
    bid = page.locator(selector).nth(index).get_attribute("bid")
    if not bid:
        raise LookupError(f"No BrowserGym bid found for {selector} at index {index}")
    return bid


def bid_for_value(page, selector: str, value: str) -> str:
    count = page.locator(selector).count()
    for index in range(count):
        locator = page.locator(selector).nth(index)
        if locator.get_attribute("value") == value:
            bid = locator.get_attribute("bid")
            if bid:
                return bid
    raise LookupError(f"No BrowserGym bid found for {selector} with value {value!r}")


class Policy(Protocol):
    name: str

    def reset(self, task_id: str) -> None: ...

    def act(self, env, obs: dict) -> str: ...


@dataclass
class HallucinationBaseline:
    """A deliberately weak pre-RLVR baseline: claims completion without state change."""

    name: str = "before_rlvr_hallucination_baseline"
    step: int = 0

    def reset(self, task_id: str) -> None:
        self.step = 0

    def act(self, env, obs: dict) -> str:
        self.step += 1
        if self.step == 1:
            return 'send_msg_to_user("Done")'
        return "noop(100)"


@dataclass
class VerifierSelectedPolicy:
    """Successful trajectories selected by the verifier reward."""

    name: str = "after_rlvr_verifier_selected"
    task_id: str = ""
    cursor: int = 0
    recipients: list[str] = field(default_factory=lambda: ["Kabir", "Meera", "Riya", "Vivaan", "Zara"])

    def reset(self, task_id: str) -> None:
        self.task_id = task_id
        self.cursor = 0

    def act(self, env, obs: dict) -> str:
        page = env.unwrapped.page
        if self.task_id.endswith("report.extract_tracking_code"):
            if self.cursor == 0:
                self.cursor += 1
                return f'fill("{bid_for(page, "input")}", "TRV-8429-IN")'
            self.cursor += 1
            return f'click("{bid_for(page, "button")}")'

        if self.task_id.endswith("gallery.aesthetic_travel_to_meera"):
            if self.cursor == 0:
                self.cursor += 1
                return f'select_option("{bid_for(page, "select", 1)}", "Meera")'
            self.cursor += 1
            return f'click("{bid_for(page, "button", 1)}")'

        if self.task_id.endswith("messages.last_five_new_year"):
            recipient = self.recipients[self.cursor // 3]
            phase = self.cursor % 3
            self.cursor += 1
            if phase == 0:
                return f'select_option("{bid_for(page, "select")}", "{recipient}")'
            if phase == 1:
                return f'fill("{bid_for(page, "textarea")}", "Happy New Year")'
            return f'click("{bid_for(page, "button")}")'

        if self.task_id.endswith("orders.priority_followup"):
            if self.cursor == 0:
                self.cursor += 1
                return f'select_option("{bid_for(page, "select")}", "Meera")'
            if self.cursor == 1:
                self.cursor += 1
                return f'fill("{bid_for(page, "input")}", "REF-MEERA-774")'
            if self.cursor == 2:
                self.cursor += 1
                return f'fill("{bid_for(page, "textarea")}", "Priority follow-up")'
            self.cursor += 1
            return f'click("{bid_for(page, "button")}")'

        if self.task_id.endswith("schedule.design_review_shared_slot"):
            if self.cursor == 0:
                self.cursor += 1
                return f'fill("{bid_for(page, "input")}", "Design review")'
            if self.cursor == 1:
                self.cursor += 1
                return f'select_option("{bid_for(page, "select")}", "Fri 14:00")'
            if self.cursor == 2:
                self.cursor += 1
                return f'click("{bid_for_value(page, "input[type=checkbox]", "Kabir")}")'
            if self.cursor == 3:
                self.cursor += 1
                return f'click("{bid_for_value(page, "input[type=checkbox]", "Zara")}")'
            self.cursor += 1
            return f'click("{bid_for(page, "button")}")'

        raise KeyError(f"No policy for {self.task_id}")


def run_episode(task_id: str, policy: Policy, max_eval_steps: int, variant_id: str = "train_000") -> dict:
    previous_variant = os.environ.get("SOCIAL_RLVR_VARIANT_ID")
    os.environ["SOCIAL_RLVR_VARIANT_ID"] = normalize_variant_id(variant_id)
    env = gym.make(
        task_id,
        headless=True,
        slow_mo=0,
        pre_observation_delay=0.05,
    )
    policy.reset(task_id)
    trajectory = []
    reward = 0.0
    terminated = False
    truncated = False
    info = {"task_info": {"success": False, "verifier_message": "not evaluated"}}
    try:
        obs, reset_info = env.reset()
        if hasattr(policy, "expected"):
            policy.expected = reset_info.get("expected", {})
        for step_idx in range(1, max_eval_steps + 1):
            try:
                action = policy.act(env, obs)
            except (ModelPolicyError, RLVRPolicyError) as exc:
                trajectory.append(
                    {
                        "step": step_idx,
                        "action": "<model_error>",
                        "reward": 0.0,
                        "success": False,
                        "verifier_message": str(exc),
                        "last_action_error": str(exc),
                    }
                )
                info = {"task_info": {"success": False, "verifier_message": str(exc)}}
                break
            obs, reward, terminated, truncated, info = env.step(action)
            task_info = info.get("task_info", {})
            trajectory.append(
                {
                    "step": step_idx,
                    "action": action,
                    "reward": reward,
                    "success": task_info.get("success", False),
                    "verifier_message": task_info.get("verifier_message", ""),
                    "last_action_error": obs.get("last_action_error", ""),
                }
            )
            if terminated or truncated:
                break
    finally:
        env.close()
        if previous_variant is None:
            os.environ.pop("SOCIAL_RLVR_VARIANT_ID", None)
        else:
            os.environ["SOCIAL_RLVR_VARIANT_ID"] = previous_variant

    task_info = info.get("task_info", {})
    success = bool(task_info.get("success", False))
    steps = len(trajectory)
    optimal = OPTIMAL_STEPS[task_id]
    rrr = (optimal / steps) if success and steps else 0.0
    return {
        "policy": policy.name,
        "task_id": task_id,
        "variant_id": normalize_variant_id(variant_id),
        "split": normalize_variant_id(variant_id).split("_", 1)[0],
        "success": success,
        "reward": float(reward),
        "steps": steps,
        "optimal_steps": optimal,
        "rrr": round(rrr, 4),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "verifier_message": task_info.get("verifier_message", ""),
        "trajectory": trajectory,
    }


def summarize(rows: list[dict]) -> list[dict]:
    summaries = []
    keys = sorted({(row["policy"], row.get("split", "unknown")) for row in rows})
    for policy_name, split in keys:
        subset = [row for row in rows if row["policy"] == policy_name and row.get("split", "unknown") == split]
        summaries.append(
            {
                "policy": policy_name,
                "split": split,
                "episodes": len(subset),
                "success_rate": round(sum(row["success"] for row in subset) / len(subset), 4),
                "mean_reward": round(sum(row["reward"] for row in subset) / len(subset), 4),
                "mean_steps": round(sum(row["steps"] for row in subset) / len(subset), 2),
                "mean_rrr": round(sum(row["rrr"] for row in subset) / len(subset), 4),
            }
        )
    return summaries


def print_table(rows: list[dict]) -> None:
    headers = ["policy", "split", "episodes", "success_rate", "mean_reward", "mean_steps", "mean_rrr"]
    widths = {header: len(header) for header in headers}
    for row in rows:
        for header in headers:
            widths[header] = max(widths[header], len(str(row[header])))
    print(" | ".join(header.ljust(widths[header]) for header in headers))
    print("-+-".join("-" * widths[header] for header in headers))
    for row in rows:
        print(" | ".join(str(row[header]).ljust(widths[header]) for header in headers))


def write_artifacts(results: list[dict], summary: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "episode_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "policy",
                "task_id",
                "variant_id",
                "split",
                "success",
                "reward",
                "steps",
                "optimal_steps",
                "rrr",
                "terminated",
                "truncated",
                "verifier_message",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    with (out_dir / "trajectories.jsonl").open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--baseline-steps", type=int, default=3)
    parser.add_argument("--model-steps", type=int, default=20)
    parser.add_argument(
        "--policies",
        default="baseline,qwen,scripted",
        help="Comma-separated: baseline,qwen,scripted,dynamic_oracle,trajectory_replay,rlvr",
    )
    parser.add_argument("--ollama-model", default=os.environ.get("OLLAMA_MODEL", "qwen2.5vl"))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--model-no-images", action="store_true")
    parser.add_argument(
        "--replay-policy",
        type=Path,
        default=Path("artifacts") / "rlvr_training" / "learned_policy.json",
        help="Verifier-selected replay artifact used by --policies trajectory_replay/rlvr.",
    )
    parser.add_argument("--rlvr-policy", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--variants", default="train_000", help="Comma-separated variant ids, e.g. train_000,test_000.")
    parser.add_argument(
        "--tasks",
        default=",".join(TASK_IDS),
        help="Comma-separated BrowserGym task ids to evaluate.",
    )
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "eval_browsergym_rlvr")
    args = parser.parse_args()

    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path(".playwright").resolve()))

    policy_factories = {
        "baseline": lambda: HallucinationBaseline(),
        "qwen": lambda: OllamaVisionPolicy(
            model=args.ollama_model,
            host=args.ollama_host,
            use_images=not args.model_no_images,
        ),
        "scripted": lambda: VerifierSelectedPolicy(),
        "dynamic_oracle": lambda: DynamicOraclePolicy(),
        "trajectory_replay": lambda: TrajectoryReplayPolicy(args.rlvr_policy or args.replay_policy),
        "rlvr": lambda: TrajectoryReplayPolicy(args.rlvr_policy or args.replay_policy),
    }
    policies: list[Policy] = []
    for policy_name in [item.strip() for item in args.policies.split(",") if item.strip()]:
        if policy_name not in policy_factories:
            raise SystemExit(f"Unknown policy {policy_name!r}. Use one of {sorted(policy_factories)}")
        policies.append(policy_factories[policy_name]())

    task_ids = [item.strip() for item in args.tasks.split(",") if item.strip()]
    unknown_tasks = set(task_ids) - set(TASK_IDS)
    if unknown_tasks:
        raise SystemExit(f"Unknown task ids: {sorted(unknown_tasks)}")

    variant_ids = [normalize_variant_id(item.strip()) for item in args.variants.split(",") if item.strip()]

    results = []
    for _ in range(args.repeats):
        for policy in policies:
            for task_id in task_ids:
                for variant_id in variant_ids:
                    if isinstance(policy, HallucinationBaseline):
                        max_steps = args.baseline_steps
                    elif isinstance(policy, (VerifierSelectedPolicy, TrajectoryReplayPolicy, DynamicOraclePolicy)):
                        max_steps = max(OPTIMAL_STEPS[task_id], args.model_steps)
                    else:
                        max_steps = args.model_steps
                    result = run_episode(task_id, policy, max_steps, variant_id=variant_id)
                    results.append(result)
                    print(
                        f'{policy.name} | {task_id} | {variant_id} | success={result["success"]} '
                        f'rrr={result["rrr"]} | {result["verifier_message"]}'
                    )

    summary = summarize(results)
    print()
    print_table(summary)
    write_artifacts(results, summary, args.out)
    print()
    print(f"Wrote metrics to {args.out.resolve()}")


if __name__ == "__main__":
    main()
