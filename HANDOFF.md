# Arch Breaker 2: handoff

For anyone (person or Claude) picking this up. Bug reports and ideas go in GitHub Issues or Discussions on this repo.

## What it is

A brick breaker built for Omarchy (Arch Linux + Hyprland). Python 3 + pygame, fully offline. It follows the live Omarchy theme (all 22 stock themes checked), uses the system font and Omarchy-style menus, and installs per user with no sudo. Version 2.0.0, finished 2026-11-14.

- Code and docs: `github.com/rseaver06-ui/arch-breaker-2`. Bar plugin: `github.com/rseaver06-ui/arch-breaker-2-plugin`.
- Installed copy: `~/.local/opt/arch-breaker-2`, launcher entry "Arch Breaker 2", save at `~/.local/share/arch-breaker-2/save.json`.
- Run from the folder without installing: `python3 -m arch_breaker2`. Install/update: `sh packaging/install.sh`. Tests: `PYTHONPATH=. uvx pytest -q` (17 pass).

## The game in one minute

Aim with the paddle (edges steep, middle straight), add spin by moving as you hit. Speed rises per paddle hit, capped per level. Three lives in single player; a life goes only when your *last* ball drops. Power-ups: Wide, Shield, Multiball, Passthrough, Slow. Last brick has a 20 s countdown. From level 8 the wall creeps down. Modes: Daily (shared seed), Endless (top 5), Versus.

**Versus** (2 on one keyboard, or vs CPU on Easy/Normal/Hard): one shared wall, each player owns half the bottom and a ball. **Any ball through your side costs you 25 points**, whoever's it was; it comes back a second later. No lives, no knockouts. Ball color = who scores its bricks (last to touch). Wall clear ends it, highest score wins. P1: A/D + W. P2: arrows + Up.

## Decisions that were made on purpose

- Versus was first built with lives *and* points and owner-pays. It was changed to score-only, side-pays, 25 points. Simpler to read; aiming becomes offense. Recorded in `docs/design.md`.
- Sticky power-up dropped (it stalls the rhythm). No unlockables.
- Sound effects are synthesized in code (no files). Music: four Zodik tracks, CC-BY 3.0, credited in `arch_breaker2/music/CREDITS.txt`.
- Rules (`arch_breaker2/sim/`) are pure Python, deterministic, no pygame. Inputs (`io/`) and drawing (`render/`) are separate. A test proves two matches from the same seed and inputs stay identical. This is the groundwork for online play.

## Where the code lives

| Path | What |
|---|---|
| `arch_breaker2/sim/const.py` | every tunable number (speeds, penalty, timers) |
| `arch_breaker2/sim/step.py` | the rules, one tick at a time |
| `arch_breaker2/sim/levelgen.py` | seeded, mirrored layouts |
| `arch_breaker2/io/cpu.py` | the computer player |
| `arch_breaker2/render/theme.py` | reads Omarchy's `colors.toml`, live |
| `arch_breaker2/render/draw.py` | all drawing and menus |
| `arch_breaker2/app.py` | window, scenes, settings, effects |
| `arch_breaker2/audio.py` | synthesized sounds + music |
| `packaging/` | install.sh, uninstall.sh, make_icon.py |
| `docs/design.md` | why everything is the way it is |
| `docs/next.md` | what to do next |

## What's next (paused)

Online Versus for 2 to 4 players. Plan: lockstep with a 3-tick input delay. Step 1: same-network play with a room code (works across the internet with Tailscale), no server. Step 2: a small relay on a free host for strangers. The rules already handle 4 zones. Collaborators welcome: say hello in Discussions. MIT licensed (music CC-BY 3.0, see `arch_breaker2/music/CREDITS.txt`).

## Open tuning questions

The 25-point penalty, 1 s respawn, CPU reaction times (0.40 / 0.20 / 0.05 s) and ball speed cap came from reasoning, not from many players. Real two-player sessions should move some of them.
