from __future__ import annotations

import os

import gymnasium as gym


def main() -> None:
    import browsergym.miniwob  # noqa: F401

    if "MINIWOB_URL" not in os.environ:
        raise SystemExit(
            "MINIWOB_URL is not set. Start miniwob-plusplus/miniwob/html with an HTTP "
            "server, then set MINIWOB_URL to that base URL before running this script."
        )

    env = gym.make("browsergym/miniwob.click-test")
    obs, info = env.reset()
    print("task:", info.get("task_name", "browsergym/miniwob.click-test"))
    print("obs keys:", sorted(obs.keys()))
    obs, reward, terminated, truncated, info = env.step("noop()")
    print("first step:", {"reward": reward, "terminated": terminated, "truncated": truncated})
    env.close()


if __name__ == "__main__":
    main()
