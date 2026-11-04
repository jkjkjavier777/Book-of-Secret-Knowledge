import json
import random
import re
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "learned.json"
CUE = re.compile(r"^say it like this:\s*(.+)$", re.I)


def norm(text):
    return " ".join(re.findall(r"[a-z']+", text.lower()))


class Learner:
    """Bends the bot toward how you talk. No model code."""

    def __init__(self):
        try:
            self.data = json.loads(PATH.read_text())
        except (OSError, ValueError):
            self.data = {}
        self.data.setdefault("scores", {})
        self.data.setdefault("corrections", {})
        self.last = None    # (normalized input, reply, raw input)
        self.to_log = None  # (raw input, answer worth training on)

    def _save(self):
        PATH.write_text(json.dumps(self.data, indent=2))

    def observe(self, text, reply):
        self.last = (norm(text), reply, text)

    def correction_for(self, text):
        options = self.data["corrections"].get(norm(text))
        return random.choice(options) if options else None

    def pick(self, pool):
        weights = [max(0.1, 1 + self.data["scores"].get(r, 0)) for r in pool]
        return random.choices(pool, weights)[0]

    def handle(self, text):
        """Feedback commands. Returns a note, or None if text is normal chat."""
        self.to_log = None
        text = text.strip()
        if text not in ("+", "-") and not CUE.match(text):
            return None
        if not self.last:
            return "(nothing to correct yet)"
        key, reply, raw = self.last
        scores = self.data["scores"]
        if text == "+":
            scores[reply] = scores.get(reply, 0) + 1
            self.to_log = (raw, reply)
            note = "(kept)"
        elif text == "-":
            scores[reply] = scores.get(reply, 0) - 1
            note = "(dropped a notch)"
        else:
            new = CUE.match(text).group(1).strip()
            self.data["corrections"].setdefault(key, []).append(new)
            scores[reply] = scores.get(reply, 0) - 1
            self.to_log = (raw, new)
            note = "(learned)"
        self._save()
        return note
