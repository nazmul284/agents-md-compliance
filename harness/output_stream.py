"""For every instructed 'report' run, did the CLI report go to stdout or to stderr (logging's default)?
usage: python output_stream.py <work_dir>   (reads <work_dir>/runs/*-report-r*)"""
import re, sys
from collections import Counter
from pathlib import Path
W = Path(sys.argv[1]); res = {}
for d in sorted(W.glob("runs/*-report-r*")):
    agent, cond = d.name.split("-")[0], d.name.split("-")[1]
    if cond == "none":
        continue
    code = "\n".join(p.read_text() for p in (d / "src/inventory").glob("*.py"))
    if "basicConfig" not in code and "StreamHandler" not in code:
        kind = "no logging config"
    elif re.search(r"stream\s*=\s*sys\.stdout|StreamHandler\(\s*sys\.stdout", code):
        kind = "stdout"
    else:
        kind = "stderr (default)"
    res.setdefault(agent, []).append(kind)
for a, v in res.items():
    print(a, len(v), dict(Counter(v)))
