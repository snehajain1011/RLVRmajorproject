from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

import requests

from social_rlvr_web.observation import axtree_to_text, dom_to_text, screenshot_to_base64_png


ACTION_RE = re.compile(
    r"^(click|fill|select_option|noop|send_msg_to_user|scroll|keyboard_press|press)\(.*\)$"
)


class ModelPolicyError(RuntimeError):
    pass


@dataclass
class OllamaVisionPolicy:
    name: str = ""
    model: str = "qwen2.5vl"
    host: str = "http://127.0.0.1:11434"
    temperature: float = 0.2
    num_ctx: int = 2048
    num_predict: int = 96
    timeout_seconds: int = 600
    use_images: bool = True
    task_id: str = ""
    step: int = 0

    def __post_init__(self) -> None:
        self.host = os.environ.get("OLLAMA_HOST", self.host).rstrip("/")
        self.model = os.environ.get("OLLAMA_MODEL", self.model)
        if not self.name:
            safe_model = self.model.replace(":", "_").replace(".", "_")
            modality = "vision" if self.use_images else "text"
            self.name = f"{safe_model}_ollama_{modality}_zero_shot"

    def reset(self, task_id: str) -> None:
        self.task_id = task_id
        self.step = 0

    def act(self, env, obs: dict[str, Any]) -> str:
        del env
        self.step += 1
        prompt = self._build_prompt(obs)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
        }
        if self.use_images:
            payload["images"] = [screenshot_to_base64_png(obs["screenshot"], max_width=640)]
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.Timeout as exc:
            raise ModelPolicyError(
                f"Ollama model call timed out after {self.timeout_seconds}s for {self.model}."
            ) from exc
        except requests.RequestException as exc:
            raise ModelPolicyError(
                f"Could not reach Ollama at {self.host}. Install/start Ollama and pull {self.model}."
            ) from exc
        if response.status_code != 200:
            raise ModelPolicyError(f"Ollama returned {response.status_code}: {response.text[:500]}")

        data = response.json()
        raw = data.get("response", "")
        action = self._parse_action(raw)
        if action is None:
            return "noop(100)"
        return action

    def _build_prompt(self, obs: dict[str, Any]) -> str:
        goal = obs.get("goal", "")
        axtree = axtree_to_text(obs.get("axtree_object"), max_lines=80)
        dom = dom_to_text(obs.get("dom_object"), max_lines=100)
        last_error = obs.get("last_action_error", "")
        valid_bids = self._valid_bid_lines(obs.get("axtree_object"))
        return f"""
You are controlling a BrowserGym web task.

Goal:
{goal}

Return exactly one next action as JSON:
{{"action": "click(\\"bid\\")"}}

Allowed action formats:
- click("17")
- fill("16", "text")
- select_option("12", "visible option text")
- noop(100)

Rules:
- Use only numeric bid values from the valid element IDs below.
- Never output literal placeholder strings like click("bid") or fill("bid", "text").
- Do not say the task is done unless the page state was actually changed.
- Prefer one concrete UI action per turn.
- For select dropdowns, use select_option.
- For text fields, use fill.
- For checkboxes and buttons, use click.

Last action error:
{last_error}

Valid element IDs:
{valid_bids}

Accessibility tree:
{axtree}

DOM summary:
{dom}
""".strip()

    @staticmethod
    def _valid_bid_lines(axtree: Any) -> str:
        if not isinstance(axtree, dict):
            return ""
        lines = []
        for node in axtree.get("nodes", []):
            if not isinstance(node, dict) or "browsergym_id" not in node:
                continue
            role = node.get("role", {})
            name = node.get("name", {})
            role_value = role.get("value", "") if isinstance(role, dict) else str(role)
            name_value = name.get("value", "") if isinstance(name, dict) else str(name)
            bid = node["browsergym_id"]
            if role_value in {"textbox", "button", "combobox", "menuitem", "link", "checkbox"} or name_value:
                lines.append(f'- bid="{bid}" role={role_value} name="{name_value}"')
        return "\n".join(lines[:80])

    @staticmethod
    def _parse_action(raw: str) -> str | None:
        try:
            data = json.loads(raw)
            action = data.get("action", "")
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                return None
            try:
                action = json.loads(match.group(0)).get("action", "")
            except json.JSONDecodeError:
                return None
        action = str(action).strip()
        if ACTION_RE.match(action):
            return action
        return None
