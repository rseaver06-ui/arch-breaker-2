"""Draws a State onto the 640x360 canvas. Reads state, never changes it."""
import pygame

from ..sim import const as C

LETTER = {"wide": "W", "shield": "S", "multi": "M", "pass": "P", "slow": "L"}


class Fonts:
    def __init__(self, path):
        mk = lambda s: pygame.font.Font(path, s) if path else pygame.font.Font(None, s + 4)
        self.s, self.m, self.l = mk(9), mk(12), mk(22)


def text(c, font, s, x, y, color, anchor="topleft"):
    img = font.render(s, True, color)
    r = img.get_rect(**{anchor: (x, y)})
    c.blit(img, r)
    return r


def plate(c, rect, th, pad=8):
    r = pygame.Rect(rect).inflate(pad * 2, pad * 2)
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(s, th.plate, s.get_rect(), border_radius=6)
    c.blit(s, r)
    return r


def court(c, th):
    c.fill(th.bg)
    pygame.draw.rect(c, th.bg_light, (C.COURT_L - 3, C.COURT_T - 3, C.COURT_R - C.COURT_L + 6, C.COURT_B - C.COURT_T + 6), 3)


def play(c, st, th, f, fx):
    court(c, th)
    for br in st.bricks:
        col = th.row(br.row)
        pygame.draw.rect(c, col, (br.x, br.y, C.BRICK_W, C.BRICK_H), border_radius=2)
        for i in range(br.hp - 1):
            inset = 2 + i * 3
            pygame.draw.rect(c, th.row_bright(br.row) if th.dark else th.bg,
                             (br.x + inset, br.y + inset, C.BRICK_W - 2 * inset, C.BRICK_H - 2 * inset), 1)
    for d in st.drops:
        r = pygame.Rect(0, 0, C.DROP_SIZE, C.DROP_SIZE)
        r.center = (d.x, d.y)
        pygame.draw.rect(c, th.accent, r, border_radius=2)
        text(c, f.s, LETTER[d.kind], r.centerx + 1, r.centery, th.bg, "center")
    if len(st.players) > 1:
        for p in st.players[1:]:
            for y in range(C.PADDLE_Y - 12, C.COURT_B, 6):
                pygame.draw.line(c, th.muted, (p.zone_l, y), (p.zone_l, y + 3))
    for p in st.players:
        if not p.alive:
            if len(st.players) > 1:
                pygame.draw.line(c, th.muted, (p.zone_l + 2, C.COURT_B - 1), (p.zone_r - 2, C.COURT_B - 1), 3)
            continue
        col = th.fg_bright if fx.flash > 0 else th.players[p.owner]
        pygame.draw.rect(c, col, (p.x - p.half, C.PADDLE_Y, p.w, C.PADDLE_H), border_radius=3)
        if p.shield > 0:
            pygame.draw.line(c, th.players[p.owner], (p.zone_l, C.COURT_B - 2), (p.zone_r, C.COURT_B - 2), 2)
    for b in st.balls:
        pygame.draw.circle(c, th.players[b.owner], (b.x, b.y), C.BALL_R)
    for px, py, _, _, life, col in fx.parts:
        pygame.draw.rect(c, col, (px, py, 2, 2))
    hud(c, st, th, f, fx.labels)


def hud(c, st, th, f, labels=None):
    if len(st.players) > 1:
        return hud_versus(c, st, th, f, labels or {})
    p = st.players[0]
    text(c, f.m, f"SCORE {p.score}", C.COURT_L, 12, th.fg)
    text(c, f.m, f"LEVEL {st.level}", C.W // 2, 12, th.fg_dark, "midtop")
    for i in range(p.lives):
        pygame.draw.circle(c, th.accent, (C.COURT_R - 6 - i * 12, 18), 3)
    if p.lives == 0 and p.alive:
        pygame.draw.circle(c, th.muted, (C.COURT_R - 6, 18), 3, 1)
    if st.streak > 1:
        text(c, f.s, f"streak {st.streak}", C.W // 2, 26, th.fg_dark, "midtop")
    chain = max((b.chain for b in st.balls), default=0)
    if chain >= 2:
        text(c, f.m, f"x{chain}", C.COURT_R - 60, 12, th.accent, "topright")
    if len(st.bricks) == 1 and st.last_brick_t > 0:
        text(c, f.m, f"{st.last_brick_t:0.1f}", C.W // 2, C.COURT_B - 40, th.fg_dark, "center")
    labels = []
    if p.wide_t > 0:
        labels.append(f"WIDE {p.wide_t:0.0f}")
    if p.pass_t > 0:
        labels.append(f"PASS {p.pass_t:0.0f}")
    if st.slow_t > 0:
        labels.append(f"SLOW {st.slow_t:0.0f}")
    if labels:
        text(c, f.s, "   ".join(labels), C.COURT_L, 26, th.fg_dark)


def menu(c, th, f, title, items, sel, hint, sub=None):
    rows = [f.l.get_height() + 6] + [f.m.get_height() + 4] * len(items)
    if sub:
        rows.insert(1, f.s.get_height() * len(sub) + 6)
    h = sum(rows) + 16 + f.s.get_height() + 10
    w = max(220, f.s.size(hint)[0] + 28)
    box = pygame.Rect(0, 0, w, h)
    box.center = (C.W // 2, C.H // 2)
    plate(c, box, th)
    y = box.top + 8
    text(c, f.l, title, box.centerx, y, th.fg, "midtop")
    y += rows[0]
    if sub:
        for line in sub:
            text(c, f.s, line, box.centerx, y, th.fg_dark, "midtop")
            y += f.s.get_height()
        y += 6
    for i, it in enumerate(items):
        rh = f.m.get_height() + 4
        if i == sel:
            pygame.draw.rect(c, th.accent, (box.left + 10, y, w - 20, rh), border_radius=4)
        text(c, f.m, it, box.left + 18, y + rh // 2, th.bg if i == sel else th.fg, "midleft")
        y += rh
    text(c, f.s, hint, box.centerx, box.bottom - 8, th.fg_dark, "midbottom")


def hud_versus(c, st, th, f, labels):
    for i, p in enumerate(st.players[:2]):
        col = th.players[p.owner]
        right = i == 1
        x = C.COURT_R if right else C.COURT_L
        anchor = "topright" if right else "topleft"
        tag = labels.get(p.owner, f"P{p.owner + 1}")
        text(c, f.m, f"{tag} {p.score}" if not right else f"{p.score} {tag}", x, 8, col if p.alive else th.muted, anchor)
        for k in range(p.lives):
            dx = C.COURT_R - 4 - k * 10 if right else C.COURT_L + 4 + k * 10
            pygame.draw.circle(c, col, (dx, 28), 3)
        if not p.alive:
            text(c, f.s, "OUT", x, 24, th.muted, anchor)
    text(c, f.s, f"{len(st.bricks)} left", C.W // 2, 12, th.fg_dark, "midtop")
    if len(st.bricks) == 1 and st.last_brick_t > 0:
        text(c, f.m, f"{st.last_brick_t:0.1f}", C.W // 2, C.COURT_B - 40, th.fg_dark, "center")
