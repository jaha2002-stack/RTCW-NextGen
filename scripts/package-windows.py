"""Build the renderer smoke engineering ZIP from a Windows Release build."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "ea29c006e84fedcc0e7c173c383a087ce0a8c0d5"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_input(path):
    if path.is_symlink() or not path.is_file() or not path.stat().st_size:
        raise ValueError(f"Expected a non-empty regular file: {path}")
    return path.read_bytes()


def pe_x64(data):
    if data[:2] != b"MZ" or len(data) < 64:
        return False
    offset = struct.unpack_from("<I", data, 60)[0]
    return data[offset:offset + 6] == b"PE\0\0\x64\x86"


def collect(root, build):
    files = {}
    for name, path in {
        "RBDoom3BFG.exe": build / "Release/RBDoom3BFG.exe",
        "rbdmap.exe": build / "tools/compilers/Release/rbdmap.exe",
    }.items():
        data = read_input(path)
        if not pe_x64(data):
            raise ValueError(f"Expected a Windows x64 executable: {path}")
        files[name] = data

    for source, destination in {
        "LICENSE.md": "LICENSE.md",
        "LICENSE_EXCEPTIONS.md": "LICENSE_EXCEPTIONS.md",
        "neo/extern/nvrhi/LICENSE.txt": "licenses/NVRHI.txt",
        "neo/extern/ShaderMake/LICENSE.txt": "licenses/ShaderMake.txt",
        "base/default.cfg": "base/default.cfg",
        "scripts/renderer-smoke.cmd": "Run Renderer Smoke.cmd",
        "scripts/compile-native-level.py": "tools/compile-native-level.py",
        "tests/fixtures/renderer-smoke.mtr": "base/materials/renderer-smoke.mtr",
        "tests/fixtures/renderer_smoke_white.tga": "base/textures/renderer_smoke_white.tga",
        "docs/rtcwnextgen/RELEASE-PROCESS.md": "README.md",
    }.items():
        files[destination] = read_input(root / source)

    shaders = root / "base/renderprogs2/dxil"
    shader_files = sorted(shaders.rglob("*.bin"))
    if not shader_files:
        raise ValueError(f"Missing DXIL output: {shaders}")
    for path in shader_files:
        files[path.relative_to(root).as_posix()] = read_input(path)
    return files


def write_package(output, files, manifest):
    files = dict(files)
    files["BUILD-MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    files["SHA256SUMS.txt"] = "".join(
        f"{digest(data)}  {name}\n" for name, data in sorted(files.items())
    ).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as work:
        staged = Path(work) / output.name
        with zipfile.ZipFile(staged, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                archive.writestr(zipfile.ZipInfo(name), data, compress_type=zipfile.ZIP_DEFLATED)
        extraction = Path(work) / "extracted"
        with zipfile.ZipFile(staged) as archive:
            if archive.namelist() != sorted(files) or archive.testzip() is not None:
                raise ValueError("ZIP inventory or ZIP CRC validation failed")
            archive.extractall(extraction)
        for name, original in files.items():
            if digest((extraction / name).read_bytes()) != digest(original):
                raise ValueError(f"Extracted checksum mismatch: {name}")
        checksum = digest(staged.read_bytes())
        staged.replace(output)
    output.with_suffix(".zip.sha256").write_text(f"{checksum}  {output.name}\n", encoding="ascii")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    changes = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True
    )
    if changes:
        raise ValueError("Package from a clean source checkout")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    submodules = subprocess.check_output(
        ["git", "submodule", "status", "--recursive"], cwd=ROOT, text=True
    ).splitlines()
    if not submodules or any(line[0] != " " for line in submodules):
        raise ValueError("Initialize all submodules at their pinned commits")
    manifest = {
        "scope": "P01 renderer smoke test",
        "source_sha": sha,
        "upstream_sha": UPSTREAM,
        "submodules": {line.split()[1]: line.split()[0] for line in submodules},
        "toolchain": "VS 2022 / MSVC 14.44 / Windows SDK 10.0.26100.0 / CMake 3.31.6 / ISPC 1.26.0",
        "configuration": "Release",
        "backend": "DX12 / DXIL",
        "platform": "Windows x64",
    }
    output = args.out / f"RTCW-NextGen-P01-{sha[:12]}-win-x64.zip"
    write_package(output, collect(ROOT, ROOT / "build-windows"), manifest)
    print(output)


if __name__ == "__main__":
    main()
