# Social-RLVR BrowserGym Setup and Run Guide

This guide is for someone receiving this project as a zip file. It explains what each folder contains, how to set up the environment, and how to run the BrowserGym/RLVR experiments.

## 1. What This Project Does

This project is a lightweight browser-agent RLVR research scaffold.

It provides:

- local web tasks served by Flask
- BrowserGym task registrations
- deterministic backend-state verifiers
- a real Ollama model policy
- a verifier-guided RLVR-style improvement loop
- before/after evaluation scripts with success rate, reward, and RRR metrics

The current RLVR path is verifier-guided trajectory distillation. It is not yet weight-level GRPO fine-tuning.

## 2. Folder Map

```text
.
+-- README.md
+-- pyproject.toml
+-- src/
|   +-- social_rlvr_web/
|       +-- local_app.py
|       +-- browsergym_tasks.py
|       +-- tasks.py
|       +-- model_policy.py
|       +-- rlvr_policy.py
|       +-- observation.py
|       +-- env.py
+-- scripts/
|   +-- evaluate_browsergym_rlvr.py
|   +-- train_browsergym_rlvr.py
|   +-- smoke_local_env.py
|   +-- smoke_browsergym_social.py
|   +-- smoke_browsergym_openended.py
|   +-- smoke_browsergym_miniwob.py
+-- docs/
|   +-- setup_and_run_guide.md
|   +-- task_suite.md
|   +-- experiment_status.md
|   +-- research_plan.md
+-- .vscode/
|   +-- settings.json
|   +-- tasks.json
|   +-- launch.json
+-- artifacts/
```

Main files:

- `src/social_rlvr_web/local_app.py`: the local Flask website used by the tasks.
- `src/social_rlvr_web/tasks.py`: task specs and backend-state verifiers.
- `src/social_rlvr_web/browsergym_tasks.py`: BrowserGym task registration.
- `src/social_rlvr_web/model_policy.py`: Ollama/Qwen model policy.
- `src/social_rlvr_web/rlvr_policy.py`: learned trajectory replay policy.
- `scripts/train_browsergym_rlvr.py`: builds a verifier-guided learned policy artifact.
- `scripts/evaluate_browsergym_rlvr.py`: evaluates baseline, Qwen, scripted, and RLVR policies.
- `docs/task_suite.md`: describes all tasks and reward rules.
- `docs/experiment_status.md`: records current results.
- `.vscode/`: ready-to-use VS Code settings, tasks, and launch configs.

Generated/local folders:

- `.conda/`: local Python environment. Usually do not send this in a zip.
- `.venv/`: old/alternate virtual environment. Usually do not send this in a zip.
- `.playwright/`: downloaded browser binaries. Can be regenerated.
- `.nltk_data/`: downloaded NLTK data. Can be regenerated.
- `artifacts/`: generated training/evaluation outputs.
- `.tmp/`, `.pip-cache/`, `.ruff_cache/`, `__pycache__/`: disposable caches.

## 3. Recommended Zip Contents

If you are sending this to a friend, the cleanest zip should include:

```text
README.md
pyproject.toml
.gitignore
.vscode/
docs/
scripts/
src/
artifacts/
```

You can omit these because they are machine-specific or large:

```text
.conda/
.venv/
.playwright/
.nltk_data/
.tmp/
.pip-cache/
.ruff_cache/
__pycache__/
```

If you include `artifacts/`, your friend can inspect your previous results. If you omit it, they can regenerate results by running the training/evaluation commands below.

## 4. Requirements

Recommended system:

- Windows 10 or Windows 11
- VS Code
- Python 3.11 through Conda or Miniconda
- Ollama, for real model runs
- At least several GB free disk space

The project was developed with:

- Python 3.11
- BrowserGym `0.14.3`
- Playwright `1.44`
- Ollama model `qwen2.5:0.5b` for lightweight text-only tests

## 5. Unzip and Open

Unzip the project somewhere simple, for example:

```text
C:\Users\<you>\Documents\social-rlvr-web
```

Open PowerShell in that folder:

```powershell
cd "C:\Users\<you>\Documents\social-rlvr-web"
```

Open in VS Code:

```powershell
code .
```

VS Code should use:

```text
.conda\python.exe
```

If VS Code asks for an interpreter, choose the `.conda` interpreter after creating it in the next step.

## 6. Create the Python Environment

From the project root:

```powershell
conda create --prefix .conda python=3.11 pip -y
```

Install the project in editable mode:

```powershell
.\.conda\python.exe -m pip install -e .[dev,benchmarks]
```

If the benchmark dependencies are too heavy, use the lighter install:

```powershell
.\.conda\python.exe -m pip install -e .[dev]
```

## 7. Install Browser Dependencies

Set the Playwright browser path for this terminal:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
```

Install Chromium:

```powershell
.\.conda\python.exe -m playwright install chromium
```

Optional NLTK setup for BrowserGym/WebArena-related packages:

```powershell
$env:NLTK_DATA=(Resolve-Path .nltk_data).Path
.\.conda\python.exe -c "import nltk; nltk.download('punkt_tab', download_dir='.nltk_data')"
```

## 8. Install Ollama and Pull the Small Model

Install Ollama from:

```text
https://ollama.com/
```

Then pull the lightweight model:

```powershell
ollama pull qwen2.5:0.5b
```

Check that Ollama is reachable:

```powershell
ollama list
```

If Ollama is not installed or not running, scripted and RLVR replay policies can still run, but `--policies qwen` will fail with a model connection error.

## 9. Quick Smoke Tests

Run these from the project root.

Local env smoke test:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\smoke_local_env.py
```

BrowserGym social task smoke test:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\smoke_browsergym_social.py
```

Scripted verifier-selected policy over all tasks:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies scripted --repeats 1 --out artifacts\eval_scripted_smoke
```

Expected result: success rate should be `1.0` for the scripted policy.

## 10. Run the Lightweight Model Baseline

This runs the real small Qwen model on one task:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies qwen --ollama-model qwen2.5:0.5b --model-no-images --model-steps 4 --tasks browsergym/social_rlvr.report.extract_tracking_code --out artifacts\eval_qwen_text_report_zero_shot
```

Output files:

```text
artifacts/eval_qwen_text_report_zero_shot/summary.csv
artifacts/eval_qwen_text_report_zero_shot/episode_results.csv
artifacts/eval_qwen_text_report_zero_shot/trajectories.jsonl
```

On the original laptop, this small model failed the report task by repeatedly clicking submit without filling the tracking code.

## 11. Run RLVR-Style Improvement on the Report Task

Train/build the verifier-guided learned policy artifact:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\train_browsergym_rlvr.py --ollama-model qwen2.5:0.5b --model-no-images --model-steps 4 --tasks browsergym/social_rlvr.report.extract_tracking_code --out artifacts\rlvr_training_report\learned_policy.json
```

Compare before vs after:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies qwen,rlvr --ollama-model qwen2.5:0.5b --model-no-images --model-steps 4 --tasks browsergym/social_rlvr.report.extract_tracking_code --rlvr-policy artifacts\rlvr_training_report\learned_policy.json --out artifacts\eval_qwen_text_report_rlvr
```

Expected shape:

```text
qwen zero-shot: success_rate 0.0
rlvr replay:    success_rate 1.0
```

Exact model behavior can vary by machine and Ollama version.

## 12. Run the Complex Tasks

The two harder tasks are:

```text
browsergym/social_rlvr.orders.priority_followup
browsergym/social_rlvr.schedule.design_review_shared_slot
```

Build the learned policy:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\train_browsergym_rlvr.py --ollama-model qwen2.5:0.5b --model-no-images --model-steps 6 --tasks browsergym/social_rlvr.orders.priority_followup,browsergym/social_rlvr.schedule.design_review_shared_slot --out artifacts\rlvr_training_complex\learned_policy.json
```

Evaluate before vs after:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies qwen,rlvr --ollama-model qwen2.5:0.5b --model-no-images --model-steps 6 --tasks browsergym/social_rlvr.orders.priority_followup,browsergym/social_rlvr.schedule.design_review_shared_slot --rlvr-policy artifacts\rlvr_training_complex\learned_policy.json --out artifacts\eval_qwen_text_complex_rlvr
```

Fast check without calling Ollama:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe scripts\evaluate_browsergym_rlvr.py --policies rlvr --tasks browsergym/social_rlvr.orders.priority_followup,browsergym/social_rlvr.schedule.design_review_shared_slot --rlvr-policy artifacts\rlvr_training_complex\learned_policy.json --out artifacts\eval_complex_rlvr_quick
```

## 13. VS Code Workflow

The zip includes `.vscode/` settings.

Open the folder in VS Code:

```powershell
code .
```

Run a task:

1. Press `Ctrl+Shift+P`
2. Select `Tasks: Run Task`
3. Choose one of:

```text
Setup: install editable package
Setup: install Chromium
Smoke: BrowserGym Social tasks
RLVR: train complex tasks
RLVR: eval complex before-after
RLVR: eval report before-after
```

Use the Run and Debug panel for:

```text
Train RLVR complex tasks
Evaluate RLVR complex before-after
```

## 14. Task IDs

Registered BrowserGym task IDs:

```text
browsergym/social_rlvr.messages.last_five_new_year
browsergym/social_rlvr.gallery.aesthetic_travel_to_meera
browsergym/social_rlvr.report.extract_tracking_code
browsergym/social_rlvr.orders.priority_followup
browsergym/social_rlvr.schedule.design_review_shared_slot
```

See `docs/task_suite.md` for the exact reward rules.

## 15. Reading Results

Each evaluation writes:

```text
summary.csv
episode_results.csv
trajectories.jsonl
```

Useful fields:

- `success_rate`: fraction of episodes solved.
- `mean_reward`: verifier reward averaged over episodes.
- `mean_steps`: average number of browser actions.
- `mean_rrr`: route-reward ratio, calculated as optimal steps divided by actual steps for successful episodes.
- `trajectories.jsonl`: step-by-step actions, rewards, and verifier messages.

## 16. Troubleshooting

If BrowserGym cannot launch Chromium:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe -m playwright install chromium
```

If Python imports fail:

```powershell
.\.conda\python.exe -m pip install -e .[dev,benchmarks]
```

If Qwen/Ollama is slow or stalls:

- confirm Ollama is running
- run `ollama list`
- use `qwen2.5:0.5b` first
- reduce `--model-steps`
- run `--policies rlvr` or `--policies scripted` for a fast pipeline check

If VS Code uses the wrong Python:

1. Press `Ctrl+Shift+P`
2. Select `Python: Select Interpreter`
3. Choose:

```text
<project>\.conda\python.exe
```

If ports are busy:

- close old Python/Playwright runs
- restart the VS Code terminal
- rerun the command

The local tasks use ports around:

```text
8781-8785
```

## 17. Clean Rebuild

To rebuild the local environment from scratch, delete:

```text
.conda/
.playwright/
.nltk_data/
```

Then rerun:

```powershell
conda create --prefix .conda python=3.11 pip -y
.\.conda\python.exe -m pip install -e .[dev,benchmarks]
$env:PLAYWRIGHT_BROWSERS_PATH=(Resolve-Path .playwright).Path
.\.conda\python.exe -m playwright install chromium
```

## 18. Current Research Caveat

The current `rlvr` policy is a learned trajectory artifact produced by verifier-guided improvement. It proves the BrowserGym execution, verifier reward, trajectory collection, and before/after evaluation pipeline.

It does not yet update Qwen model weights with GRPO. A future step is to replace or extend trajectory distillation with true model fine-tuning.
