#!/bin/sh
# Removes the program, launcher, menu entry and icon. Keeps the save file.
set -u
rm -rf "$HOME/.local/opt/arch-breaker-2"
rm -f "$HOME/.local/bin/arch-breaker-2" \
      "$HOME/.local/share/applications/arch-breaker-2.desktop" \
      "$HOME/.local/share/icons/hicolor/256x256/apps/arch-breaker-2.png"
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
echo "Arch Breaker 2 removed. Save file kept at ~/.local/share/arch-breaker-2/save.json."
