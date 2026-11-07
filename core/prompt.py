import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "store" / "corpus.txt"
FACTS = ROOT / "data" / "facts.txt"
STOP = {
    "the", "a", "an", "is", "are", "was", "to", "of", "and", "it", "in", "me", "i",
    "do", "does", "what", "who", "when", "where", "why", "how", "tell", "about",
    "you", "your", "my", "this", "that", "for", "on", "with",
}


def _w(text):
    return {w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOP}


def load_facts():
    try:
        lines = FACTS.read_text().splitlines()
    except OSError:
        return []
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def add_fact(text):
    text = " ".join(text.split())
    if not text:
        return "(usage: /fact <one sentence>)"
    if text.lower() in {f.lower() for f in load_facts()}:
        return "(already known)"
    FACTS.parent.mkdir(exist_ok=True)
    with FACTS.open("a") as f:
        f.write(text + "\n")
    return "(fact saved)"


def fact_summary():
    facts = load_facts()
    tail = "\n".join("  " + f for f in facts[-5:])
    return f"({len(facts)} facts)" + ("\n" + tail if tail else "")


def _pairs():
    try:
        raw = CORPUS.read_text()
    except OSError:
        return []
    out = []
    for block in raw.split("\n\n"):
        lines = block.strip().split("\n")
        rest = " ".join(lines[1:])
        if len(lines) >= 2 and lines[0].startswith("you: ") and rest.startswith("bot: "):
            out.append((lines[0][5:], rest[5:]))
    return out


def _examples(learner):
    out, seen = [], set()
    scores = learner.data["scores"]
    items = [(q, a) for q, answers in learner.data["corrections"].items() for a in answers]
    items += [(q, a) for q, a in _pairs() if scores.get(a, 0) > 0]
    for q, a in items:
        key = (q.lower().strip(), a)
        if key not in seen:
            seen.add(key)
            out.append((q, a))
    return out


def build(text, learner, rules, k=3):
    """Notes for the LLM: matching facts, closest approved answers, one rule."""
    said = _w(text)
    if not said:
        return []
    notes = []
    hits = []
    for fact in load_facts():
        s = len(said & _w(fact)) / len(said)
        if s > 0:
            hits.append((s, fact))
    hits.sort(key=lambda t: -t[0])
    notes += [f"Fact: {f[:200]}" for _, f in hits[:k]]
    scored = []
    for q, a in _examples(learner):
        qw = _w(q)
        if qw:
            s = len(said & qw) / len(said | qw)
            if s > 0:
                scored.append((s, q, a))
    scored.sort(key=lambda t: -t[0])
    notes += [f'When asked "{q}", a good answer is: {a[:200]}' for _, q, a in scored[:k]]
    best, top = None, 0
    for r in rules:
        s = len(said & set(r["match"]))
        if s > top:
            best, top = r, s
    if best:
        notes.append("Known answer from the book: " + best["say"][0][:200])
    return notes
