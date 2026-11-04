from core.generator import Generator
from core.memory import Memory
from learning import corpus

EXIT = {"quit", "exit", "bye"}


def main():
    gen = Generator()
    mem = Memory()
    print("Book of Secret Knowledge. 'quit' leaves.")
    print("+ / - rate the last reply. 'say it like this: ...' corrects it.")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        note = gen.learner.handle(text)
        if note:
            print(note)
            continue
        mem.add("you", text)
        reply = gen.reply(text, mem.history())
        mem.add("bot", reply)
        corpus.append(text, reply)
        print(f"bot> {reply}")
        if text.lower() in EXIT:
            break


if __name__ == "__main__":
    main()
