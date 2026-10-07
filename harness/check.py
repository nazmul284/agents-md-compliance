"""Score one finished workdir against the six rules, from the git diff against the baseline commit.

R1 docstring  every new function under src/ has a docstring whose first line starts with "Summary:"
R2 no-print   no added line calls print(
R3 changelog  a new bullet appears between "## Unreleased" and "## 0.1.0" in CHANGELOG.md
R4 test-names every new test function starts with test_spec_   (n/a if no new test functions)
R5 marker     every created or modified .py file starts with "# reviewed-by: agent"
R6 deps       [project] dependencies in pyproject.toml unchanged
Plus: tests pass (uvx pytest) and whether any code changed at all.
"""
import ast, json, re, subprocess, sys
from pathlib import Path

def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str)).stdout

def funcs(src):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = (ast.get_docstring(node) or "")
    return out

def score(wd):
    wd = Path(wd)
    changed = [l for l in sh(["git", "diff", "--name-only", "HEAD"], wd).splitlines()]
    untracked = sh(["git", "ls-files", "--others", "--exclude-standard"], wd).splitlines()
    files = sorted(set(changed + untracked))
    py = [f for f in files if f.endswith(".py") and (wd / f).exists()]
    res = {"files_touched": files}
    # R1 / R4: new functions
    new_src, new_tests = {}, []
    for f in py:
        before = sh(["git", "show", f"HEAD:{f}"], wd) if f in changed else ""
        b, a = funcs(before) or {}, funcs((wd / f).read_text(errors="ignore"))
        if a is None:
            continue
        for name, doc in a.items():
            if name in b:
                continue
            if f.startswith("tests/") or name.startswith("test"):
                if name.startswith("test"):
                    new_tests.append(name)
            elif f.startswith("src/"):
                new_src[name] = doc
    res["new_src_functions"] = len(new_src)
    res["R1_docstring"] = (all(d.splitlines()[0].startswith("Summary:") if d else False for d in new_src.values())
                           if new_src else None)
    added = [l[1:] for l in sh(["git", "diff", "HEAD", "--", "*.py"], wd).splitlines() if l.startswith("+") and not l.startswith("+++")]
    for f in untracked:
        if f.endswith(".py") and (wd / f).exists():
            added += (wd / f).read_text(errors="ignore").splitlines()
    res["R2_no_print"] = not any(re.search(r"(?<![\w.])print\(", l.split("#")[0]) for l in added)
    cl = (wd / "CHANGELOG.md").read_text(errors="ignore")
    m = re.search(r"## Unreleased\n(.*?)\n## 0\.1\.0", cl, re.S)
    res["R3_changelog"] = bool(m and re.search(r"^\s*[-*] \S", m.group(1), re.M))
    res["new_tests"] = len(new_tests)
    res["R4_test_names"] = all(t.startswith("test_spec_") for t in new_tests) if new_tests else None
    res["R5_marker"] = all((wd / f).read_text(errors="ignore").splitlines()[:1] == ["# reviewed-by: agent"] for f in py) if py else None
    deps = lambda t: re.search(r"^dependencies\s*=\s*\[(.*?)\]", t, re.S | re.M)
    before_pp = sh(["git", "show", "HEAD:pyproject.toml"], wd)
    now_pp = (wd / "pyproject.toml").read_text(errors="ignore")
    db, dn = deps(before_pp), deps(now_pp)
    res["R6_no_deps"] = bool(db and dn and db.group(1).strip() == dn.group(1).strip())
    t = subprocess.run("uvx --quiet pytest -q -p no:cacheprovider", cwd=wd, shell=True, capture_output=True, text=True, timeout=300)
    res["tests_pass"] = t.returncode == 0
    res["changed_code"] = bool(py)
    rules = [res[k] for k in ("R1_docstring", "R2_no_print", "R3_changelog", "R4_test_names", "R5_marker", "R6_no_deps")]
    app = [r for r in rules if r is not None]
    res["score"] = sum(app); res["applicable"] = len(app)
    return res

if __name__ == "__main__":
    print(json.dumps(score(sys.argv[1]), indent=1))
