"""Window, scenes, fixed-step loop, save file, and the small game-feel effects."""
import datetime
import json
import os
import random
import time

os.environ.setdefault("SDL_VIDEO_WAYLAND_WMCLASS", "arch-breaker-2")
os.environ.setdefault("SDL_VIDEO_X11_WMCLASS", "arch-breaker-2")
import pygame

from .sim import const as C
from .sim.state import Input, new_game
from .sim.step import step, next_level
from .render.theme import Theme, font_path
from .render import draw

SAVE = os.path.expanduser("~/.local/share/arch-breaker-2/save.json")
TITLE_ITEMS = ("Daily", "Endless", "Quit")
PAUSE_ITEMS = ("Resume", "Restart", "Main menu")


class Fx:
    def __init__(self):
        self.pause = 0
        self.shake = 0.0
        self.flash = 0.0
        self.parts = []
        self.rng = random.Random()

    def burst(self, x, y, col):
        for _ in range(8):
            a = self.rng.uniform(-1, 1)
            self.parts.append([x, y, a * 90, self.rng.uniform(-80, 20), 0.3, col])

    def tick(self, dt):
        self.shake = max(0.0, self.shake - dt)
        self.flash = max(0.0, self.flash - dt)
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 300 * dt
            p[4] -= dt
        self.parts = [p for p in self.parts if p[4] > 0]


def load_save():
    try:
        with open(SAVE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"daily": {}, "top": [], "streak": 0}


def write_save(data):
    try:
        os.makedirs(os.path.dirname(SAVE), exist_ok=True)
        with open(SAVE, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def today():
    return datetime.date.today().strftime("%Y%m%d")


def read_inputs(keys, n):
    p1 = Input(keys[pygame.K_LEFT] or keys[pygame.K_a], keys[pygame.K_RIGHT] or keys[pygame.K_d],
               keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP])
    return [p1] + [Input() for _ in range(n - 1)]


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Arch Breaker 2")
        info = pygame.display.Info()
        scale = max(1, min((info.current_w - 80) // C.W, (info.current_h - 80) // C.H, 3))
        self.win = pygame.display.set_mode((C.W * scale, C.H * scale), pygame.RESIZABLE)
        self.canvas = pygame.Surface((C.W, C.H))
        self.theme = Theme()
        self.fonts = draw.Fonts(font_path())
        self.save = load_save()
        self.fx = Fx()
        self.scene = "title"
        self.sel = 0
        self.mode = "daily"
        self.st = None
        self.clear_t = 0.0
        self.smoke = int(os.environ.get("AB2_SMOKE", "0"))
        if self.smoke:
            self.start("endless", 123)
            self.st.balls[0].held = False

    # scenes -----------------------------------------------------------
    def start(self, mode, seed=None):
        self.mode = mode
        if seed is None:
            seed = int(today()) if mode == "daily" else random.randrange(1, 10 ** 6)
        self.st = new_game(seed, 1)
        self.scene = "play"
        self.fx = Fx()

    def record(self):
        p = self.st.players[0]
        s = self.save
        if self.mode == "daily":
            s["daily"][today()] = max(s["daily"].get(today(), 0), p.score)
        else:
            s["top"] = sorted(s["top"] + [[p.score, self.st.level, self.st.seed]], reverse=True)[:5]
        s["streak"] = max(s.get("streak", 0), self.st.streak)
        write_save(s)

    def key(self, k):
        if k == pygame.K_F11 or k == pygame.K_f and self.scene != "play":
            pygame.display.toggle_fullscreen()
            return
        if self.scene == "title":
            if k in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(TITLE_ITEMS)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(TITLE_ITEMS)
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                if self.sel == 2:
                    self.running = False
                else:
                    self.start(("daily", "endless")[self.sel])
            elif k == pygame.K_ESCAPE:
                self.running = False
        elif self.scene == "play":
            if k in (pygame.K_ESCAPE, pygame.K_p):
                self.scene, self.sel = "pause", 0
        elif self.scene == "pause":
            if k in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(PAUSE_ITEMS)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(PAUSE_ITEMS)
            elif k == pygame.K_ESCAPE:
                self.scene = "play"
            elif k == pygame.K_r:
                self.start(self.mode, self.st.seed)
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                if self.sel == 0:
                    self.scene = "play"
                elif self.sel == 1:
                    self.start(self.mode, self.st.seed)
                else:
                    self.scene, self.sel = "title", 0
        elif self.scene == "over":
            if k == pygame.K_r:
                self.start(self.mode, self.st.seed)
            elif k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.scene, self.sel = "title", 0

    # simulation -------------------------------------------------------
    def tick(self):
        dt = C.TICK
        self.fx.tick(dt)
        if self.scene == "play":
            if self.fx.pause > 0:
                self.fx.pause -= 1
                return
            ev = step(self.st, read_inputs(pygame.key.get_pressed(), len(self.st.players)))
            for e in ev:
                if e[0] == "brick":
                    self.fx.pause = 2
                    self.fx.burst(e[1], e[2], self.theme.row(e[3]))
                    if e[4] >= 3:
                        self.fx.shake = 0.15
                elif e[0] == "paddle" and e[1]:
                    self.fx.flash = 0.12
                elif e[0] == "lose":
                    self.fx.shake = 0.15
            if self.st.mode == "clear":
                self.scene, self.clear_t = "clear", 1.2
            elif self.st.mode == "over":
                self.record()
                self.scene = "over"
        elif self.scene == "clear":
            self.clear_t -= dt
            if self.clear_t <= 0:
                next_level(self.st)
                self.scene = "play"

    # drawing ----------------------------------------------------------
    def render(self):
        c, th, f = self.canvas, self.theme, self.fonts
        if self.scene == "title":
            draw.court(c, th)
            best = self.save["daily"].get(today(), 0)
            top = self.save["top"][0][0] if self.save["top"] else 0
            sub = [f"today's best {best}", f"endless best {top}", f"best streak {self.save.get('streak', 0)}"]
            draw.menu(c, th, f, "ARCH BREAKER 2", TITLE_ITEMS, self.sel, "ENTER  Select     F11  Fullscreen", sub)
        else:
            draw.play(c, self.st, th, f, self.fx)
            if self.scene == "pause":
                draw.menu(c, th, f, "PAUSED", PAUSE_ITEMS, self.sel, "ESC  Resume     R  Restart")
            elif self.scene == "clear":
                r = draw.plate(c, pygame.Rect(C.W // 2 - 70, C.H // 2 - 14, 140, 28), th)
                draw.text(c, f.l, f"LEVEL {self.st.level} CLEAR", r.centerx, r.centery, th.fg, "center")
            elif self.scene == "over":
                p = self.st.players[0]
                draw.menu(c, th, f, "GAME OVER", (), 0, "SPACE  Menu     R  Retry this seed",
                          [f"score {p.score}", f"level {self.st.level}", f"seed {self.st.seed}"])
        ww, wh = self.win.get_size()
        s = max(1, min(ww // C.W, wh // C.H))
        ox, oy = (ww - C.W * s) // 2, (wh - C.H * s) // 2
        if self.fx.shake > 0:
            ox += self.fx.rng.randint(-2, 2) * s
            oy += self.fx.rng.randint(-2, 2) * s
        self.win.fill(th.bg)
        self.win.blit(pygame.transform.scale(c, (C.W * s, C.H * s)), (ox, oy))
        pygame.display.flip()

    def run(self):
        self.running = True
        clock = pygame.time.Clock()
        acc, last, frames = 0.0, time.perf_counter(), 0
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    self.key(e.key)
            now = time.perf_counter()
            acc = min(acc + (now - last), 0.1)
            last = now
            while acc >= C.TICK:
                self.tick()
                acc -= C.TICK
            if self.theme.poll():
                pass
            self.render()
            clock.tick(120)
            frames += 1
            if self.smoke and frames >= self.smoke:
                if os.environ.get("AB2_SHOT"):
                    pygame.image.save(self.canvas, os.environ["AB2_SHOT"])
                self.running = False
        pygame.quit()


def main():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("Arch Breaker 2 needs Python 3 and pygame. On Omarchy run:\n  sudo pacman -S --needed python python-pygame")
        raise SystemExit(1)
    App().run()
