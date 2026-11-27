"""Inspect the structure and surface references of a local IBSP v47 file."""

import argparse
import json
import os
from pathlib import Path
import struct
import sys

# Layout and fixed record sizes verified against qfiles.h and tr_bsp.c at iortcw 438e7d413b5f.
LUMP_LAYOUT = (
    ("entities", None),
    ("shaders", 72),
    ("planes", 16),
    ("nodes", 36),
    ("leafs", 48),
    ("leaf_surfaces", 4),
    ("leaf_brushes", 4),
    ("models", 40),
    ("brushes", 12),
    ("brush_sides", 8),
    ("draw_vertices", 44),
    ("draw_indices", 4),
    ("fogs", 72),
    ("surfaces", 104),
    ("lightmaps", 128 * 128 * 3),
    ("light_grid", 8),
    ("visibility", None),
)
HEADER = struct.Struct("<4si" + "ii" * len(LUMP_LAYOUT))
# Skip shader, fog and surface type, then read first/number of vertices and indices.
SURFACE_REFERENCES = struct.Struct("<12x4i76x")
MAX_SURFACES = 0x20000
MAX_DRAW_INDICES = 0x80000


def read_header(stream, size):
    header = stream.read(HEADER.size)
    if len(header) != HEADER.size or size < HEADER.size:
        raise ValueError(f"Truncated IBSP header (expected {HEADER.size} bytes)")
    magic, version, *table = HEADER.unpack(header)
    if magic != b"IBSP":
        raise ValueError("Expected an IBSP signature")
    if version != 47:
        raise ValueError(f"Unsupported IBSP version {version} (expected 47)")

    lumps = {}
    ranges = []
    for (name, record_size), offset, length in zip(LUMP_LAYOUT, table[::2], table[1::2]):
        if offset < 0 or length < 0 or offset > size or length > size - offset:
            raise ValueError(f"IBSP lump {name} falls outside the file")
        if length:
            if offset < HEADER.size:
                raise ValueError(f"IBSP lump {name} overlaps the header")
            ranges.append((offset, offset + length, name))
        lump = {"offset": offset, "size": length}
        if record_size is not None:
            if length % record_size:
                raise ValueError(f"IBSP lump {name} is not a whole number of {record_size}-byte records")
            lump["records"] = length // record_size
        lumps[name] = lump

    previous_end = HEADER.size
    for start, end, name in sorted(ranges):
        if start < previous_end:
            raise ValueError(f"IBSP lump {name} overlaps another lump")
        previous_end = end

    return {"format": "IBSP", "version": version, "size": size, "lumps": lumps}


def _read_section(stream, name, section):
    stream.seek(section["offset"])
    data = stream.read(section["size"])
    if len(data) != section["size"]:
        raise ValueError(f"Truncated IBSP lump {name}")
    return data


def check_surface_references(stream, lumps):
    """Check surface ranges against the vertex and index tables of a seekable file."""
    surface_count = lumps["surfaces"]["records"]
    index_count = lumps["draw_indices"]["records"]
    vertex_count = lumps["draw_vertices"]["records"]
    if surface_count > MAX_SURFACES or index_count > MAX_DRAW_INDICES:
        raise ValueError("IBSP surface or index table exceeds v47 limits")

    surfaces = _read_section(stream, "surfaces", lumps["surfaces"])
    indices = struct.unpack(f"<{index_count}i", _read_section(stream, "draw_indices", lumps["draw_indices"]))
    referenced_indices = 0
    for number, (first_vertex, vertices, first_index, count) in enumerate(SURFACE_REFERENCES.iter_unpack(surfaces)):
        if first_vertex < 0 or vertices < 0 or first_vertex + vertices > vertex_count:
            raise ValueError(f"IBSP surface {number} vertex range falls outside the vertex table")
        if first_index < 0 or count < 0 or first_index + count > index_count:
            raise ValueError(f"IBSP surface {number} index range falls outside the index table")
        # Bound the work even if many surfaces point at the same index range.
        referenced_indices += count
        if referenced_indices > MAX_DRAW_INDICES:
            raise ValueError("IBSP index references exceed the v47 draw-index limit")
        for index in indices[first_index:first_index + count]:
            if index < 0 or index >= vertices:
                raise ValueError(f"IBSP surface {number} contains an index outside its vertex range")
    return surface_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bsp_file", type=Path)
    args = parser.parse_args()
    try:
        with args.bsp_file.open("rb") as stream:
            report = read_header(stream, os.fstat(stream.fileno()).st_size)
            report["checked_surfaces"] = check_surface_references(stream, report["lumps"])
    except (OSError, ValueError) as error:
        print(f"{args.bsp_file}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
