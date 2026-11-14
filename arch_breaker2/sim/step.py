"""One tick of the rules. step(state, inputs) mutates state and returns events.

Events are tuples the renderer and sound use: ("brick", x, y, row, chain),
("paddle", edge), ("lose", owner), ("shield", owner), ("drop", kind, owner),
("clear",), ("over",), ("wall",), ("crumble",).
Only +, -, *, / and sqrt are used, so the same inputs replay identically.
"""
from math import sqrt

from . import const as C
from .state import Ball, Drop, State, Input


def _norm(vx, vy):
    L = sqrt(vx * vx + vy * vy) or 1.0
    return vx / L, vy / L


def _min_vy(vx, vy):
    if abs(vy) < C.MIN_VY:
        s = -1.0 if vy < 0 else 1.0
        vy = s * C.MIN_VY
        vx = (-1.0 if vx < 0 else 1.0) * sqrt(1.0 - C.MIN_VY * C.MIN_VY)
    return vx, vy


def _toward(v, target, rate):
    if v < target:
        return min(target, v + rate)
    return max(target, v - rate)


def _paddles(st: State, inputs, dt):
    for p, inp in zip(st.players, inputs):
        if not p.alive:
            continue
        target = (float(inp.right) - float(inp.left)) * C.PADDLE_MAX
        rate = C.PADDLE_MAX * dt / (C.PADDLE_ACCEL_T if target else C.PADDLE_DECEL_T)
        p.vx = _toward(p.vx, target, rate)
        p.x += p.vx * dt
        lo, hi = p.zone_l + p.half, p.zone_r - p.half
        if p.x < lo:
            p.x, p.vx = lo, 0.0
        elif p.x > hi:
            p.x, p.vx = hi, 0.0
        if p.wide_t > 0:
            p.wide_t -= dt
            if p.wide_t <= 0:
                p.w = float(C.PADDLE_W)
        if p.pass_t > 0:
            p.pass_t -= dt


def _launch(st: State, inputs):
    for b in st.balls:
        if not b.held:
            continue
        p = st.players[b.owner]
        b.x, b.y = p.x, C.PADDLE_Y - C.BALL_R - 1
        if inputs[b.owner].launch:
            b.held = False
            vx = p.vx / C.PADDLE_MAX * C.SPIN
            b.vx, b.vy = _norm(vx, -1.0)


def _paddle_hit(st: State, b: Ball, p, ev):
    offset = max(-1.0, min(1.0, (b.x - p.x) / p.half))
    vx = offset * C.MAX_SIN + p.vx / C.PADDLE_MAX * C.SPIN
    vx = max(-0.95, min(0.95, vx))
    vy = -sqrt(1.0 - vx * vx)
    b.vx, b.vy = _min_vy(*_norm(vx, vy))
    b.y = C.PADDLE_Y - C.BALL_R
    b.speed = min(C.speed_cap(st.level), b.speed + C.BALL_PER_HIT)
    b.owner = p.owner
    b.chain = 0
    st.paddle_hits += 1
    st.hits_since_loss += 1
    st.creep_hits += 1
    ev.append(("paddle", abs(offset) >= C.EDGE_FRAC))


def _pick_kind(st: State) -> str:
    since_loss = (st.tick - st.last_loss_tick) * C.TICK
    if since_loss < C.HELP_WINDOW:
        return st.rng.choice(("wide", "shield"))
    if st.hits_since_loss > C.HOT_STREAK:
        return st.rng.choice(("multi", "pass", "slow", "wide"))
    return st.rng.choice(C.KINDS)


def _break(st: State, br, b: Ball, ev, pierce):
    br.hp -= 1
    if br.hp > 0:
        return False
    st.bricks.remove(br)
    b.chain += 1
    p = st.players[b.owner]
    p.score += 10 * br.hp0 + 5 * (b.chain - 1)
    ev.append(("brick", br.x + C.BRICK_W / 2, br.y + C.BRICK_H / 2, br.row, b.chain))
    if br.drop:
        st.drops.append(Drop(br.x + C.BRICK_W / 2, br.y + C.BRICK_H / 2, _pick_kind(st), b.owner))
    if len(st.bricks) == 1:
        st.last_brick_t = C.LAST_BRICK_T
    return True


def _ball_bricks(st: State, b: Ball, ev):
    bl, br_, bt, bb = b.x - C.BALL_R, b.x + C.BALL_R, b.y - C.BALL_R, b.y + C.BALL_R
    for br in st.bricks:
        if br_ <= br.x or bl >= br.x + C.BRICK_W or bb <= br.y or bt >= br.y + C.BRICK_H:
            continue
        p = st.players[b.owner]
        pierce = p.pass_t > 0 and br.hp == 1
        if len(st.bricks) == 1:
            st.last_brick_t = C.LAST_BRICK_T
        if pierce:
            _break(st, br, b, ev, True)
            return
        dx = min(br_ - br.x, br.x + C.BRICK_W - bl)
        dy = min(bb - br.y, br.y + C.BRICK_H - bt)
        if dx < dy:
            b.vx = -b.vx
            b.x += dx if b.vx > 0 else -dx
        else:
            b.vy = -b.vy
            b.y += dy if b.vy > 0 else -dy
        b.vx, b.vy = _min_vy(b.vx, b.vy)
        _break(st, br, b, ev, False)
        return


def _spawn_for(st: State, p):
    st.balls.append(Ball(p.x, C.PADDLE_Y - C.BALL_R - 1, 0.0, -1.0, C.BALL_BASE, p.owner))


def _lose_ball(st: State, b: Ball, ev):
    p = st.players[b.owner]
    st.balls.remove(b)
    p.lives -= 1
    st.last_loss_tick = st.tick
    st.hits_since_loss = 0
    st.lost_this_level = True
    st.streak = 0
    ev.append(("lose", p.owner))
    if any(o.owner == p.owner for o in st.balls):
        return
    if p.lives > 0:
        _spawn_for(st, p)
        st.balls[-1].speed = C.BALL_BASE + (b.speed - C.BALL_BASE) / 2.0
    else:
        p.alive = False


def _balls(st: State, ev, dt):
    scale = C.SLOW_SCALE if st.slow_t > 0 else 1.0
    for b in list(st.balls):
        if b.held or b not in st.balls:
            continue
        dist = b.speed * scale * dt
        n = int(dist / 2.0) + 1
        sub = dist / n
        for _ in range(n):
            b.x += b.vx * sub
            b.y += b.vy * sub
            if b.x - C.BALL_R < C.COURT_L:
                b.x, b.vx = C.COURT_L + C.BALL_R, abs(b.vx)
                ev.append(("wall",))
            elif b.x + C.BALL_R > C.COURT_R:
                b.x, b.vx = C.COURT_R - C.BALL_R, -abs(b.vx)
                ev.append(("wall",))
            if b.y - C.BALL_R < C.COURT_T:
                b.y, b.vy = C.COURT_T + C.BALL_R, abs(b.vy)
                ev.append(("wall",))
            if b.vy > 0 and b.y + C.BALL_R >= C.PADDLE_Y and b.y - C.BALL_R <= C.PADDLE_Y + C.PADDLE_H:
                for p in st.players:
                    if p.alive and abs(b.x - p.x) <= p.half + C.BALL_R:
                        _paddle_hit(st, b, p, ev)
                        break
            if b.y - C.BALL_R > C.COURT_B:
                p = st.players[b.owner]
                if p.shield > 0:
                    p.shield -= 1
                    b.y, b.vy = C.COURT_B - C.BALL_R, -abs(b.vy)
                    ev.append(("shield", p.owner))
                else:
                    _lose_ball(st, b, ev)
                    break
            _ball_bricks(st, b, ev)
            if b not in st.balls:
                break


def _apply_drop(st: State, d: Drop, p, ev):
    ev.append(("drop", d.kind, p.owner))
    if d.kind == "wide":
        p.w, p.wide_t = float(C.WIDE_W), C.WIDE_T
    elif d.kind == "shield":
        p.shield = min(3, p.shield + 1)
    elif d.kind == "pass":
        p.pass_t = C.PASS_T
    elif d.kind == "slow":
        st.slow_t = C.SLOW_T
    elif d.kind == "multi":
        for b in [x for x in st.balls if x.owner == p.owner and not x.held]:
            for side in (-0.45, 0.45):
                if len(st.balls) >= C.MAX_BALLS:
                    break
                vx, vy = _min_vy(*_norm(b.vx + side, b.vy))
                st.balls.append(Ball(b.x, b.y, vx, vy, b.speed, p.owner, False, b.chain))


def _drops(st: State, ev, dt):
    for d in list(st.drops):
        d.y += C.DROP_SPEED * dt
        if d.y > C.COURT_B:
            st.drops.remove(d)
            continue
        if d.y + C.DROP_SIZE / 2 >= C.PADDLE_Y and d.y - C.DROP_SIZE / 2 <= C.PADDLE_Y + C.PADDLE_H:
            for p in st.players:
                if p.alive and abs(d.x - p.x) <= p.half + C.DROP_SIZE / 2:
                    st.drops.remove(d)
                    _apply_drop(st, d, p, ev)
                    break


def _creep(st: State, ev):
    if st.level < C.CREEP_LEVEL or st.creep_hits < C.CREEP_HITS:
        return
    st.creep_hits = 0
    for br in st.bricks:
        br.y += C.BRICK_H + C.GAP_Y
    if any(br.y + C.BRICK_H >= C.PADDLE_Y - 8 for br in st.bricks):
        for p in st.players:
            p.alive = False
        st.mode = "over"
        ev.append(("over",))


def step(st: State, inputs) -> list:
    ev = st.events = []
    if st.mode != "play":
        return ev
    dt = C.TICK
    st.tick += 1
    if st.slow_t > 0:
        st.slow_t -= dt
    _paddles(st, inputs, dt)
    _launch(st, inputs)
    _balls(st, ev, dt)
    _drops(st, ev, dt)
    if len(st.bricks) == 1 and st.last_brick_t > 0:
        st.last_brick_t -= dt
        if st.last_brick_t <= 0:
            st.bricks.clear()
            ev.append(("crumble",))
    _creep(st, ev)
    if st.mode == "play" and not st.bricks:
        st.mode = "clear"
        if not st.lost_this_level:
            st.streak += 1
        for p in st.players:
            if p.alive:
                p.score += C.CLEAR_BONUS * st.level
        ev.append(("clear",))
    elif st.mode == "play" and not any(p.alive for p in st.players):
        st.mode = "over"
        ev.append(("over",))
    return ev


def next_level(st: State) -> None:
    from .state import start_level
    st.level += 1
    start_level(st)
