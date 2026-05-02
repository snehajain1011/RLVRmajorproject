from __future__ import annotations

import gymnasium as gym

import browsergym.core  # noqa: F401
from social_rlvr_web.local_app import LocalAppServer


def main() -> None:
    server = LocalAppServer(port=8770)
    server.start()
    env = gym.make(
        "browsergym/openended",
        task_kwargs={
            "start_url": f"{server.base_url}/report",
            "goal": "Inspect the local RLVR report task.",
        },
    )
    try:
        obs, info = env.reset()
        print("goal:", obs.get("goal"))
        print("obs keys:", sorted(obs.keys()))
        _, reward, terminated, truncated, _ = env.step("noop()")
        print("first step:", {"reward": reward, "terminated": terminated, "truncated": truncated})
    finally:
        env.close()
        server.stop()


if __name__ == "__main__":
    main()
