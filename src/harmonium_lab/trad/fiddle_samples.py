"""Banques du comparatif : cache privé, empreintes et inventaire SF2/phdr."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

from .download import Fetcher


def presets(path: Path) -> list[dict]:
    """Lit le chunk phdr sans charger les échantillons ; indices MIDI zéro-based."""
    with path.open("rb") as stream:
        header = stream.read(12)
        if len(header) != 12 or header[:4] != b"RIFF" or header[8:] != b"sfbk":
            raise ValueError(f"SF2 RIFF/sfbk invalide : {path}")
        end = struct.unpack_from("<I", header, 4)[0] + 8

        def chunks(stop: int) -> list[dict] | None:
            while stream.tell() + 8 <= stop:
                tag, size = struct.unpack("<4sI", stream.read(8))
                start = stream.tell()
                if start + size > stop:
                    raise ValueError("chunk SF2 tronqué")
                if tag == b"LIST":
                    kind = stream.read(4)
                    if kind == b"pdta":
                        found = chunks(start + size)
                        if found is not None:
                            return found
                elif tag == b"phdr":
                    if size % 38 or size < 38:
                        raise ValueError("phdr invalide")
                    rows = []
                    for _ in range(size // 38 - 1):
                        name, program, bank, *_ = struct.unpack("<20sHHHIII", stream.read(38))
                        rows.append({"name": name.split(b"\0")[0].decode("latin1"),
                                     "bank": bank, "program": program})
                    return rows
                stream.seek(start + size + size % 2)
            return None

        result = chunks(end)
        if result is None:
            raise ValueError("phdr absent")
        return result


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def acquire(rows: list[dict], raw: Path, *, offline: bool = False,
            inventory: bool = False, fetcher: Fetcher | None = None) -> list[dict]:
    fetcher = fetcher or Fetcher(offline=offline)
    raw.mkdir(parents=True, exist_ok=True)
    for row in rows:
        if row["status"] != "accepted" or row.get("build"):
            continue
        dest = raw / (row["id"] + ".sf2")
        if not dest.exists():
            download = raw / (row["id"] + ".zip") if row.get("member") else dest
            fetcher.get(row["url"], download)
            if row.get("member"):
                with zipfile.ZipFile(download) as archive:
                    with archive.open(row["member"]) as source, dest.open("wb") as target:
                        import shutil
                        shutil.copyfileobj(source, target)
        actual = digest(dest)
        if row.get("sha256") and actual != row["sha256"]:
            raise ValueError(f"empreinte différente : {dest}")
        available = presets(dest)
        chosen = row["selected"]
        if not any(p["bank"] == chosen["bank"] and p["program"] == chosen["program"] for p in available):
            raise ValueError(f"preset choisi absent : {row['id']}")
        if inventory:
            row.update(sha256=actual, size_bytes=dest.stat().st_size,
                       violin_presets=[p for p in available if "violin" in p["name"].lower()
                                       or "fiddle" in p["name"].lower()])
        elif not row.get("sha256"):
            raise ValueError(f"empreinte absente : {row['id']} (inventaire requis)")
        print(f"{row['id']}: {dest.stat().st_size} octets ; SHA256 {actual}", flush=True)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("samples/fiddles/manifest.jsonl"))
    parser.add_argument("--raw", type=Path, default=Path("samples/fiddles/raw"))
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--inventory", action="store_true", help="actualise tailles, empreintes et phdr")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.manifest.read_text().splitlines() if line.strip()]
    acquire(rows, args.raw, offline=args.offline, inventory=args.inventory)
    if args.inventory:
        args.manifest.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


if __name__ == "__main__":
    main()
