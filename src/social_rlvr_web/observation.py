from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image


def screenshot_to_base64_png(screenshot: Any, max_width: int = 900) -> str:
    image = Image.fromarray(screenshot)
    if image.width > max_width:
        ratio = max_width / image.width
        image = image.resize((max_width, int(image.height * ratio)))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def axtree_to_text(node: Any, *, max_lines: int = 140) -> str:
    lines: list[str] = []

    def value_of(item: Any) -> str:
        if isinstance(item, dict):
            if "value" in item:
                return str(item["value"])
            return ""
        return str(item or "")

    def walk(current: Any, depth: int = 0) -> None:
        if len(lines) >= max_lines:
            return
        if isinstance(current, dict):
            bid = current.get("browsergym_id") or current.get("bid") or ""
            role = value_of(current.get("role") or current.get("node", {}).get("role"))
            name = value_of(current.get("name") or current.get("node", {}).get("name"))
            value = value_of(current.get("value") or current.get("node", {}).get("value"))
            interesting = any([bid, role, name, value])
            if interesting:
                prefix = "  " * min(depth, 4)
                bid_text = f" bid={bid}" if bid else ""
                value_text = f" value={value}" if value else ""
                lines.append(f"{prefix}- role={role}{bid_text} name={name}{value_text}".strip())
            if "nodes" in current and isinstance(current["nodes"], list):
                for child in current["nodes"]:
                    walk(child, depth)
            for key in ("children", "childIds"):
                children = current.get(key)
                if isinstance(children, list):
                    for child in children:
                        walk(child, depth + 1)
        elif isinstance(current, list):
            for child in current:
                walk(child, depth)

    walk(node)
    return "\n".join(lines[:max_lines])


def dom_to_text(node: Any, *, max_lines: int = 180) -> str:
    lines: list[str] = []

    def walk(current: Any, depth: int = 0) -> None:
        if len(lines) >= max_lines:
            return
        if isinstance(current, dict):
            bid = current.get("browsergym_id") or current.get("bid") or current.get("attributes", {}).get("bid")
            tag = current.get("tag") or current.get("nodeName") or current.get("backendNodeId") or ""
            attrs = current.get("attributes", {})
            if isinstance(attrs, dict):
                label = attrs.get("aria-label") or attrs.get("name") or attrs.get("placeholder") or attrs.get("value")
            else:
                label = ""
            text = current.get("text") or current.get("nodeValue") or ""
            if bid or label or text:
                prefix = "  " * min(depth, 4)
                bid_text = f" bid={bid}" if bid else ""
                label_text = f" label={label}" if label else ""
                text_text = f" text={str(text).strip()[:80]}" if str(text).strip() else ""
                lines.append(f"{prefix}- tag={tag}{bid_text}{label_text}{text_text}".strip())
            for key in ("children", "childNodes"):
                children = current.get(key)
                if isinstance(children, list):
                    for child in children:
                        walk(child, depth + 1)
        elif isinstance(current, list):
            for child in current:
                walk(child, depth)

    walk(node)
    return "\n".join(lines[:max_lines])
