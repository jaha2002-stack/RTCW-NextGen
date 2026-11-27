"""Convert a permitted, loose IBSP v46/v47 map and material mapping to native RBDoom3BFG inputs."""

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile

from ibsp_metadata import check_surface_references, read_header

TABLES = {
    "shaders": struct.Struct("<64s2I"),
    "planes": struct.Struct("<4f"),
    "models": struct.Struct("<6f4i"),
    "brushes": struct.Struct("<3i"),
    "brush_sides": struct.Struct("<2i"),
    "draw_vertices": struct.Struct("<5f8x3f4x"),
    "draw_indices": struct.Struct("<i"),
    "surfaces": struct.Struct("<7i68x2i"),
}
MAX_BSP_BYTES = 128 * 1024 * 1024
MAX_RECORDS = 1_048_576
CONTENTS_SOLID = 1
CONTENTS_PLAYERCLIP = 0x10000
CONTENTS_MONSTERCLIP = 0x20000
COLLISION = "textures/ibsp_import/solid"
CLIP_FLAGS = CONTENTS_PLAYERCLIP | CONTENTS_MONSTERCLIP
CLIP_MATERIALS = {
    CONTENTS_PLAYERCLIP: "playerclip",
    CONTENTS_MONSTERCLIP: "monsterclip",
    CLIP_FLAGS: "playerclip\nmonsterclip",
}
MESH = (1, 3)
PATCH = 2
TOKEN = re.compile(rb'\s+|//[^\r\n]*|\{|\}|"[^"\r\n]*"')
SAFE_PATH = re.compile(r"[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)*")


def checked_slice(table, first, count, description):
    if first < 0 or count < 0 or first + count > len(table):
        raise ValueError(f"{description} exceeds its lump bounds")
    return table[first:first + count]


def entry(table, index, description):
    if index < 0 or index >= len(table):
        raise ValueError(f"{description} index {index} is out of bounds")
    return table[index]


def quoted(value):
    if any(ord(char) < 32 or ord(char) == 127 for char in value) or '"' in value:
        raise ValueError("An entity or resource string contains an unsupported character")
    return f'"{value}"'


def parse_entities(data):
    data = data.rstrip(b"\0")
    entities = []
    fields = None
    key = None
    position = 0
    while position < len(data):
        match = TOKEN.match(data, position)
        if not match:
            raise ValueError(f"Unsupported IBSP entity token at byte {position}")
        token = match[0]
        position = match.end()
        if token.isspace() or token.startswith(b"//"):
            continue
        if token == b"{" and fields is None:
            fields = {}
        elif token == b"}" and fields is not None and key is None:
            entities.append(fields)
            fields = None
        elif token.startswith(b'"') and fields is not None:
            value = token[1:-1].decode("utf-8")
            if key is None:
                if not value or value.lower() in fields:
                    raise ValueError(f"Empty or duplicate entity key: {value}")
                key = value.lower()
            else:
                fields[key], key = value, None
        else:
            raise ValueError(f"Invalid IBSP entity at byte {position}")
    if fields is not None or not entities or entities[0].get("classname") != "worldspawn":
        raise ValueError("IBSP must start with a complete worldspawn")
    return entities


def values(numbers):
    if not all(math.isfinite(number) and abs(number) < 1e8 for number in numbers):
        raise ValueError("IBSP contains non-finite or out-of-range geometry")
    return " ".join(format(number, ".9g") for number in numbers)


def native_material(shader, solid=False):
    name = hashlib.sha256(shader.encode("utf-8")).hexdigest()[:20]
    return f"textures/ibsp_import/{name}" + ("_solid" if solid else "")


def write_mesh(stream, material, vertices, indices):
    if len(indices) < 3 or len(indices) % 3:
        raise ValueError("IBSP mesh triangles need a non-empty index list divisible by three")
    stream.write(f'{{\nmeshDef\n{{\n( {len(vertices)} {len(indices) // 3} 0 0 0 )\n(\n')
    for vertex in vertices:
        stream.write(f'( {values(vertex)} )\n')
    stream.write(')\n(\n')
    for i in range(0, len(indices), 3):
        a, b, c = indices[i:i + 3]
        base, second, third = vertices[a], vertices[b], vertices[c]
        ab = [second[axis] - base[axis] for axis in range(3)]
        ac = [third[axis] - base[axis] for axis in range(3)]
        cross = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        # A native winding follows the outward normal with clockwise indices.
        if sum(cross[axis] * sum(v[axis + 5] for v in (base, second, third)) for axis in range(3)) > 0:
            b, c = c, b
        stream.write(f'{quoted(material)} 3 = {a} {b} {c}\n')
    stream.write(')\n}\n}\n')


def write_patch(stream, material, vertices, width, height):
    if width < 3 or height < 3 or width % 2 != 1 or height % 2 != 1 or width * height != len(vertices):
        raise ValueError(f"Invalid IBSP quadratic patch grid {width}×{height}")
    stream.write(f'{{\npatchDef2\n{{\n{quoted(material)}\n( {width} {height} 0 0 0 )\n(\n')
    # IBSP control points are row-major. idMapPatch reads columns first.
    for column in range(width):
        stream.write('( ' + ' '.join(f'( {values(vertices[row * width + column][:5])} )'
                                    for row in range(height)) + ' )\n')
    stream.write(')\n}\n}\n')


def write_brush(stream, sides, planes, material):
    if len(sides) < 4 or len(sides) > 128:
        raise ValueError("An IBSP brush needs 4–128 sides")
    stream.write('{\nbrushDef3\n{\n')
    for plane_index, _ in sides:
        x, y, z, distance = entry(planes, plane_index, "Brush plane")
        if abs(x * x + y * y + z * z - 1) > 0.01:
            raise ValueError(f"IBSP brush plane {plane_index} needs a unit normal")
        stream.write(f'( {values((x, y, z, -distance))} ) ( ( 1 0 0 ) ( 0 1 0 ) ) {quoted(material)} 0 0 0\n')
    stream.write('}\n}\n')


def read_tables(source):
    with source.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        if size > MAX_BSP_BYTES:
            raise ValueError("IBSP exceeds the offline import size limit")
        header = read_header(stream, size, versions=(46, 47))
        lumps = header["lumps"]
        if any(lumps[name]["records"] > MAX_RECORDS for name in TABLES):
            raise ValueError("IBSP geometry exceeds the offline record limit")
        check_surface_references(stream, lumps)
        tables = {}
        for name, layout in TABLES.items():
            stream.seek(lumps[name]["offset"])
            tables[name] = tuple(layout.iter_unpack(stream.read(lumps[name]["size"])))
        stream.seek(lumps["entities"]["offset"])
        entities = parse_entities(stream.read(lumps["entities"]["size"]))
        stream.seek(0)
        checksum = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return header["version"], tables, entities, checksum.hexdigest()


def convert_model(stream, model, tables, materials, omitted):
    _, _, _, _, _, _, first_surface, surface_count, first_brush, brush_count = model
    shaders = tables["shaders"]
    for first_side, side_count, shader_index in checked_slice(tables["brushes"], first_brush, brush_count, "Model brushes"):
        _, _, contents = entry(shaders, shader_index, "Brush shader")
        sides = checked_slice(tables["brush_sides"], first_side, side_count, "Brush sides")
        for _, side_shader in sides:
            entry(shaders, side_shader, "Brush side shader")
        if contents & CONTENTS_SOLID:
            write_brush(stream, sides, tables["planes"], COLLISION)
        elif contents & CLIP_FLAGS:
            write_brush(stream, sides, tables["planes"], f"textures/ibsp_import/clip_{contents & CLIP_FLAGS:x}")
        else:
            omitted[f"brush contents {contents:#x}"] += 1

    for surface in checked_slice(tables["surfaces"], first_surface, surface_count, "Model surfaces"):
        shader_index, _, kind, first_vertex, count, first_index, index_count, width, height = surface
        name, _, contents = entry(shaders, shader_index, "Surface shader")
        shader = name.split(b"\0", 1)[0].decode("utf-8")
        if kind != PATCH and kind not in MESH:
            omitted[f"surface type {kind}"] += 1
            continue
        vertices = checked_slice(tables["draw_vertices"], first_vertex, count, "Surface vertices")
        solid = kind == PATCH and bool(contents & CONTENTS_SOLID)
        material = native_material(shader, solid)
        materials[material] = shader
        if kind == PATCH:
            write_patch(stream, material, vertices, width, height)
        else:
            indices = [index for index, in checked_slice(tables["draw_indices"], first_index, index_count, "Surface indices")]
            write_mesh(stream, material, vertices, indices)


def write_map(stream, tables, entities, model_mapping):
    stream.write("Version 2\n")
    materials = {}
    omitted = Counter()
    models = tables["models"]
    if not models:
        raise ValueError("IBSP has no world geometry model")
    used = {0}
    native_names = set()
    external_models = set()
    for number, fields in enumerate(entities):
        fields = dict(fields)
        if not fields.get("classname"):
            raise ValueError(f"IBSP entity {number} has no classname")
        model = None
        reference = fields.get("model", "")
        if number == 0:
            model = models[0]
        elif reference.startswith("*"):
            if not re.fullmatch(r"\*[1-9][0-9]*", reference):
                raise ValueError(f"Invalid inline model reference {reference}")
            index = int(reference[1:])
            if index in used:
                raise ValueError(f"Repeated inline model reference {reference}")
            used.add(index)
            model = entry(models, index, "Entity model")
            name = f"ibsp_model_{index}"
            fields.update(name=name, model=name)
            fields["source_classname"] = fields["classname"]
            fields["classname"] = "func_static"
        elif reference:
            fields["source_model"] = reference
            if reference in model_mapping:
                fields["model"] = model_mapping[reference]
                fields["source_classname"] = fields["classname"]
                fields["classname"] = "func_static"
                external_models.add(fields["model"])
            else:
                omitted["external model references"] += 1
                del fields["model"]
        if fields.get("name"):
            if fields["name"].lower() in native_names:
                raise ValueError(f"Duplicate native entity name {fields['name']}")
            native_names.add(fields["name"].lower())

        stream.write("{\n")
        for key, value in fields.items():
            stream.write(f"{quoted(key)} {quoted(value)}\n")
        if model is not None:
            convert_model(stream, model, tables, materials, omitted)
        stream.write("}\n")
    omitted["unreferenced inline models"] += len(models) - len(used)
    return materials, external_models, {key: count for key, count in omitted.items() if count}


def resource_path(root, value, directory, suffix):
    if not isinstance(value, str) or not SAFE_PATH.fullmatch(value) or ".." in value.split("/"):
        raise ValueError(f"Unsafe resource path: {value!r}")
    path = Path(value)
    if path.parts[0] != directory or path.suffix != suffix:
        raise ValueError(f"Expected a resource path within {directory}/ ending in {suffix}: {value}")
    source = (root / path).resolve(strict=True)
    if not source.is_relative_to(root) or not source.is_file():
        raise ValueError(f"File falls outside supplied resources: {value}")
    return path, source


def write_materials(stream, materials, options, resources, destination):
    stream.write("_default\n{\n{ map _default }\n}\n")
    stream.write("_tracemodel\n{\ncollision\n}\n")
    # rbdmap uses caulk to bound compiled mesh submodels.
    stream.write("textures/common/caulk\n{\nforceOpaque\n}\n")
    for name, function in (("sinTable", math.sin), ("cosTable", math.cos)):
        samples = ", ".join(f"{function(math.tau * sample / 256):.8f}" for sample in range(256))
        stream.write(f"table {name} {{ {{ {samples} }} }}\n")
    stream.write(f"{COLLISION}\n{{\nforceOpaque\nnoShadows\n}}\n")
    for flags, parameters in CLIP_MATERIALS.items():
        stream.write(f"textures/ibsp_import/clip_{flags:x}\n{{\nnonsolid\n{parameters}\n}}\n")
    for material, shader in sorted(materials.items()):
        settings = options.get(shader)
        if not isinstance(settings, dict) or "texture" not in settings:
            raise ValueError(f"Missing material mapping for {shader!r}")
        relative, texture = resource_path(resources, settings["texture"], "textures", ".tga")
        output = destination / relative
        if not output.exists():
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(texture, output)
        alpha = settings.get("alpha", 1)
        scale = settings.get("scale", [1, 1])
        rotate = settings.get("rotate", 0)
        if not isinstance(alpha, (int, float)) or not 0 < alpha <= 1:
            raise ValueError(f"Material {shader!r} has invalid alpha")
        if not isinstance(scale, list) or len(scale) != 2 or not all(isinstance(n, (int, float)) and n for n in scale):
            raise ValueError(f"Material {shader!r} needs a two-component nonzero UV scale")
        if not isinstance(rotate, (int, float)):
            raise ValueError(f"Material {shader!r} has invalid UV rotation")
        uv_scale = values(scale).replace(" ", ", ")
        uv_rotate = f"rotate {values((rotate / 360,))}\n" if rotate else ""
        coverage = "forceOpaque" if alpha == 1 else "translucent\ntwoSided"
        solid = "" if material.endswith("_solid") else "nonsolid\nqer_nocarve\n"
        blend = "" if alpha == 1 else f"blend blend\nalpha {alpha:.9g}\n"
        stream.write(f"{material}\n{{\n{coverage}\n{solid}noShadows\n{{\n"
                     f"{blend}map {relative.with_suffix('').as_posix()}\nscale {uv_scale}\n{uv_rotate}}}\n}}\n")


def import_level(source, mapping, resources, output, navigation_def=None):
    version, tables, entities, source_sha256 = read_tables(source)
    options = json.loads(mapping.read_text(encoding="utf-8"))
    if not isinstance(options, dict):
        raise ValueError("Material mapping must be a JSON object")
    model_mapping = options.pop("$models", {})
    if not isinstance(model_mapping, dict) or not all(isinstance(value, str) for value in model_mapping.values()):
        raise ValueError("Model mapping must map source references to native OBJ paths")
    if output.exists() or output.is_symlink():
        raise ValueError(f"Output already exists: {output}")
    resources = resources.resolve(strict=True)
    if not resources.is_dir() or output.resolve().is_relative_to(resources):
        raise ValueError("Use a resource directory and an output outside that directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ibsp-import-", dir=output.parent) as temporary:
        staged = Path(temporary) / "level"
        assets = staged / "assets"
        (assets / "materials").mkdir(parents=True)
        with (staged / "imported.map").open("w", encoding="utf-8", newline="\n") as stream:
            materials, models, omitted = write_map(stream, tables, entities, model_mapping)
        with (assets / "materials/ibsp_import.mtr").open("w", encoding="ascii", newline="\n") as stream:
            write_materials(stream, materials, options, resources, assets)
        for model in sorted(models):
            relative, path = resource_path(resources, model, "models", ".obj")
            (assets / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, assets / relative)
        if navigation_def is not None:
            (assets / "def").mkdir()
            shutil.copyfile(navigation_def, assets / "def/navigation.def")
        manifest = {"source": source.name, "sha256": source_sha256, "version": version, "entities": len(entities),
                    "materials": materials, "models": sorted(models), "unconverted": omitted}
        (staged / "import.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError(f"Output already exists: {output}")
        staged.rename(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="loose BSP file that you have permission to convert")
    parser.add_argument("--materials", type=Path, required=True, help="JSON mapping of BSP shaders to native texture paths and parameters")
    parser.add_argument("--resources", type=Path, required=True, help="root containing mapped TGA files")
    parser.add_argument("--out", type=Path, required=True, help="new directory for native MAP, assets and import manifest")
    parser.add_argument("--navigation-def", type=Path, help="optional native AAS definitions to stage for compilation")
    args = parser.parse_args()
    try:
        print(import_level(args.source, args.materials, args.resources, args.out, args.navigation_def))
    except (OSError, ValueError, struct.error) as error:
        print(f"{args.source}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
