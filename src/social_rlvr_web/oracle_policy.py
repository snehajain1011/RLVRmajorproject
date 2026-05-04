from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from social_rlvr_web.actions import action_dict_to_browsergym


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


@dataclass
class DynamicOraclePolicy:
    """Content-reading oracle for solvability checks and SFT data, not a learning baseline."""

    name: str = "dynamic_oracle"
    task_id: str = ""
    cursor: int = 0
    expected: dict[str, Any] = field(default_factory=dict)

    def reset(self, task_id: str) -> None:
        self.task_id = task_id
        self.cursor = 0
        self.expected = {}

    def act(self, env, obs: dict[str, Any]) -> str:
        page = env.unwrapped.page
        if not self.expected:
            task = getattr(env.unwrapped, "task", None)
            self.expected = getattr(task, "expected", {}) if task is not None else {}
            self.expected = self.expected or obs.get("extra_element_properties", {}).get("expected", {})
            self.expected = self.expected or self._expected_from_state(env)

        if self.task_id.endswith("report.extract_tracking_code"):
            return self._report_action(page)
        if self.task_id.endswith("gallery.aesthetic_travel_to_meera"):
            return self._gallery_action(page)
        if self.task_id.endswith("messages.last_five_new_year"):
            return self._messages_action(page)
        if self.task_id.endswith("orders.priority_followup"):
            return self._orders_action(page)
        if self.task_id.endswith("schedule.design_review_shared_slot"):
            return self._schedule_action(page)
        raise KeyError(f"No dynamic oracle for {self.task_id}")

    def _expected_from_state(self, env) -> dict[str, Any]:
        try:
            import requests

            response = requests.get(f"{env.unwrapped.task.base_url}/api/state", timeout=5)
            response.raise_for_status()
            return response.json().get("expected", {})
        except Exception:
            return {}

    def _report_action(self, page) -> str:
        if self.cursor == 0:
            self.cursor += 1
            code = page.locator("strong").first.inner_text().strip()
            return action_dict_to_browsergym({"type": "fill", "bid": bid_for(page, "input"), "value": code}).action
        self.cursor += 1
        return action_dict_to_browsergym({"type": "click", "bid": bid_for(page, "button")}).action

    def _gallery_action(self, page) -> str:
        target_title = self.expected.get("image_id", "")
        forms = page.locator("form")
        target_index = 0
        for index in range(forms.count()):
            image_id = forms.nth(index).locator('input[name="image_id"]').get_attribute("value")
            if image_id == target_title:
                target_index = index
                break
        if self.cursor == 0:
            self.cursor += 1
            return action_dict_to_browsergym(
                {
                    "type": "select_option",
                    "bid": bid_for(page, "select", target_index),
                    "value": self.expected.get("recipient", "Meera"),
                }
            ).action
        self.cursor += 1
        return action_dict_to_browsergym({"type": "click", "bid": bid_for(page, "button", target_index)}).action

    def _messages_action(self, page) -> str:
        recipients = self.expected.get("recipients", ["Kabir", "Meera", "Riya", "Vivaan", "Zara"])
        recipient = recipients[self.cursor // 3]
        phase = self.cursor % 3
        self.cursor += 1
        if phase == 0:
            return action_dict_to_browsergym({"type": "select_option", "bid": bid_for(page, "select"), "value": recipient}).action
        if phase == 1:
            return action_dict_to_browsergym(
                {"type": "fill", "bid": bid_for(page, "textarea"), "value": self.expected.get("text", "Happy New Year")}
            ).action
        return action_dict_to_browsergym({"type": "click", "bid": bid_for(page, "button")}).action

    def _orders_action(self, page) -> str:
        if self.cursor == 0:
            self.cursor += 1
            return action_dict_to_browsergym(
                {"type": "select_option", "bid": bid_for(page, "select"), "value": self.expected.get("recipient", "Meera")}
            ).action
        if self.cursor == 1:
            self.cursor += 1
            return action_dict_to_browsergym(
                {"type": "fill", "bid": bid_for(page, "input"), "value": self.expected.get("reference", "REF-MEERA-774")}
            ).action
        if self.cursor == 2:
            self.cursor += 1
            return action_dict_to_browsergym(
                {"type": "fill", "bid": bid_for(page, "textarea"), "value": self.expected.get("note", "Priority follow-up")}
            ).action
        self.cursor += 1
        return action_dict_to_browsergym({"type": "click", "bid": bid_for(page, "button")}).action

    def _schedule_action(self, page) -> str:
        attendees = self.expected.get("attendees", ["Kabir", "Zara"])
        if self.cursor == 0:
            self.cursor += 1
            return action_dict_to_browsergym(
                {"type": "fill", "bid": bid_for(page, "input"), "value": self.expected.get("title", "Design review")}
            ).action
        if self.cursor == 1:
            self.cursor += 1
            return action_dict_to_browsergym(
                {"type": "select_option", "bid": bid_for(page, "select"), "value": self.expected.get("slot", "Fri 14:00")}
            ).action
        if self.cursor in (2, 3):
            attendee = attendees[self.cursor - 2]
            self.cursor += 1
            return action_dict_to_browsergym(
                {"type": "click", "bid": bid_for_value(page, "input[type=checkbox]", attendee)}
            ).action
        self.cursor += 1
        return action_dict_to_browsergym({"type": "click", "bid": bid_for(page, "button")}).action
