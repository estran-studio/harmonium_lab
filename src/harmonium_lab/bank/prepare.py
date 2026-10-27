"""Manifeste de synthèse numpy → WAV PCM16 vérifiés, sans réseau.

Les empreintes portent sur les WAV préparés. `--inventory` est la seule
opération qui actualise les empreintes et fenêtres de boucle versionnées.
Une construction normale resynthétise et vérifie chaque entrée : modifier une
recette ne peut pas être masqué par un ancien cache.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from . import SAMPLE_RATE, resolve_bank_dir
from .synth import synthesize_entry


def sha256_of(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_manifest(root: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines()
            if line.strip()]
    ids = set()
    for row in rows:
        for field in ("id", "source", "author", "license", "preset", "root_key"):
            if field not in row or row[field] in (None, ""):
                raise ValueError(f"{row.get('id', '?')} : champ {field} requis")
        if row["id"] in ids or Path(row["id"]).name != row["id"]:
            raise ValueError(f"identifiant en double ou invalide : {row['id']}")
        ids.add(row["id"])
    return rows


def prepare(root: Path, *, inventory: bool = False) -> list[dict[str, Any]]:
    rows = read_manifest(root)
    prepared = root / "prepared"
    prepared.mkdir(parents=True, exist_ok=True)
    for row in rows:
        audio, start, end = synthesize_entry(row)
        if not np.all(np.isfinite(audio)):
            raise ValueError(f"{row['id']} : signal non fini")
        pcm = np.rint(np.clip(audio, -1, 1) * 32767).astype("<i2")
        path = prepared / f"{row['id']}.wav"
        sf.write(path, pcm, SAMPLE_RATE, subtype="PCM_16")
        digest = sha256_of(path)
        window = [start, end]
        if inventory:
            row.update(sha256=digest, bytes=path.stat().st_size,
                       loop_window=window, duration_s=len(audio) / SAMPLE_RATE)
        elif digest != row.get("sha256") or window != row.get("loop_window"):
            raise ValueError(f"{row['id']} : empreinte ou boucle différente du manifeste "
                             "(inventaire explicite requis)")
        print(f"{row['id']} : {digest}")
    if inventory:
        (root / "manifest.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inventory", action="store_true")
    args = parser.parse_args()
    prepare(resolve_bank_dir(args.root), inventory=args.inventory)


if __name__ == "__main__":
    main()
