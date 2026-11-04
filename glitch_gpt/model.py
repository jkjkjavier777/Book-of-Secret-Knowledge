import numpy as np

K = 8  # context window, in characters


def load(path):
    z = np.load(path, allow_pickle=False)
    p = {k: z[k] for k in z.files}
    p["chars"] = [str(c) for c in p["chars"]]
    return p


def forward(p, ctx):
    x = p["E"][ctx].reshape(len(ctx), -1)
    h = np.tanh(x @ p["W1"] + p["b1"])
    return h @ p["W2"] + p["b2"], (x, h)


def generate(p, prompt, n=160, temp=0.8, seed=None):
    chars = p["chars"]
    ix = {c: i for i, c in enumerate(chars)}
    ids = [ix.get("\n", 0)] * K + [ix[c] for c in prompt if c in ix]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        logits, _ = forward(p, np.array([ids[-K:]]))
        z = logits[0] / temp
        z -= z.max()
        pr = np.exp(z)
        pr /= pr.sum()
        i = int(rng.choice(len(pr), p=pr))
        if chars[i] == "\n":
            break
        out.append(chars[i])
        ids.append(i)
    return "".join(out).strip()
