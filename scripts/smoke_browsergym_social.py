from __future__ import annotations

from typing import Any

import gymnasium as gym

import social_rlvr_web.browsergym_tasks  # noqa: F401


def bid_for(page, selector: str, index: int = 0) -> str:
    bid = page.locator(selector).nth(index).get_attribute("bid")
    if not bid:
        raise LookupError(f"No BrowserGym bid found for {selector} at index {index}")
    return bid


def run_report() -> None:
    env = gym.make("browsergym/social_rlvr.report.extract_tracking_code", headless=True)
    try:
        obs, info = env.reset()
        page = env.unwrapped.page
        input_bid = bid_for(page, "input")
        obs, *_ = env.step(f'fill("{input_bid}", "TRV-8429-IN")')
        button_bid = bid_for(page, "button")
        _, reward, terminated, truncated, info = env.step(f'click("{button_bid}")')
        print("browsergym report", reward, terminated, truncated, info["task_info"]["verifier_message"])
    finally:
        env.close()


def run_gallery() -> None:
    env = gym.make("browsergym/social_rlvr.gallery.aesthetic_travel_to_meera", headless=True)
    try:
        obs, info = env.reset()
        page = env.unwrapped.page
        select_bid = bid_for(page, "select", index=1)
        obs, *_ = env.step(f'select_option("{select_bid}", "Meera")')
        button_bid = bid_for(page, "button", index=1)
        _, reward, terminated, truncated, info = env.step(f'click("{button_bid}")')
        print("browsergym gallery", reward, terminated, truncated, info["task_info"]["verifier_message"])
    finally:
        env.close()


def run_messages() -> None:
    env = gym.make("browsergym/social_rlvr.messages.last_five_new_year", headless=True)
    try:
        obs, info = env.reset()
        page = env.unwrapped.page
        for recipient in ["Kabir", "Meera", "Riya", "Vivaan", "Zara"]:
            select_bid = bid_for(page, "select")
            obs, *_ = env.step(f'select_option("{select_bid}", "{recipient}")')
            textarea_bid = bid_for(page, "textarea")
            obs, *_ = env.step(f'fill("{textarea_bid}", "Happy New Year")')
            button_bid = bid_for(page, "button")
            obs, reward, terminated, truncated, info = env.step(f'click("{button_bid}")')
        print(
            "browsergym messages",
            reward,
            terminated,
            truncated,
            info["task_info"]["verifier_message"],
        )
    finally:
        env.close()


def summarize_observation(obs: dict[str, Any]) -> None:
    keys = sorted(obs.keys())
    screenshot = obs.get("screenshot")
    shape = getattr(screenshot, "shape", None)
    goal = obs.get("goal", "")
    print("obs keys:", keys)
    print("screenshot shape:", shape)
    print("goal:", goal)


if __name__ == "__main__":
    env = gym.make("browsergym/social_rlvr.report.extract_tracking_code", headless=True)
    try:
        obs, _ = env.reset()
        summarize_observation(obs)
    finally:
        env.close()
    run_report()
    run_gallery()
    run_messages()
