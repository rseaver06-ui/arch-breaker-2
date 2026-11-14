"""Draws the launcher icon in the current Omarchy theme. Flat, one shape, no text."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pygame  # noqa: E402
from arch_breaker2.render.theme import Theme  # noqa: E402

out = sys.argv[1]
pygame.init()
th = Theme()
S = 256
s = pygame.Surface((S, S), pygame.SRCALPHA)
pygame.draw.rect(s, th.bg, (0, 0, S, S), border_radius=56)
for r in range(3):
    for c in range(4):
        pygame.draw.rect(s, th.row(r), (40 + c * 46, 52 + r * 28, 40, 20), border_radius=5)
pygame.draw.rect(s, th.accent, (80, 196, 96, 14), border_radius=7)
pygame.draw.circle(s, th.accent, (128, 164), 11)
pygame.image.save(s, out)
