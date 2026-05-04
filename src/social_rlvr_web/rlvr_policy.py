from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class RLVRPolicyError(RuntimeError):
    pass


@dataclass
class TrajectoryReplayPolicy:
    """Replay verifier-selected trajectories; this is memorization, not model learning."""

    artifact_path: Path
    name: str = ""
    task_id: str = ""
    cursor: int = 0
    task_actions: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        artifact = json.loads(Path(self.artifact_path).read_text(encoding="utf-8"))
        policies = artifact.get("task_policies", {})
        if not isinstance(policies, dict):
            raise RLVRPolicyError(f"Invalid RLVR artifact: {self.artifact_path}")

        for task_id, policy_data in policies.items():
            actions = policy_data.get("actions", [])
            if not actions or not all(isinstance(action, str) for action in actions):
                continue
            self.task_actions[task_id] = actions

        if not self.task_actions:
            raise RLVRPolicyError(f"No learned task actions found in {self.artifact_path}")

        if not self.name:
            method = artifact.get("method", "trajectory_replay")
            base_policy = artifact.get("base_policy", "policy")
            self.name = f"trajectory_replay_{method}_{base_policy}"

    def reset(self, task_id: str) -> None:
        self.task_id = task_id
        self.cursor = 0
        if task_id not in self.task_actions:
            raise RLVRPolicyError(f"No learned trajectory for task {task_id!r}")

    def act(self, env: Any, obs: dict[str, Any]) -> str:
        del env, obs
        actions = self.task_actions[self.task_id]
        if self.cursor >= len(actions):
            return "noop(100)"
        action = actions[self.cursor]
        self.cursor += 1
        return action


LearnedTrajectoryPolicy = TrajectoryReplayPolicy
