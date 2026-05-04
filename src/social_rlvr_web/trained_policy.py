from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from social_rlvr_web.actions import action_dict_to_browsergym
from social_rlvr_web.serializer import BrowserStateSerializer


class TrainedPolicyError(RuntimeError):
    pass


@dataclass
class TrainedTransformersPolicy:
    """Inference wrapper for a base model plus SFT/RL adapter checkpoint."""

    model_name_or_path: str
    adapter_path: str | None = None
    name: str = "trained_transformers_policy"
    max_new_tokens: int = 96
    temperature: float = 0.7
    serializer: BrowserStateSerializer = field(default_factory=BrowserStateSerializer)
    task_id: str = ""
    history: list[str] = field(default_factory=list)
    model: Any = None
    tokenizer: Any = None

    def __post_init__(self) -> None:
        try:
            import torch  # noqa: F401
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise TrainedPolicyError(
                "TrainedTransformersPolicy requires torch, transformers, and peft. "
                "Install the HPC dependencies before using trained model policies."
            ) from exc

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name_or_path,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True,
        )
        if self.adapter_path:
            self.model = PeftModel.from_pretrained(self.model, self.adapter_path)
        self.model.eval()

    def reset(self, task_id: str) -> None:
        self.task_id = task_id
        self.history = []

    def act(self, env: Any, obs: dict[str, Any]) -> str:
        del env
        prompt = self.serializer.prompt(obs, self.history)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=True,
            temperature=self.temperature,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        text = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True)
        action = self._parse_json_action(text)
        self.history.append(action)
        return action

    @staticmethod
    def _parse_json_action(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            return "noop(100)"
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return "noop(100)"
        return action_dict_to_browsergym(data).action


def assert_adapter_exists(adapter_path: str | Path) -> None:
    path = Path(adapter_path)
    if not path.exists():
        raise TrainedPolicyError(f"Adapter checkpoint does not exist: {path}")
