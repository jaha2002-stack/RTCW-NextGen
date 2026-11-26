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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path, help="installation root or its Main directory")
    args = parser.parse_args()
    try:
        messages, ready = inspect(args.installation)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print("\n".join(messages))
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
