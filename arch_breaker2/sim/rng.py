"""Tiny seeded generator (xorshift32). Same seed, same sequence, on any machine."""


class Rng:
    def __init__(self, seed: int):
        self.s = (seed & 0xFFFFFFFF) or 0x9E3779B9

    def next(self) -> int:
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        self.s = s
        return s

    def below(self, n: int) -> int:
        return self.next() % n

    def unit(self) -> float:
        return self.next() / 4294967296.0

    def choice(self, seq):
        return seq[self.below(len(seq))]
