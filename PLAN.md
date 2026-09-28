# Asteroids (Scratch) — full version plan

## Features
- [x] Menu: PLAY / CONFIG / CREDITS buttons, title, high score line, drifting rocks in the background
- [x] Credits: Daniel Godri Neto; Asteroids (Atari, 1979); Nyan Cat by Chris Torres (fan tribute)
- [x] Config: sound on/off, volume 100/75/50/25, controls (arrows / WASD), style (classic / nyan)
- [x] Style swaps every costume and sound: ship→Pop-Tart cat with rainbow trail, rocks→yarn balls, UFO→dog saucer
- [x] Arcade rules: tap-to-fire, max 4 shots on screen, hyperspace (1-in-8 malfunction), 20/50/100 pts,
      waves 4→6→8→10→11, UFOs large (200, random shots) / small (1000, aimed), extra life every 10,000,
      debris explosions (heartbeat + saucer sounds removed on request), respawn only when the center is clear, high score + initials

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

## Verify
- [x] Headless scratch-vm test: menu/config/credits flows, style + sound routing, waves, firing cap, splits,
      UFO, extra life, death/respawn, game over → initials → menu
- [x] Browser (real renderer): collisions, SafeZone with ghost effect, both styles' visuals, HUD
