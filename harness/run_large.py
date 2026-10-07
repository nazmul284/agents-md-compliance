"""Large-repo follow-up: the same tasks in fixture_large/ (~2,000 files). Records compliance and
whether the agent opened each instruction file (Claude via stream-json tool calls, Codex via its
command log). usage: python run_large.py <work_dir> [--reps 2]"""
import argparse, json, re, shutil, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from run import CONDITIONS, TASKS
from check import score

HERE = Path(__file__).resolve().parent; FIX = HERE.parent / "fixture_large"
CELLS = [("codex", "claude_md"), ("codex", "agents_md"), ("claude", "both_no_import"), ("claude", "claude_md")]
MODEL = {"claude": "claude-sonnet-5-5", "codex": "gpt-5.6-sol"}

def reads(agent, stdout):
    seen = []
    for line in stdout.splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if agent == "codex":
            it = ev.get("item", {})
            if ev.get("type") == "item.completed" and it.get("type") == "command_execution":
                seen.append(it.get("command", ""))
        else:
            msg = ev.get("message")
            if isinstance(msg, dict):
                for b in msg.get("content", []) or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        seen.append(json.dumps(b.get("input")))
    return {"tool_calls": len(seen),
            "opened_AGENTS_md": next((i + 1 for i, c in enumerate(seen) if "AGENTS.md" in c), None),
            "opened_CLAUDE_md": next((i + 1 for i, c in enumerate(seen) if "CLAUDE.md" in c), None)}

ap = argparse.ArgumentParser(); ap.add_argument("work"); ap.add_argument("--reps", type=int, default=2)
a = ap.parse_args(); work = Path(a.work).resolve(); out = work / "large"; out.mkdir(parents=True, exist_ok=True)
for rep in range(1, a.reps + 1):
    for task in TASKS:
        for agent, cond in CELLS:
            name = f"large-{agent}-{cond}-{task}-r{rep}"
            f = out / f"{name}.json"
            if f.exists():
                continue
            wd = work / "runs_large" / name
            shutil.rmtree(wd, ignore_errors=True)
            shutil.copytree(FIX, wd, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            for fn, body in CONDITIONS[cond].items():
                (wd / fn).write_text(body)
            g = lambda *x: subprocess.run(["git", *x], cwd=wd, capture_output=True)
            g("init", "-q"); g("add", "-A"); g("-c", "user.name=f", "-c", "user.email=f@e.com", "commit", "-qm", "base")
            if agent == "claude":
                cmd = ["claude", "-p", TASKS[task], "--model", MODEL[agent], "--dangerously-skip-permissions",
                       "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                       "--no-session-persistence", "--output-format", "stream-json", "--verbose"]
            else:
                cmd = ["codex", "exec", "-m", MODEL[agent], "--dangerously-bypass-approvals-and-sandbox", "--ignore-user-config",
                       "--ignore-rules", "--ephemeral", "--skip-git-repo-check", "--json", TASKS[task]]
            t0 = time.time()
            p = subprocess.run(cmd, cwd=wd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1800)
            rec = {"name": name, "agent": agent, "condition": cond, "task": task, "rep": rep, "rc": p.returncode,
                   "wall_s": round(time.time() - t0, 1), **reads(agent, p.stdout), **score(wd)}
            rec.pop("files_touched", None)
            f.write_text(json.dumps(rec, indent=1))
            print(json.dumps({k: rec[k] for k in ("name", "score", "applicable", "opened_AGENTS_md", "opened_CLAUDE_md", "tool_calls")}), flush=True)
