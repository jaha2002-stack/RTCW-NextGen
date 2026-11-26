"""Run P00 synthetic project checks, including a real map compile when requested."""

import argparse
import hashlib
import importlib.util
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_windows", Path(__file__).with_name("package-windows.py"))
PACKAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGE)
RBDMAP = None


class PackageTests(unittest.TestCase):
    def test_allowlist_and_checksums(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / "build"
            binary = bytearray(70)
            binary[:2] = b"MZ"
            struct.pack_into("<I", binary, 60, 64)
            binary[64:] = b"PE\0\0\x64\x86"
            inputs = {
                "build/Release/RBDoom3BFG.exe": binary,
                "build/tools/compilers/Release/rbdmap.exe": binary,
                "LICENSE.md": b"license",
                "LICENSE_EXCEPTIONS.md": b"exceptions",
                "neo/extern/nvrhi/LICENSE.txt": b"license",
                "neo/extern/ShaderMake/LICENSE.txt": b"license",
                "base/default.cfg": b"configuration",
                "docs/rtcwnextgen/RELEASE-PROCESS.md": b"instructions",
                "base/renderprogs2/dxil/synthetic.bin": b"shader",
                "base/pak000.pk4": b"must be excluded",
                "base/game.resources": b"must be excluded",
            }
            for name, data in inputs.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            files = PACKAGE.collect(root, build)
            output = root / "artifact.zip"
            PACKAGE.write_package(output, files, {"scope": "test"})
            self.assertEqual(
                output.with_suffix(".zip.sha256").read_text().split()[0],
                hashlib.sha256(output.read_bytes()).hexdigest(),
            )
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), set(files) | {"SHA256SUMS.txt", "BUILD-MANIFEST.json"})
                self.assertNotIn("base/pak000.pk4", archive.namelist())
                self.assertNotIn("base/game.resources", archive.namelist())
            (root / "base/renderprogs2/dxil/synthetic.bin").unlink()
            with self.assertRaisesRegex(ValueError, "DXIL"):
                PACKAGE.collect(root, build)

    def test_reject_non_windows_binary(self):
        self.assertFalse(PACKAGE.pe_x64(b"\x7fELF"))
        self.assertFalse(PACKAGE.pe_x64(b"MZ" + bytes(62)))


class MapCompilerTests(unittest.TestCase):
    def test_generates_geometry_and_collision(self):
        if RBDMAP is None:
            self.skipTest("supply --rbdmap to exercise the compiled tool")
        with tempfile.TemporaryDirectory(prefix="rtcwnextgen-dmap-") as temporary:
            fixture = Path(temporary)
            base = fixture / "base"
            (base / "maps").mkdir(parents=True)
            (base / "materials").mkdir()
            shutil.copyfile(ROOT / "base/default.cfg", base / "default.cfg")
            (base / "materials/cloud_room.mtr").write_text(
                "textures/test/cloud_room { forceOpaque forceshadows }\n"
                "_tracemodel { collision }\n",
                encoding="ascii",
            )
            shutil.copyfile(ROOT / "tests/fixtures/cloud_room.map", base / "maps/cloud_room.map")
            result = subprocess.run(
                [str(RBDMAP), "-nogui", "+set", "fs_basepath", str(fixture),
                 "+set", "fs_savepath", str(fixture), "noAAS", "maps/cloud_room.map"],
                cwd=fixture, capture_output=True, text=True, errors="replace", timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            proc = base / "maps/cloud_room.proc"
            collision = base / "maps/cloud_room.cm"
            self.assertTrue(proc.is_file() and collision.is_file(), result.stdout + result.stderr)
            self.assertIn(b"_area0", proc.read_bytes())
            self.assertTrue(collision.read_bytes().startswith(b'CM "1.00"'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rbdmap", type=Path)
    args = parser.parse_args()
    if args.rbdmap is not None:
        RBDMAP = args.rbdmap.resolve(strict=True)
    unittest.main(argv=[__file__], verbosity=2)
