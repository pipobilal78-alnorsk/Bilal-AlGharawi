---
name: generate
description: Generates images and videos (ads, product shots, short clips) across several AI models and providers while keeping cost under a stated budget. Use when the user asks to create images or videos with multiple models, compare model cost, or "make ads" with a spending cap.
---

# Generate

Produce images and videos with the cheapest provider that meets the requested quality, and never exceed the budget.

## Files

- `models.json` — models, their type (image/video) and per-provider price per output (USD). The prices are placeholders: replace them with the real provider prices before use.
- `settings.json` — `auto_pick_cheapest`, `quality`, `parallel_jobs`, `default_output`, `monthly_limit_usd`, `hard_stop_at_limit`.
- `generate.py` — plans the job, estimates the cost, enforces the limits, runs jobs in parallel and records spend.
- `outputs/` — results, the prompts used, and `spend.json`.

## Step 1 — Brainstorm before building

Ask only what is missing:

1. Goal: how many outputs, image or video, size or duration.
2. Materials: product photo, logo, text, colors, reference examples.
3. Models and budget: how many models to try, quality level, maximum cost per request and per month.
4. Review: what makes a result acceptable, and when to stop and ask before continuing.

## Step 2 — Plan, then get approval

1. Read `models.json` and `settings.json`.
2. Choose the models that fit the request and split the number of outputs between them.
3. Write a detailed `prompt` for each shot, adapted to the chosen model's abilities.
4. Run `python3 generate.py plan <plan.json>` and show the user the models, the provider chosen for each, and the expected total cost. Do not start generating before the user approves.

## Step 3 — Generate

Run `python3 generate.py run <plan.json>` only after approval.

- With `auto_pick_cheapest` on, the cheapest provider that satisfies `quality` is chosen per job.
- The run stops by itself if the request budget or `monthly_limit_usd` would be exceeded (when `hard_stop_at_limit` is true). If that happens, stop the process and propose a cheaper plan.
- Each result is saved in `outputs/` with a JSON file holding the exact model, provider, prompt and cost.

## Step 4 — Review

Check every result, report the real cost from `outputs/spend.json`, and offer to regenerate only the failed ones.

## Safety

- API keys come from environment variables (`PROVIDER_<NAME>_KEY`), never from files in the repository.
- Never print or commit keys.
- Never run a paid job without an approved plan.
