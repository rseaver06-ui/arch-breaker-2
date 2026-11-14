"""A computer player. It is just another input source, so it works online later too."""
from ..sim import const as C
from ..sim.rng import Rng
from ..sim.state import Input

LEVELS = {"easy": (0.40, 40.0), "normal": (0.20, 16.0), "hard": (0.05, 4.0)}


class Cpu:
    def __init__(self, owner: int, level: str = "normal", seed: int = 0):
        self.owner = owner
        self.delay, self.miss = LEVELS[level]
        self.rng = Rng(seed ^ 0xC9A1)
        self.timer = 0.0
        self.hold = 0.0
        self.target = None

    def _landing(self, b):
        """Where a falling ball crosses the paddle line, with side-wall bounces."""
        if b.vy <= 0:
            return None
        t = (C.PADDLE_Y - C.BALL_R - b.y) / (b.vy * b.speed)
        x = b.x + b.vx * b.speed * t
        w = C.COURT_R - C.COURT_L - 2 * C.BALL_R
        rel = (x - C.COURT_L - C.BALL_R) % (2 * w)
        if rel > w:
            rel = 2 * w - rel
        return t, C.COURT_L + C.BALL_R + rel

    def input(self, st) -> Input:
        p = st.players[self.owner]
        if not p.alive:
            return Input()
        if any(b.held and b.owner == self.owner for b in st.balls):
            self.hold += C.TICK
            return Input(launch=self.hold > 0.6)
        self.hold = 0.0
        self.timer -= C.TICK
        if self.timer <= 0:
            self.timer = self.delay
            best = None
            for b in st.balls:
                if b.held:
                    continue
                hit = self._landing(b)
                if not hit:
                    continue
                t, x = hit
                in_zone = p.zone_l <= x <= p.zone_r
                if not in_zone and b.owner != self.owner:
                    continue
                key = (0 if in_zone else 1, t)
                if best is None or key < best[0]:
                    best = (key, x)
            if best:
                self.target = best[1] + (self.rng.unit() * 2 - 1) * self.miss
            else:
                self.target = (p.zone_l + p.zone_r) / 2
        if self.target is None:
            return Input()
        d = self.target - p.x
        if abs(d) < 4:
            return Input()
        return Input(left=d < 0, right=d > 0)
