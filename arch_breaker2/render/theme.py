"""Reads Omarchy's live theme. Re-checks the file twice a second; swaps live."""
import os
import subprocess
import time
import tomllib

PATHS = (
    os.path.expanduser("~/.local/state/omarchy/current/theme/colors.toml"),
    os.path.expanduser("~/.config/omarchy/current/theme/colors.toml"),
)
HUES = ("red", "orange", "yellow", "green", "cyan", "blue", "magenta")
FALLBACK = {
    "mode": "dark", "accent": "#f2b544", "selection": "#3a3222", "muted": "#4a4034",
    "background": "#161412", "dark_background": "#100f0d", "darker_background": "#0b0a09",
    "lighter_background": "#24211d", "foreground": "#eae3d6", "dark_foreground": "#8a8275",
    "light_foreground": "#d6cfc2", "bright_foreground": "#fff8ec",
    "red": "#e05a4a", "orange": "#f08a3a", "yellow": "#f2c94c", "green": "#7bb661",
    "cyan": "#5bbcb8", "blue": "#5c8fd6", "magenta": "#b07cd6", "brown": "#8c6b4a",
}


def _rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


class Theme:
    def __init__(self):
        self.path = None
        self.mtime = None
        self.last_check = 0.0
        self.load()

    def poll(self) -> bool:
        now = time.monotonic()
        if now - self.last_check < 0.5:
            return False
        self.last_check = now
        path = self._find()
        mtime = os.path.getmtime(path) if path else None
        if path != self.path or mtime != self.mtime:
            self.load()
            return True
        return False

    def _find(self):
        for p in PATHS:
            if os.path.isfile(p):
                return p
        return None

    def load(self):
        self.path = self._find()
        data = dict(FALLBACK)
        if self.path:
            try:
                with open(self.path, "rb") as f:
                    data.update(tomllib.load(f))
                self.mtime = os.path.getmtime(self.path)
            except (OSError, tomllib.TOMLDecodeError):
                pass
        g = lambda k: _rgb(data.get(k, FALLBACK[k]))
        self.dark = data.get("mode", "dark") != "light"
        self.bg, self.bg_dark, self.bg_darker, self.bg_light = (
            g("background"), g("dark_background"), g("darker_background"), g("lighter_background"))
        self.fg, self.fg_dark, self.fg_light, self.fg_bright = (
            g("foreground"), g("dark_foreground"), g("light_foreground"), g("bright_foreground"))
        self.accent, self.muted, self.selection = g("accent"), g("muted"), g("selection")
        self.hues = [g(h) for h in HUES]
        self.bright = [_rgb(data.get("bright_" + h, data.get(h, FALLBACK[h]))) for h in HUES]
        self.players = [self.accent, g("magenta"), g("cyan"), g("yellow")]
        self.plate = (*(self.bg_darker if self.dark else self.bg_light), 215)

    def row(self, r):
        return self.hues[r % len(self.hues)]

    def row_bright(self, r):
        return self.bright[r % len(self.bright)]


def font_path():
    """The Omarchy system font, if it is installed."""
    try:
        import pygame
        for name in ("jetbrainsmononerdfont", "jetbrainsmononfm", "jetbrainsmono"):
            p = pygame.font.match_font(name)
            if p:
                return p
    except Exception:
        pass
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", "monospace"], capture_output=True, text=True, timeout=2)
        if out.returncode == 0 and os.path.isfile(out.stdout.strip()):
            return out.stdout.strip()
    except Exception:
        pass
    return None
