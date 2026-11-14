#!/bin/sh
# Installs Arch Breaker 2 for the current user only. No sudo, ever.
set -eu
SRC="$(cd "$(dirname "$0")/.." && pwd)"
APP="$HOME/.local/opt/arch-breaker-2"
BIN="$HOME/.local/bin/arch-breaker-2"
DESKTOP="$HOME/.local/share/applications/arch-breaker-2.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

if ! python3 -c "import pygame" >/dev/null 2>&1; then
  echo "Arch Breaker 2 needs Python 3 and pygame. On Omarchy, install them with:" >&2
  echo "  sudo pacman -S --needed python python-pygame" >&2
  echo "Then run this installer again." >&2
  exit 1
fi

rm -rf "$APP"
mkdir -p "$APP" "$(dirname "$BIN")" "$(dirname "$DESKTOP")" "$ICON_DIR"
cp -r "$SRC/arch_breaker2" "$APP/"
cp "$SRC/packaging/uninstall.sh" "$APP/uninstall.sh"
find "$APP" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

cat > "$BIN" <<LAUNCH
#!/bin/sh
export PYTHONPATH="$APP\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m arch_breaker2 "\$@"
LAUNCH
chmod +x "$BIN" "$APP/uninstall.sh"

python3 "$SRC/packaging/make_icon.py" "$ICON_DIR/arch-breaker-2.png"

cat > "$DESKTOP" <<DESK
[Desktop Entry]
Type=Application
Version=1.0
Name=Arch Breaker 2
GenericName=Brick Breaker
Comment=A brick breaker built for Omarchy
Exec=$BIN
Icon=arch-breaker-2
Terminal=false
Categories=Game;ArcadeGame;
Keywords=game;arcade;breakout;bricks;arch;omarchy;
StartupWMClass=arch-breaker-2
DESK

gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
echo "Installed. Search for \"Arch Breaker 2\" in the launcher (Super + Space)."
echo "Your save file lives at ~/.local/share/arch-breaker-2/save.json and is never removed."
