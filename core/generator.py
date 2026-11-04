import json
import re
from pathlib import Path

from core import llm
from core.learner import Learner

ROOT = Path(__file__).resolve().parent.parent
REPLIES = ROOT / "data" / "replies.json"
CHECKPOINT = ROOT / "store" / "glitch_gpt.npz"


def _words(text):
    return re.findall(r"[a-z']+", text.lower())


class Generator:
    """The only door to the model. Corrections, gated model, then rules."""

    def __init__(self):
        data = json.loads(REPLIES.read_text())
        self.rules = data["rules"]
        self.default = data["default"]
        self.learner = Learner()
        self.model = None
        if CHECKPOINT.exists():
            try:
                from glitch_gpt import model
                self.model = model.load(CHECKPOINT)
            except Exception:
                self.model = None

    def reply(self, text, history=()):
        out = self.learner.correction_for(text)
        if not out:
            out = llm.ask(list(history), text, self._notes())
        if not out and self.model:
            out = self._from_model(text, history)
        out = out or self._from_rules(text)
        self.learner.observe(text, out)
        return out

    def _notes(self):
        c = self.learner.data["corrections"]
        return [f'When asked "{k}", answer: {a[-1]}' for k, a in c.items()][-10:]

    def _trusted(self):
        texts = [s for r in self.rules for s in r["say"]] + self.default
        for answers in self.learner.data["corrections"].values():
            texts += answers
        return set(_words(" ".join(texts)))

    def _from_model(self, text, history):
        from glitch_gpt import model
        out = model.generate(self.model, f"you: {text}\nbot:")
        words = _words(out)
        if not words or not set(words) <= self._trusted():
            return None
        return out

    def _from_rules(self, text):
        said = set(_words(text))
        best, score = None, 0
        for rule in self.rules:
            s = len(said & set(rule["match"]))
            if s > score:
                best, score = rule, s
        pool = best["say"] if best else self.default
        return self.learner.pick(pool)
