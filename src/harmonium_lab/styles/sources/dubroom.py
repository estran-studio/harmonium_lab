"""Dubroom Original Reggae MIDI Files (CC BY-NC-SA 4.0) : sections multipistes reggae/dub.

105 morceaux originaux d'un même collectif, partition MIDI séquencée : mesure de motifs et
voicings, **pas** de micro-timing humain. Style déduit de l'album « reggae/dub » (pas de sous-genre).
Le nom de piste (« Ska Gitaar », « Percussive Orgel », « Riddim ») complète le programme GM.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Iterator

from ..core import Piece, meter_of, monophonic_bass, read_midi
from .lmd import BASS_PROGRAMS, GUITAR_PROGRAMS, KEYS_PROGRAMS, _polyphony


def pieces(archive: Path) -> Iterator[Piece]:
    with zipfile.ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            if not name.lower().endswith(".mid"):
                continue
            try:
                mid = read_midi(z.read(name))
            except Exception:  # noqa: BLE001 — MIDI corrompu : ignorer
                continue
            meter = meter_of(mid)
            if meter is None or mid.signature_changes or meter[0] not in (4.0, 3.0):
                continue
            drums = [n for t in mid.tracks if t.is_drums for n in t.notes]
            bass_tracks = [
                t
                for t in mid.tracks
                if not t.is_drums
                and (
                    t.program in BASS_PROGRAMS
                    or re.search(r"\b(bass|bas|riddim)\b", t.name, re.I)
                )
            ]
            bass_track = max(bass_tracks, key=lambda t: len(t.notes), default=None)
            bass = monophonic_bass(bass_track.notes) if bass_track else []
            comps = []
            for t in mid.tracks:
                if t.is_drums or t is bass_track or t.program is None:
                    continue
                kind = (
                    "guitar"
                    if t.program in GUITAR_PROGRAMS
                    else ("keys" if t.program in KEYS_PROGRAMS else None)
                )
                if kind is None:
                    continue
                poly, n_att = _polyphony(t.notes)
                if n_att > 24 and (
                    poly >= 0.10
                    or (
                        re.search("ska|gitaar|orgel|piano", t.name, re.I)
                        and poly >= 0.03
                    )
                ):
                    comps.append((poly * n_att, kind, t.notes))
            comp, kind = [], "comp"
            if comps:
                _, kind, comp = max(comps, key=lambda x: x[0])
            if not (len(bass) > 32 and len(comp) > 32 and len(drums) > 32):
                continue
            yield Piece(
                source="dubroom",
                pid=name,
                styles=["reggae"],
                bpm=mid.bpm,
                beats_per_bar=meter[0],
                compound=meter[1],
                bass=bass,
                comp=comp,
                comp_kind=kind,
                drums=drums,
                performer="Dubroom/Messian Dread",
                quantized=True,
                notes={"tag": "original reggae/dub MIDI"},
            )
