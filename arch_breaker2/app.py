"""Window, scenes, fixed-step loop, save file, settings, and the small game-feel effects."""
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
from .io.cpu import Cpu
from .audio import Audio, DEFAULTS, MUSIC_CHOICES, MUSIC_LABEL

SAVE = os.path.expanduser("~/.local/share/arch-breaker-2/save.json")
TITLE_ITEMS = ("Daily", "Endless", "Versus", "Settings", "Quit")
PAUSE_ITEMS = ("Resume", "Restart", "Settings", "Main menu")
VERSUS_ITEMS = ("2 Players", "vs CPU")
DIFFS = ("easy", "normal", "hard")
SET_KEYS = ("music", "sfx", "music_vol", "shake", "shards", "back")


class Fx:
    def __init__(self, settings):
        self.s = settings
        self.pause = 0
        self.shake = 0.0
        self.flash = 0.0
        self.parts = []
        self.floats = []
        self.labels = {}
        self.rng = random.Random()

    def burst(self, x, y, col):
        if not self.s["shards"]:
            return
        for _ in range(8):
            a = self.rng.uniform(-1, 1)
            self.parts.append([x, y, a * 90, self.rng.uniform(-80, 20), 0.3, col])

    def jolt(self, t=0.15):
        if self.s["shake"]:
            self.shake = t

    def tick(self, dt):
        self.shake = max(0.0, self.shake - dt)
        self.flash = max(0.0, self.flash - dt)
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 300 * dt
            p[4] -= dt
        self.parts = [p for p in self.parts if p[4] > 0]
        for f in self.floats:
            f[1] -= 18 * dt
            f[3] -= dt
        self.floats = [f for f in self.floats if f[3] > 0]


def load_save():
    data = {"daily": {}, "top": [], "streak": 0, "settings": {}}
    try:
        with open(SAVE) as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    data["settings"] = {**DEFAULTS, **data.get("settings", {})}
    return data


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
    if n == 1:
        return [Input(keys[pygame.K_LEFT] or keys[pygame.K_a], keys[pygame.K_RIGHT] or keys[pygame.K_d],
                      keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP])]
    p1 = Input(keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_w])
    p2 = Input(keys[pygame.K_LEFT], keys[pygame.K_RIGHT], keys[pygame.K_UP])
    return [p1, p2] + [Input() for _ in range(n - 2)]


class App:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Arch Breaker 2")
        info = pygame.display.Info()
        scale = max(1, min((info.current_w - 80) // C.W, (info.current_h - 80) // C.H, 3))
        self.win = pygame.display.set_mode((C.W * scale, C.H * scale), pygame.RESIZABLE)
        self.canvas = pygame.Surface((C.W, C.H))
        self.theme = Theme()
        self.fonts = draw.Fonts(font_path())
        self.save = load_save()
        self.set = self.save["settings"]
        self.audio = Audio(self.set)
        self.fx = Fx(self.set)
        self.scene = "title"
        self.back = "title"
        self.sel = self.vsel = self.ssel = 0
        self.mode = "daily"
        self.st = None
        self.clear_t = 0.0
        self.cpu = None
        self.vs_cpu = False
        self.diff = 1
        self.smoke = int(os.environ.get("AB2_SMOKE", "0"))
        if self.smoke:
            sc = os.environ.get("AB2_SCENE")
            if sc == "versus-play":
                self.vs_cpu = True
                self.start("versus", 123)
            else:
                self.start("endless", 123)
            for b in self.st.balls:
                b.held = False
            if sc and sc != "versus-play":
                self.scene = sc

    # scenes -----------------------------------------------------------
    def start(self, mode, seed=None):
        self.mode = mode
        if seed is None:
            seed = int(today()) if mode == "daily" else random.randrange(1, 10 ** 6)
        versus = mode == "versus"
        self.st = new_game(seed, 2 if versus else 1, versus)
        self.scene = "play"
        self.fx = Fx(self.set)
        self.cpu = Cpu(1, DIFFS[self.diff], seed) if versus and self.vs_cpu else None
        if self.cpu:
            self.fx.labels = {1: "CPU"}
        self.audio.music()

    def record(self):
        p = self.st.players[0]
        s = self.save
        if self.mode == "daily":
            s["daily"][today()] = max(s["daily"].get(today(), 0), p.score)
        else:
            s["top"] = sorted(s["top"] + [[p.score, self.st.level, self.st.seed]], reverse=True)[:5]
        s["streak"] = max(s.get("streak", 0), self.st.streak)
        write_save(s)

    def adjust(self, key, d):
        s = self.set
        if key == "music":
            i = MUSIC_CHOICES.index(s["music"])
            s["music"] = MUSIC_CHOICES[(i + d) % len(MUSIC_CHOICES)]
            if self.st and self.scene != "title":
                self.audio.music()
        elif key in ("sfx", "music_vol"):
            s[key] = round(max(0.0, min(1.0, s[key] + 0.1 * d)), 1)
        elif key in ("shake", "shards", "mute"):
            s[key] = not s[key]
        self.audio.apply()
        write_save(self.save)

    def menu_nav(self, k, n, attr):
        if k in (pygame.K_UP, pygame.K_w):
            setattr(self, attr, (getattr(self, attr) - 1) % n)
        elif k in (pygame.K_DOWN, pygame.K_s):
            setattr(self, attr, (getattr(self, attr) + 1) % n)

    def key(self, k):
        if k == pygame.K_F11 or (k == pygame.K_f and self.scene != "play"):
            pygame.display.toggle_fullscreen()
            return
        if k == pygame.K_m:
            self.adjust("mute", 0)
        elif k == pygame.K_LEFTBRACKET:
            self.adjust("sfx", -1)
        elif k == pygame.K_RIGHTBRACKET:
            self.adjust("sfx", 1)
        elif k == pygame.K_MINUS:
            self.adjust("music_vol", -1)
        elif k == pygame.K_EQUALS:
            self.adjust("music_vol", 1)
        sc = self.scene
        if sc == "title":
            self.menu_nav(k, len(TITLE_ITEMS), "sel")
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                pick = TITLE_ITEMS[self.sel]
                if pick == "Quit":
                    self.running = False
                elif pick == "Versus":
                    self.scene, self.vsel = "versus", 0
                elif pick == "Settings":
                    self.scene, self.back, self.ssel = "settings", "title", 0
                else:
                    self.start(pick.lower())
            elif k == pygame.K_ESCAPE:
                self.running = False
        elif sc == "versus":
            if k in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                self.vsel = 1 - self.vsel
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.diff = (self.diff - 1) % 3
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.diff = (self.diff + 1) % 3
            elif k == pygame.K_ESCAPE:
                self.scene = "title"
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                self.vs_cpu = self.vsel == 1
                self.start("versus")
        elif sc == "settings":
            self.menu_nav(k, len(SET_KEYS), "ssel")
            key = SET_KEYS[self.ssel]
            if k in (pygame.K_LEFT, pygame.K_a) and key != "back":
                self.adjust(key, -1)
            elif k in (pygame.K_RIGHT, pygame.K_d) and key != "back":
                self.adjust(key, 1)
            elif k == pygame.K_ESCAPE or (k in (pygame.K_RETURN, pygame.K_SPACE) and key == "back"):
                self.scene = self.back
            elif k in (pygame.K_RETURN, pygame.K_SPACE) and key in ("shake", "shards"):
                self.adjust(key, 1)
        elif sc == "play":
            if k in (pygame.K_ESCAPE, pygame.K_p):
                self.scene, self.sel = "pause", 0
        elif sc == "pause":
            self.menu_nav(k, len(PAUSE_ITEMS), "sel")
            if k == pygame.K_ESCAPE:
                self.scene = "play"
            elif k == pygame.K_r:
                self.start(self.mode, self.st.seed)
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                pick = PAUSE_ITEMS[self.sel]
                if pick == "Resume":
                    self.scene = "play"
                elif pick == "Restart":
                    self.start(self.mode, self.st.seed)
                elif pick == "Settings":
                    self.scene, self.back, self.ssel = "settings", "pause", 0
                else:
                    self.scene, self.sel = "title", 0
                    self.audio.stop_music()
        elif sc == "over":
            if k == pygame.K_r:
                self.start(self.mode, self.st.seed)
            elif k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.scene, self.sel = "title", 0
                self.audio.stop_music()

    # simulation -------------------------------------------------------
    def tick(self):
        dt = C.TICK
        self.fx.tick(dt)
        if self.scene == "play":
            if self.fx.pause > 0:
                self.fx.pause -= 1
                return
            inputs = read_inputs(pygame.key.get_pressed(), len(self.st.players))
            if self.cpu:
                inputs[1] = self.cpu.input(self.st)
            ev = step(self.st, inputs)
            th, fx, au = self.theme, self.fx, self.audio
            for e in ev:
                kind = e[0]
                if kind == "brick":
                    fx.pause = 2
                    fx.burst(e[1], e[2], th.row(e[3]))
                    if e[4] >= 3:
                        fx.jolt()
                    au.play("brick", e[4])
                elif kind == "paddle":
                    if e[1]:
                        fx.flash = 0.12
                    au.play("edge" if e[1] else "paddle")
                elif kind == "lose":
                    fx.jolt()
                    au.play("lose")
                elif kind == "penalty":
                    fx.jolt(0.1)
                    fx.floats.append([e[2], C.COURT_B - 24, f"-{C.PENALTY}", 1.0, th.players[e[1]]])
                    au.play("penalty")
                elif kind in ("wall", "drop", "shield", "clear"):
                    au.play(kind)
            if self.st.mode == "clear" and self.mode != "versus":
                self.scene, self.clear_t = "clear", 1.2
            elif self.st.mode in ("clear", "over"):
                if self.mode != "versus":
                    self.record()
                self.scene = "over"
        elif self.scene == "clear":
            self.clear_t -= dt
            if self.clear_t <= 0:
                next_level(self.st)
                self.scene = "play"

    # drawing ----------------------------------------------------------
    def settings_items(self):
        s = self.set
        onoff = lambda b: "On" if b else "Off"
        return (f"Music   < {MUSIC_LABEL[s['music']]} >", f"Effects volume   < {int(s['sfx'] * 10)} >",
                f"Music volume   < {int(s['music_vol'] * 10)} >", f"Screen shake   {onoff(s['shake'])}",
                f"Brick shards   {onoff(s['shards'])}", "Back")

    def render(self):
        c, th, f = self.canvas, self.theme, self.fonts
        sc = self.scene
        if sc in ("title", "versus") or (sc == "settings" and self.back == "title"):
            draw.court(c, th)
        else:
            draw.play(c, self.st, th, f, self.fx)
        if sc == "title":
            best = self.save["daily"].get(today(), 0)
            top = self.save["top"][0][0] if self.save["top"] else 0
            sub = [f"today's best {best}", f"endless best {top}", f"best streak {self.save.get('streak', 0)}", f"theme {th.name}"]
            draw.menu(c, th, f, "ARCH BREAKER 2", TITLE_ITEMS, self.sel, "ENTER  Select     F11  Fullscreen", sub)
        elif sc == "versus":
            sub = ["P1   A D   W launches", "P2   ← →   ↑ launches", f"CPU   <  {DIFFS[self.diff]}  >",
                   "a ball through your side: -25"]
            draw.menu(c, th, f, "VERSUS", VERSUS_ITEMS, self.vsel, "ENTER  Start     ← →  Difficulty     ESC  Back", sub)
        elif sc == "settings":
            mute = "   (muted: M)" if self.set["mute"] else ""
            draw.menu(c, th, f, "SETTINGS", self.settings_items(), self.ssel, "← →  Change     ESC  Back",
                      ["music by Zodik, CC-BY 3.0" + mute])
        elif sc == "pause":
            draw.menu(c, th, f, "PAUSED", PAUSE_ITEMS, self.sel, "ESC  Resume     R  Restart")
        elif sc == "clear":
            r = draw.plate(c, pygame.Rect(C.W // 2 - 70, C.H // 2 - 14, 140, 28), th)
            draw.text(c, f.l, f"LEVEL {self.st.level} CLEAR", r.centerx, r.centery, th.fg, "center")
        elif sc == "over" and self.mode == "versus":
            ps = self.st.players
            title = "DRAW" if ps[0].score == ps[1].score else f"P{1 if ps[0].score > ps[1].score else 2} WINS"
            draw.menu(c, th, f, title, (), 0, "SPACE  Menu     R  Rematch",
                      [f"P1 {ps[0].score}     P2 {ps[1].score}", f"seed {self.st.seed}"])
        elif sc == "over":
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
            self.theme.poll()
            self.render()
            clock.tick(120)
            frames += 1
            if self.smoke and frames >= self.smoke:
                if os.environ.get("AB2_SHOT"):
                    pygame.image.save(self.canvas, os.environ["AB2_SHOT"])
                self.running = False
        write_save(self.save)
        pygame.quit()


def main():
    App().run()
