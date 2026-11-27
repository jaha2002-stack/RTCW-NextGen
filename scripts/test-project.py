"""Run synthetic project checks, including a real map compile when requested."""

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

import ibsp_metadata
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
                "scripts/renderer-smoke.cmd": b"launcher",
                "scripts/native-level-check.cmd": b"native check launcher",
                "scripts/compile-native-level.py": b"compiler wrapper",
                "tests/fixtures/renderer-smoke.mtr": b"material",
                "tests/fixtures/renderer_smoke_white.tga": b"texture",
                "tests/fixtures/native-level/materials/cloud_room.mtr": b"native room material",
                "tests/fixtures/native-level/def/navigation.def": b"navigation definition",
                "build/native-level/base/maps/level.map": b"authored map",
                "build/native-level/base/maps/level.proc": b"compiled geometry",
                "build/native-level/base/maps/level.cm": b"compiled collisions",
                "build/native-level/base/maps/level.aas48": b"compiled navigation",
                "build/native-level/level-build.json": b"level manifest",
                "docs/rtcwnextgen/RELEASE-PROCESS.md": b"instructions",
                "docs/rtcwnextgen/P01-P02-TEST-CARD.md": b"PC test card",
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
                self.assertEqual(archive.read("Run Renderer Smoke.cmd"), b"launcher")
                self.assertEqual(archive.read("Run Native Level Check.cmd"), b"native check launcher")
                self.assertEqual(archive.read("tools/compile-native-level.py"), b"compiler wrapper")
                self.assertEqual(archive.read("base/materials/renderer-smoke.mtr"), b"material")
                self.assertEqual(archive.read("base/textures/renderer_smoke_white.tga"), b"texture")
                for extension in ("map", "proc", "cm", "aas48"):
                    name = f"base/maps/level.{extension}"
                    self.assertEqual(archive.read(name), inputs[f"build/native-level/{name}"])
                self.assertEqual(archive.read("base/materials/cloud_room.mtr"), b"native room material")
                self.assertEqual(archive.read("base/def/navigation.def"), b"navigation definition")
                self.assertEqual(archive.read("P02-LEVEL-MANIFEST.json"), b"level manifest")
                self.assertEqual(archive.read("TEST-CARD.md"), b"PC test card")
            (root / "base/renderprogs2/dxil/synthetic.bin").unlink()
            with self.assertRaisesRegex(ValueError, "DXIL"):
                PACKAGE.collect(root, build)

    def test_reject_non_windows_binary(self):
        self.assertFalse(PACKAGE.pe_x64(b"\x7fELF"))
        self.assertFalse(PACKAGE.pe_x64(b"MZ" + bytes(62)))


class MapCompilerTests(unittest.TestCase):
    def setUp(self):
        if RBDMAP is None:
            self.skipTest("supply --rbdmap to exercise the compiled tool")
        temporary = tempfile.TemporaryDirectory(prefix="rtcwnextgen-dmap-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "author room.map"
        self.assets = self.root / "author assets"
        self.output = self.root / "native level"
        fixtures = ROOT / "tests/fixtures"
        shutil.copyfile(fixtures / "cloud_room.map", self.source)
        shutil.copytree(fixtures / "native-level", self.assets)
        (self.assets / "textures").mkdir()
        shutil.copyfile(fixtures / "renderer_smoke_white.tga", self.assets / "textures/renderer_smoke_white.tga")

    def run_compiler(self, aas=None):
        command = [sys.executable, "-B", str(ROOT / "scripts/compile-native-level.py"), str(self.source),
                   "--rbdmap", str(RBDMAP), "--assets", str(self.assets), "--out", str(self.output)]
        if aas is not None:
            command.extend(("--aas", aas))
        return subprocess.run(
            command, cwd=self.root, capture_output=True, text=True, errors="replace", timeout=60,
        )

    def test_compiles_geometry_collision_and_navigation_without_changing_input(self):
        original = self.source.read_bytes()
        result = self.run_compiler("aas48")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        maps = self.output / "base/maps"
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual((maps / "level.map").read_bytes(), original)
        proc = (maps / "level.proc").read_bytes()
        self.assertIn(b"_area0", proc)
        self.assertIn(b"textures/test/cloud_room_panel", proc)
        self.assertTrue((maps / "level.cm").read_bytes().startswith(b'CM "1.00"'))
        self.assertTrue((maps / "level.aas48").read_bytes().startswith(b'DewmAAS "1.07"'))
        manifest = json.loads((self.output / "level-build.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["map"], "maps/level")
        for name, digest in manifest["sha256"].items():
            self.assertEqual(hashlib.sha256((self.output / name).read_bytes()).hexdigest(), digest)
        result = self.run_compiler("aas48")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Output already exists", result.stderr)

    def test_missing_navigation_output_is_a_failure(self):
        result = self.run_compiler("aas_missing")
        self.assertEqual(result.returncode, 1)
        self.assertIn("rbdmap did not produce level.aas_missing", result.stderr)
        self.assertFalse(self.output.exists())

    def test_valve220_compiles_the_authored_room_at_the_expected_scale(self):
        shutil.copyfile(ROOT / "tests/fixtures/cloud_room_valve220.map", self.source)
        result = self.run_compiler()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        proc = (self.output / "base/maps/level.proc").read_bytes()
        vertices = [record.split() for record in re.findall(rb"\(([^()]*)\)", proc)]
        corners = {tuple(float(value) for value in record[:3]) for record in vertices if len(record) == 8}
        expected = {(x, y, z) for x in (-128, 128) for y in (-128, 128) for z in (0, 128)}
        self.assertEqual(corners, expected)
        self.assertIn(b"textures/test/cloud_room_panel", proc)
        self.assertFalse((self.output / "base/maps/level.aas48").exists())


class BspMetadataTests(unittest.TestCase):
    @staticmethod
    def make_fixture(*lumps, magic=b"IBSP", version=47, payload=b"synthetic fixture"):
        ranges = list(lumps) + [(0, 0)] * (17 - len(lumps))
        return struct.pack("<4si34i", magic, version, *(value for pair in ranges for value in pair)) + payload

    def make_surface_fixture(self, vertices, indices, surfaces):
        sections = {
            10: bytes(44 * vertices),
            11: struct.pack(f"<{len(indices)}i", *indices),
            13: b"".join(struct.pack("<12x4i76x", *surface) for surface in surfaces),
        }
        ranges = [(0, 0)] * 17
        payload = bytearray()
        for number, section in sections.items():
            ranges[number] = (144 + len(payload), len(section))
            payload.extend(section)
        return self.make_fixture(*ranges, payload=bytes(payload))

    def test_reads_only_the_header(self):
        fixture = self.make_fixture((216, 4), (144, 72), payload=bytes(76))
        stream = io.BytesIO(fixture)
        info = ibsp_metadata.read_header(stream, len(fixture))
        self.assertEqual(stream.tell(), 144)
        self.assertEqual((info["format"], info["version"], info["size"]), ("IBSP", 47, len(fixture)))
        self.assertEqual(len(info["lumps"]), 17)
        self.assertEqual(info["lumps"]["entities"], {"offset": 216, "size": 4})
        self.assertEqual(info["lumps"]["shaders"], {"offset": 144, "size": 72, "records": 1})
        self.assertEqual(info["lumps"]["visibility"], {"offset": 0, "size": 0})

    def test_reports_truncated_headers_and_unsupported_formats(self):
        for data, message in (
            (b"IBSP", "Truncated IBSP header"),
            (self.make_fixture(magic=b"XBSP"), "Expected an IBSP signature"),
            (self.make_fixture(version=46), "Unsupported IBSP version 46"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                ibsp_metadata.read_header(io.BytesIO(data), len(data))

    def test_rejects_invalid_lump_ranges(self):
        for ranges, message in (
            (((144, -2),), "entities falls outside the file"),
            (((-1, 2),), "entities falls outside the file"),
            (((144, 400),), "entities falls outside the file"),
            (((400, 0),), "entities falls outside the file"),
            (((142, 2),), "entities overlaps the header"),
            (((144, 2), (144, 72)), "shaders overlaps another lump"),
            (((144, 2), (148, 2)), "shaders is not a whole number of 72-byte records"),
        ):
            with self.subTest(ranges=ranges), self.assertRaisesRegex(ValueError, message):
                data = self.make_fixture(*ranges, payload=bytes(72))
                ibsp_metadata.read_header(io.BytesIO(data), len(data))

    def test_cli_resolves_archives_then_loose_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            main = Path(temporary) / "Main"
            maps = main / "Maps"
            maps.mkdir(parents=True)
            loose = maps / "fixture.bsp"
            loose.write_bytes(self.make_fixture((144, 3)))
            with zipfile.ZipFile(main / "z_other.pk3", "w") as archive:
                archive.writestr("maps/fixture.bsp", self.make_fixture((144, 4)))
            priority_pack = main / "sp_pak3.pk3"
            with zipfile.ZipFile(priority_pack, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("MAPS/FIXTURE.BSP", self.make_fixture((144, 5)))
                archive.writestr("maps/invalid.bsp", b"IBSP")

            command = [sys.executable, "-B", str(ROOT / "scripts/rtcw_data.py"), str(main), "--bsp-info"]
            result = subprocess.run([*command, "maps/fixture.bsp"], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["source"], "sp_pak3.pk3:MAPS/FIXTURE.BSP")
            self.assertEqual(report["lumps"]["entities"]["size"], 5)

            result = subprocess.run([*command, "maps/invalid.bsp"], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 1)
            self.assertIn("sp_pak3.pk3:maps/invalid.bsp: Truncated IBSP header", result.stderr)
            self.assertFalse(result.stdout)

            priority_pack.unlink()
            (main / "z_other.pk3").unlink()
            result = subprocess.run([*command, "maps/fixture.bsp"], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(Path(report["source"]), loose.resolve())
            self.assertEqual(report["lumps"]["entities"]["size"], 3)

    def test_local_surface_reference_check(self):
        fixture = self.make_surface_fixture(6, [0, 1, 2, 2, 1, 0], [(0, 3, 0, 3), (3, 3, 3, 3)])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "two surfaces.bsp"
            path.write_bytes(fixture)
            command = [sys.executable, "-B", str(ROOT / "scripts/ibsp_metadata.py"), str(path)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["checked_surfaces"], 2)
            self.assertEqual(path.read_bytes(), fixture)

    def test_local_surface_reference_check_reports_invalid_references(self):
        for surface, indices, message in (
            ((2, 3, 0, 3), [0, 1, 2], "vertex range falls outside"),
            ((0, 3, 2, 3), [0, 1, 2], "index range falls outside"),
            ((0, 3, 0, 3), [0, 1, 3], "index outside its vertex range"),
            ((0, 3, 0, 3), [0, -1, 1], "index outside its vertex range"),
        ):
            with self.subTest(surface=surface, indices=indices), self.assertRaisesRegex(ValueError, message):
                fixture = self.make_surface_fixture(3, indices, [surface])
                stream = io.BytesIO(fixture)
                metadata = ibsp_metadata.read_header(stream, len(fixture))
                ibsp_metadata.check_surface_references(stream, metadata["lumps"])


class RTCWDataTests(unittest.TestCase):
    def test_state_directory_is_separate_and_not_created(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installation = root / "Installed Game"
            main = installation / "mAiN"
            main.mkdir(parents=True)
            state = root / "Player Data" / "state"

            self.assertEqual(rtcw_data.check_state_directory(main, state), state.resolve())
            self.assertFalse(state.parent.exists())
            for overlap in (root, installation, installation / "cache", main, main / "saves"):
                with self.subTest(overlap=overlap), self.assertRaisesRegex(ValueError, "overlaps"):
                    rtcw_data.check_state_directory(installation, overlap)

            ordinary_file = root / "file"
            ordinary_file.write_text("fixture", encoding="ascii")
            for path in (ordinary_file, ordinary_file / "state"):
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, "passes through a file"):
                    rtcw_data.check_state_directory(installation, path)

    def test_state_directory_resolves_directory_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installation = root / "installation"
            installation.mkdir()
            content = root / "relocated Main"
            content.mkdir()
            alias = root / "alias"
            try:
                (installation / "Main").symlink_to(content, target_is_directory=True)
                alias.symlink_to(installation, target_is_directory=True)
            except OSError as error:
                if getattr(error, "winerror", None) == 1314:
                    self.skipTest("Windows runner lacks permission to create directory symlinks")
                raise

            for overlap in (alias / "cache", content / "saves"):
                with self.subTest(overlap=overlap), self.assertRaisesRegex(ValueError, "overlaps"):
                    rtcw_data.check_state_directory(installation, overlap)

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
