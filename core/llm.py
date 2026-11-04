import json
import urllib.request

URL = "http://127.0.0.1:8080/v1/chat/completions"
SYSTEM = (
    "You are the Book of Secret Knowledge, a small archive-bot running "
    "offline on its owner's phone. You learn from the owner's corrections. "
    "Be curious and brief: one to three sentences. Never claim training "
    "or knowledge you cannot name. Say plainly when you don't know."
)


def ask(history, text, notes=(), timeout=180):
    """Returns the model's reply, or None if the server is down."""
    system = SYSTEM
    if notes:
        system += "\nThings the user taught you:\n" + "\n".join(notes)
    msgs = [{"role": "system", "content": system}]
    for who, t in history:
        msgs.append({"role": "user" if who == "you" else "assistant", "content": t})
    if not history or history[-1][1] != text:
        msgs.append({"role": "user", "content": text})
    body = json.dumps({"messages": msgs, "max_tokens": 120, "temperature": 0.7}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip() or None
    except Exception:
        return None
