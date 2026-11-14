"""Sound effects synthesized at startup (no files), and the Zodik music tracks."""
import array
import math
import os

import pygame

RATE = 22050
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")
TRACKS = (("path-zion", "Path Zion"), ("future-travel", "Future Travel"),
          ("lord-of-zorg-i", "Lord of Zorg I"), ("tedox", "Tedox"))
MUSIC_CHOICES = ("random",) + tuple(t[0] for t in TRACKS) + ("off",)
MUSIC_LABEL = {"random": "Random", "off": "Off", **dict(TRACKS)}
DEFAULTS = {"music": "random", "sfx": 0.7, "music_vol": 0.5, "mute": False, "shake": True, "shards": True}


def _tone(f0, ms, vol=0.5, f1=None, square=False):
    n = int(RATE * ms / 1000)
    f1 = f0 if f1 is None else f1
    buf = array.array("h")
    phase = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        phase += 2 * math.pi * f / RATE
        v = math.sin(phase)
        if square:
            v = 0.6 if v > 0 else -0.6
        env = 1.0 - i / n
        buf.append(int(v * env * vol * 32767))
    return pygame.mixer.Sound(buffer=buf.tobytes())


class Audio:
    def __init__(self, settings):
        self.s = settings
        self.ok = bool(pygame.mixer.get_init())
        self.last = None
        if not self.ok:
            return
        semis = (0, 2, 4, 5, 7, 9, 11, 12, 14)
        self.chain = [_tone(440 * 2 ** (k / 12), 60, 0.5, square=True) for k in semis]
        self.fx = {
            "paddle": _tone(220, 50, 0.45),
            "edge": _tone(330, 70, 0.5, 440),
            "wall": _tone(330, 25, 0.2),
            "lose": _tone(300, 260, 0.5, 120),
            "penalty": _tone(200, 140, 0.5, 140, square=True),
            "drop": _tone(660, 120, 0.4, 990),
            "shield": _tone(520, 120, 0.4, 390),
            "clear": _tone(523, 320, 0.45, 1046),
        }
        self.apply()

    def apply(self):
        if not self.ok:
            return
        v = 0.0 if self.s["mute"] else float(self.s["sfx"])
        for snd in list(self.fx.values()) + self.chain:
            snd.set_volume(v)
        pygame.mixer.music.set_volume(0.0 if self.s["mute"] else float(self.s["music_vol"]))

    def play(self, name, chain=0):
        if not self.ok:
            return
        if name == "brick":
            self.chain[min(chain - 1, len(self.chain) - 1)].play()
        elif name in self.fx:
            self.fx[name].play()

    def music(self, rng=None):
        """Start the chosen track. Random never repeats the one that just played."""
        if not self.ok:
            return
        choice = self.s["music"]
        if choice == "off":
            pygame.mixer.music.stop()
            return
        if choice == "random":
            import random
            names = [t[0] for t in TRACKS if t[0] != self.last] or [t[0] for t in TRACKS]
            choice = random.choice(names)
        path = os.path.join(MUSIC_DIR, choice + ".ogg")
        if choice == self.last and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            self.last = choice
        except pygame.error:
            pass
        self.apply()

    def stop_music(self):
        if self.ok:
            pygame.mixer.music.stop()
