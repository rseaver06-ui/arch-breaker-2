# What I'd do next

In order.

1. **Online Versus for up to 4 players.** The rules already take N players and the simulation is deterministic (the replay test proves it). The plan in `docs/design.md`: lockstep with a 3-tick input delay over UDP or WebSocket, one player hosting. Steps: a `NetInput` source in `io/` that sends your `Input` each tick and waits for everyone else's; a lobby screen with a room code; a short pause on lag spikes instead of a desync. 3 and 4 player zones work today; the keyboard just doesn't have room for them locally.
2. **Play it with people.** The Versus penalty (25), respawn delay (1 s), CPU reaction times and the ball speed cap all came from reasoning, not from a table of players. An evening of two-player matches will move some of those numbers.
3. **Controller support.** Single player on an SN30 Pro (left stick / D-pad, A to launch, Start to pause) through the same `Input` record. Arch Breaker 1 only ever tested its pad in simulation; this one should be tested on the real pad.
4. **Daily seed leaderboard, local only.** Keep each day's best so you can see your history, and show yesterday's seed so you can retry it.
5. **A short tutorial on first run.** Three lines over the first level: aim with the edges, spin with movement, catch the letters.
6. **Omarchy menu entry.** A one-line `omarchy-menu` extension so the game is reachable from the Omarchy root menu, not only the app launcher.
