from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def bootstrap_ci(values: list[float], *, samples: int = 2000, seed: int = 13) -> tuple[float, float]:
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        draw = [rng.choice(values) for _ in values]
        estimates.append(sum(draw) / len(draw))
    estimates.sort()
    return estimates[int(0.025 * samples)], estimates[int(0.975 * samples)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-results", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "metrics" / "bootstrap_ci.csv")
    parser.add_argument("--samples", type=int, default=2000)
    args = parser.parse_args()

    with args.episode_results.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    groups = {}
    for row in rows:
        key = (row["policy"], row.get("split", "unknown"))
        groups.setdefault(key, []).append(1.0 if row["success"].lower() == "true" else 0.0)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["policy", "split", "episodes", "success_rate", "ci_low", "ci_high"])
        writer.writeheader()
        for (policy, split), values in sorted(groups.items()):
            low, high = bootstrap_ci(values, samples=args.samples)
            writer.writerow(
                {
                    "policy": policy,
                    "split": split,
                    "episodes": len(values),
                    "success_rate": round(sum(values) / len(values), 4),
                    "ci_low": round(low, 4),
                    "ci_high": round(high, 4),
                }
            )
    print(f"Wrote bootstrap CIs to {args.out.resolve()}")


if __name__ == "__main__":
    main()
