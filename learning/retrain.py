import json
import sys
from pathlib import Path

import numpy as np

from glitch_gpt.model import K, forward

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "store" / "corpus.txt"
LEARNED = ROOT / "data" / "learned.json"
OUT = ROOT / "store" / "glitch_gpt.npz"
EXIT = {"quit", "exit", "bye"}
D, H = 16, 128


def build_text():
    raw = CORPUS.read_text().strip() if CORPUS.exists() else ""
    keep = []
    for block in raw.split("\n\n"):
        first = block.split("\n")[0]
        if first.lower().removeprefix("you:").strip() in EXIT:
            continue
        if block:
            keep.append(block)
    try:
        fixes = json.loads(LEARNED.read_text())["corrections"]
    except (OSError, ValueError, KeyError):
        fixes = {}
    for key, answers in fixes.items():
        for a in answers:
            keep += [f"you: {key}\nbot: {a}"] * 3  # your words, weighted up
    return "\n\n".join(keep) + "\n\n"


def main(steps=3000, lr=0.1, batch=64):
    text = build_text()
    if len(text) < 300:
        sys.exit(f"corpus too small ({len(text)} chars). Talk more.")
    chars = sorted(set(text))
    ix = {c: i for i, c in enumerate(chars)}
    V = len(chars)
    data = np.array([ix[c] for c in text])
    n = len(data) - K
    X = np.stack([data[i:i + K] for i in range(n)])
    Y = data[K:]
    rng = np.random.default_rng(0)
    p = {
        "E": rng.normal(0, 0.1, (V, D)),
        "W1": rng.normal(0, (K * D) ** -0.5, (K * D, H)),
        "b1": np.zeros(H),
        "W2": rng.normal(0, H ** -0.5, (H, V)),
        "b2": np.zeros(V),
    }
    for step in range(steps + 1):
        idx = rng.integers(0, n, batch)
        ctx, y = X[idx], Y[idx]
        logits, (x, h) = forward(p, ctx)
        logits -= logits.max(1, keepdims=True)
        pr = np.exp(logits)
        pr /= pr.sum(1, keepdims=True)
        loss = -np.log(pr[np.arange(batch), y] + 1e-9).mean()
        dl = pr
        dl[np.arange(batch), y] -= 1
        dl /= batch
        dW2, db2 = h.T @ dl, dl.sum(0)
        dz = (dl @ p["W2"].T) * (1 - h ** 2)
        dW1, db1 = x.T @ dz, dz.sum(0)
        dx = (dz @ p["W1"].T).reshape(batch, K, D)
        dE = np.zeros_like(p["E"])
        np.add.at(dE, ctx, dx)
        for k, g in (("E", dE), ("W1", dW1), ("b1", db1), ("W2", dW2), ("b2", db2)):
            p[k] -= lr * g
        if step % 500 == 0:
            print(f"step {step}  loss {loss:.3f}")
    OUT.parent.mkdir(exist_ok=True)
    np.savez(OUT, chars=np.array(chars), **p)
    print(f"saved {OUT.name}")


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:2]))
