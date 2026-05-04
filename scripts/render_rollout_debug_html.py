from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "debug" / "rollouts.html")
    args = parser.parse_args()

    episodes = []
    with args.trajectories.open("r", encoding="utf-8") as handle:
        for line in handle:
            episodes.append(json.loads(line))
            if len(episodes) >= args.limit:
                break

    parts = ["<html><body><h1>Rollout Debug</h1>"]
    for episode in episodes:
        parts.append(
            "<section>"
            f"<h2>{html.escape(episode['policy'])} | {html.escape(episode['task_id'])} | "
            f"{html.escape(episode.get('variant_id', ''))}</h2>"
            f"<p>success={episode['success']} reward={episode['reward']} "
            f"message={html.escape(episode.get('verifier_message', ''))}</p>"
            "<ol>"
        )
        for step in episode.get("trajectory", []):
            parts.append(
                "<li>"
                f"<code>{html.escape(step.get('action', ''))}</code> "
                f"reward={step.get('reward')} success={step.get('success')} "
                f"{html.escape(step.get('verifier_message', ''))}"
                "</li>"
            )
        parts.append("</ol></section>")
    parts.append("</body></html>")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote rollout debug HTML to {args.out.resolve()}")


if __name__ == "__main__":
    main()
