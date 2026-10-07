"""Re-run Claude Code on the trap condition (AGENTS.md + unrelated CLAUDE.md) with stream-json,
and record which files it opened before editing. usage: python trace_claude.py <work_dir>"""
import json, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from run import FIXTURE, CONDITIONS, TASKS
from check import score
work = Path(sys.argv[1]).resolve(); out = []
for cond in ("both_no_import",):
    for task, prompt in TASKS.items():
        wd = work / "trace" / f"{cond}-{task}"
        shutil.rmtree(wd, ignore_errors=True)
        shutil.copytree(FIXTURE, wd, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        for f, b in CONDITIONS[cond].items():
            (wd / f).write_text(b)
        g = lambda *a: subprocess.run(["git", *a], cwd=wd, capture_output=True)
        g("init", "-q"); g("add", "-A"); g("-c", "user.name=f", "-c", "user.email=f@e.com", "commit", "-qm", "b")
        p = subprocess.run(["claude", "-p", prompt, "--model", "claude-sonnet-5-5", "--dangerously-skip-permissions",
                            "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                            "--no-session-persistence", "--output-format", "stream-json", "--verbose"],
                           cwd=wd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1200)
        calls = []
        for line in p.stdout.splitlines():
            try:
                ev = json.loads(line)
            except Exception:
                continue
            for blk in (ev.get("message", {}) or {}).get("content", []) if isinstance(ev.get("message"), dict) else []:
                if isinstance(blk, dict) and blk.get("type") == "tool_use":
                    calls.append({"tool": blk["name"], "input": json.dumps(blk.get("input"))[:160]})
        reads = [i for i, c in enumerate(calls) if "AGENTS.md" in c["input"]]
        edits = [i for i, c in enumerate(calls) if c["tool"] in ("Edit", "Write", "MultiEdit")]
        rec = {"condition": cond, "task": task, "tool_calls": len(calls), "first_agents_md_call": reads[0] + 1 if reads else None,
               "first_edit_call": edits[0] + 1 if edits else None, "calls": calls[:12], **score(wd)}
        out.append(rec)
        print(task, "calls", len(calls), "AGENTS.md first touched at call", rec["first_agents_md_call"], "first edit", rec["first_edit_call"], "score", rec["score"], "/", rec["applicable"], flush=True)
(work / "trace.json").write_text(json.dumps(out, indent=1))
