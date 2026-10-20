"""Téléchargement idempotent des échantillons de pieds (chantier SK1).

Lit `samples/feet/manifest.jsonl` (versionné : url, licence, auteur,
sha256, rôle) et remplit `samples/feet/raw/` (gitignoré). Les fichiers
déjà présents avec la bonne empreinte sont sautés ; toute empreinte
fausse provoque un nouveau téléchargement puis une erreur explicite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from harmonium_lab.feet import feet_dir
from harmonium_lab.trad.download import Fetcher


def read_manifest(root: Path) -> list[dict]:
    manifest = root / "manifest.jsonl"
    if not manifest.is_file():
        raise RuntimeError(f"manifeste introuvable ({manifest})")
    return [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(root: Path, delay: float = 0.3, offline: bool = False) -> tuple[int, int]:
    """Télécharge les manquants. Retourne (téléchargés, déjà en cache)."""
    entries = read_manifest(root)
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher(delay_s=delay, offline=offline)
    done, cached = 0, 0
    for e in entries:
        dest = raw / f"{e['id']}.mp3"
        if dest.is_file() and sha256_of(dest) == e["sha256"]:
            cached += 1
            continue
        if dest.is_file():
            dest.unlink()  # empreinte fausse : on retélécharge
        fetcher.get(e["url"], dest)
        digest = sha256_of(dest)
        if digest != e["sha256"]:
            dest.unlink(missing_ok=True)
            raise RuntimeError(
                f"{e['id']} : empreinte {digest} ≠ manifeste {e['sha256']} "
                f"(source {e['url']})")
        done += 1
    return done, cached


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="feet-fetch",
                                 description="Télécharge les échantillons de pieds (manifest.jsonl → raw/)")
    ap.add_argument("--root", type=Path, default=feet_dir(), help="dossier samples/feet")
    ap.add_argument("--delay", type=float, default=0.3, help="secondes entre requêtes")
    ap.add_argument("--offline", action="store_true", help="n'utilise que le cache raw/")
    args = ap.parse_args(argv)
    try:
        done, cached = fetch(args.root, args.delay, args.offline)
    except RuntimeError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    print(f"pieds : {done} téléchargés, {cached} déjà en cache ({args.root / 'raw'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
