from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from social_rlvr_web.actions import validate_bid
from social_rlvr_web.checkpoints import ReplayCheckpoint


class BrowserPolicy(Protocol):
    name: str

    def reset(self, task_id: str) -> None: ...

    def act(self, env: Any, obs: dict[str, Any]) -> str: ...


@dataclass
class ContinuationScore:
    candidate_action: str
    terminal_reward: float
    success: bool
    steps: int
    valid: bool
    invalid_reason: str = ""
    trajectory: list[dict[str, Any]] = field(default_factory=list)


def score_candidate_with_terminal_continuation(
    *,
    checkpoint: ReplayCheckpoint,
    candidate_action: str,
    continuation_policy: BrowserPolicy,
    max_steps: int,
) -> ContinuationScore:
    env, obs, info = checkpoint.clone_env(headless=True)
    trajectory: list[dict[str, Any]] = []
    reward = 0.0
    terminated = False
    truncated = False
    validity = validate_bid(candidate_action, obs)
    action = validity.action if not validity.valid else candidate_action
    try:
        obs, reward, terminated, truncated, info = env.step(action)
        task_info = info.get("task_info", {})
        trajectory.append(
            {
                "step": len(checkpoint.history) + 1,
                "action": action,
                "candidate": True,
                "valid": validity.valid,
                "invalid_reason": validity.reason,
                "reward": reward,
                "success": task_info.get("success", False),
                "verifier_message": task_info.get("verifier_message", ""),
            }
        )
        continuation_policy.reset(checkpoint.task_id)
        for step_idx in range(len(checkpoint.history) + 2, max_steps + 1):
            if terminated or truncated:
                break
            next_action = continuation_policy.act(env, obs)
            next_validity = validate_bid(next_action, obs)
            if not next_validity.valid:
                next_action = next_validity.action
            obs, reward, terminated, truncated, info = env.step(next_action)
            task_info = info.get("task_info", {})
            trajectory.append(
                {
                    "step": step_idx,
                    "action": next_action,
                    "candidate": False,
                    "valid": next_validity.valid,
                    "invalid_reason": next_validity.reason,
                    "reward": reward,
                    "success": task_info.get("success", False),
                    "verifier_message": task_info.get("verifier_message", ""),
                }
            )
    finally:
        env.close()

    task_info = info.get("task_info", {})
    return ContinuationScore(
        candidate_action=candidate_action,
        terminal_reward=float(reward if task_info.get("success", False) else 0.0),
        success=bool(task_info.get("success", False)),
        steps=len(trajectory),
        valid=validity.valid,
        invalid_reason=validity.reason,
        trajectory=trajectory,
    )


def group_relative_advantages(rewards: list[float], *, epsilon: float = 1e-6) -> list[float]:
    if not rewards:
        return []
    mean = sum(rewards) / len(rewards)
    variance = sum((reward - mean) ** 2 for reward in rewards) / len(rewards)
    std = variance**0.5
    if std < epsilon:
        return [0.0 for _ in rewards]
    return [(reward - mean) / (std + epsilon) for reward in rewards]


def write_jsonl(path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
