"""Tiny Python DSL for writing Scratch 3 scripts and packaging them as an .sb3 file."""
import hashlib
import json
import zipfile

# Scratch primitive shadow types
NUM, POS, WHOLE, INT, ANGLE, TEXT = 4, 5, 6, 7, 8, 10


class Blk:
    def __init__(self, op, inputs=None, fields=None, mutation=None, shadow=False):
        self.op, self.inputs, self.fields = op, inputs or {}, fields or {}
        self.mutation, self.shadow = mutation, shadow


class Var:
    def __init__(self, name):
        self.name = name


class Lst:
    def __init__(self, name):
        self.name = name


class Msg:
    def __init__(self, name):
        self.name = name


V = Var


def menu(op, field, value):
    return Blk(op, fields={field: [value, None]}, shadow=True)


def _menu_input(op, menu_op, field, value, inp=None, extra_inputs=None, fields=None):
    """Block whose dropdown is either a fixed string or a reporter covering the menu."""
    inp = inp or field
    if isinstance(value, str):
        slot = (menu(menu_op, field, value), None)
    else:
        slot = (value, menu(menu_op, field, ""))
    return Blk(op, {inp: slot, **(extra_inputs or {})}, fields)


# --- events ---
def when_flag(): return Blk("event_whenflagclicked")
def when_clicked(): return Blk("event_whenthisspriteclicked")
def when_msg(name): return Blk("event_whenbroadcastreceived", fields={"BROADCAST_OPTION": Msg(name)})
def broadcast(name, default=None):
    """Broadcast a fixed message, or a reporter that names one (default = any declared message)."""
    if isinstance(name, str):
        return Blk("event_broadcast", {"BROADCAST_INPUT": (Msg(name), None)})
    return Blk("event_broadcast", {"BROADCAST_INPUT": (name, Msg(default))})
def broadcast_wait(name): return Blk("event_broadcastandwait", {"BROADCAST_INPUT": (Msg(name), None)})

# --- control ---
def forever(*body): return Blk("control_forever", {"SUBSTACK": (list(body), None)})
def if_(cond, *body): return Blk("control_if", {"CONDITION": (cond, None), "SUBSTACK": (list(body), None)})
def if_else(cond, body, other):
    return Blk("control_if_else", {"CONDITION": (cond, None), "SUBSTACK": (body, None), "SUBSTACK2": (other, None)})
def repeat(n, *body): return Blk("control_repeat", {"TIMES": (n, WHOLE), "SUBSTACK": (list(body), None)})
def repeat_until(cond, *body):
    return Blk("control_repeat_until", {"CONDITION": (cond, None), "SUBSTACK": (list(body), None)})
def wait(s): return Blk("control_wait", {"DURATION": (s, POS)})
def wait_until(cond): return Blk("control_wait_until", {"CONDITION": (cond, None)})
def _stop(option, hasnext):
    return Blk("control_stop", fields={"STOP_OPTION": [option, None]}, mutation={"hasnext": hasnext})
def stop_this(): return _stop("this script", "false")
def stop_other(): return _stop("other scripts in sprite", "true")
def create_clone(of):
    return Blk("control_create_clone_of",
               {"CLONE_OPTION": (menu("control_create_clone_of_menu", "CLONE_OPTION", of), None)})
def when_clone(): return Blk("control_start_as_clone")
def delete_clone(): return Blk("control_delete_this_clone")

# --- motion ---
def move(n): return Blk("motion_movesteps", {"STEPS": (n, NUM)})
def turn_right(d): return Blk("motion_turnright", {"DEGREES": (d, NUM)})
def turn_left(d): return Blk("motion_turnleft", {"DEGREES": (d, NUM)})
def point_dir(d): return Blk("motion_pointindirection", {"DIRECTION": (d, ANGLE)})
def point_towards(obj):
    return Blk("motion_pointtowards", {"TOWARDS": (menu("motion_pointtowards_menu", "TOWARDS", obj), None)})
def goto_xy(x, y): return Blk("motion_gotoxy", {"X": (x, NUM), "Y": (y, NUM)})
def goto(target): return Blk("motion_goto", {"TO": (menu("motion_goto_menu", "TO", target), None)})
def change_x(d): return Blk("motion_changexby", {"DX": (d, NUM)})
def change_y(d): return Blk("motion_changeyby", {"DY": (d, NUM)})
def set_x(x): return Blk("motion_setx", {"X": (x, NUM)})
def set_y(y): return Blk("motion_sety", {"Y": (y, NUM)})
def rot_style(s): return Blk("motion_setrotationstyle", fields={"STYLE": [s, None]})
def x_pos(): return Blk("motion_xposition")
def y_pos(): return Blk("motion_yposition")
def direction(): return Blk("motion_direction")

# --- looks ---
def show(): return Blk("looks_show")
def hide(): return Blk("looks_hide")
def switch_costume(name): return _menu_input("looks_switchcostumeto", "looks_costume", "COSTUME", name)
def switch_backdrop(name): return _menu_input("looks_switchbackdropto", "looks_backdrops", "BACKDROP", name)
def set_effect(effect, v): return Blk("looks_seteffectto", {"VALUE": (v, NUM)}, {"EFFECT": [effect, None]})
def change_effect(effect, v): return Blk("looks_changeeffectby", {"CHANGE": (v, NUM)}, {"EFFECT": [effect, None]})
def set_ghost(v): return set_effect("GHOST", v)
def clear_effects(): return Blk("looks_cleargraphiceffects")
def set_size(v): return Blk("looks_setsizeto", {"SIZE": (v, NUM)})
def go_front(): return Blk("looks_gotofrontback", fields={"FRONT_BACK": ["front", None]})

# --- sound ---
def start_sound(name): return _menu_input("sound_play", "sound_sounds_menu", "SOUND_MENU", name)
def play_until_done(name): return _menu_input("sound_playuntildone", "sound_sounds_menu", "SOUND_MENU", name)
def stop_all_sounds(): return Blk("sound_stopallsounds")
def set_volume(v): return Blk("sound_setvolumeto", {"VOLUME": (v, NUM)})

# --- sensing ---
def key(k): return _menu_input("sensing_keypressed", "sensing_keyoptions", "KEY_OPTION", k)
def touching(obj):
    return Blk("sensing_touchingobject",
               {"TOUCHINGOBJECTMENU": (menu("sensing_touchingobjectmenu", "TOUCHINGOBJECTMENU", obj), None)})
def distance_to(obj):
    return Blk("sensing_distanceto",
               {"DISTANCETOMENU": (menu("sensing_distancetomenu", "DISTANCETOMENU", obj), None)})
def attr_of(prop, obj):
    return Blk("sensing_of", {"OBJECT": (menu("sensing_of_object_menu", "OBJECT", obj), None)},
               {"PROPERTY": [prop, None]})
def ask(question): return Blk("sensing_askandwait", {"QUESTION": (question, TEXT)})
def answer(): return Blk("sensing_answer")

# --- operators ---
def _bin(op, a, b): return Blk(op, {"NUM1": (a, NUM), "NUM2": (b, NUM)})
def add(a, b): return _bin("operator_add", a, b)
def sub(a, b): return _bin("operator_subtract", a, b)
def mul(a, b): return _bin("operator_multiply", a, b)
def div(a, b): return _bin("operator_divide", a, b)
def mod(a, b): return _bin("operator_mod", a, b)
def _cmp(op, a, b): return Blk(op, {"OPERAND1": (a, TEXT), "OPERAND2": (b, TEXT)})
def gt(a, b): return _cmp("operator_gt", a, b)
def lt(a, b): return _cmp("operator_lt", a, b)
def eq(a, b): return _cmp("operator_equals", a, b)
def and_(a, b): return Blk("operator_and", {"OPERAND1": (a, None), "OPERAND2": (b, None)})
def or_(a, b): return Blk("operator_or", {"OPERAND1": (a, None), "OPERAND2": (b, None)})
def not_(a): return Blk("operator_not", {"OPERAND": (a, None)})
def rand(a, b): return Blk("operator_random", {"FROM": (a, NUM), "TO": (b, NUM)})
def mathop(op, x): return Blk("operator_mathop", {"NUM": (x, NUM)}, {"OPERATOR": [op, None]})
def join(*parts):
    """Scratch join takes two strings; longer lists nest to the right."""
    if len(parts) == 1:
        return parts[0]
    return Blk("operator_join", {"STRING1": (parts[0], TEXT), "STRING2": (join(*parts[1:]), TEXT)})
def letter(i, s): return Blk("operator_letter_of", {"LETTER": (i, WHOLE), "STRING": (s, TEXT)})
def length(s): return Blk("operator_length", {"STRING": (s, TEXT)})

# --- data ---
def set_var(name, v): return Blk("data_setvariableto", {"VALUE": (v, TEXT)}, {"VARIABLE": Var(name)})
def change_var(name, v): return Blk("data_changevariableby", {"VALUE": (v, NUM)}, {"VARIABLE": Var(name)})
def add_to(lst, item): return Blk("data_addtolist", {"ITEM": (item, TEXT)}, {"LIST": Lst(lst)})
def delete_item(i, lst): return Blk("data_deleteoflist", {"INDEX": (i, INT)}, {"LIST": Lst(lst)})
def delete_all(lst): return Blk("data_deletealloflist", fields={"LIST": Lst(lst)})
def item(i, lst): return Blk("data_itemoflist", {"INDEX": (i, INT)}, {"LIST": Lst(lst)})
def list_length(lst): return Blk("data_lengthoflist", fields={"LIST": Lst(lst)})

# --- pen ---
def pen_clear(): return Blk("pen_clear")
def stamp(): return Blk("pen_stamp")

# --- custom blocks (no arguments; pass data through variables) ---
def define(proccode, warp=False):
    proto = Blk("procedures_prototype", shadow=True, mutation={
        "proccode": proccode, "argumentids": "[]", "argumentnames": "[]",
        "argumentdefaults": "[]", "warp": "true" if warp else "false"})
    return Blk("procedures_definition", {"custom_block": (proto, None)})
def call(proccode):
    return Blk("procedures_call", mutation={"proccode": proccode, "argumentids": "[]", "warp": "false"})


class Serializer:
    """Flattens nested Blk trees into Scratch's flat {id: block} map."""

    def __init__(self, prefix, variables, lists, broadcasts):
        self.prefix, self.variables, self.lists, self.broadcasts = prefix, variables, lists, broadcasts
        self.blocks, self.count = {}, 0

    def _id(self):
        self.count += 1
        return f"{self.prefix}{self.count}"

    def _ref(self, obj):
        if isinstance(obj, Var):
            return [obj.name, self.variables[obj.name]]
        if isinstance(obj, Lst):
            return [obj.name, self.lists[obj.name]]
        if isinstance(obj, Msg):
            return [obj.name, self.broadcasts[obj.name]]
        return obj

    def _covering(self, val, parent):
        if isinstance(val, Var):
            return [12, val.name, self.variables[val.name]]
        return self.block(val, parent)

    def _input(self, val, stype, parent):
        if isinstance(stype, Blk):  # dropdown menu covered by a reporter
            return [3, self._covering(val, parent), self.block(stype, parent)]
        if isinstance(stype, Msg):  # broadcast slot covered by a reporter
            return [3, self._covering(val, parent), [11, stype.name, self.broadcasts[stype.name]]]
        if isinstance(val, list):
            return [2, self.stack(val, parent)] if val else None
        if isinstance(val, Msg):
            return [1, [11, val.name, self.broadcasts[val.name]]]
        if isinstance(val, Var):
            return [3, [12, val.name, self.variables[val.name]], [stype, "0"]]
        if isinstance(val, Blk):
            bid = self.block(val, parent)
            if val.shadow:
                return [1, bid]
            if stype is None:
                return [2, bid]
            return [3, bid, [stype, "" if stype == TEXT else "0"]]
        return [1, [stype, str(val)]]

    def block(self, b, parent, top=False):
        bid = self._id()
        d = {"opcode": b.op, "next": None, "parent": parent, "inputs": {}, "fields": {},
             "shadow": b.shadow, "topLevel": top}
        self.blocks[bid] = d
        for name, (val, stype) in b.inputs.items():
            encoded = self._input(val, stype, bid)
            if encoded is not None:
                d["inputs"][name] = encoded
        d["fields"] = {name: self._ref(val) for name, val in b.fields.items()}
        if b.mutation is not None:
            d["mutation"] = {"tagName": "mutation", "children": [], **b.mutation}
        return bid

    def stack(self, blks, parent, xy=None):
        # The VM would happily run blocks placed after a cap block, but the Scratch editor can't load
        # such a script and silently drops it and every script after it from the code area.
        for b in blks[:-1]:
            if _is_cap(b):
                raise ValueError(f"'{b.op}' is a cap block: nothing may follow it (wrap it in an if)")
        first = prev = None
        for b in blks:
            bid = self.block(b, prev or parent, top=(xy is not None and prev is None))
            if prev:
                self.blocks[prev]["next"] = bid
            else:
                first = bid
            prev = bid
        if xy:
            self.blocks[first]["x"], self.blocks[first]["y"] = xy
        return first


def _is_cap(b):
    if b.op in ("control_delete_this_clone", "control_forever"):
        return True
    return b.op == "control_stop" and b.mutation["hasnext"] == "false"


def serialize_scripts(prefix, scripts, variables, lists, broadcasts):
    ser = Serializer(prefix, variables, lists, broadcasts)
    for i, script in enumerate(scripts):
        ser.stack(script, None, xy=(40 + 520 * (i % 4), 40 + 700 * (i // 4)))
    return ser.blocks


def _asset(raw, ext, assets):
    md5 = hashlib.md5(raw).hexdigest()
    assets[f"{md5}.{ext}"] = raw
    return md5


def costume_entry(name, svg, cx, cy, assets):
    md5 = _asset(svg.encode(), "svg", assets)
    return {"assetId": md5, "name": name, "md5ext": f"{md5}.svg", "dataFormat": "svg",
            "rotationCenterX": cx, "rotationCenterY": cy}


def sound_entry(name, wav, rate, sample_count, assets):
    md5 = _asset(wav, "wav", assets)
    return {"assetId": md5, "name": name, "dataFormat": "wav", "format": "", "rate": rate,
            "sampleCount": sample_count, "md5ext": f"{md5}.wav"}


def write_sb3(path, targets, assets, extensions=()):
    project = {"targets": targets, "monitors": [], "extensions": list(extensions),
               "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": ""}}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json", json.dumps(project))
        for fname, raw in assets.items():
            z.writestr(fname, raw)
