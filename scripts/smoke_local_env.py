from __future__ import annotations

from social_rlvr_web import BrowserRLVREnv


def element_index(obs: dict, *, tag: str | None = None, name: str | None = None) -> int:
    for item in obs["dom"]:
        if tag is not None and item["tag"] != tag:
            continue
        haystack = f'{item["name"]} {item["text"]}'.lower()
        if name is None or name.lower() in haystack:
            return item["index"]
    raise LookupError(f"No element found for tag={tag!r}, name={name!r}")


def run_report() -> None:
    env = BrowserRLVREnv("report.extract_tracking_code", headless=True)
    try:
        obs, _ = env.reset()
        input_id = element_index(obs, tag="input")
        obs, reward, terminated, truncated, info = env.step(f'fill({input_id}, "TRV-8429-IN")')
        button_id = element_index(obs, tag="button", name="submit")
        _, reward, terminated, truncated, info = env.step(f"click({button_id})")
        print("report", reward, terminated, truncated, info["verifier_message"])
    finally:
        env.close()


def run_gallery() -> None:
    env = BrowserRLVREnv("gallery.aesthetic_travel_to_meera", headless=True, port=8766)
    try:
        obs, _ = env.reset()
        selects = [item["index"] for item in obs["dom"] if item["tag"] == "select"]
        buttons = [item["index"] for item in obs["dom"] if item["tag"] == "button"]
        travel_card_select = selects[1]
        travel_card_button = buttons[1]
        obs, *_ = env.step(f'select({travel_card_select}, "Meera")')
        _, reward, terminated, truncated, info = env.step(f"click({travel_card_button})")
        print("gallery", reward, terminated, truncated, info["verifier_message"])
    finally:
        env.close()


def run_messages() -> None:
    env = BrowserRLVREnv("messages.last_five_new_year", headless=True, port=8767)
    try:
        obs, _ = env.reset()
        recipients = ["Kabir", "Meera", "Riya", "Vivaan", "Zara"]
        for recipient in recipients:
            select_id = element_index(obs, tag="select")
            obs, *_ = env.step(f'select({select_id}, "{recipient}")')
            textarea_id = element_index(obs, tag="textarea")
            obs, *_ = env.step(f'fill({textarea_id}, "Happy New Year")')
            button_id = element_index(obs, tag="button", name="send")
            obs, reward, terminated, truncated, info = env.step(f"click({button_id})")
        print("messages", reward, terminated, truncated, info["verifier_message"])
    finally:
        env.close()


if __name__ == "__main__":
    run_report()
    run_gallery()
    run_messages()
