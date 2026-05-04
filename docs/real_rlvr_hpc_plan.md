# Real RLVR HPC Plan

This repo previously used `rlvr` to mean verifier-selected trajectory replay. That is not model learning. The replay artifact is now treated as a memorization baseline.

The research-grade target is real model training on the planned HPC machine:

- 224 CPU threads
- 250 GB RAM
- 2x NVIDIA RTX ADA 6000 GPUs
- up to 7 days

## Main Claim

Evaluate whether verifier-reward training improves a browser agent beyond zero-shot, few-shot prompting, SFT imitation, and trajectory replay.

## Default Model

Use text-only `Qwen/Qwen2.5-3B-Instruct` as the main model.

Do not make Qwen2.5-VL-7B the default. VL and 7B runs are ablations/stretch goals because screenshot tokens make browser RL throughput expensive.

## Variants

The local task suite now supports deterministic variants:

- `train_000 ...`
- `val_000 ...`
- `test_000 ...`

Use:

```powershell
python scripts/generate_task_variants.py --train-count 50 --val-count 20 --test-count 20
```

The dynamic oracle must solve train/val/test variants before training claims are made.

## Step-Level RLOO/GRPO

Do not treat one full browser trajectory as one TRL completion. Browser tasks are multi-step environments.

At browser state `s_t`:

1. serialize goal, observation, history, and valid actions
2. sample `G=8` candidate actions from the current policy
3. reconstruct the same state for each candidate
4. execute candidate action
5. continue with the current policy until terminal or max steps
6. score sparse terminal verifier reward only
7. compute group-relative advantages
8. update the adapter

The continuation policy must be the current trainable policy, not the dynamic oracle. The oracle is for SFT data and solvability checks.

## State Cloning

Default: `ReplayCheckpoint`.

- Store action history from reset to `s_t`.
- Clone by starting a fresh env and replaying prior actions.
- Correct for local tasks and MiniWoB.
- Slow but reliable.

Optimization: `LocalSnapshotCheckpoint`.

- Local Flask tasks expose `/api/snapshot` and `/api/restore`.
- This is only valid for Social-RLVR local tasks.
- Do not rely on it for MiniWoB.

## Reward

Headline reward is sparse terminal verifier reward:

```text
1.0 if final backend verifier passes
0.0 otherwise
```

Do not add valid-action or partial-progress rewards to the headline method.

Reward shaping may be implemented only as an ablation named `shaped_reward_baseline`.

## Required Comparisons

Main table:

- `zero_shot_3b`
- `few_shot_3b`
- `sft_3b`
- `rloo_3b`
- `grpo_3b`
- `trajectory_replay`
- `dynamic_oracle`

Main 3B comparison gets 3 seeds. Ablations get 1 seed.

## Acceptance Criteria

Do not call the project real RLVR until:

- SFT adapter checkpoint exists
- RL adapter checkpoint exists
- evaluation loads trained adapters and calls the model
- replay baseline is separate and labeled memorization
- dynamic oracle solves all local variants
- RLOO/GRPO uses terminal continuation rollouts
- main results include held-out test variants
- bootstrap 95% confidence intervals are reported
- trajectories are logged and inspectable
