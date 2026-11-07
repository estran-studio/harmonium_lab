"""FiloBass (CC BY 4.0) : 48 lignes de basse jazz transcrites (notes, accords, mesures).

Lecture de `notebooks_and_scripts/note_data.csv` (une ligne par note ou silence : hauteur MIDI,
position globale et durée en temps de noire, accord, mesure). Positions de la **partition** : ni
micro-timing ni vélocité (`quantized`), mais hauteurs, rythmes et accords vérifiés. Tempo : les
`syncpoints/<titre>.json` donnent un point par **mesure** (instant en secondes du début de mesure
dans l'enregistrement) : tempo = 4 × 60 / écart médian. Aucun titre n'est étiqueté par style : tous
les morceaux sont en 4/4 à 100–236 BPM, donc `swing` (aucune ballade lente ni valse).
"""

from __future__ import annotations

import csv
import io
import json
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

from fractions import Fraction

from ...backing.chords import from_engine, note_pc
from ..core import ChordSpan, Note, Piece

ROOT = "FiloBass ISMIR Publication/"


def tempo_of(z: zipfile.ZipFile, title: str) -> float | None:
    try:
        sync = json.loads(z.read(f"{ROOT}syncpoints/{title}.json"))
    except KeyError:
        return None
    gaps = [b[1] - a[1] for a, b in zip(sync, sync[1:]) if b[1] > a[1]]
    return 240.0 / statistics.median(gaps) if gaps else None


def pc_of(name: str) -> int:
    """Nom music21 (`B-` = si bémol, `F#`) → classe de hauteur."""
    return note_pc(name.replace("-", "b"))


def beats_of(text: str) -> float:
    return float(Fraction(text))


def chord_of(row: dict[str, str]):
    kind = {"minmaj7": "mMaj7", "maj7#11": "maj7#11"}.get(
        row["chord_kind"], row["chord_kind"]
    )
    root = pc_of(row["chord_root"])
    bass = pc_of(row["chord_bass"][1:]) if row["chord_bass"] else root
    try:
        return from_engine(root, bass, kind)
    except Exception:  # noqa: BLE001 — accord hors grammaire du moteur : compté, jamais deviné
        return None


def pieces(archive: Path) -> Iterator[Piece]:
    with zipfile.ZipFile(archive) as z:
        rows = list(
            csv.DictReader(
                io.TextIOWrapper(
                    z.open(f"{ROOT}notebooks_and_scripts/note_data.csv"),
                    encoding="utf-8",
                )
            )
        )
        by_title: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_title[row["title"]].append(row)
        for title, items in sorted(by_title.items()):
            notes, spans, seen = [], [], set()
            for row in items:
                if row["type"] == "Note" and row["note_midi"]:
                    notes.append(
                        Note(
                            beats_of(row["note_global_offset"]),
                            beats_of(row["note_duration"]),
                            int(float(row["note_midi"])),
                            None,
                        )
                    )
                if row["chord"] and row["chord_id"] not in seen:
                    seen.add(row["chord_id"])
                    chord = chord_of(row)
                    if chord is not None:
                        start = beats_of(row["chord_global_offset"])
                        spans.append(
                            ChordSpan(
                                start, start + beats_of(row["chord_duration"]), chord
                            )
                        )
            spans.sort(key=lambda s: s.start)
            notes.sort(key=lambda n: n.on)
            tempo = tempo_of(z, title)
            yield Piece(
                source="filobass",
                pid=title,
                styles=["swing"],
                bpm=tempo,
                beats_per_bar=4.0,
                bass=notes,
                chords=spans or None,
                performer=items[0]["player"],
                quantized=True,
                feel="ternary",
                notes={
                    "chord_symbols": "racine music21, type du CSV",
                    "timing": "partition",
                },
            )
