import copy
from math import sqrt

from arch_breaker2.sim import const as C
from arch_breaker2.sim.levelgen import generate
from arch_breaker2.sim.rng import Rng
from arch_breaker2.sim.state import Input, new_game
from arch_breaker2.sim.step import step, next_level

L, R, GO = Input(left=True), Input(right=True), Input(launch=True)


def run(st, inputs_fn, ticks):
    evs = []
    for t in range(ticks):
        evs += step(st, [inputs_fn(t)])
    return evs


def test_same_seed_same_wall():
    a, b = generate(42, 3), generate(42, 3)
    assert [(x.col, x.row, x.hp, x.drop) for x in a] == [(x.col, x.row, x.hp, x.drop) for x in b]
    assert generate(42, 3) != generate(43, 3) or generate(42, 4) != generate(42, 3)


def test_walls_are_mirrored_and_get_harder():
    for lvl in (1, 4, 7, 12):
        bricks = generate(7, lvl)
        cells = {(b.col, b.row, b.hp) for b in bricks}
        assert all((C.COLS - 1 - c, r, hp) in cells for c, r, hp in cells)
        assert len(bricks) >= 8
    assert max(b.hp for b in generate(7, 1)) == 1
    assert len(generate(7, 10)) > len(generate(7, 1))


def test_replay_is_identical():
    rng = Rng(5)
    script = [[L, R, GO, Input()][rng.below(4)] for _ in range(1800)]
    a, b = new_game(99), new_game(99)
    for inp in script:
        step(a, [inp])
        step(b, [inp])
    assert a.tick == b.tick and a.players[0].score == b.players[0].score
    assert [(x.x, x.y, x.vx, x.vy) for x in a.balls] == [(x.x, x.y, x.vx, x.vy) for x in b.balls]
    assert len(a.bricks) == len(b.bricks)


def test_launch_and_paddle_bounce_limits():
    st = new_game(1)
    step(st, [GO])
    b = st.balls[0]
    assert not b.held and b.vy < 0
    # drive the ball into the paddle from the far edge and check the angle stays legal
    p = st.players[0]
    b.x, b.y, b.vx, b.vy = p.x + p.half - 1, C.PADDLE_Y - C.BALL_R - 1, 0.0, 1.0
    step(st, [Input()])
    assert b.vy < 0 and abs(b.vy) >= C.MIN_VY - 1e-9
    assert abs(sqrt(b.vx ** 2 + b.vy ** 2) - 1.0) < 1e-9
    assert b.vx > 0.5  # edge hit sends it out steeply


def test_breaking_bricks_scores_and_chains():
    st = new_game(3)
    step(st, [GO])
    b = st.balls[0]
    br = st.bricks[-1]
    n = len(st.bricks)
    b.x, b.y, b.vx, b.vy = br.x + C.BRICK_W / 2, br.y + C.BRICK_H + C.BALL_R + 1, 0.0, -1.0
    ev = step(st, [Input()])
    assert len(st.bricks) == n - 1 or br.hp < br.hp0
    assert st.players[0].score > 0 or br.hp < br.hp0
    if len(st.bricks) == n - 1:
        assert any(e[0] == "brick" for e in ev) and b.chain == 1 and b.vy > 0


def test_losing_balls_costs_lives_then_game_over():
    st = new_game(2)
    for life in (2, 1, 0):
        step(st, [GO])
        b = st.balls[0]
        b.y, b.vy, b.vx = C.COURT_B + 20, 1.0, 0.0
        ev = step(st, [Input()])
        assert ("lose", 0) in ev and st.players[0].lives == life
    assert st.mode == "over" and not st.players[0].alive


def test_shield_saves_one_ball():
    st = new_game(2)
    st.players[0].shield = 1
    step(st, [GO])
    b = st.balls[0]
    b.y, b.vy, b.vx = C.COURT_B + 20, 1.0, 0.0
    ev = step(st, [Input()])
    assert ("shield", 0) in ev and st.players[0].lives == C.LIVES and b.vy < 0


def test_last_brick_crumbles_and_level_clears():
    st = new_game(4)
    st.bricks = st.bricks[:1]
    st.last_brick_t = C.LAST_BRICK_T
    pass
    ticks = int(C.LAST_BRICK_T / C.TICK) + 2
    for _ in range(ticks):
        step(st, [Input()])
        if st.mode != "play":
            break
    assert st.mode == "clear" and st.streak == 1
    lvl = st.level
    next_level(st)
    assert st.level == lvl + 1 and st.bricks and st.balls[0].held


def test_speed_climbs_with_hits_and_caps():
    st = new_game(6)
    step(st, [GO])
    b = st.balls[0]
    for _ in range(60):
        b.x, b.y, b.vx, b.vy = st.players[0].x, C.PADDLE_Y - C.BALL_R - 1, 0.0, 1.0
        step(st, [Input()])
    assert b.speed == C.speed_cap(st.level) and st.paddle_hits == 60


def test_helpful_drop_after_a_loss():
    st = new_game(8)
    st.last_loss_tick = st.tick
    st.hits_since_loss = 0
    from arch_breaker2.sim.step import _pick_kind
    kinds = {_pick_kind(st) for _ in range(40)}
    assert kinds <= {"wide", "shield"}


def test_theme_reloads_when_file_changes(tmp_path, monkeypatch):
    import os, time
    from arch_breaker2.render.theme import Theme
    f = tmp_path / "colors.toml"
    f.write_text('mode = "dark"\naccent = "#ff0000"\n')
    monkeypatch.setenv("AB2_THEME", str(f))
    th = Theme()
    assert th.accent == (255, 0, 0) and th.dark
    f.write_text('mode = "light"\naccent = "#00ff00"\n')
    os.utime(f, (time.time() + 5, time.time() + 5))
    th.last_check = 0
    assert th.poll() and th.accent == (0, 255, 0) and not th.dark


def _two():
    st = new_game(11, 2)
    for b in st.balls:
        b.held = False
    return st


def test_poach_catching_a_ball_makes_it_yours():
    st = _two()
    p2 = st.players[1]
    b = st.balls[0]
    assert b.owner == 0
    b.x, b.y, b.vx, b.vy = p2.x, C.PADDLE_Y - C.BALL_R - 1, 0.0, 1.0
    step(st, [Input(), Input()])
    assert b.owner == 1 and b.vy < 0


def test_lost_ball_charges_its_owner_wherever_it_falls():
    st = _two()
    b = st.balls[0]
    b.x, b.y, b.vy = st.players[1].x, C.COURT_B + 20, 1.0
    step(st, [Input(), Input()])
    assert st.players[0].lives == C.LIVES - 1 and st.players[1].lives == C.LIVES


def test_knocked_out_zone_is_a_wall():
    st = _two()
    st.players[1].alive = False
    b = st.balls[0]
    b.x, b.y, b.vy = st.players[1].x, C.COURT_B + 20, 1.0
    ev = step(st, [Input(), Input()])
    assert b.vy < 0 and st.players[0].lives == C.LIVES and ("wall",) in ev


def test_match_ends_when_one_player_is_left():
    st = _two()
    st.players[1].lives = 1
    b = st.balls[1]
    b.x, b.y, b.vy = st.players[1].x, C.COURT_B + 20, 1.0
    step(st, [Input(), Input()])
    assert not st.players[1].alive and st.mode == "over"


def test_cpu_is_deterministic_and_chases_the_ball():
    from arch_breaker2.io.cpu import Cpu
    def play():
        st = _two()
        cpus = [Cpu(0, "hard", 11), Cpu(1, "normal", 11)]
        xs = []
        for _ in range(900):
            step(st, [c.input(st) for c in cpus])
            xs.append((st.players[0].x, st.players[1].x))
        return st, xs
    a, xa = play()
    b, xb = play()
    assert xa == xb and a.players[0].score == b.players[0].score
    assert a.paddle_hits > 3   # the CPUs actually return the ball
