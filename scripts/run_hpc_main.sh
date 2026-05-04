#!/usr/bin/env bash
set -euo pipefail

export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$PWD/.playwright}"

python -m pip install -e '.[hpc,benchmarks]'
python -m playwright install chromium

python scripts/generate_task_variants.py --out artifacts/variants/local_variants.json
python scripts/collect_oracle_trajectories.py --splits train --train-count 50 --out artifacts/rollouts/oracle_train.jsonl
python scripts/build_sft_dataset.py --trajectories artifacts/rollouts/oracle_train.jsonl --augment-factor 5 --out artifacts/sft/browser_sft.jsonl
python scripts/train_sft_policy.py --dataset artifacts/sft/browser_sft.jsonl --out artifacts/checkpoints/sft_qwen25_3b

python scripts/evaluate_generalization.py \
  --policies dynamic_oracle,trajectory_replay \
  --train-count 5 \
  --val-count 5 \
  --test-count 5 \
  --out artifacts/eval_generalization_smoke

echo "HPC smoke pipeline complete. Run train_browser_rloo.py with sampled model candidate actions next."
