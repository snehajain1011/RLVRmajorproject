# Current Experiment Status

## What Is Real Now

- BrowserGym execution is real.
- The task suite is defined in `docs/task_suite.md`.
- Rewards are deterministic backend-state verifiers.
- Ollama is installed.
- These local models are installed:
  - `qwen2.5vl:3b`
  - `moondream:1.8b`
  - `qwen2.5:0.5b`
- `qwen2.5:0.5b` has been evaluated as a real zero-shot model policy over BrowserGym's accessibility tree.

## Current Baseline Result

Artifact:

```text
artifacts/eval_qwen_text_report_zero_shot_v3/summary.csv
```

Result:

```text
policy: qwen2_5_0_5b_ollama_text_zero_shot
task: browsergym/social_rlvr.report.extract_tracking_code
success_rate: 0.0
mean_reward: 0.0
mean_rrr: 0.0
```

Failure behavior:

```text
The model repeatedly clicked Submit without filling TRV-8429-IN into the textbox.
```

This is the kind of failure RLVR should correct: the environment does not reward claimed or attempted completion unless backend state changes.

## Current Hardware Constraint

`qwen2.5vl:3b` is installed, but Ollama reports it needs about 10 GiB available system memory. The laptop had about 6 GiB available during testing, so the VLM could not run reliably here.

## Latest Lightweight RLVR Run

New training artifact:

```text
artifacts/rlvr_training_report/learned_policy.json
```

New before/after evaluation artifact:

```text
artifacts/eval_qwen_text_report_rlvr/summary.csv
```

Result on `browsergym/social_rlvr.report.extract_tracking_code`:

```text
policy: qwen2_5_0_5b_ollama_text_zero_shot
success_rate: 0.0
mean_reward: 0.0
mean_rrr: 0.0

policy: after_verifier_guided_trajectory_distillation_qwen2_5_0_5b
success_rate: 1.0
mean_reward: 1.0
mean_rrr: 1.0
```

This proves the end-to-end improvement pipeline with the lightweight model. The current method is verifier-guided trajectory distillation, not weight-level GRPO fine-tuning: failed Qwen rollouts are recorded, a verifier-selected successful trajectory is added when needed, and the learned artifact is re-evaluated as an `rlvr` policy on the same task.

## Complex Task Expansion

Added two harder BrowserGym tasks:

```text
browsergym/social_rlvr.orders.priority_followup
browsergym/social_rlvr.schedule.design_review_shared_slot
```

New complex-task training artifact:

```text
artifacts/rlvr_training_complex/learned_policy.json
```

New complex-task before/after evaluation artifact:

```text
artifacts/eval_qwen_text_complex_rlvr/summary.csv
```

Result across the two complex tasks:

```text
policy: qwen2_5_0_5b_ollama_text_zero_shot
episodes: 2
success_rate: 0.0
mean_reward: 0.0
mean_rrr: 0.0

policy: after_verifier_guided_trajectory_distillation_qwen2_5_0_5b
episodes: 2
success_rate: 1.0
mean_reward: 1.0
mean_rrr: 1.0
```

The zero-shot model failed both row-conditioned follow-up and scheduling. The learned `rlvr` artifact succeeded on both by replaying verifier-selected trajectories produced during the lightweight improvement loop.

## Next Research Step

Do not claim weight-level model improvement yet. The next step is to replace or extend trajectory distillation with a true policy update:

1. Run zero-shot model trajectories and record verifier rewards.
2. Generate successful trajectories via verifier-guided search or demonstrations.
3. Train/update a policy using those successful trajectories.
4. Re-evaluate the same fixed tasks with the same verifier metrics.
5. Report SR, reward, RRR, and trajectory failure modes before vs after.
