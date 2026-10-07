"""Build fixture_large/: the same project plus 1,500 plugin modules and 500 docs pages (seeded),
so that a full file listing is long and the instruction file is one name among ~2,000."""
import random, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
L = ROOT / "fixture_large"
shutil.rmtree(L, ignore_errors=True); shutil.copytree(ROOT / "fixture", L)
rng = random.Random(7)
words = "price stock order vendor ledger batch audit route quota tariff ship bin rack pallet sku carrier invoice refund".split()
(L / "src/inventory/plugins").mkdir(parents=True); (L / "src/inventory/plugins/__init__.py").write_text("")
for i in range(1500):
    a, b = rng.sample(words, 2)
    (L / f"src/inventory/plugins/{a}_{b}_{i:04d}.py").write_text(
        f'"""Plugin {i}: {a} {b} adjustments."""\n\n\ndef apply_{a}_{b}_{i}(value: float) -> float:\n'
        f'    """Return the value with the {a} {b} rule applied."""\n    return round(value * {1 + rng.random():.3f}, 2)\n')
for i in range(500):
    a, b = rng.sample(words, 2)
    d = L / "docs" / a; d.mkdir(parents=True, exist_ok=True)
    (d / f"{b}-{i:03d}.md").write_text(f"# {a.title()} {b}\n\n" + " ".join(rng.choice(words) for _ in range(120)) + "\n")
(L / "README.md").write_text("# inventory\n\nA tiny inventory library with a plugin system. See docs/ for details on each plugin family.\n")
print("files:", sum(1 for p in L.rglob("*") if p.is_file()))
