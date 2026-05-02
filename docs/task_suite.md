# Social-RLVR BrowserGym Task Suite

This suite is designed to test whether a browser agent improves after RLVR training with objective backend-state rewards.

## Task Classes

### 1. Multi-Step Iteration

Task ID:

```text
browsergym/social_rlvr.messages.last_five_new_year
```

Instruction:

```text
Send "Happy New Year" to the last five friends.
```

Reward:

```text
1.0 if backend messages contain exact text "Happy New Year" for Kabir, Meera, Riya, Vivaan, and Zara.
0.0 otherwise.
```

Why it matters:

The model must repeat a UI workflow over multiple distinct targets without hallucinating partial completion.

### 2. Visual-Semantic Retrieval

Task ID:

```text
browsergym/social_rlvr.gallery.aesthetic_travel_to_meera
```

Instruction:

```text
Find an aesthetic travel image and send it to Meera.
```

Reward:

```text
1.0 if backend shared_images contains image_id=img_travel and recipient=Meera.
0.0 otherwise.
```

Why it matters:

The model must bind visual/semantic content to the correct UI action and recipient.

### 3. Data Extraction

Task ID:

```text
browsergym/social_rlvr.report.extract_tracking_code
```

Instruction:

```text
Extract the shipment tracking code into the report form.
```

Reward:

```text
1.0 if backend reports contain tracking_code=TRV-8429-IN.
0.0 otherwise.
```

Why it matters:

The model must read a page value, preserve it exactly, and submit it through the UI.

### 4. Row-Conditioned Follow-up

Task ID:

```text
browsergym/social_rlvr.orders.priority_followup
```

Instruction:

```text
Find the high priority order, then create a follow-up for that owner with the exact reference code and note "Priority follow-up".
```

Reward:

```text
1.0 if backend followups contain recipient=Meera, reference=REF-MEERA-774, and note="Priority follow-up".
0.0 otherwise.
```

Why it matters:

The model must read a table, select the row that satisfies a condition, preserve a reference code exactly, and fill a multi-field form.

### 5. Constraint-Based Scheduling

Task ID:

```text
browsergym/social_rlvr.schedule.design_review_shared_slot
```

Instruction:

```text
Schedule a design review with Kabir and Zara in the only shared open slot.
```

Reward:

```text
1.0 if backend meetings contain title="Design review", slot="Fri 14:00", and exactly attendees Kabir and Zara.
0.0 otherwise.
```

Why it matters:

The model must infer a shared open slot from a small availability table, choose multiple attendees, and avoid adding distractor contacts.

## Main Metrics

- SR: success rate across episodes.
- Mean reward: verifier reward averaged across episodes.
- RRR: optimal_steps / actual_steps for successful episodes; 0 for failed episodes.
- Trajectory log: exact BrowserGym actions and verifier messages per step.
