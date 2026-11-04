from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "store" / "corpus.txt"


def append(user, bot):
    """One exchange per block. Nothing else lives here."""
    PATH.parent.mkdir(exist_ok=True)
    with PATH.open("a") as f:
        f.write(f"you: {user}\nbot: {bot}\n\n")
