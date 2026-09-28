# Asteroids (Scratch) — full version plan

## Features
- [x] Menu: PLAY / CONFIG / CREDITS buttons, title, high score line, drifting rocks in the background
- [x] Credits: Daniel Godri Neto; Asteroids (Atari, 1979); Nyan Cat by Chris Torres (fan tribute)
- [x] Config: sound on/off, volume 100/75/50/25, controls (arrows / WASD), style (classic / nyan)
- [x] Style swaps every costume and sound: ship→Pop-Tart cat with rainbow trail, rocks→yarn balls, UFO→dog saucer
- [x] Arcade rules: tap-to-fire, max 4 shots on screen, hyperspace (1-in-8 malfunction), 20/50/100 pts,
      waves 4→6→8→10→11, UFOs large (200, random shots) / small (1000, aimed), extra life every 10,000,
      debris explosions (heartbeat + saucer sounds removed on request), respawn only when the center is clear, high score + initials
- [x] Game feel: floating score pop-ups, "WAVE N" banner, ship-death screen flash, split rocks pop to size
- [x] Build mode: 4th menu button, roguelite run with a `mode` global; after each wave (level > 0) the game
      pauses (`state "upgrade"`) and offers 3 of {multishot, rapid fire, pierce, engine, shield, hyperspace
      stabilizer, +1 life} on Card clones, picked by clicking or pressing 1/2/3; upgrades stack into levels
      and persist for the run (reset on "start game"); arcade PLAY is untouched (mode "arcade", all upgrade
      levels stay 0)

## Risks / edge cases (each one is a checklist item)
- [x] Clone deletion cuts off its sounds → all audio plays from one Sfx sprite via broadcasts
- [x] Clones receive broadcasts → screen handlers start with `if clone = 1 then delete this clone`; rock `new wave` guarded too
- [x] Nothing may follow a cap block (`delete this clone`, `forever`, `stop this script`): the VM runs it, but the
      editor drops that script and all later ones, then throws "glow stack" errors that freeze the stage.
      The generator now refuses to build such a script (sb3.py `_is_cap`)
- [x] Explosion position race (many clones set shared vars in one frame) → FIFO `fx` list consumed by Particle original
- [x] Hidden sprites can't be touched → bullets / ship / UFO wait one frame before vanishing
- [x] Ship-vs-rock also splits the rock → rocks check `touching Ship`; children get spawn protection frames
- [x] Respawn inside a rock → SafeZone (ghosted circle) waits until the center is clear
- [x] Style/volume/controls persist between games (stored in variables, not reset by the green flag)
- [x] HUD via pen stamping must not flash the HUD sprite → redraw runs without screen refresh
- [x] Scratch fencing keeps sprites partly on stage → wrap at ±235 and keep smallest rock ≥ 22px
- [x] Player shots don't wrap (changed on request): they vanish on `touching edge`; rocks, ship and UFO shots still wrap
- [x] Score pop-ups reuse the `fx`-list FIFO pattern (`pops` list) so many simultaneous hits don't race each other
- [x] Wave banner runs as its own concurrent stage thread (tracks `last level`) so its 1.5s wait never blocks
      the wave-spawn `broadcast_wait` loop
- [x] Split "pop" only applies to freshly split children (gated on `safe > 0`), so menu/wave rocks are unaffected;
      the ease loop is a plain (non-warp) repeat, so it spans a few real frames — that's fine since it finishes
      before the rock's own collision-checking forever loop starts, and it only extends (never shortens) the
      existing spawn-protection window
- [x] Build mode: the wave-clear "3 clones write a shared var" race is avoided by giving each upgrade-pool
      pick its own `pick(n)` step (rand + delete from `pool` happen inside one atomic block, not across
      clones), so no FIFO list is needed there
- [x] Multishot's per-bullet spread reuses the same "read-then-increment a shared var before any yield"
      trick as the existing FIFO-list races: the ship sets `burst` to 1, then each of the N Bullet clones
      claims `burst` and increments it as the very first (non-yielding) blocks of its clone script, so the
      N clones can't interleave on the same counter
- [x] Pierce bullets must not burn a charge every frame they overlap the same rock (or its just-split
      children): a bullet-local `immune` countdown (~4 frames) after each pierce hit, separate from the
      rock's own `safe` spawn-protection window, since `touching()` alone doesn't know a hit was "already
      processed"
- [x] Shield/invulnerability must not let the ship farm points by ramming: rocks read the ship's `invuln`
      local var via `attr_of` and skip `touching Ship` entirely while it's > 0
- [x] Pausing for the upgrade pick must not break death/respawn: the ship's main loop gates on
      `busy = 0 AND state = "play"`, but an in-progress `die()` call chain (wait(2) + respawn) is not
      interrupted since it's already inside one forever-loop iteration when the pause starts
- [x] UFO must not linger once the wave-clear pause starts: `state = "upgrade"` is added to its flight
      loop's exit condition so it leaves immediately instead of flying until its normal on/off-screen check
- [x] Bullet/UfoShot clones must not survive into the upgrade screen (they'd keep flying over the cards and
      leave `shots` non-zero): both delete themselves on "show upgrades", same pattern as "menu"/"start game"
- [x] Pre-existing latent bug found while testing build mode's fast menu→game transition: the menu's 6
      attract-mode rocks spawn over several frames (a plain `repeat`); clicking a menu button fast enough
      lets late iterations create clones *after* `state` already left "menu", so those clones never receive
      the "start game" broadcast that's supposed to wipe them and leak into gameplay (inflating the rock
      count and desyncing it from `rocks`). Fixed by gating each iteration's `create_clone` on
      `state = "menu"` still holding

## Verify
- [x] Headless scratch-vm test: menu/config/credits flows, style + sound routing, waves, firing cap, splits,
      UFO, extra life, death/respawn, game over → initials → menu
- [x] Headless scratch-vm test: build mode — BUILD MODE button sets mode, wave-clear opens a 3-distinct-
      choice upgrade screen with 3 cards, picking by key applies the level and resumes; multishot spread,
      pierce survival, shield-absorbs-a-hit, hyperspace stabilizer (~20 forced rolls); arcade PLAY never
      shows the upgrade screen
- [x] Browser (real renderer): collisions, SafeZone with ghost effect, both styles' visuals, HUD
- [ ] Browser (real renderer): build mode — card legibility/text fit at both styles, card layout vs. the
      "CHOOSE AN UPGRADE" header (no overlap), ship blink during shield invulnerability, HUD "SHIELD n" line
      position under the lives row

## Known issues
- The headless scratch-vm test harness is occasionally flaky on this machine under CPU contention (a
      `waitFor` times out) even on unmodified pre-build-mode code, confirmed by repeated runs before this
      feature existed. One concrete cause (the attract-mode clone race above) is now fixed; re-running
      `npm test` reproduces a clean `ALL CHECKS PASSED` the large majority of the time.
