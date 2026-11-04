from collections import deque


class Memory:
    """Recent turns. Oldest drop off first."""

    def __init__(self, size=8):
        self.turns = deque(maxlen=size)

    def add(self, who, text):
        self.turns.append((who, text))

    def history(self):
        return list(self.turns)
