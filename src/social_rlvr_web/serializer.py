from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from social_rlvr_web.model_policy import OllamaVisionPolicy
from social_rlvr_web.observation import axtree_to_text, dom_to_text


@dataclass
class BrowserStateSerializer:
    max_axtree_lines: int = 90
    max_dom_lines: int = 80
    max_history: int = 8

    def prompt(self, obs: dict[str, Any], history: list[str]) -> str:
        goal = obs.get("goal", "")
        axtree = axtree_to_text(obs.get("axtree_object"), max_lines=self.max_axtree_lines)
        dom = dom_to_text(obs.get("dom_object"), max_lines=self.max_dom_lines)
        valid_bids = OllamaVisionPolicy._valid_bid_lines(obs.get("axtree_object"))
        history_text = "\n".join(history[-self.max_history :]) or "(none)"
        return f"""
You are a browser agent. Choose exactly one next action.

Goal:
{goal}

Action history:
{history_text}

Return one JSON object only:
{{"type": "click", "bid": "17"}}
{{"type": "fill", "bid": "16", "value": "text"}}
{{"type": "select_option", "bid": "12", "value": "visible option text"}}
{{"type": "noop"}}

Use only bids from this list:
{valid_bids}

Accessibility tree:
{axtree}

DOM summary:
{dom}
""".strip()
