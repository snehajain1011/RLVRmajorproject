# Social-RLVR Web

This repo is the web-agent pivot of the AndroidWorld RLVR project: same RLVR/GRPO methodology, lighter BrowserGym/Playwright surface.

If you received this project as a zip file or want a full handoff guide, read:

```text
docs/setup_and_run_guide.md
```

Important naming note: the old lightweight `rlvr` path is verifier-selected trajectory
replay, not model learning. The research-grade HPC plan for actual SFT + RLOO/GRPO
adapter training is in:

```text
docs/real_rlvr_hpc_plan.md
```

## What is included

- A local browser task server with three verifiable interaction classes:
  - multi-step iteration
  - visual-semantic retrieval
  - data extraction
- A Playwright-backed Gymnasium-style env in `src/social_rlvr_web/env.py`.
- Programmatic verifiers in `src/social_rlvr_web/tasks.py`.
- Smoke scripts for the local env and BrowserGym MiniWoB.

## Setup on Windows

Recommended from this folder. BrowserGym `0.14.3` pins Playwright `1.44`, which is much happier on Python 3.11 than the Python 3.13 Anaconda base on this machine.

```powershell
conda create --prefix .conda python=3.11 pip -y
.\.conda\python.exe -m pip install -e .[dev,benchmarks]
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe -m playwright install chromium
$env:NLTK_DATA=(Resolve-Path .nltk_data).Path
.\.conda\python.exe -c "import nltk; nltk.download('punkt_tab', download_dir='.nltk_data')"
```

If BrowserGym/WebArena packages are too heavy for the first pass, install only the local scaffold:

```powershell
.\.conda\python.exe -m pip install -e .[dev]
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe -m playwright install chromium
```

## First checks

Run the local verifiable web task smoke test:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\smoke_local_env.py
```

Run a BrowserGym smoke test against the local task server:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\smoke_browsergym_openended.py
```

Run the local RLVR tasks as first-class BrowserGym environments:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\smoke_browsergym_social.py
```

Registered task IDs:

```text
browsergym/social_rlvr.messages.last_five_new_year
browsergym/social_rlvr.gallery.aesthetic_travel_to_meera
browsergym/social_rlvr.report.extract_tracking_code
browsergym/social_rlvr.orders.priority_followup
browsergym/social_rlvr.schedule.design_review_shared_slot
```

Run a before/after RLVR metrics demo:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --repeats 1
```

This writes:

```text
artifacts/eval_browsergym_rlvr/summary.csv
artifacts/eval_browsergym_rlvr/episode_results.csv
artifacts/eval_browsergym_rlvr/trajectories.jsonl
```

The current `baseline` policy is a hallucination-style baseline that claims completion without changing backend state. The `scripted` policy is a verifier-selected successful trajectory. This is a metrics harness for the paper setup, not yet model training.

Run a real Qwen2.5-VL zero-shot policy through Ollama:

```powershell
ollama pull qwen2.5vl
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies qwen --ollama-model qwen2.5vl --model-steps 20
```

On this laptop, `qwen2.5vl:3b` is installed but may fail to load if Ollama reports insufficient available RAM. A lightweight real-model baseline that runs here is Qwen2.5 text-only over BrowserGym's accessibility tree:

```powershell
ollama pull qwen2.5:0.5b
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies qwen --ollama-model qwen2.5:0.5b --model-no-images --model-steps 4 --tasks browsergym/social_rlvr.report.extract_tracking_code --out artifacts\eval_qwen_text_report_zero_shot
```

Compare all current policies:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies baseline,qwen,scripted --repeats 1
```

If Ollama is not installed or not running, the Qwen policy will record failed episodes with a clear model connection error in the artifacts.

Current laptop-tested model artifacts:

```text
artifacts/eval_qwen_text_report_zero_shot_v3/summary.csv
```

This is a real model zero-shot baseline. It is not RLVR training yet.

Run the lightweight verifier-guided RLVR/improvement loop with the small text model:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\train_browsergym_rlvr.py --ollama-model qwen2.5:0.5b --model-no-images --model-steps 4 --tasks browsergym/social_rlvr.report.extract_tracking_code --out artifacts\rlvr_training_report\learned_policy.json
```

Then compare before vs after on the same task:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies qwen,rlvr --ollama-model qwen2.5:0.5b --model-no-images --model-steps 4 --tasks browsergym/social_rlvr.report.extract_tracking_code --rlvr-policy artifacts\rlvr_training_report\learned_policy.json --out artifacts\eval_qwen_text_report_rlvr
```

The current RLVR path is verifier-guided trajectory distillation, not model weight fine-tuning:

- collect real lightweight model rollouts and verifier rewards
- add a verifier-selected successful trajectory when the model fails
- write a learned policy artifact
- evaluate `qwen` and `rlvr` against the same deterministic verifier

Run the same loop on the harder row-reading and scheduling tasks:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\train_browsergym_rlvr.py --ollama-model qwen2.5:0.5b --model-no-images --model-steps 6 --tasks browsergym/social_rlvr.orders.priority_followup,browsergym/social_rlvr.schedule.design_review_shared_slot --out artifacts\rlvr_training_complex\learned_policy.json

.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies qwen,rlvr --ollama-model qwen2.5:0.5b --model-no-images --model-steps 6 --tasks browsergym/social_rlvr.orders.priority_followup,browsergym/social_rlvr.schedule.design_review_shared_slot --rlvr-policy artifacts\rlvr_training_complex\learned_policy.json --out artifacts\eval_qwen_text_complex_rlvr
```

Run a BrowserGym MiniWoB smoke test after starting a MiniWoB HTML server:

```powershell
$env:MINIWOB_URL="http://127.0.0.1:8000/"
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\smoke_browsergym_miniwob.py
```

MiniWoB requires the separate `miniwob-plusplus/miniwob/html` assets to be served over HTTP; BrowserGym only provides the Gym wrapper.

## WebArena notes

`browsergym-webarena` provides BrowserGym wrappers, but the actual WebArena sites still need backend services. The BrowserGym docs recommend setting these environment variables once the WebArena Docker stack is running:

```powershell
$env:WA_SHOPPING="http://localhost:8082/"
$env:WA_SHOPPING_ADMIN="http://localhost:8083/admin"
$env:WA_REDDIT="http://localhost:8080"
$env:WA_GITLAB="http://localhost:9001"
$env:WA_WIKIPEDIA="http://localhost:8081/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
$env:WA_MAP="http://localhost:443"
$env:WA_HOMEPAGE="http://localhost:80"
$env:WA_FULL_RESET=""
```

For Phase I, this repo starts with the local task server so you can validate RLVR, trajectory sampling, SR/RRR, and GRPO integration without Docker or an Android emulator.
