"""Everything the rules know about. No pygame here."""
from dataclasses import dataclass, field

from .rng import Rng
from . import const as C


@dataclass
class Input:
    left: bool = False
    right: bool = False
    launch: bool = False


@dataclass
class Brick:
    col: int
    row: int
    hp: int
    hp0: int
    drop: bool
    x: float
    y: float


@dataclass
class Paddle:
    owner: int
    x: float          # center
    vx: float
    w: float
    zone_l: float
    zone_r: float
    lives: int
    score: int = 0
    wide_t: float = 0.0
    pass_t: float = 0.0
    shield: int = 0
    alive: bool = True

    @property
    def half(self) -> float:
        return self.w / 2.0


@dataclass
class Ball:
    x: float
    y: float
    vx: float         # unit direction
    vy: float
    speed: float
    owner: int
    held: bool = True
    chain: int = 0


@dataclass
class Drop:
    x: float
    y: float
    kind: str
    owner: int


@dataclass
class State:
    seed: int
    level: int
    rng: Rng
    players: list
    balls: list = field(default_factory=list)
    bricks: list = field(default_factory=list)
    drops: list = field(default_factory=list)
    tick: int = 0
    slow_t: float = 0.0
    paddle_hits: int = 0
    hits_since_loss: int = 0
    last_loss_tick: int = -100000
    last_brick_t: float = 0.0
    creep_hits: int = 0
    lost_this_level: bool = False
    streak: int = 0
    mode: str = "play"    # play | clear | over
    versus: bool = False
    respawn: dict = field(default_factory=dict)
    events: list = field(default_factory=list)


def new_game(seed: int, n_players: int = 1, versus: bool = False) -> State:
    court_w = C.COURT_R - C.COURT_L
    players = []
    for i in range(n_players):
        zl = C.COURT_L + court_w * i / n_players
        zr = C.COURT_L + court_w * (i + 1) / n_players
        players.append(Paddle(i, (zl + zr) / 2.0, 0.0, float(C.PADDLE_W), zl, zr, C.LIVES))
    st = State(seed=seed, level=1, rng=Rng(seed), players=players, versus=versus)
    start_level(st)
    return st


def start_level(st: State) -> None:
    from .levelgen import generate
    st.bricks = generate(st.seed, st.level)
    st.drops = []
    st.balls = []
    st.respawn = {}
    st.slow_t = 0.0
    st.last_brick_t = 0.0
    st.creep_hits = 0
    st.lost_this_level = False
    st.mode = "play"
    for p in st.players:
        if p.alive:
            p.w = float(C.PADDLE_W)
            p.wide_t = p.pass_t = 0.0
            p.x = (p.zone_l + p.zone_r) / 2.0
            p.vx = 0.0
            st.balls.append(Ball(p.x, C.PADDLE_Y - C.BALL_R - 1, 0.0, -1.0, C.BALL_BASE, p.owner))
