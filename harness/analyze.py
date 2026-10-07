"""Summarise results/runs/*.json and results/trace.json into results/summary.json and tables.txt."""
import glob, json
from collections import defaultdict
from pathlib import Path
R = Path(__file__).resolve().parent.parent / "results"
rs = [json.load(open(f)) for f in sorted(glob.glob(str(R / "runs" / "*.json")))]
RULES = [("R1_docstring", "docstring 'Summary:'"), ("R2_no_print", "no print()"), ("R3_changelog", "CHANGELOG entry"),
         ("R4_test_names", "test_spec_ names"), ("R5_marker", "marker comment"), ("R6_no_deps", "no new deps")]
COND = [("none", "no file"), ("agents_md", "AGENTS.md"), ("claude_md", "CLAUDE.md"),
        ("claude_imports", "CLAUDE.md imports it"), ("both_no_import", "both, no import")]
g = defaultdict(list)
for r in rs:
    g[(r["agent"], r["condition"])].append(r)
summ = {}
for (a, c), v in g.items():
    sc, ap = sum(r["score"] for r in v), sum(r["applicable"] for r in v)
    summ[f"{a}/{c}"] = {"runs": len(v), "rules_followed": sc, "rules_applicable": ap, "pct": round(100 * sc / ap, 1),
                        "fully_compliant_runs": sum(r["score"] == r["applicable"] for r in v),
                        "tests_pass": sum(r["tests_pass"] for r in v),
                        "per_rule": {k: [sum(r[k] is True for r in v), sum(r[k] is not None for r in v)] for k, _ in RULES}}
trace = json.loads((R / "trace.json").read_text())
summ["trace_claude_both_no_import"] = [{"task": t["task"], "score": t["score"], "applicable": t["applicable"],
                                        "agents_md_read_at_call": t["first_agents_md_call"]} for t in trace]
(R / "summary.json").write_text(json.dumps(summ, indent=1))
L = ["Rules followed, all three tasks x three runs per cell (9 runs)", "",
     f"{'instruction files':22}{'Claude Code':>14}{'Codex':>12}", f"{'-'*21:22}{'-'*12:>14}{'-'*10:>12}"]
for c, lab in COND:
    cells = []
    for a in ("claude", "codex"):
        s = summ.get(f"{a}/{c}")
        cells.append(f"{s['pct']:.0f}% ({s['fully_compliant_runs']}/9)" if s else "not run")
    L.append(f"{lab:22}{cells[0]:>14}{cells[1]:>12}")
L += ["", "(n/9) = runs that followed every applicable rule", "", "",
      "With no instruction file: which rules happened anyway", "",
      f"{'rule':22}{'Claude Code':>14}{'Codex':>12}", f"{'-'*21:22}{'-'*12:>14}{'-'*10:>12}"]
for k, lab in RULES:
    a, b = summ["claude/none"]["per_rule"][k], summ["codex/none"]["per_rule"][k]
    L.append(f"{lab:22}{f'{a[0]}/{a[1]}':>14}{f'{b[0]}/{b[1]}':>12}")
(R / "tables.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))
