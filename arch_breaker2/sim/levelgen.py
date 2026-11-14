"""Mirror-symmetric layouts that get harder slowly. Same seed and level, same wall."""
from .rng import Rng
from .state import Brick
from . import const as C


def rows_for(level: int) -> int:
    return min(C.MAX_ROWS, 3 + level // 2)


def family_for(level: int, rng: Rng) -> str:
    if level < 3:
        return rng.choice(("full", "arch"))
    if level < 5:
        return rng.choice(("full", "arch", "checker"))
    return rng.choice(("arch", "checker", "pockets", "pillars"))


def _mask(family: str, rows: int, rng: Rng):
    half = C.COLS // 2
    m = [[True] * half for _ in range(rows)]
    if family == "arch":
        for r in range(rows):
            for c in range(max(0, 2 - r)):
                m[r][c] = False
    elif family == "checker":
        for r in range(rows):
            if r % 2 == 1:
                for c in range(half):
                    if c % 2 == 1:
                        m[r][c] = False
    elif family == "pockets":
        for _ in range(2 + rng.below(3)):
            r, c = rng.below(rows), rng.below(half)
            m[r][c] = False
            if r + 1 < rows:
                m[r + 1][c] = False
    elif family == "pillars":
        gap = 1 + rng.below(2)
        for r in range(rows):
            for c in range(half):
                if c % (gap + 1) == gap:
                    m[r][c] = False
    return m


def generate(seed: int, level: int):
    rng = Rng(seed * 1000003 + level * 7919)
    rows = rows_for(level)
    fam = family_for(level, rng)
    m = _mask(fam, rows, rng)
    half = C.COLS // 2
    out = []
    for r in range(rows):
        for c in range(half):
            if not m[r][c]:
                continue
            hp = 1
            if level >= 3 and r < max(1, rows // 3) and rng.unit() < 0.5:
                hp = 2
            if level >= 5 and r == 0 and rng.unit() < 0.5:
                hp = 3
            drop = rng.unit() < 0.12
            for cc in (c, C.COLS - 1 - c):
                x = C.GRID_L + cc * (C.BRICK_W + C.GAP_X)
                y = C.GRID_T + r * (C.BRICK_H + C.GAP_Y)
                out.append(Brick(cc, r, hp, hp, drop, float(x), float(y)))
    if len(out) < 8:  # a pocket layout that ate too much: fall back to a full wall
        return generate(seed + 1, level) if fam != "full" else out
    return out
