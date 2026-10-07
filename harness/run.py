"""Run every (agent, condition, task, rep) cell, then score it. Resumable.

usage: python run.py <work_dir> [--reps 2] [--jobs 3]
"""
import argparse, json, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from check import score

HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent / "fixture"
RULES = (HERE / "rules.md").read_text()
UNRELATED = "# CLAUDE.md\n\nThis is the inventory library. Run the tests with `uvx pytest`.\n"
CONDITIONS = {
    "none":           {},
    "agents_md":      {"AGENTS.md": RULES},
    "claude_md":      {"CLAUDE.md": RULES},
    "claude_imports": {"AGENTS.md": RULES, "CLAUDE.md": "# CLAUDE.md\n\n@AGENTS.md\n"},
    "both_no_import": {"AGENTS.md": RULES, "CLAUDE.md": UNRELATED},
}
TASKS = {
    "report":   "Add a command-line report: a function that computes the total value of all items "
                "(quantity times unit price), and a `python -m inventory` entry point that shows each item and the total.",
    "validate": "Make the inventory reject negative quantities: adding an Item whose quantity is below zero should "
                "raise ValueError. Add tests for it.",
    "csv":      "Add CSV export: a method that writes the inventory to a CSV file with the columns sku, name, "
                "quantity and unit_price. Add a test for it.",
}
AGENTS = {"claude": ("claude-sonnet-5-5", list(CONDITIONS)),
          "codex": ("gpt-5.6-sol", ["none", "agents_md", "claude_md", "both_no_import"])}

def cmd(agent, model, task):
    if agent == "claude":
        return ["claude", "-p", task, "--model", model, "--dangerously-skip-permissions",
                "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--no-session-persistence", "--output-format", "json"]
    return ["codex", "exec", "-m", model, "--dangerously-bypass-approvals-and-sandbox", "--ignore-user-config",
            "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "--json", task]

def run(cell, work):
    agent, cond, task, rep = cell
    name = f"{agent}-{cond}-{task}-r{rep}"
    out = work / "results" / f"{name}.json"
    if out.exists():
        return json.loads(out.read_text())
    wd = work / "runs" / name
    shutil.rmtree(wd, ignore_errors=True)
    shutil.copytree(FIXTURE, wd, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    for fname, body in CONDITIONS[cond].items():
        (wd / fname).write_text(body)
    g = lambda *a: subprocess.run(["git", *a], cwd=wd, capture_output=True)
    g("init", "-q"); g("add", "-A"); g("-c", "user.name=f", "-c", "user.email=f@e.com", "commit", "-qm", "baseline")
    model = AGENTS[agent][0]
    t0 = time.time()
    try:
        p = subprocess.run(cmd(agent, model, TASKS[task]), cwd=wd, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=1200)
        rc, log = p.returncode, p.stdout[-20000:] + "\n--- stderr ---\n" + p.stderr[-5000:]
    except subprocess.TimeoutExpired:
        rc, log = "timeout", ""
    (work / "logs").mkdir(exist_ok=True)
    (work / "logs" / f"{name}.log").write_text(log)
    rec = {"name": name, "agent": agent, "model": model, "condition": cond, "task": task, "rep": rep,
           "rc": rc, "wall_s": round(time.time() - t0, 1), **score(wd)}
    if agent == "claude":
        try:
            rec["cost_usd"] = json.loads(p.stdout).get("total_cost_usd")
        except Exception:
            pass
    out.write_text(json.dumps(rec, indent=1))
    print(json.dumps({k: rec[k] for k in ("name", "rc", "score", "applicable", "tests_pass", "wall_s")}), flush=True)
    return rec

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("work"); ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=3); ap.add_argument("--only", default=None)
    a = ap.parse_args(); work = Path(a.work).resolve(); (work / "results").mkdir(parents=True, exist_ok=True)
    cells = [(ag, c, t, r) for r in range(1, a.reps + 1) for t in TASKS for ag, (_, conds) in AGENTS.items() for c in conds]
    if a.only:
        cells = [c for c in cells if "-".join(map(str, c)).startswith(a.only)]
    print(len(cells), "cells", flush=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(lambda c: run(c, work), cells))
