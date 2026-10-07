"""Grouped bars: % of rules followed by instruction-file arrangement. usage: uv run --with matplotlib python charts.py <out.png>"""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
s = json.loads((Path(__file__).resolve().parent.parent / "results" / "summary.json").read_text())
COND = [("none", "no file"), ("agents_md", "AGENTS.md"), ("claude_md", "CLAUDE.md"),
        ("claude_imports", "CLAUDE.md\nimports AGENTS.md"), ("both_no_import", "both files,\nno import")]
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=200)
for j, (agent, color, dx) in enumerate((("claude", "#c2410c", -0.19), ("codex", "#334155", 0.19))):
    for i, (c, _) in enumerate(COND):
        v = s.get(f"{agent}/{c}")
        if not v:
            ax.text(i + dx, 3, "not\nrun", ha="center", fontsize=8, color="#9ca3af"); continue
        ax.bar(i + dx, v["pct"], width=0.36, color=color, zorder=2)
        ax.text(i + dx, v["pct"] + 1.5, f"{v['pct']:.0f}%", ha="center", fontsize=9.5, color="#1f2328")
ax.set_xticks(range(len(COND)), [l for _, l in COND], fontsize=10)
ax.set_ylim(0, 112); ax.set_ylabel("% of applicable rules followed (9 runs each)", fontsize=10, color="#6b7280")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.tick_params(colors="#6b7280"); ax.grid(axis="y", color="#eeeeee", zorder=0)
ax.legend(handles=[Patch(color="#c2410c", label="Claude Code (Sonnet 5.5)"), Patch(color="#334155", label="Codex (GPT-5.6-Sol)")],
          loc="upper left", bbox_to_anchor=(0.0, -0.17), ncol=2, frameon=False, fontsize=10)
fig.text(0.02, 0.96, "Any instruction file worked, including ones the docs do not expect", fontsize=13.5, weight="bold", color="#1f2328")
fig.text(0.02, 0.915, "Six house rules, three coding tasks, three runs each; scored from the git diff", fontsize=10, color="#6b7280")
fig.text(0.02, 0.012, "Claude Code 2.1.289 · Codex CLI 0.154.0 · 81 runs, 7 Oct 2026 · github.com/nazmul284/agents-md-compliance", fontsize=6.8, color="#6b7280")
fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.25)
fig.savefig(sys.argv[1], facecolor="white"); print("ok")
