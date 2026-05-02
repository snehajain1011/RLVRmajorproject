# Phase I Research Plan: RLVR + GRPO for Browser Agents

## Framing

The project reframes the AndroidWorld objective as browser-agent RLVR:

> Can Large Multimodal browser agents improve on complex web tasks when trained with verifiable rewards and GRPO instead of subjective preference feedback or critic-based PPO?

The surface changes from Android UI to browser UI, but the training loop remains stable:

- screenshot observation
- structured UI tree observation
- discrete UI actions
- deterministic task verifier
- grouped trajectory sampling
- group-relative policy update

## Local task classes

1. Multi-step iteration
   - Example: send a greeting to the last five contacts.
   - Verifier: backend message log contains exactly the required recipients and text.

2. Visual-semantic retrieval
   - Example: choose the aesthetic travel image and send it to a target contact.
   - Verifier: backend state records the expected image id and recipient.

3. Data extraction
   - Example: copy a specific value from a profile/order page into a report form.
   - Verifier: backend submitted answer equals the hidden ground-truth value.

## Metrics

- Success Rate (SR): percentage of episodes whose verifier returns success.
- Reversed Redundancy Ratio (RRR): penalizes repeated or unnecessary actions before success.
- Mean trajectory length: lower is better after success is maintained.
- Failure taxonomy: wrong target, partial completion, hallucinated completion, UI dead end.

## Experiment sequence

1. Validate environment determinism with scripted trajectories.
2. Connect zero-shot Qwen2.5-VL/Ollama policy to screenshot + DOM observations.
3. Collect failed/successful grouped trajectories per instruction.
4. Add GRPO update loop using verifier reward as the only reward signal.
5. Compare zero-shot, SFT cold start, and RLVR+GRPO variants.
6. Move from local task server to MiniWoB, then WebArena/VisualWebArena.

