"""Minimal .aseprite reader: first frame of an RGBA (32-bit) sprite, visible layers composited in order.

Spec: https://github.com/aseprite/aseprite/blob/main/docs/ase-file-specs.md
"""
import struct
import zlib

_HEADER, _FRAME_HEADER = 128, 16
_LAYER, _CEL = 0x2004, 0x2005
_RAW_CEL, _COMPRESSED_CEL = 0, 2


def read_rgba(path):
    """Return (width, height, pixels) where pixels[y][x] = (r, g, b, a)."""
    data = open(path, "rb").read()
    _, magic, _, width, height, depth = struct.unpack_from("<IHHHHH", data, 0)
    if magic != 0xA5E0:
        raise ValueError(f"{path}: not an .aseprite file")
    if depth != 32:
        raise ValueError(f"{path}: only RGBA sprites are supported (color depth {depth}); "
                         "switch it to Sprite > Color Mode > RGB Color in Aseprite")

    pixels = [[(0, 0, 0, 0)] * width for _ in range(height)]
    frame_size, _, old_chunks, _, _, new_chunks = struct.unpack_from("<IHHH2sI", data, _HEADER)
    pos, end = _HEADER + _FRAME_HEADER, _HEADER + frame_size
    visible_layers, layer_index = set(), 0
    for _ in range(new_chunks or old_chunks):
        chunk_size, chunk_type = struct.unpack_from("<IH", data, pos)
        body = pos + 6
        if chunk_type == _LAYER:
            if struct.unpack_from("<H", data, body)[0] & 1:  # visible flag
                visible_layers.add(layer_index)
            layer_index += 1
        elif chunk_type == _CEL:
            _draw_cel(data, body, pos + chunk_size, pixels, visible_layers)
        pos += chunk_size
        if pos >= end:
            break
    return width, height, pixels


def _draw_cel(data, body, chunk_end, pixels, visible_layers):
    layer, x0, y0, opacity, cel_type = struct.unpack_from("<HhhBH", data, body)
    if layer not in visible_layers:
        return
    w, h = struct.unpack_from("<HH", data, body + 16)
    raw = data[body + 20:chunk_end]
    if cel_type == _COMPRESSED_CEL:
        raw = zlib.decompress(raw)
    elif cel_type != _RAW_CEL:
        raise ValueError(f"unsupported cel type {cel_type} (linked cels / tilemaps)")
    for y in range(h):
        for x in range(w):
            r, g, b, a = raw[(y * w + x) * 4:(y * w + x) * 4 + 4]
            a = a * opacity // 255
            if a and 0 <= y0 + y < len(pixels) and 0 <= x0 + x < len(pixels[0]):
                pixels[y0 + y][x0 + x] = (r, g, b, a)  # ponytail: top cel wins, no alpha blending
