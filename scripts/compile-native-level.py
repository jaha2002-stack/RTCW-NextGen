"""Compile an authored .map into a separate, native RBDoom3BFG level directory."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

OUTPUTS = {"proc": b"mapProcFile003", "cm": b'CM "1.00"'}


def compile_level(compiler, source, assets, output, navigation, map_name="level"):
    if source.suffix.lower() != ".map" or not source.is_file():
        raise ValueError("Expected an authored .map source file")
    if not assets.is_dir():
        raise ValueError(f"Asset directory does not exist: {assets}")
    if re.fullmatch(r"[a-z0-9_-]+", map_name) is None:
        raise ValueError("Expected a lowercase native map name")
    if any(re.fullmatch(r"aas[a-zA-Z0-9_]+", extension) is None for extension in navigation):
        raise ValueError("Expected a native AAS extension such as aas48")
    if output.exists() or output.is_symlink():
        raise ValueError(f"Output already exists: {output}")
    output = output.resolve()
    assets = assets.resolve()
    if output.is_relative_to(assets):
        raise ValueError("Output must be outside the input asset directory")

    source_data = source.read_bytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-level-", dir=output.parent) as temporary:
        staged = Path(temporary) / "level"
        base = staged / "base"
        maps = base / "maps"
        maps.mkdir(parents=True)
        for directory in ("materials", "textures", "def"):
            if (assets / directory).is_dir():
                shutil.copytree(assets / directory, base / directory)

        map_path = f"maps/{map_name}"
        (base / f"{map_path}.map").write_bytes(source_data)
        (base / "default.cfg").write_text("// Native level compilation and preview.\n", encoding="ascii")
        command = [str(compiler.resolve(strict=True)), "-nogui", "+set", "fs_basepath", str(staged),
                   "+set", "fs_savepath", str(staged)]
        if not navigation:
            command.append("noAAS")
        command.append(f"{map_path}.map")
        result = subprocess.run(command, cwd=staged, capture_output=True, text=True, errors="replace", timeout=180)
        log = result.stdout + result.stderr
        if result.returncode:
            raise ValueError(f"rbdmap exited with code {result.returncode}\n{log[-4000:]}")

        expected = OUTPUTS | {extension: b'DewmAAS "1.07"' for extension in navigation}
        checksums = {f"base/{map_path}.map": hashlib.sha256(source_data).hexdigest()}
        for extension, header in expected.items():
            path = maps / f"{map_name}.{extension}"
            if not path.is_file():
                raise ValueError(f"rbdmap did not produce {path.name}\n{log[-4000:]}")
            data = path.read_bytes()
            if not data.startswith(header):
                raise ValueError(f"Unexpected native file header in {path.name}")
            checksums[path.relative_to(staged).as_posix()] = hashlib.sha256(data).hexdigest()

        manifest = {"map": map_path, "source": source.name, "sha256": checksums}
        (staged / "level-build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (staged / "rbdmap.log").write_text(log, encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise ValueError(f"Output already exists: {output}")
        staged.rename(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="authored .map file")
    parser.add_argument("--rbdmap", type=Path, required=True, help="path to the RBDoom3BFG map compiler")
    parser.add_argument("--assets", type=Path, required=True, help="directory with authored materials, textures and defs")
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    parser.add_argument("--aas", action="append", default=[], metavar="EXTENSION", help="require an AAS output, e.g. aas48")
    parser.add_argument("--map-name", default="level", help="name of the compiled map (default: level)")
    args = parser.parse_args()
    try:
        print(compile_level(args.rbdmap, args.source, args.assets, args.out, args.aas, args.map_name))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
