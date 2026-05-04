from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any

import gymnasium as gym
import requests

import social_rlvr_web.browsergym_tasks  # noqa: F401


@dataclass
class ReplayCheckpoint:
    """Reconstruct a browser state by resetting and replaying prior actions."""

    task_id: str
    variant_id: str
    history: list[str] = field(default_factory=list)

    backend: str = "replay"

    def clone_env(self, *, headless: bool = True):
        previous_variant = os.environ.get("SOCIAL_RLVR_VARIANT_ID")
        os.environ["SOCIAL_RLVR_VARIANT_ID"] = self.variant_id
        env = gym.make(
            self.task_id,
            headless=headless,
            slow_mo=0,
            pre_observation_delay=0.05,
        )
        if previous_variant is None:
            os.environ.pop("SOCIAL_RLVR_VARIANT_ID", None)
        else:
            os.environ["SOCIAL_RLVR_VARIANT_ID"] = previous_variant
        obs, info = env.reset()
        for action in self.history:
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        return env, obs, info


@dataclass
class LocalSnapshotCheckpoint:
    """Backend-state snapshot optimization for the local Social-RLVR Flask tasks."""

    task_id: str
    variant_id: str
    base_url: str
    state: dict[str, Any]
    storage_state: dict[str, Any] | None = None

    backend: str = "local_snapshot"

    @classmethod
    def capture(cls, *, task_id: str, variant_id: str, base_url: str, page: Any) -> "LocalSnapshotCheckpoint":
        response = requests.post(f"{base_url}/api/snapshot", timeout=5)
        response.raise_for_status()
        storage_state = page.context.storage_state() if page is not None else None
        return cls(
            task_id=task_id,
            variant_id=variant_id,
            base_url=base_url,
            state=response.json()["state"],
            storage_state=storage_state,
        )

    def restore_backend(self) -> None:
        response = requests.post(f"{self.base_url}/api/restore", json={"state": self.state}, timeout=5)
        response.raise_for_status()
