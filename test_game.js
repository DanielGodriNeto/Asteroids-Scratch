// End-to-end headless test of asteroids.sb3 in the real Scratch VM (no renderer: collisions are forced).
const fs = require('fs');
const assert = require('assert');
const VM = require('scratch-vm');

const sleep = ms => new Promise(r => setTimeout(r, ms));
const frames = n => sleep(n * 1000 / 30 + 30);

(async () => {
    const vm = new VM();
    await vm.loadProject(fs.readFileSync(process.argv[2]));
    const rt = vm.runtime;

    // headless VM has no renderer -> never requests redraw -> many ticks per frame; force 1 tick per frame
    const seq = rt.sequencer, step1 = seq.stepThread.bind(seq);
    seq.stepThread = th => { step1(th); rt.redrawRequested = true; };

    const played = [];
    for (const op of ['sound_play', 'sound_playuntildone']) {
        const prim = rt._primitives[op];
        rt._primitives[op] = (args, util) => { played.push(`${util.target.getName()}:${args.SOUND_MENU}`); return prim(args, util); };
    }
    let question = null;
    rt.on('QUESTION', q => { if (q !== null) question = q; });
    let bulletsMade = 0;
    rt.on('targetWasCreated', t => { if (t.sprite.name === 'Bullet') bulletsMade++; });

    const stage = rt.getTargetForStage();
    // Scratch stores `set var to 0` as the string "0"; compare numerically where it looks numeric
    const norm = v => (typeof v === 'string' && v.trim() !== '' && !isNaN(v) ? Number(v) : v);
    const g = n => norm(stage.lookupVariableByNameAndType(n).value);
    const setG = (n, v) => { stage.lookupVariableByNameAndType(n).value = v; };
    const sprite = n => rt.getSpriteTargetByName(n);
    const clones = n => rt.targets.filter(t => !t.isOriginal && t.sprite.name === n);
    const local = (t, n) => norm(t.lookupVariableByNameAndType(n).value);
    const costume = t => t.getCostumes()[t.currentCostume].name;
    const buttons = () => clones('Button').map(b => local(b, 'action')).sort();
    const label = a => costume(clones('Button').find(b => local(b, 'action') === a));
    const waitFor = async (cond, what, ms = 6000) => {
        const t0 = Date.now();
        while (!cond()) { if (Date.now() - t0 > ms) throw new Error(`timed out waiting for: ${what}`); await sleep(20); }
    };
    const click = async action => {
        const b = clones('Button').find(x => local(x, 'action') === action);
        assert(b, `button ${action} exists (have ${buttons()})`);
        rt.startHats('event_whenthisspriteclicked', null, b);
        await frames(3);
    };
    const keyDown = (k, down) => vm.postIOData('keyboard', {key: k, isDown: down});
    const tap = async k => { keyDown(k, true); await frames(2); keyDown(k, false); await frames(2); };
    const hitOnce = (t, obj) => {
        let used = false;
        const orig = t.isTouchingObject.bind(t);
        t.isTouchingObject = o => (o === obj && !used ? (used = true) : orig(o));
    };
    const heard = s => played.includes(`Sfx:${s}`);
    const ok = msg => console.log('  ok -', msg);

    vm.start();
    vm.greenFlag();

    console.log('menu');
    await waitFor(() => g('state') === 'menu' && buttons().length === 3, 'menu buttons');
    assert.deepStrictEqual(buttons(), ['config', 'credits', 'play']);
    assert(sprite('Title').visible && costume(sprite('Title')) === 'classic title');
    assert.strictEqual(costume(stage), 'classic space');
    await waitFor(() => clones('Asteroid').length === 6, 'attract rocks');
    ok('title, 3 buttons, 6 drifting rocks, classic backdrop');

    console.log('credits');
    await click('credits');
    assert.strictEqual(g('state'), 'credits');
    assert.deepStrictEqual(buttons(), ['back']);
    assert(sprite('Panel').visible && costume(sprite('Panel')) === 'credits' && !sprite('Title').visible);
    assert(heard('classic click'));
    await click('back');
    assert.strictEqual(g('state'), 'menu');
    ok('credits panel + back');

    console.log('config');
    await click('config');
    assert.deepStrictEqual(buttons(), ['back', 'controls', 'sound', 'style', 'volume']);
    assert.deepStrictEqual(['sound', 'volume', 'controls', 'style'].map(label),
        ['btn sound on', 'btn volume 100', 'btn controls arrows', 'btn style classic']);
    assert.strictEqual(costume(sprite('Panel')), 'config arrows');
    await click('sound');
    assert.strictEqual(g('sound'), 'off'); assert.strictEqual(label('sound'), 'btn sound off');
    await click('sound');
    assert.strictEqual(g('sound'), 'on');
    await click('volume');
    assert.strictEqual(g('volume'), 75); assert.strictEqual(label('volume'), 'btn volume 75');
    assert.strictEqual(sprite('Sfx').volume, 75);
    for (let i = 0; i < 3; i++) await click('volume');
    assert.strictEqual(g('volume'), 100); assert.strictEqual(sprite('Sfx').volume, 100);
    await click('controls');
    assert.strictEqual(g('controls'), 'wasd'); assert.strictEqual(costume(sprite('Panel')), 'config wasd');
    await click('style');
    assert.strictEqual(g('style'), 'nyan'); assert.strictEqual(label('style'), 'btn style nyan');
    assert.strictEqual(costume(stage), 'nyan space');
    assert(clones('Asteroid').every(r => costume(r).startsWith('nyan rock')));
    await click('back');
    assert.strictEqual(costume(sprite('Title')), 'nyan title');
    assert(heard('nyan click'));
    ok('sound toggle, volume cycles 100→75→…→100 (Sfx volume follows), WASD, nyan style swaps art');

    console.log('play (nyan, WASD)');
    await click('play');
    assert.strictEqual(g('state'), 'play');
    assert.deepStrictEqual(buttons(), []);
    await waitFor(() => g('level') === 1 && clones('Asteroid').length === 4, 'wave 1');
    assert.strictEqual(g('rocks'), 4);
    assert.strictEqual(g('banner'), 'WAVE 1', 'wave banner shows');
    await waitFor(() => g('banner') === '', 'wave banner clears');
    const ship = sprite('Ship');
    assert(ship.visible && costume(ship).startsWith('nyan ship'));
    assert.deepStrictEqual(['key left', 'key right', 'key thrust', 'key fire', 'key hyper'].map(g), ['a', 'd', 'w', 'space', 's']);
    assert(clones('Asteroid').every(r => costume(r).startsWith('nyan rock')));
    ok('wave 1 = 4 yarn balls, cat ship, WASD keys applied');

    // firing rules
    const b0 = bulletsMade;
    await tap(' ');
    assert.strictEqual(bulletsMade - b0, 1);
    assert(heard('nyan fire'));
    keyDown(' ', true); await frames(12); keyDown(' ', false); await frames(2);
    assert.strictEqual(bulletsMade - b0, 2, 'holding fire shoots once');
    let maxAlive = 0;
    for (let i = 0; i < 10; i++) {
        keyDown(' ', true); await sleep(40); keyDown(' ', false); await sleep(40);
        maxAlive = Math.max(maxAlive, clones('Bullet').length);
    }
    assert(maxAlive <= 4, `max 4 shots on screen (saw ${maxAlive})`);
    assert.strictEqual(maxAlive, 4);
    await waitFor(() => clones('Bullet').length === 0 && g('shots') === 0, 'bullets expire and shots counter returns to 0');
    ok('tap-to-fire, max 4 shots, shots counter consistent');

    // thrust / turn
    const d0 = ship.direction;
    keyDown('w', true); keyDown('d', true); await frames(15);
    assert.strictEqual(g('thrusting'), 1);
    assert(clones('Trail').length > 0, 'rainbow trail while thrusting');
    keyDown('w', false); keyDown('d', false); await frames(3);
    assert.strictEqual(g('thrusting'), 0);
    assert.notStrictEqual(ship.direction, d0);
    assert(heard('nyan thrust'));
    ok('thrust, turn, rainbow trail, purr sound');

    // hyperspace (force the no-malfunction roll)
    const rnd = Math.random; Math.random = () => 0.3;
    await tap('s');
    assert(!ship.visible, 'ship vanishes into hyperspace');
    await waitFor(() => ship.visible && local(ship, 'busy') === 0, 'ship returns from hyperspace', 2000);
    Math.random = rnd;
    assert.strictEqual(g('lives'), 3);
    ok('hyperspace');

    // splitting (forced collisions)
    const score0 = g('score');
    hitOnce(clones('Asteroid')[0], 'Bullet');
    await frames(3);
    assert.deepStrictEqual(clones('Asteroid').map(r => local(r, 'tier')).sort(), [2, 2, 3, 3, 3]);
    assert.strictEqual(g('rocks'), 5);
    assert.strictEqual(g('score') - score0, 20);
    assert(heard('nyan boom 3'));
    await waitFor(() => clones('Popup').length > 0, 'score popup appears');
    await waitFor(() => clones('Particle').length > 0, 'debris particles');
    const medium = clones('Asteroid').find(r => local(r, 'tier') === 2);
    hitOnce(medium, 'UfoShot');
    await frames(9);
    assert.strictEqual(g('score') - score0, 20, 'saucer shots split rocks but score nothing');
    assert(heard('nyan boom 2'));
    const small = clones('Asteroid').find(r => local(r, 'tier') === 1);
    hitOnce(small, 'Ship');
    await frames(9);
    assert.strictEqual(g('score') - score0, 120, 'ramming a small rock scores 100');
    assert.strictEqual(g('rocks'), clones('Asteroid').length);
    ok('20/50/100 scoring, UFO shots score nothing, ramming scores, rocks counter matches clones');

    // extra life
    const lives0 = g('lives');
    setG('score', 10000);
    await frames(3);
    assert.strictEqual(g('lives'), lives0 + 1);
    assert.strictEqual(g('next life'), 20000);
    assert(heard('nyan life'));
    ok('extra life at 10,000');

    // rocks still wrap around the screen
    const drifter = clones('Asteroid')[0];
    drifter.setXY(234, 0); drifter.setDirection(90);
    await frames(4);
    assert(clones('Asteroid').includes(drifter) && drifter.x < -200, `rock wrapped to the left side (x=${drifter.x})`);
    ok('rocks wrap around the screen');

    // player shots do NOT wrap: a shot reaching the edge vanishes and frees its slot
    await waitFor(() => clones('Bullet').length === 0, 'no shots in flight');
    await tap(' ');
    const shot = clones('Bullet')[0];
    assert(shot && g('shots') === 1);
    hitOnce(shot, '_edge_');  // no renderer headless: stand in for reaching the stage edge
    await frames(2);
    assert(!clones('Bullet').includes(shot) && g('shots') === 0, 'shot vanished at the edge');
    ok('player shots vanish at the screen edge (no wrap)');

    // saucer
    const ufo = sprite('UFO');
    await waitFor(() => ufo.visible, 'a saucer appears', 16000);
    assert.strictEqual(costume(ufo), 'nyan ufo');
    const small_ufo = local(ufo, 'small') === 1;
    await waitFor(() => clones('UfoShot').length > 0, 'saucer fires', 3000);
    const s1 = g('score');
    hitOnce(ufo, 'Bullet');
    await frames(3);
    assert(!ufo.visible);
    assert.strictEqual(g('score') - s1, small_ufo ? 1000 : 200);
    await waitFor(() => clones('Popup').length > 0, 'saucer score popup appears');
    ok(`${small_ufo ? 'small' : 'large'} dog saucer flew, fired bones, was shot for ${small_ufo ? 1000 : 200}`);

    // death + respawn
    const flash = sprite('Flash');
    const lives1 = g('lives');
    hitOnce(ship, 'Asteroid');
    await frames(3);
    assert(!ship.visible && g('lives') === lives1 - 1);
    assert(heard('nyan ship boom'));
    assert(flash.visible, 'death flash shown');
    await waitFor(() => !flash.visible, 'death flash fades');
    await waitFor(() => ship.visible && local(ship, 'busy') === 0, 'respawn', 4000);
    assert.strictEqual(ship.x, 0); assert.strictEqual(ship.y, 0);
    ok('death, debris, respawn at center');

    // game over -> initials -> menu
    ship.isTouchingObject = o => o === 'Asteroid';
    await waitFor(() => g('state') === 'gameover', 'game over', 15000);
    assert(sprite('Panel').visible && costume(sprite('Panel')) === 'nyan gameover');
    const finalScore = g('score');
    await waitFor(() => question !== null, 'high score prompt', 5000);
    rt.emit('ANSWER', 'dgn');
    await waitFor(() => g('state') === 'menu' && buttons().length === 3, 'back to menu');
    assert.strictEqual(g('high score'), finalScore);
    assert.strictEqual(g('high name'), 'dgn');
    delete ship.isTouchingObject;
    ok(`game over, high score ${finalScore} saved as "dgn", back to menu`);

    console.log('classic style + sound off');
    await click('config'); await click('style'); await click('sound'); await click('back');
    assert.strictEqual(g('style'), 'classic'); assert.strictEqual(g('sound'), 'off');
    const heardBefore = played.length;
    await click('play');
    await waitFor(() => g('level') === 1 && clones('Asteroid').length === 4, 'wave 1 again');
    assert.strictEqual(costume(ship), 'classic ship 1');
    assert(clones('Asteroid').every(r => costume(r).startsWith('classic rock')));
    await tap(' ');
    keyDown('w', true); await frames(10);
    const flameSeen = ['classic ship 1', 'classic ship 2'].includes(costume(ship));
    keyDown('w', false);
    assert(flameSeen && clones('Trail').length === 0, 'classic ship has no rainbow trail');
    assert.strictEqual(played.length, heardBefore, 'sound off = silence');
    ok('classic art, no trail, sound off mutes everything');

    // wave 2 = 6 rocks
    for (const r of clones('Asteroid')) { r.lookupVariableByNameAndType('tier').value = 1; hitOnce(r, 'Bullet'); }
    await waitFor(() => g('level') === 2 && clones('Asteroid').length === 6, 'wave 2', 5000);
    assert.strictEqual(g('rocks'), 6);
    ok('wave 2 = 6 rocks');

    // removed on request: no looping heartbeat, no saucer siren/bark
    assert(!sprite('Sfx').sprite.sounds.some(s => /beat|ufo/.test(s.name)), 'no beat/ufo sounds in the project');
    assert(!played.some(p => /beat|ufo/.test(p)), 'no beat/ufo sound ever played');
    ok(`only one-shot effects + thrust played: ${[...new Set(played.map(p => p.replace(/^Sfx:/, '')))].sort().join(', ')}`);

    vm.stopAll();
    console.log('ALL CHECKS PASSED');
    process.exit(0);
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
