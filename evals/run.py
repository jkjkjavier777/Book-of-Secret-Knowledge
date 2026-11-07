import json
import sys
import time
from pathlib import Path

from core import llm, prompt
from core.generator import Generator

HERE = Path(__file__).resolve().parent


def check(case, out):
    low = out.lower()
    ok = all(m.lower() in low for m in case.get("must", []))
    if case.get("must_any"):
        ok = ok and any(m.lower() in low for m in case["must_any"])
    return ok and not any(m.lower() in low for m in case.get("none", []))


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    label = sys.argv[2] if len(sys.argv) > 2 else ""
    cases = json.loads((HERE / "cases.json").read_text())
    if llm.ask([], "hi") is None:
        sys.exit("LLM server is down. Start llama-server first.")
    gen = Generator()
    gen.learner.data = {"scores": {}, "corrections": {}}  # in memory only
    prompt._pairs = lambda: []
    total = passed = 0
    per_case = {}
    for c in cases:
        facts = c.get("facts", [])
        prompt.load_facts = lambda facts=facts: facts
        gen.mode = c.get("mode")
        wins, last = 0, ""
        for _ in range(runs):
            out = llm.ask([], c["ask"], gen._notes(c["ask"]), gen.mode) or ""
            last = out
            wins += check(c, out)
        total += runs
        passed += wins
        per_case[c["id"]] = wins
        print(f"{c['id']:<26} {wins}/{runs}")
        if wins < runs:
            print("   last:", last.replace("\n", " ")[:110])
    pct = round(100 * passed / total)
    print(f"\nscore {passed}/{total} ({pct}%)")
    row = {"t": time.strftime("%Y-%m-%d %H:%M"), "label": label, "runs": runs,
           "passed": passed, "total": total, "cases": per_case}
    with (HERE / "results.jsonl").open("a") as f:
        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
