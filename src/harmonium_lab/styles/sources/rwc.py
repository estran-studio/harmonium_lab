"""RWC-MDB (archive du site AIST, Zenodo CC BY-NC-SA) : MIDI multipistes étiquetés.

ZIP externe (`RWC-website.zip`, SHA256 épinglé) ; trois ZIP internes SMF de 1,6 / 0,7 / 1,3 Mo.
`RM-G001..100` : 33 sous-genres, exactement trois morceaux par genre selon la table primaire
`website/rwc-mdb-g.html` ; mappings `G_STYLES` ci-dessous. Les Jazz 50 et Popular 100 ne sont pas
étiquetés à ce niveau fin : jazz = swing/ballade/valse **uniquement si mètre, tempo et feel**,
popular = pop large. Séquence MIDI de studio, pas prises multipistes jouées en direct.
Le site original exige un Pledge recherche non redistribuable, tandis que Zenodo indique
CC BY-NC-SA : seuls agrégats internes sont versionnés, aucune note ni titre.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Iterator

from ..core import Piece, detect_feel, meter_of, monophonic_bass, read_midi
from .lmd import BASS_PROGRAMS, GUITAR_PROGRAMS, KEYS_PROGRAMS, _polyphony

G_STYLES: dict[str, tuple[int, ...]] = {
    "pop": (1, 2, 3),
    "rock": (7, 8, 9),
    "funk": (22, 23, 24),
    "soul": (25, 26, 27),
    "swing": (28, 29, 30, 31, 32, 33),
    "bossa": (37, 38, 39),
    "samba": (40, 41, 42),
    "reggae": (43, 44, 45),
    "blues_shuffle": (64, 65, 66),
}


def _style(
    group: str, id_: int, meter: tuple[float, bool], bpm: float | None, feel: str
) -> str | None:
    if group == "G":
        for style, nums in G_STYLES.items():
            if id_ in nums:
                if style == "blues_shuffle" and feel != "ternary":
                    return None
                return style
        return None
    if group == "J":
        if meter == (3.0, False):
            return "jazz_waltz"
        if meter == (4.0, False) and bpm is not None:
            return "ballad" if bpm < 80 else "swing" if feel == "ternary" else None
        return None
    if group == "P" and meter == (4.0, False):
        return "pop"
    return None


def pieces(archive: Path) -> Iterator[Piece]:
    with zipfile.ZipFile(archive) as outer:
        for group in ("G", "J", "PR"):
            inner_path = f"website/SMF/{group}/RWC-MDB-{group}-2001.SMF.zip"
            with zipfile.ZipFile(io.BytesIO(outer.read(inner_path))) as inner:
                for name in sorted(inner.namelist()):
                    m = re.search(r"RM-([GJPR])(\d{3})\.MID$", name)
                    if not m:
                        continue
                    kind, id_ = m.group(1), int(m.group(2))
                    if kind == "R":  # libre de droits mais sans genre précis
                        continue
                    if kind == "G" and not any(id_ in v for v in G_STYLES.values()):
                        continue
                    try:
                        mid = read_midi(inner.read(name))
                    except Exception:  # noqa: BLE001 — MIDI corrompu : écarté
                        continue
                    meter = meter_of(mid)
                    if meter is None or mid.signature_changes:
                        continue
                    drums = [n for t in mid.tracks if t.is_drums for n in t.notes]
                    bass_tracks = [
                        t
                        for t in mid.tracks
                        if not t.is_drums
                        and (
                            t.program in BASS_PROGRAMS
                            or re.search(r"\bbass\b", t.name, re.I)
                        )
                    ]
                    bass_track = max(
                        bass_tracks, key=lambda t: len(t.notes), default=None
                    )
                    bass = monophonic_bass(bass_track.notes) if bass_track else []
                    comps = []
                    for t in mid.tracks:
                        if (
                            t.is_drums
                            or t is bass_track
                            or t.program is None
                            or re.search(r"drum|melody|melo|lead|solo", t.name, re.I)
                        ):
                            continue
                        kind_comp = (
                            "guitar"
                            if t.program in GUITAR_PROGRAMS
                            else ("keys" if t.program in KEYS_PROGRAMS else None)
                        )
                        if kind_comp is None:
                            continue
                        poly, n_att = _polyphony(t.notes)
                        if n_att > 24 and poly >= 0.12:
                            comps.append((poly * n_att, kind_comp, t.notes))
                    comp, kind_comp = [], "comp"
                    if comps:
                        _, kind_comp, comp = max(comps, key=lambda x: x[0])
                    onsets = [
                        n.on for n in drums if n.pitch in (42, 44, 46, 51, 53, 59)
                    ] or [n.on for n in comp]
                    feel, _ = detect_feel(onsets)
                    style = _style(kind, id_, meter, mid.bpm, feel)
                    if style is None:
                        continue
                    yield Piece(
                        source="rwc",
                        pid=f"{kind}{id_:03d}",
                        styles=[style],
                        bpm=mid.bpm,
                        beats_per_bar=meter[0],
                        compound=meter[1],
                        bass=bass if len(bass) >= 32 else [],
                        comp=comp if len(comp) >= 32 else [],
                        comp_kind=kind_comp,
                        drums=drums if len(drums) >= 32 else [],
                        performer=None,
                        quantized=True,
                        feel=feel,
                        notes={
                            "rwc_category": kind,
                            "rwc_genre_table": "website/rwc-mdb-g.html",
                        },
                    )
