import sys

try:
    import pygame  # noqa: F401
except ImportError:
    print("Arch Breaker 2 needs Python 3 and pygame. On Omarchy run:\n"
          "  sudo pacman -S --needed python python-pygame", file=sys.stderr)
    raise SystemExit(1)

from .app import main

main()
