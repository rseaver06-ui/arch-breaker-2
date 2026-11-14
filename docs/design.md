# Arch Breaker 2: design

Written before any code. Plain words on purpose. Each choice says why.

## Tools

**Python 3 + pygame 2.6 (SDL 2.32).** It is already installed on this machine, it runs offline, it draws crisp whole-number pixel scaling, and the whole game can live in one small folder under `~/.local`. Arch Breaker 1 proved it fits Omarchy. A compiled engine would add install steps for no gain in a game this size. The game rules will be plain Python with integer math, so the same inputs always produce the same result. That is what online play needs later.

## 1. Fun

### A great minute

Launch. The ball climbs, cracks a brick, comes back. You slide under it and catch it on the paddle's edge to **aim** it into a gap. It slips behind the front row and **chains** four bricks off the ceiling while you wait. It drops fast and wide; you **save** it with the last pixel of the paddle. Two bricks left. One. Clear.

The core loop is *aim, chain, save*. Everything else serves those three moments.

### Aiming is the skill

- Where the ball hits the paddle sets the angle (edges steep, middle straight, 60° max, never flat).
- **Moving the paddle as you hit adds "spin"**: a small push in the paddle's direction. A still paddle is predictable; a moving one lets a good player curve the ball into a gap. This is the easy-to-learn, hard-to-master part.
- The ball is a round 6-pixel dot. Round reads better than a square at any scale.

### Game feel (the few that matter)

| Effect | When | Size |
|---|---|---|
| Paddle snap | Always | Full speed in 0.06 s, stops in 0.08 s. Never floaty. |
| Hit pause | Brick breaks | 2 frames of freeze. Makes every break feel solid. |
| Shards | Brick breaks | 6 to 10 small bits in the brick's color, gone in 0.3 s. |
| Combo pitch | Each brick in a chain | Hit sound rises a step each time; resets when the ball touches the paddle. You *hear* the chain. |
| Shake | Chain of 3+, or a lost ball | 2 pixels, 0.15 s. Not on ordinary hits. |
| Paddle flash | Edge save (outer 15 % of paddle) | Brief accent-color pulse. Rewards the close save. |

No shake on normal hits, no flashing screens, nothing that fights readability. Everything can be turned off in Settings.

### Difficulty curve

- **Speed climbs with paddle hits, not time.** Each paddle hit adds a little speed until a per-level cap. Losing a ball resets speed halfway. So a careful player is never punished for taking their time, and a long rally gets tense on its own.
- **Levels ramp three things in turn:** more bricks (levels 1 to 3), tougher bricks with 2 and 3 hit points shown as inset outlines (from level 3), and layouts with pockets and shields that need aiming (from level 5). From level 8 the whole wall creeps down one row every 12 paddle hits, so stalling stops working.
- **Quiet helping hand:** if you lost a ball in the last 20 seconds, the next power-up drop is a helpful one (wide or shield). Nothing announces this. If you're on a hot streak, drops lean to multiball and passthrough, which are fun but risky.
- **No single winning strategy:** the creeping wall beats hiding, the speed cap per level beats "just get it behind the wall and wait", and the last-brick countdown (20 s, then it crumbles for no points) beats stalling.
- Three lives. A shield save does not count as a life.

### Power-ups (kept from AB1, trimmed)

Wide (12 s), Shield (one save), Multiball (×2, up to 6), Passthrough (8 s), Slow (8 s). Sticky is dropped: catching the ball stalls the rhythm. Drops fall straight down and are caught by the paddle.

### Replay value

- **Daily seed.** Everyone gets the same levels today. Local best shown next to it. One line of text, big pull.
- **Endless run.** Random seed, score and level reached. Top 5 local scores.
- **Streak.** Levels cleared in a row without losing a ball. Shown on the title screen.

No unlockables. They would be filler.

### Controls (single player)

Left/Right or A/D to move. Space to launch. Esc to pause. That's all. F11 for fullscreen. Controller: left stick or D-pad and A, if a pad is plugged in; the game never requires one.

## 2. Native to Omarchy

### What Omarchy looks like

Read from the live system: 22 stock themes (17 dark, 5 light). Every theme ships `colors.toml` with a `mode` flag, an `accent`, four background shades, four foreground shades, a `selection` and `muted` color, and eight named hues (red, yellow, orange, green, cyan, blue, magenta, brown) with bright versions. The bar and menus use the theme background, the theme foreground for text, and the accent for anything active. The system font is **JetBrainsMono Nerd Font**. Windows have 8-pixel rounded corners and no borders in the default look. Menus are plain vertical lists with the highlighted row in the accent color.

### How the game uses the theme

| Game part | Theme color |
|---|---|
| Court | `background` |
| Court walls, HUD plate | `lighter_background` |
| Paddle, ball, menu highlight | `accent` |
| Text | `foreground`; hints in `dark_foreground` |
| Bricks, by row | `red`, `orange`, `yellow`, `green`, `cyan`, `blue`, `magenta` |
| Tough-brick outlines | `bright_*` of the same hue |
| Shards | the brick's color |
| Text backing plate | `darker_background` at 85 % on dark themes; `lighter_background` on light themes |

The game re-reads `colors.toml` whenever its timestamp changes (checked twice a second). Switching themes recolors the game live, mid-rally. The `mode` flag flips the plate and shadow choices so light themes stay readable. If the file is missing, a built-in fallback palette is used. Tested against all 22 stock themes before phase 3 ends.

### Looking like part of the system

- The theme font for every piece of text, loaded from the system; falls back to pygame's mono font if missing.
- Menus are vertical lists, highlighted row in accent, like `omarchy-menu`. Key hints written the Omarchy way: `SPACE  Launch`, `ESC  Back`.
- The window titles itself "Arch Breaker 2" and sets its app id to `arch-breaker-2`, so Hyprland rules can target it.
- Tiling friendly: the 640×360 canvas scales by the largest whole number that fits and letterboxes in theme background, so a tiled half-screen window still looks right. F11 goes fullscreen on the monitor it's on. The game never changes monitor scale.
- No sudo, ever. If pygame is missing, the launcher prints the exact `sudo pacman -S --needed python python-pygame` line and stops.

### Install

`~/.local/opt/arch-breaker-2/` for the program, `~/.local/bin/arch-breaker-2` launcher, `~/.local/share/applications/arch-breaker-2.desktop` so the Omarchy launcher finds "Arch Breaker 2", an icon in the Omarchy flat style, save file at `~/.local/share/arch-breaker-2/save.json`. Uninstall removes everything except the save. Arch Breaker 1 is left completely alone.

## 3. Multiplayer

### Five ideas, scored 1 to 5

| Idea | What it is | Fun | Simple | Scales to 4 | Total |
|---|---|---|---|---|---|
| **Face-off** | AB1's mode: paddles left and right, shared wall in the middle. | 3 | 4 | 3 | 10 |
| **Garbage** | Split screen, each player has their own wall. Bricks you break get sent to the opponent as new bricks. Last one standing. | 4 | 3 | 4 | 11 |
| **Relay** | Co-op. One court, two paddles side by side at the bottom, shared lives. The ball changes to your color when you hit it; points to you, loss to the team. | 3 | 5 | 4 | 12 |
| **Claim** | Shared wall. Hitting a brick paints it your color; the second hit breaks it and whoever breaks it scores. Steal painted bricks. | 4 | 2 | 3 | 9 |
| **Poach** | Shared court, two paddles at the bottom, each in its own half. **Each player has their own ball.** Your ball scores for you. If your ball drifts into the other half, they can catch it, and then it's theirs. Lose your ball past the bottom and you lose a life. | 5 | 4 | 5 | 14 |

### Pick: Poach

Why it wins:

- **Same controls as single player.** Nothing new to learn. Move, launch.
- **Cooperation and competition in one rule.** Catching the other player's ball saves them from losing a life *and* steals their scoring. Do you help or hunt? The choice is the game.
- **Always something to do.** Two balls in play from the start. No waiting on the other player's turn.
- **Scales cleanly.** Four players is four zones along the bottom, four balls, same rule. Three works too. The rule never changes with player count.
- **Reads instantly.** Each ball and paddle is a player color. Bricks flash the color of whoever broke them.

Rules in full:

- Court is shared. One brick wall, same generator as single player.
- N players, N equal-width zones along the bottom. Each has a paddle that cannot leave its zone, one ball, three lives, a score.
- A ball is owned by whoever last touched it with their paddle. Bricks score for the owner. Owner color shows on the ball.
- A ball that passes the bottom costs its *owner* a life, wherever it fell. Lose three and you're out; your zone becomes a wall for everyone else.
- Power-ups drop toward the nearest paddle and only that paddle can take them. Multiball spawns balls owned by the taker.
- Match ends when the wall is clear (highest score wins) or one player is left standing.
- Draw on equal score. No sudden death; keep it simple.

### Keyboard layout for two

Chosen for comfort and to avoid key ghosting (cheap keyboards drop the third key when three keys share a matrix row or column).

| | Move | Launch |
|---|---|---|
| P1 (left zone) | A / D | W |
| P2 (right zone) | Left / Right arrows | Up arrow |

The two sets are at opposite ends of the keyboard, so hands don't collide and the keys sit in different matrix rows. Esc pauses for everyone. Each player's keys are shown in their color on the setup screen.

For a future local 4 players: P3 J / L + I, P4 numpad 4 / 6 + 8. Not built now.

### CPU opponent

A CPU is just another input source. It watches the ball that will reach its zone soonest, moves toward where that ball will land, and reacts after a delay. Easy: 0.40 s delay and misses by up to 40 px. Normal: 0.20 s and 16 px. Hard: 0.05 s and 4 px. Hard also goes after your ball when it drifts into its zone. Easy and Normal only poach if the ball lands on them.

### Online later: the plan

**Approach: lockstep with a small input delay.** Every player's input for tick T is sent to everyone; the game only advances tick T when it has every player's input. A 3-tick (50 ms at 60 Hz) delay hides normal internet lag. Rollback is better for fighting games but is a lot more code; a paddle game at 60 Hz plays fine on lockstep. If lag spikes, the game pauses briefly rather than desyncing.

**What the code does now so that works later:**

- `sim/`: the rules. One function `step(state, inputs)` advances one tick. Pure Python, integers only, no randomness except a seeded generator inside the state. No pygame imports.
- `io/`: input sources. Keyboard, CPU, and later network all produce the same small `Input` record (left, right, launch) per player per tick.
- `render/`: reads state, draws. Never changes state.
- A replay test: run two copies of the sim with the same seed and the same recorded inputs and check the states match byte for byte at every tick. This is the proof that online play won't desync.

## What's not in this version

No online play, no accounts, no network code, no local 4-player, no sticky power-up, no unlockables.
