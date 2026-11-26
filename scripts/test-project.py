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

import rtcw_data

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
                "scripts/play-signal-room.cmd": b"game launcher",
                "scripts/renderer-smoke.cmd": b"launcher",
                "tests/fixtures/renderer-smoke.mtr": b"material",
                "tests/fixtures/signal-room.mtr": b"room material",
                "tests/fixtures/renderer_smoke_white.tga": b"texture",
                "docs/rtcwnextgen/RELEASE-PROCESS.md": b"instructions",
                "docs/rtcwnextgen/SIGNAL-ROOM-TEST-CARD.md": b"test card",
                "base/renderprogs2/dxil/synthetic.bin": b"shader",
                "base/pak000.pk4": b"must be excluded",
                "Main/pak0.pk3": b"must be excluded",
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
                self.assertNotIn("Main/pak0.pk3", archive.namelist())
                self.assertEqual(archive.read("Play Signal Room.cmd"), b"game launcher")
                self.assertEqual(archive.read("Run Renderer Smoke.cmd"), b"launcher")
                self.assertEqual(archive.read("base/materials/renderer-smoke.mtr"), b"material")
                self.assertEqual(archive.read("base/materials/signal-room.mtr"), b"room material")
                self.assertEqual(archive.read("base/textures/renderer_smoke_white.tga"), b"texture")
                self.assertEqual(archive.read("TEST-CARD.md"), b"test card")
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


class RTCWDataTests(unittest.TestCase):
    def test_locate_respects_single_player_precedence(self):
        with tempfile.TemporaryDirectory() as temporary:
            main = Path(temporary) / "Main"
            main.mkdir()
            for name, entry in (
                ("z_override.pk3", "maps/fixture.bsp"),
                ("SP_PAK2.PK3", "Maps/Fixture.bsp"),
                ("sp_pak3.pk3", "MAPS/FIXTURE.BSP"),
                ("mp_override.pk3", "maps/multiplayer.bsp"),
            ):
                with zipfile.ZipFile(main / name, "w") as archive:
                    archive.writestr(entry, "synthetic test data")
            folder = main / "Maps"
            folder.mkdir()
            (folder / "fixture.bsp").write_text("loose copy")
            loose = folder / "extra.bsp"
            loose.write_text("loose only")

            self.assertEqual(
                rtcw_data.locate_resource(main, "maps\\fixture.bsp"),
                ((main / "sp_pak3.pk3").resolve(), "MAPS/FIXTURE.BSP"),
            )
            self.assertEqual(rtcw_data.locate_resource(main, "MAPS/extra.bsp"), (loose.resolve(), None))
            self.assertIsNone(rtcw_data.locate_resource(main, "maps/multiplayer.bsp"))

    def test_locate_rejects_unsafe_paths_and_invalid_packs(self):
        with tempfile.TemporaryDirectory() as temporary:
            main = Path(temporary) / "Main"
            main.mkdir()
            (main / "pak0.pk3").write_bytes(b"invalid ZIP")
            for target in ("../outside.txt", "/etc/example", "C:\\temp\\example", "maps//fixture.bsp"):
                with self.subTest(target=target), self.assertRaisesRegex(ValueError, "relative resource path"):
                    rtcw_data.locate_resource(main, target)
            with self.assertRaisesRegex(ValueError, "cannot read PK3 directory"):
                rtcw_data.locate_resource(main, "maps/fixture.bsp")

    def test_inventory_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            main = root / "mAiN"
            main.mkdir()
            for name in rtcw_data.REQUIRED:
                with zipfile.ZipFile(main / name.upper(), "w") as archive:
                    archive.writestr("synthetic.txt", "test")
                    if name == "pak0.pk3":
                        archive.writestr("Maps/Escape1.BSP", "synthetic fixture")
            before = {path.name: path.read_bytes() for path in main.iterdir()}
            messages, ready = rtcw_data.inspect(root)
            self.assertTrue(ready, messages)
            self.assertIn("maps/escape1.bsp: present in pak0.pk3", messages)
            self.assertEqual(rtcw_data.inspect(main), (messages, ready))
            self.assertEqual({path.name: path.read_bytes() for path in main.iterdir()}, before)

    def test_inventory_reports_missing_and_invalid_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            main = Path(temporary) / "Main"
            main.mkdir()
            (main / "pak0.pk3").write_bytes(b"invalid ZIP")
            with zipfile.ZipFile(main / "sp_pak1.pk3", "w"):
                pass
            messages, ready = rtcw_data.inspect(main)
            self.assertFalse(ready)
            self.assertTrue(any(line.startswith("pak0.pk3: cannot read PK3 directory") for line in messages))
            self.assertIn("sp_pak1.pk3: no file entries", messages)
            self.assertIn("sp_pak2.pk3: missing file", messages)
            self.assertIn("maps/escape1.bsp: absent from the inspected archives", messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rbdmap", type=Path)
    args = parser.parse_args()
    if args.rbdmap is not None:
        RBDMAP = args.rbdmap.resolve(strict=True)
    unittest.main(argv=[__file__], verbosity=2)
