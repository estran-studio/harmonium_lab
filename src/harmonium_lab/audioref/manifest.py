"""Lecture et filtrage d'un manifeste de pistes audio (JSONL)."""

from __future__ import annotations

import json
from pathlib import Path


def load_manifest(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_filters(pairs: list[str] | None) -> dict[str, str]:
    """`["zone=desert", "type=zone"]` → `{"zone": "desert", "type": "zone"}`."""
    out: dict[str, str] = {}
    for pair in pairs or []:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise ValueError(f"filtre invalide « {pair} » : attendu champ=valeur")
        out[key] = value
    return out


def select(rows: list[dict], filters: dict[str, str]) -> list[dict]:
    """Lignes dont chaque champ filtré vaut la valeur donnée (comparaison texte)."""
    return [r for r in rows if all(str(r.get(k)) == v for k, v in filters.items())]


def track_path(row: dict, root: Path) -> Path:
    path = root / row["file"]
    if not path.is_file():
        raise FileNotFoundError(f"piste absente : {path}")
    return path
