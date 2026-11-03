#!/usr/bin/env python3
"""Plan, cost-check and run generation jobs under a spending limit.

Usage:
  generate.py plan <plan.json> [--max-usd N]
  generate.py run  <plan.json> [--max-usd N]

plan.json: {"jobs": [{"model": "gemini", "prompt": "...", "count": 2}, ...]}
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
SPEND = OUT / "spend.json"


def load(name):
    return json.loads((HERE / name).read_text())


def month_key():
    return datetime.now(timezone.utc).strftime("%Y-%m")


def month_spend():
    if not SPEND.exists():
        return 0.0
    return json.loads(SPEND.read_text()).get(month_key(), 0.0)


def price_job(job, models, settings):
    model = models.get(job["model"])
    if model is None:
        sys.exit(f"unknown model: {job['model']}")
    providers = model["providers"]
    # Without auto_pick_cheapest the job must name its provider.
    if settings["auto_pick_cheapest"]:
        provider = min(providers, key=providers.get)
    else:
        provider = job.get("provider")
        if provider not in providers:
            sys.exit(f"job for {job['model']} must name one of {sorted(providers)}")
    each = providers[provider]
    count = job.get("count", 1)
    return {**job, "provider": provider, "unit_usd": each, "count": count, "total_usd": round(each * count, 4)}


def make_plan(path, max_usd):
    models, settings = load("models.json"), load("settings.json")
    jobs = [price_job(j, models, settings) for j in json.loads(Path(path).read_text())["jobs"]]
    total = round(sum(j["total_usd"] for j in jobs), 4)
    spent = month_spend()
    limit = settings["monthly_limit_usd"]
    problems = []
    if max_usd is not None and total > max_usd:
        problems.append(f"plan costs ${total} > request budget ${max_usd}")
    if spent + total > limit:
        problems.append(f"plan would bring the month to ${round(spent + total, 4)} > limit ${limit}")
    return jobs, total, spent, problems, settings


def print_plan(jobs, total, spent, problems):
    for j in jobs:
        print(f"{j['count']} x {j['model']} via {j['provider']} @ ${j['unit_usd']} = ${j['total_usd']}")
    print(f"total ${total} | spent this month ${round(spent, 4)}")
    for p in problems:
        print("BLOCKED:", p)


def run_one(job, index):
    # Provider calls are not wired up: add one per provider here, reading its key
    # from the PROVIDER_<NAME>_KEY environment variable.
    raise NotImplementedError(f"no client implemented for provider '{job['provider']}'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["plan", "run"])
    ap.add_argument("plan_file")
    ap.add_argument("--max-usd", type=float)
    args = ap.parse_args()

    jobs, total, spent, problems, settings = make_plan(args.plan_file, args.max_usd)
    print_plan(jobs, total, spent, problems)
    if args.command == "plan":
        return
    if problems and settings["hard_stop_at_limit"]:
        sys.exit(1)

    OUT.mkdir(exist_ok=True)
    results = []
    with ThreadPoolExecutor(settings["parallel_jobs"]) as pool:
        for i, res in enumerate(pool.map(lambda a: run_one(*a), [(j, i) for i, j in enumerate(jobs)])):
            results.append(res)
    data = json.loads(SPEND.read_text()) if SPEND.exists() else {}
    data[month_key()] = round(spent + total, 4)
    SPEND.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
