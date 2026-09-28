"""Generate asteroids.sb3 — arcade Asteroids for Scratch 3, with a menu, config screen and a Nyan Cat style.

Run: python build_sb3.py  ->  writes asteroids.sb3 next to this file.
"""
import pathlib

import assets
from sb3 import *  # noqa: F403 — the block DSL reads best unqualified

GLOBALS = {
    "state": "menu", "score": 0, "lives": 3, "level": 0, "rocks": 0, "shots": 0, "next life": 10000,
    "thrusting": 0, "high score": 0, "high name": "---", "banner": "", "last level": 0,
    # settings survive between games (only the config screen changes them)
    "sound": "on", "volume": 100, "controls": "arrows", "style": "classic",
    "key left": "left arrow", "key right": "right arrow", "key thrust": "up arrow",
    "key fire": "space", "key hyper": "down arrow",
}
LISTS = ["fx",  # explosion queue: x, y, kind (rock|ship) triples consumed by the Particle sprite
         "pops"]  # score popup queue: x, y, value triples consumed by the Popup sprite
SFX_EVENTS = ["fire", "boom 1", "boom 2", "boom 3", "ship boom", "life", "click"]
BROADCASTS = ["menu", "config", "credits", "start game", "new wave", "game over", "respawn check",
              "settings changed", "style changed", "flash"] + [f"sfx {e}" for e in SFX_EVENTS]

MENU_BUTTONS = [("play", -20), ("config", -60), ("credits", -100)]
CONFIG_BUTTONS = [("sound", 95), ("volume", 55), ("controls", 15), ("style", -25), ("back", -150)]
SETTINGS = ["sound", "volume", "controls", "style"]


# ---------------- shared script pieces ----------------

def toggle(var, a, b):
    return if_else(eq(V(var), a), [set_var(var, b)], [set_var(var, a)])


def any_touching(*objs):
    cond = touching(objs[-1])
    for obj in reversed(objs[:-1]):
        cond = or_(touching(obj), cond)
    return cond


def push_fx(kind):
    return [add_to("fx", x_pos()), add_to("fx", y_pos()), add_to("fx", kind)]


def push_pop(value):
    return [add_to("pops", x_pos()), add_to("pops", y_pos()), add_to("pops", value)]


def wrap_def():
    return [define("wrap"),
            if_(gt(x_pos(), 235), set_x(-230)),
            if_(lt(x_pos(), -235), set_x(230)),
            if_(gt(y_pos(), 175), set_y(-170)),
            if_(lt(y_pos(), -175), set_y(170))]


def delete_if_clone():
    """`delete this clone` is a cap block, so it needs an if around it when more blocks follow."""
    return if_(eq(V("clone"), 1), delete_clone())


def cleared_on_screen_change():
    """Clones vanish when the game starts or returns to the menu (the original ignores it)."""
    return [[when_msg("menu"), delete_clone()], [when_msg("start game"), delete_clone()]]


# ---------------- stage: game flow ----------------

def stage_scripts():
    return [
        [when_flag(), broadcast("menu")],
        [when_msg("menu"), set_var("state", "menu"), switch_backdrop(join(V("style"), " space"))],
        [when_msg("style changed"), switch_backdrop(join(V("style"), " space"))],
        [when_msg("config"), set_var("state", "config")],
        [when_msg("credits"), set_var("state", "credits")],
        [when_msg("start game"),
         set_var("state", "play"), set_var("score", 0), set_var("lives", 3), set_var("level", 0),
         set_var("rocks", 0), set_var("shots", 0), set_var("next life", 10000),
         wait(1),
         forever(wait_until(eq(V("rocks"), 0)),
                 if_(gt(V("level"), 0), wait(1.5)),
                 change_var("level", 1),
                 broadcast_wait("new wave"))],
        [when_msg("start game"),
         forever(wait_until(not_(lt(V("score"), V("next life")))),
                 change_var("lives", 1), change_var("next life", 10000), broadcast("sfx life"))],
        # wave banner: its own thread so the 1.5s display never blocks the wave-spawn loop above
        [when_msg("start game"),
         set_var("banner", ""), set_var("last level", 0),
         forever(if_(not_(eq(V("level"), V("last level"))),
                     set_var("last level", V("level")), set_var("banner", join("WAVE ", V("level"))),
                     wait(1.5), set_var("banner", "")))],
        [when_msg("game over"),
         stop_other(), set_var("state", "gameover"),
         wait(3),
         if_(gt(V("score"), V("high score")),
             ask("NEW HIGH SCORE! TYPE YOUR INITIALS:"),
             set_var("high name", join(letter(1, answer()), letter(2, answer()), letter(3, answer()))),
             if_(eq(V("high name"), ""), set_var("high name", "???")),
             set_var("high score", V("score"))),
         broadcast("menu")],
    ]


# ---------------- ship ----------------

def ship_scripts():
    return [
        [when_flag(), hide(), set_var("busy", 1)],
        [when_msg("menu"), stop_other(), hide(), set_var("busy", 1), set_var("thrusting", 0)],
        [when_msg("start game"),
         call("apply controls"),
         goto_xy(0, 0), point_dir(0), set_var("vx", 0), set_var("vy", 0),
         set_var("fire held", 1), set_var("hyper held", 1),
         clear_effects(), call("look"), go_front(), show(), set_var("busy", 0),
         forever(if_(eq(V("busy"), 0), call("steer"), call("shoot"), call("hyperspace key"), call("collide")))],
        [define("apply controls"),
         if_else(eq(V("controls"), "wasd"),
                 [set_var("key left", "a"), set_var("key right", "d"),
                  set_var("key thrust", "w"), set_var("key hyper", "s")],
                 [set_var("key left", "left arrow"), set_var("key right", "right arrow"),
                  set_var("key thrust", "up arrow"), set_var("key hyper", "down arrow")]),
         set_var("key fire", "space")],
        [define("steer"),
         if_(key(V("key left")), turn_left(6)),
         if_(key(V("key right")), turn_right(6)),
         if_else(key(V("key thrust")),
                 [change_var("vx", mul(mathop("sin", direction()), 0.2)),
                  change_var("vy", mul(mathop("cos", direction()), 0.2)),
                  set_var("thrusting", 1)],
                 [set_var("thrusting", 0)]),
         set_var("vx", mul(V("vx"), 0.98)), set_var("vy", mul(V("vy"), 0.98)),
         change_x(V("vx")), change_y(V("vy")), call("wrap"), call("look"),
         if_(and_(eq(V("style"), "nyan"),
                  or_(eq(V("thrusting"), 1), gt(add(mul(V("vx"), V("vx")), mul(V("vy"), V("vy"))), 2))),
             create_clone("Trail"))],
        [define("look"),
         change_var("frame", 1),
         if_else(eq(V("style"), "classic"),
                 [if_else(and_(eq(V("thrusting"), 1), eq(mod(V("frame"), 2), 0)),
                          [switch_costume("classic ship 2")], [switch_costume("classic ship 1")])],
                 [switch_costume(join("nyan ship ", add(mod(mathop("floor", div(V("frame"), 4)), 2), 1)))])],
        # arcade rules: one shot per key press, at most 4 on screen
        [define("shoot"),
         if_else(key(V("key fire")),
                 [if_(and_(eq(V("fire held"), 0), lt(V("shots"), 4)),
                      change_var("shots", 1), create_clone("Bullet"), broadcast("sfx fire")),
                  set_var("fire held", 1)],
                 [set_var("fire held", 0)])],
        [define("hyperspace key"),
         if_else(key(V("key hyper")),
                 [if_(eq(V("hyper held"), 0), set_var("hyper held", 1), call("hyperspace"))],
                 [set_var("hyper held", 0)])],
        [define("hyperspace"),
         set_var("busy", 1), set_var("thrusting", 0), hide(),
         wait(0.6),
         goto_xy(rand(-210, 210), rand(-150, 150)), set_var("vx", 0), set_var("vy", 0),
         show(),
         if_else(eq(rand(1, 8), 1), [call("die")], [set_var("busy", 0)])],  # 1-in-8 malfunction
        [define("collide"),
         if_(any_touching("Asteroid", "UFO", "UfoShot"), call("die"))],
        [define("die"),
         set_var("busy", 1), set_var("thrusting", 0),
         *push_fx("ship"), broadcast("sfx ship boom"), broadcast("flash"),
         wait(0),  # stay visible one more frame so the rock/UFO we hit registers the crash too
         hide(), change_var("lives", -1),
         if_else(eq(V("lives"), 0),
                 [broadcast("game over")],
                 [wait(2), broadcast_wait("respawn check"),
                  goto_xy(0, 0), point_dir(0), set_var("vx", 0), set_var("vy", 0),
                  call("look"), show(), set_var("busy", 0)])],
        wrap_def(),
    ]


def bullet_scripts():
    return [
        [when_flag(), hide()],
        *cleared_on_screen_change(),
        [when_clone(),
         switch_costume(join(V("style"), " bullet")),
         goto("Ship"), point_dir(attr_of("direction", "Ship")), move(14),
         set_var("bvx", add(mul(mathop("sin", direction()), 9), attr_of("vx", "Ship"))),
         set_var("bvy", add(mul(mathop("cos", direction()), 9), attr_of("vy", "Ship"))),
         set_var("life", 28), show(),
         repeat_until(eq(V("life"), 0),
                      change_x(V("bvx")), change_y(V("bvy")), change_var("life", -1),
                      # shots don't wrap around: they vanish when they reach the screen edge
                      if_(touching("_edge_"), set_var("life", 0)),
                      # linger one frame so the target sees the hit before we vanish
                      if_(any_touching("Asteroid", "UFO"), wait(0), set_var("life", 0))),
         change_var("shots", -1), delete_clone()],
    ]


def trail_scripts():
    return [
        [when_flag(), hide()],
        *cleared_on_screen_change(),
        [when_clone(),
         goto("Ship"), point_dir(attr_of("direction", "Ship")), move(-17), set_ghost(15), show(),
         repeat(8, change_effect("GHOST", 10)),
         delete_clone()],
    ]


# ---------------- rocks ----------------

def asteroid_scripts():
    return [
        [when_flag(), hide(), rot_style("don't rotate"), set_var("clone", 0)],
        # menu backdrop: a few harmless rocks drifting around
        [when_msg("menu"), delete_if_clone(),
         repeat(6, set_var("tier", rand(1, 3)), set_var("speed", rand(0.4, 1.0)), set_var("safe", 0),
                goto("_random_"), point_dir(rand(0, 359)), create_clone("_myself_"))],
        [when_msg("start game"), delete_clone()],
        [when_msg("style changed"), call("look")],
        [when_msg("new wave"),
         if_(eq(V("clone"), 1), stop_this()),
         set_var("count", add(mul(V("level"), 2), 2)),  # 4, 6, 8, 10, then 11 like the arcade
         if_(gt(V("count"), 11), set_var("count", 11)),
         repeat(V("count"),
                set_var("tier", 3), set_var("speed", rand(0.6, 1.4)), set_var("safe", 0),
                goto("_random_"),
                repeat_until(gt(distance_to("Ship"), 150), goto("_random_")),
                point_dir(rand(0, 359)), change_var("rocks", 1), create_clone("_myself_"))],
        [when_clone(),
         set_var("clone", 1), set_var("shape", rand(1, 3)), call("look"), show(),
         forever(move(V("speed")), call("wrap"),
                 if_else(gt(V("safe"), 0), [change_var("safe", -1)], [call("check hits")]))],
        [define("look"),
         switch_costume(join(V("style"), " rock ", V("shape"))),
         if_(eq(V("tier"), 3), set_size(100)),
         if_(eq(V("tier"), 2), set_size(50)),
         if_(eq(V("tier"), 1), set_size(25))],
        [define("check hits"),
         if_(touching("Bullet"), set_var("award", 1), call("split")),
         if_(touching("Ship"), set_var("award", 1), call("split")),
         if_(any_touching("UFO", "UfoShot"), set_var("award", 0), call("split"))],
        # The twist: a hit rock spawns two smaller copies of itself, then vanishes.
        [define("split"),
         broadcast(join("sfx boom ", V("tier")), default="sfx boom 3"),
         *push_fx("rock"),
         if_(eq(V("award"), 1),
             if_(eq(V("tier"), 3), change_var("score", 20), *push_pop(20)),
             if_(eq(V("tier"), 2), change_var("score", 50), *push_pop(50)),
             if_(eq(V("tier"), 1), change_var("score", 100), *push_pop(100))),
         if_else(gt(V("tier"), 1),
                 [change_var("tier", -1),
                  set_var("speed", mul(V("speed"), rand(1.2, 1.6))),
                  set_var("safe", 5),  # spawn protection: children ignore whatever split them
                  change_var("rocks", 1),  # +2 children, -1 parent
                  turn_right(rand(20, 60)), create_clone("_myself_"),
                  turn_left(rand(40, 120)), create_clone("_myself_")],
                 [change_var("rocks", -1)]),
         delete_clone()],
        wrap_def(),
    ]


# ---------------- saucers ----------------

def ufo_scripts():
    leaving = or_(and_(gt(V("dx"), 0), gt(x_pos(), 230)), and_(lt(V("dx"), 0), lt(x_pos(), -230)))
    return [
        [when_flag(), hide()],
        [when_msg("menu"), stop_other(), hide()],
        [when_msg("start game"), stop_other(), hide(),
         forever(wait(rand(7, 13)), if_(eq(V("state"), "play"), call("fly")))],
        [define("fly"),
         set_var("small", 0),
         if_(or_(gt(V("score"), 40000), lt(rand(1, 100), mul(V("level"), 10))), set_var("small", 1)),
         if_else(eq(V("small"), 1), [set_size(55)], [set_size(100)]),
         switch_costume(join(V("style"), " ufo")),
         set_var("dx", add(2, V("small"))),
         if_else(eq(rand(1, 2), 1), [set_x(-235)], [set_x(235), set_var("dx", mul(V("dx"), -1))]),
         set_y(rand(-140, 140)), set_var("vy", 0), set_var("shot timer", 30), set_var("dead", 0),
         show(),
         repeat_until(or_(eq(V("dead"), 1), leaving),
                      change_x(V("dx")), change_y(V("vy")),
                      if_(gt(y_pos(), 175), set_y(-170)),
                      if_(lt(y_pos(), -175), set_y(170)),
                      if_(eq(rand(1, 45), 1), set_var("vy", mul(rand(-1, 1), 1.5))),
                      change_var("shot timer", -1),
                      if_(lt(V("shot timer"), 1),
                          create_clone("UfoShot"),
                          if_else(eq(V("small"), 1), [set_var("shot timer", 22)], [set_var("shot timer", 35)])),
                      call("check hits")),
         hide()],
        [define("check hits"),
         if_(any_touching("Bullet", "Ship"),
             if_else(eq(V("small"), 1),
                     [change_var("score", 1000), *push_pop(1000)],
                     [change_var("score", 200), *push_pop(200)]),
             call("explode")),
         if_(and_(eq(V("dead"), 0), touching("Asteroid")), call("explode"))],
        [define("explode"), set_var("dead", 1), *push_fx("ship"), broadcast("sfx boom 3"), wait(0)],
    ]


def ufoshot_scripts():
    return [
        [when_flag(), hide()],
        *cleared_on_screen_change(),
        [when_clone(),
         switch_costume(join(V("style"), " ufo shot")),
         goto("UFO"),
         # small saucers aim at you, large ones fire at random
         if_else(eq(attr_of("small", "UFO"), 1),
                 [point_towards("Ship"), turn_right(rand(-12, 12))],
                 [point_dir(rand(0, 359))]),
         move(12), set_var("life", 34), show(),
         repeat_until(eq(V("life"), 0),
                      move(6), call("wrap"), change_var("life", -1),
                      if_(any_touching("Asteroid", "Ship"), wait(0), set_var("life", 0))),
         delete_clone()],
        wrap_def(),
    ]


# ---------------- effects ----------------

def particle_scripts():
    return [
        # the original drains the fx queue and spawns debris where each explosion happened
        [when_flag(), hide(), delete_all("fx"),
         forever(repeat_until(eq(list_length("fx"), 0),
                              goto_xy(item(1, "fx"), item(2, "fx")), set_var("kind", item(3, "fx")),
                              delete_item(1, "fx"), delete_item(1, "fx"), delete_item(1, "fx"),
                              repeat(6, create_clone("_myself_"))))],
        *cleared_on_screen_change(),
        [when_clone(),
         if_else(eq(V("kind"), "rock"),
                 [switch_costume(join(V("style"), " spark")),
                  set_var("life", rand(12, 22)), set_var("speed", rand(1.0, 3.0))],
                 [switch_costume(join(V("style"), " shard")),
                  set_var("life", rand(30, 45)), set_var("speed", rand(0.4, 1.2))]),
         point_dir(rand(0, 359)),
         set_var("dx", mul(mathop("sin", direction()), V("speed"))),
         set_var("dy", mul(mathop("cos", direction()), V("speed"))),
         show(),
         repeat(V("life"), change_x(V("dx")), change_y(V("dy")), turn_right(9),
                change_effect("GHOST", div(100, V("life")))),
         delete_clone()],
    ]


def popup_scripts():
    return [
        # the original drains the pops queue and spawns a floating "+N" where each score was earned
        [when_flag(), hide(), delete_all("pops"),
         forever(repeat_until(eq(list_length("pops"), 0),
                              goto_xy(item(1, "pops"), item(2, "pops")), set_var("value", item(3, "pops")),
                              delete_item(1, "pops"), delete_item(1, "pops"), delete_item(1, "pops"),
                              create_clone("_myself_")))],
        *cleared_on_screen_change(),
        [when_clone(),
         switch_costume(join(V("style"), " pop ", V("value"))), show(),
         repeat(24, change_y(0.83), change_effect("GHOST", 4.2)),  # ~20px up over ~0.8s while fading out
         delete_clone()],
    ]


def safezone_scripts():
    return [
        [when_flag(), hide()],
        # arcade respawn: wait until nothing is near the center
        [when_msg("respawn check"),
         goto_xy(0, 0), set_ghost(100), show(),
         wait_until(not_(any_touching("Asteroid", "UFO", "UfoShot"))),
         hide()],
    ]


def flash_scripts():
    """A single brief white flash on ship death — not a strobe, so it stays one short pulse."""
    return [
        [when_flag(), hide()],
        [when_msg("menu"), hide()],
        [when_msg("flash"),
         set_ghost(65), show(),
         repeat(8, change_effect("GHOST", 4.375)),  # 65 -> 100 (fully faded) over ~8 frames
         hide()],
    ]


def sfx_scripts():
    """Every sound plays here: clones can't (deleting a clone cuts its sounds off)."""
    def sound_on():
        return eq(V("sound"), "on")

    return [
        [when_flag(), hide(), set_volume(V("volume"))],
        [when_msg("settings changed"), set_volume(V("volume")), if_(not_(sound_on()), stop_all_sounds())],
        [when_msg("menu"), stop_all_sounds()],
        *[[when_msg(f"sfx {e}"), if_(sound_on(), start_sound(join(V("style"), f" {e}")))] for e in SFX_EVENTS],
        [when_msg("start game"),
         forever(if_else(and_(eq(V("thrusting"), 1), sound_on()),
                         [play_until_done(join(V("style"), " thrust"))], [wait(0.05)]))],
    ]


# ---------------- screens ----------------

def hud_scripts():
    def signature():
        return join(V("state"), "|", V("score"), "|", V("lives"), "|", V("high score"), "|",
                    V("high name"), "|", V("style"), "|", V("banner"))

    return [
        [when_flag(), hide(), pen_clear(), set_var("sig", ""),
         forever(if_(not_(eq(V("sig"), signature())), set_var("sig", signature()), call("redraw")))],
        # runs without screen refresh, so the HUD sprite is never seen — only its pen stamps
        [define("redraw", warp=True),
         pen_clear(), show(),
         if_(or_(eq(V("state"), "play"), eq(V("state"), "gameover")),
             goto_xy(-226, 162), set_var("text", V("score")), call("draw text"),
             goto_xy(-226, 140),
             repeat(V("lives"), switch_costume(join(V("style"), " life")), stamp(), change_x(16)),
             set_y(162), set_var("text", join("HI ", V("high score"))), call("draw centered")),
         if_(eq(V("state"), "menu"),
             set_y(162), set_var("text", join("HI SCORE ", V("high score"), " ", V("high name"))),
             call("draw centered")),
         if_(and_(eq(V("state"), "play"), not_(eq(V("banner"), ""))),
             goto_xy(0, 40), set_var("text", V("banner")), call("draw centered")),
         hide()],
        [define("draw centered"), set_x(sub(6, mul(length(V("text")), 6))), call("draw text")],
        [define("draw text"),
         set_var("i", 1),
         repeat(length(V("text")),
                switch_costume("c space"),  # unknown characters draw as blanks
                switch_costume(join("c ", letter(V("i"), V("text")))),
                stamp(), change_x(12), change_var("i", 1))],
    ]


def title_scripts():
    return [
        [when_flag(), hide()],
        [when_msg("menu"), switch_costume(join(V("style"), " title")), goto_xy(0, 75), show()],
        [when_msg("style changed"), switch_costume(join(V("style"), " title"))],
        [when_msg("config"), hide()],
        [when_msg("credits"), hide()],
        [when_msg("start game"), hide()],
    ]


def panel_scripts():
    return [
        [when_flag(), hide()],
        [when_msg("menu"), hide()],
        [when_msg("start game"), hide()],
        [when_msg("config"), switch_costume(join("config ", V("controls"))), goto_xy(0, 0), show()],
        [when_msg("settings changed"), switch_costume(join("config ", V("controls")))],
        [when_msg("credits"), switch_costume("credits"), goto_xy(0, 0), show()],
        [when_msg("game over"), switch_costume(join(V("style"), " gameover")), goto_xy(0, 20), go_front(), show()],
    ]


def make_buttons(specs):
    blocks = []
    for action, y in specs:
        blocks += [set_var("action", action), goto_xy(0, y), create_clone("_myself_")]
    return blocks


def button_scripts():
    return [
        [when_flag(), hide(), set_var("clone", 0)],
        # each screen change deletes the old buttons (clones), then the original lays out the new ones
        [when_msg("menu"), delete_if_clone(), *make_buttons(MENU_BUTTONS)],
        [when_msg("config"), delete_if_clone(), *make_buttons(CONFIG_BUTTONS)],
        [when_msg("credits"), delete_if_clone(), *make_buttons([("back", -150)])],
        [when_msg("start game"), delete_clone()],
        [when_clone(), set_var("clone", 1), call("label"), go_front(), show(),
         forever(if_else(touching("_mouse_"), [set_effect("BRIGHTNESS", 30)], [set_effect("BRIGHTNESS", 0)]))],
        [when_msg("settings changed"), call("label")],
        [when_clicked(), broadcast("sfx click"), call("act")],
        [define("label"),
         switch_costume(join("btn ", V("action"))),
         *[if_(eq(V("action"), s), switch_costume(join("btn ", s, " ", V(s)))) for s in SETTINGS]],
        [define("act"),
         if_(eq(V("action"), "play"), broadcast("start game")),
         if_(eq(V("action"), "config"), broadcast("config")),
         if_(eq(V("action"), "credits"), broadcast("credits")),
         if_(eq(V("action"), "back"), broadcast("menu")),
         if_(eq(V("action"), "sound"), toggle("sound", "on", "off"), broadcast("settings changed")),
         if_(eq(V("action"), "volume"),
             change_var("volume", -25), if_(lt(V("volume"), 25), set_var("volume", 100)),
             broadcast("settings changed")),
         if_(eq(V("action"), "controls"), toggle("controls", "arrows", "wasd"), broadcast("settings changed")),
         if_(eq(V("action"), "style"), toggle("style", "classic", "nyan"),
             broadcast("style changed"), broadcast("settings changed"))],
    ]


# ---------------- project assembly ----------------

# layer order = list order (later sprites draw on top)
SPRITES = [
    # name, local variables, scripts, extra sprite props
    ("Asteroid", ["tier", "speed", "safe", "shape", "award", "clone", "count"], asteroid_scripts,
     {"rotationStyle": "don't rotate"}),
    ("Particle", ["kind", "life", "speed", "dx", "dy"], particle_scripts, {}),
    ("Trail", [], trail_scripts, {}),
    ("Bullet", ["bvx", "bvy", "life"], bullet_scripts, {}),
    ("UfoShot", ["life"], ufoshot_scripts, {}),
    ("UFO", ["small", "dx", "vy", "shot timer", "dead"], ufo_scripts, {"rotationStyle": "don't rotate"}),
    ("Ship", ["vx", "vy", "busy", "fire held", "hyper held", "frame"], ship_scripts, {"direction": 0}),
    ("Popup", ["value"], popup_scripts, {}),
    ("SafeZone", [], safezone_scripts, {}),
    ("Flash", [], flash_scripts, {}),
    ("Panel", [], panel_scripts, {}),
    ("Title", [], title_scripts, {}),
    ("Button", ["action", "clone"], button_scripts, {}),
    ("HUD", ["sig", "text", "i"], hud_scripts, {}),
    ("Sfx", [], sfx_scripts, {}),
]


def build():
    out_assets = {}
    art = assets.costumes()
    global_ids = {name: f"var_{name}" for name in GLOBALS}
    list_ids = {name: f"list_{name}" for name in LISTS}
    bcast_ids = {name: "msg_" + name.replace(" ", "_") for name in BROADCASTS}

    def costumes_for(target):
        return [costume_entry(n, s, cx, cy, out_assets) for n, s, cx, cy in art[target]]

    def sounds_for(target):
        if target != "Sfx":
            return []
        entries = []
        for name, (make, loudness) in assets.SOUNDS.items():
            samples = make()
            entries.append(sound_entry(name, assets.wav_bytes(samples, loudness), assets.RATE, len(samples),
                                       out_assets))
        return entries

    stage = {
        "isStage": True, "name": "Stage",
        "variables": {vid: [name, GLOBALS[name]] for name, vid in global_ids.items()},
        "lists": {lid: [name, []] for name, lid in list_ids.items()},
        "broadcasts": {bid: name for name, bid in bcast_ids.items()},
        "blocks": serialize_scripts("stage_", stage_scripts(), global_ids, list_ids, bcast_ids),
        "comments": {}, "currentCostume": 0, "costumes": costumes_for("Stage"),
        "sounds": [], "volume": 100, "layerOrder": 0, "tempo": 60,
        "videoTransparency": 50, "videoState": "on", "textToSpeechLanguage": None,
    }
    targets = [stage]
    for layer, (name, local_names, scripts, extra) in enumerate(SPRITES, start=1):
        local_ids = {v: f"{name}_{v}" for v in local_names}
        sprite = {
            "isStage": False, "name": name,
            "variables": {vid: [v, 0] for v, vid in local_ids.items()},
            "lists": {}, "broadcasts": {},
            "blocks": serialize_scripts(f"{name}_b", scripts(), {**global_ids, **local_ids}, list_ids, bcast_ids),
            "comments": {}, "currentCostume": 0, "costumes": costumes_for(name),
            "sounds": sounds_for(name), "volume": 100, "layerOrder": layer,
            "visible": False, "x": 0, "y": 0, "size": 100, "direction": 90,
            "draggable": False, "rotationStyle": "all around",
        }
        sprite.update(extra)
        targets.append(sprite)

    out = pathlib.Path(__file__).with_name("asteroids.sb3")
    write_sb3(out, targets, out_assets, extensions=["pen"])
    return out


if __name__ == "__main__":
    print(f"wrote {build()}")
