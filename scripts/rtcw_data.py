"""Inspect the single-player archives in a local RTCW installation."""

import argparse
from pathlib import Path
import sys
import zipfile

REQUIRED = ("pak0.pk3", "sp_pak1.pk3", "sp_pak2.pk3", "sp_pak3.pk3")
FIRST_MAP = "maps/escape1.bsp"


def find_main(installation):
    installation = installation.absolute()
    if installation.name.casefold() == "main" and installation.is_dir():
        return installation
    if not installation.is_dir():
        raise ValueError(f"Installation directory does not exist: {installation}")
    matches = [path for path in installation.iterdir() if path.name.casefold() == "main" and path.is_dir()]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one Main directory in {installation}, found {len(matches)}")
    return matches[0]


def check_state_directory(installation, state_directory):
    """Check a proposed save/cache root without creating or writing to it."""
    main = find_main(installation)
    installation_root = main.parent.resolve(strict=True)
    content_root = main.resolve(strict=True)
    try:
        state = state_directory.resolve()
    except RuntimeError as error:
        raise ValueError(f"Cannot resolve the state directory: {state_directory}") from error

    for source in (installation_root, content_root):
        if state.is_relative_to(source) or source.is_relative_to(state):
            raise ValueError(f"State directory overlaps the installation: {state} and {source}")

    for parent in (state, *state.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError(f"State directory passes through a file: {parent}")
            break
    return state


def inspect(installation):
    main = find_main(installation)
    entries = list(main.iterdir())
    messages = []
    ready = True
    map_archives = []
    for name in REQUIRED:
        matches = [entry for entry in entries if entry.name.casefold() == name]
        if len(matches) != 1 or not matches[0].is_file():
            diagnosis = "ambiguous filename" if len(matches) > 1 else "missing file"
            messages.append(f"{name}: {diagnosis}")
            ready = False
            continue
        try:
            with zipfile.ZipFile(matches[0], "r") as archive:
                files = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
        except (OSError, UnicodeError, zipfile.BadZipFile) as error:
            messages.append(f"{name}: cannot read PK3 directory ({error})")
            ready = False
            continue
        if not files:
            messages.append(f"{name}: no file entries")
            ready = False
            continue
        if any(path.casefold() == FIRST_MAP for path in files):
            map_archives.append(name)
        messages.append(f"{name}: {len(files)} file entries")

    if map_archives:
        messages.append(f"{FIRST_MAP}: present in {', '.join(map_archives)}")
    else:
        messages.append(f"{FIRST_MAP}: absent from the inspected archives")
        ready = False
    return messages, ready


def locate_resource(installation, resource):
    """Find the winning PK3 member or loose file in one offline Main directory."""
    parts = resource.replace("\\", "/").split("/")
    if any(part in ("", ".", "..") or ":" in part or "\0" in part for part in parts):
        raise ValueError("Expected a relative resource path inside Main")
    parts = [part.casefold() for part in parts]
    key = "/".join(parts)
    main = find_main(installation).resolve()

    packs = {}
    for path in main.iterdir():
        name = path.name.casefold()
        if name.startswith("mp_") or path.suffix.casefold() != ".pk3" or not path.is_file():
            continue
        if not path.resolve().is_relative_to(main):
            continue
        if name in packs:
            raise ValueError(f"Ambiguous PK3 filename: {path.name}")
        packs[name] = path

    # RTCW single-player sorts sp_* as zz_* and searches higher-sorted packs first.
    ordered = sorted(
        packs, key=lambda name: ("zz" + name[2:] if name.startswith("sp_") else name, name), reverse=True
    )
    for name in ordered:
        path = packs[name]
        try:
            with zipfile.ZipFile(path, "r") as archive:
                for entry in reversed(archive.infolist()):
                    if not entry.is_dir() and entry.filename.replace("\\", "/").casefold() == key:
                        return path, entry.filename
        except (UnicodeError, zipfile.BadZipFile) as error:
            raise ValueError(f"{path.name}: cannot read PK3 directory ({error})") from error

    loose = main
    for part in parts:
        if not loose.is_dir():
            return None
        matches = [child for child in loose.iterdir() if child.name.casefold() == part]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous loose file path: {resource}")
        if not matches or not matches[0].resolve().is_relative_to(main):
            return None
        loose = matches[0]
    return (loose, None) if loose.is_file() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path, help="installation root or its Main directory")
    checks = parser.add_mutually_exclusive_group()
    checks.add_argument("--locate", metavar="RESOURCE", help="report the source of a resource inside Main")
    checks.add_argument("--state-dir", type=Path, metavar="DIRECTORY", help="check a separate save/cache directory")
    args = parser.parse_args()
    try:
        if args.locate is not None:
            located = locate_resource(args.installation, args.locate)
            if located is None:
                print(f"{args.locate}: resource not found", file=sys.stderr)
                return 1
            path, entry = located
            print(f"{path.name}:{entry}" if entry is not None else str(path))
            return 0
        state = None
        if args.state_dir is not None:
            state = check_state_directory(args.installation, args.state_dir)
        messages, ready = inspect(args.installation)
        if state is not None:
            messages.append(f"Separate save/cache directory: {state}")
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print("\n".join(messages))
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
