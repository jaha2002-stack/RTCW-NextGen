"""Generate an original room with a curved trim, collision and a translated inline model."""

import hashlib
import json
from pathlib import Path
import struct


def write_fixture(root, resources, version=46):
    lumps = [bytearray() for _ in range(17)]

    def add(lump, layout, *values):
        lumps[lump].extend(struct.pack(layout, *values))

    lumps[0].extend(
        b'{ "classname" "worldspawn" }\n'
        b'{ "classname" "info_player_start" "origin" "-40 0 36" "angle" "0" }\n'
        b'{ "classname" "func_door" "model" "*1" "origin" "80 61 24" "angles" "0 45 0" }\n'
        b'{ "classname" "misc_model" "model" "models/source/marker.md3" "origin" "77 -24 20" '
        b'"angles" "0 30 0" "modelscale" "1.25" }\n\0'
    )
    add(1, "<64sII", b"fixture/deck", 0, 1)
    add(1, "<64sII", b"fixture/wall", 0, 1)
    add(1, "<64sII", b"fixture/pane", 0, 0)

    boxes = [
        ((-136, 136), (-116, 116), (-16, 0)),
        ((-136, 136), (-116, 116), (112, 128)),
        ((-136, -120), (-116, 116), (0, 112)),
        ((120, 136), (-116, 116), (0, 112)),
        ((-120, 120), (-116, -100), (0, 112)),
        ((-120, 120), (100, 116), (0, 112)),
        ((-6, 6), (-8, 8), (0, 27)),
    ]
    for box_index, bounds in enumerate(boxes):
        add(8, "<3i", 6 * box_index, 6, 0)
        for axis, (low, high) in enumerate(bounds):
            for normal, coordinate in ((1, high), (-1, low)):
                plane_index = len(lumps[2]) // 16
                add(2, "<4f", *(normal if i == axis else 0 for i in range(3)), normal * coordinate)
                add(9, "<2i", plane_index, 0)

    def surface(material, kind, points, normal, indices=(), patch=(0, 0)):
        add(13, "<7i68x2i", material, -1, kind, len(lumps[10]) // 44, len(points),
            len(lumps[11]) // 4, len(indices), *patch)
        for point, u, v in points:
            add(10, "<10f4B", *point, u, v, 0, 0, *normal, 255, 255, 255, 255)
        for index in indices:
            add(11, "<i", index)

    def quad(material, points, normal):
        uv = ((0.25, 0.125), (2.5, 0.125), (2.5, 1.875), (0.25, 1.875))
        surface(material, 1, [(point, *st) for point, st in zip(points, uv)], normal, (0, 1, 2, 0, 2, 3))

    quad(0, [(-120, -100, 0), (120, -100, 0), (120, 100, 0), (-120, 100, 0)], (0, 0, 1))
    quad(1, [(-120, -100, 112), (-120, 100, 112), (120, 100, 112), (120, -100, 112)], (0, 0, -1))
    quad(1, [(120, -100, 0), (120, -100, 112), (120, 100, 112), (120, 100, 0)], (-1, 0, 0))
    quad(1, [(-120, -100, 0), (-120, 100, 0), (-120, 100, 112), (-120, -100, 112)], (1, 0, 0))
    quad(1, [(-120, -100, 0), (-120, -100, 112), (120, -100, 112), (120, -100, 0)], (0, 1, 0))
    quad(1, [(-120, 100, 0), (120, 100, 0), (120, 100, 112), (-120, 100, 112)], (0, -1, 0))
    surface(2, 2, [((48 if column != 1 else 55, -56 + 12 * column, 26 + 20 * row),
                    column / 2, row / 2) for row in range(3) for column in range(3)],
            (-1, 0, 0), patch=(3, 3))
    quad(1, [(-6, -8, 0), (-6, -8, 27), (-6, 8, 27), (-6, 8, 0)], (-1, 0, 0))
    add(7, "<6f4i", -136, -116, -16, 136, 116, 128, 0, 7, 0, 6)
    add(7, "<6f4i", -6, -8, 0, 6, 8, 27, 7, 1, 6, 1)

    offset = 8 + len(lumps) * 8
    header = bytearray(struct.pack("<4si", b"IBSP", version))
    for lump in lumps:
        header.extend(struct.pack("<ii", offset, len(lump)))
        offset += len(lump)
    source = root / "author.bsp"
    source.write_bytes(header + b"".join(lumps))
    model = resources / "models/import_marker.obj"
    model.parent.mkdir(parents=True, exist_ok=True)
    shader = hashlib.sha256(b"fixture/wall").hexdigest()[:20]
    model.write_text(
        f"o Marker\nusemtl textures/ibsp_import/{shader}\n"
        "v 0 -8 0\nv 0 8 0\nv 0 8 16\nv 0 -8 16\n"
        "vt 0 0\nvt 1 0\nvt 1 1\nvt 0 1\nvn -1 0 0\n"
        "f 1/1/1 2/2/1 3/3/1\nf 1/1/1 3/3/1 4/4/1\n",
        encoding="ascii",
    )
    mapping = root / "materials.json"
    mapping.write_text(json.dumps({
        "$models": {"models/source/marker.md3": "models/import_marker.obj"},
        "fixture/deck": {"texture": "textures/relay/deck.tga", "scale": [1.5, 2], "rotate": 90},
        "fixture/wall": {"texture": "textures/relay/wall.tga"},
        "fixture/pane": {"texture": "textures/renderer_smoke_white.tga", "alpha": 0.4},
    }), encoding="utf-8")
    return source, mapping


if __name__ == "__main__":
    import sys

    directory = Path(sys.argv[1])
    directory.mkdir(parents=True)
    write_fixture(directory, Path(sys.argv[2]))
