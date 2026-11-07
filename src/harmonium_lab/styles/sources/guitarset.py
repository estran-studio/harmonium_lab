"""GuitarSet (CC BY 4.0) : comping de guitare, JAMS (notes par corde, temps et accords annotés).

Les 360 extraits sont 180 `comp` (accompagnement) et 180 `solo` ; on ne lit que `comp`. Style par
nom de fichier : `BN` bossa nova, `Funk`, `Jazz`, `Rock`, `SS` singer-songwriter. Les temps annotés
(`beat_position`) fixent les coordonnées : l'attaque est placée à la fraction de temps annotée, donc
l'écart à la grille (micro-timing de la guitare) vaut l'écart au battement annoté.
"""

from __future__ import annotations

import bisect
import json
import re
import zipfile
from pathlib import Path
from typing import Iterator

from ..core import ChordSpan, Note, Piece
from ..harmony import parse_harte

NAME = re.compile(
    r"^(?P<player>\d\d)_(?P<style>BN|Funk|Jazz|Rock|SS)(?P<prog>\d)-(?P<bpm>\d+)-(?P<key>[A-G][#b]?)_(?P<kind>comp|solo)\.jams$"
)
STYLE_OF = {
    "BN": "bossa",
    "Funk": "funk",
    "Jazz": "jazz",
    "Rock": "rock",
    "SS": "singer_songwriter",
}


def beat_map(annotation: list[dict]) -> tuple[list[float], list[int]]:
    times = [row["time"] for row in annotation]
    return times, [row["value"]["num_beats"] for row in annotation]


def to_beats(t: float, times: list[float]) -> float:
    """Instant (s) → coordonnée en temps de noire, interpolation linéaire entre battements annotés."""
    if len(times) < 2:
        return 0.0
    i = bisect.bisect_right(times, t) - 1
    i = max(0, min(i, len(times) - 2))
    span = times[i + 1] - times[i]
    return i + (t - times[i]) / span if span > 0 else float(i)


def pieces(archive: Path) -> Iterator[Piece]:
    with zipfile.ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            m = NAME.match(name)
            if not m or m["kind"] != "comp":
                continue
            doc = json.loads(z.read(name))
            ann = {}
            for a in doc["annotations"]:
                ns = a["namespace"]
                if ns == "note_midi":
                    ann.setdefault("notes", []).extend(
                        a["data"] if isinstance(a["data"], list) else []
                    )
                elif ns == "beat_position":
                    ann["beats"] = a["data"]
                elif ns == "chord" and "chords" not in ann:
                    ann["chords"] = a["data"]
                elif ns == "tempo":
                    ann["tempo"] = a["data"][0]["value"] if a["data"] else None
            beats = ann.get("beats") or []
            if len(beats) < 8:
                continue
            times, nums = beat_map(beats)
            nb = beats[0]["value"]["num_beats"]
            notes = []
            for n in sorted(ann.get("notes", []), key=lambda r: r["time"]):
                on = to_beats(n["time"], times)
                dur = to_beats(n["time"] + n["duration"], times) - on
                notes.append(Note(on, dur, int(round(n["value"])), None))
            spans = []
            for c in ann.get("chords", []):
                chord = parse_harte(c["value"])
                if chord is not None:
                    spans.append(
                        ChordSpan(
                            to_beats(c["time"], times),
                            to_beats(c["time"] + c["duration"], times),
                            chord,
                        )
                    )
            piece = Piece(
                source="guitarset",
                pid=name[:-5],
                styles=[STYLE_OF[m["style"]]],
                bpm=float(m["bpm"]),
                beats_per_bar=float(nb),
                comp=notes,
                comp_kind="guitar",
                chords=spans or None,
                performer=f"guitarist{m['player']}",
                quantized=False,
                notes={"progression": m["prog"], "key": m["key"]},
            )
            yield piece
