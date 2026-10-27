"""Transcription de boucles depuis des stems séparés (hors dépôt).

Trois voies monophoniques génériques, quantifiées sur la grille :

- `pitch_notes` : basse ou lead (pyin) → notes MIDI + degrés ;
- `drum_hits` : attaques classées kick/snare/charleston par bandes ;
- `chords_per_bar` : accord (fondamentale + majeur/mineur) par mesure.

`write_loop_midi` exporte une boucle (plage de mesures) en MIDI avec un
programme General MIDI, plus un JSON d'accompagnement (minutage source,
degrés, confiance). Les MIDI transcrits restent hors dépôt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .grid import Grid

NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

#: Qualités d'accord reconnues (triades).
CHORD_QUALITIES: dict[str, tuple[int, ...]] = {
    "maj": (0, 4, 7), "min": (0, 3, 7),
}


def sixteenth_s(grid: Grid) -> float:
    """Durée d'une double-croche (sous-division de transcription)."""
    return grid.tatum_s / 2.0


def _pyin_notes(y: np.ndarray, sr: int, fmin: float, fmax: float,
                grid: Grid, min_len_16th: int = 1) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import librosa

    f0, voiced, _prob = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=sr)
    times = np.arange(len(f0)) * 512 / sr
    step = sixteenth_s(grid)
    t0 = grid.origin_s
    cells: list[int | None] = []
    n_cells = max(1, int(np.ceil((times[-1] - t0) / step)))
    for c in range(n_cells):
        m = (times >= t0 + c * step) & (times < t0 + (c + 1) * step) & voiced
        if m.sum() >= 2:
            fr = float(np.median(f0[m]))
            cells.append(int(round(69 + 12 * np.log2(fr / 440.0))))
        else:
            cells.append(None)
    cells = _smooth_octaves(cells)
    notes: list[dict[str, Any]] = []
    i = 0
    while i < len(cells):
        if cells[i] is None:
            i += 1
            continue
        j = i
        while j + 1 < len(cells) and cells[j + 1] == cells[i]:
            j += 1
        notes.append({"midi": cells[i], "start_16th": i, "len_16th": j - i + 1})
        i = j + 1
    info = {"voiced_ratio": round(float(voiced.mean()), 4),
            "n_notes": len(notes),
            "fmin": fmin, "fmax": fmax}
    _ = min_len_16th
    return notes, info


def _smooth_octaves(midis: list[int | None]) -> list[int | None]:
    """Replie les sauts d'octave (> 7 demi-tons) vers la hauteur précédente :
    pyin hésite entre fondamental et harmoniques sur les basses saturées."""
    out: list[int | None] = []
    prev: int | None = None
    for m in midis:
        if m is None or prev is None:
            out.append(m)
        else:
            while m - prev > 7:
                m -= 12
            while prev - m > 7:
                m += 12
            out.append(m)
        if m is not None:
            prev = m
    return out


def pitch_notes(y: np.ndarray, sr: int, grid: Grid, role: str = "bass",
                fmin: float = 25.0, fmax: float = 300.0) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Notes d'une voie monophonique (`role` : `bass` ou `lead`, gammes
    pyin adaptées par défaut)."""
    if role == "lead":
        fmin, fmax = max(fmin, 150.0), max(fmax, 1200.0)
    notes, info = _pyin_notes(y, sr, fmin, fmax, grid)
    info["role"] = role
    return notes, info


def drum_hits(y: np.ndarray, sr: int, grid: Grid,
              delta: float = 0.08) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attaques classées par bandes d'énergie : kick (sous-graves présents),
    snare (médiums), charleston (aigus seuls, sans corps grave/médium).

    Les stems séparés bavent (cymbales, clics) : la règle kick exige des
    sous-graves, la règle charleston l'absence de corps. Confiance d'un
    coup = marge entre les deux meilleures parts ; à valider à l'oreille.
    """
    import librosa

    env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=128)
    peaks = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=128,
                                       units="time", delta=delta, wait=4)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=128))
    fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
    ft = librosa.times_like(np.arange(S.shape[1]), sr=sr, hop_length=128)
    sub = S[fr < 80].sum(0)
    low = S[(fr >= 80) & (fr < 200)].sum(0)
    mid = S[(fr >= 200) & (fr < 5000)].sum(0)
    high = S[fr >= 5000].sum(0)
    step = sixteenth_s(grid)
    hits = []
    margins = []
    for t in peaks:
        k = int(np.argmin(np.abs(ft - t)))
        su, lo, mi, hi = (float(sub[k]), float(low[k]), float(mid[k]), float(high[k]))
        tot = su + lo + mi + hi + 1e-12
        body = (su + lo + mi) / tot  # tout sauf les aigus seuls
        if su / tot > 0.06 and (su + lo) / tot > 0.25:
            cls, margin = "kick", (su + lo) / tot - max(mi, hi) / tot
        elif mi / tot > 0.2 and body > 0.45:
            cls, margin = "snare", mi / tot - su / tot
        elif hi / tot > 0.5:
            cls, margin = "hat", hi / tot - body
        else:
            shares = {"kick": (su + lo) / tot, "snare": mi / tot, "hat": hi / tot}
            cls = max(shares, key=shares.get)
            ordered = sorted(shares.values(), reverse=True)
            margin = ordered[0] - ordered[1]
        margins.append(margin)
        pos = int(round((t - grid.origin_s) / step))
        if pos >= 0:
            hits.append({"class": cls, "pos_16th": pos,
                         "time_s": round(float(t), 3),
                         "confidence": round(margin, 3)})
    info = {"n_hits": len(hits),
            "mean_margin": round(float(np.mean(margins)), 3) if margins else 0.0,
            "low_margin_rate": round(float(np.mean([m < 0.15 for m in margins])), 3)
            if margins else 0.0}
    return hits, info


def chords_per_bar(y: np.ndarray, grid: Grid, sr: int = 22050) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Accord par mesure : meilleure triade (12 fondamentales × maj/min)
    sur le chroma moyen. `pedal_pc` : classe présente comme fondamentale
    ou dominante dans ≥ 3/4 des mesures (pédale probable)."""
    import librosa

    ch = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=512)
    times = librosa.times_like(np.arange(ch.shape[1]), sr=sr, hop_length=512)
    templ = {}
    for q, iv in CHORD_QUALITIES.items():
        t = np.full(12, 0.2)
        for i in iv:
            t[i] = 1.0
        templ[q] = t / np.linalg.norm(t)
    chords = []
    for b in range(grid.n_bars):
        t0 = grid.bar_start(b)
        m = (times >= t0) & (times < t0 + grid.bar_s)
        v = ch[:, m].mean(1) if m.any() else np.zeros(12)
        v = v / (np.linalg.norm(v) + 1e-12)
        scored = [(float(v @ np.roll(t, r)), r, q)
                  for r in range(12) for q, t in templ.items()]
        scored.sort(reverse=True)
        s, r, q = scored[0]
        chords.append({"bar": b, "root": NAMES[r], "quality": q,
                       "score": round(s, 3),
                       "start_s": round(t0, 3)})
    roots = [c["root"] for c in chords]
    pedal = max(set(roots), key=roots.count) if roots else None
    info = {"pedal_pc": pedal,
            "pedal_share": round(roots.count(pedal) / len(roots), 3) if roots else 0.0,
            "mean_score": round(float(np.mean([c["score"] for c in chords])), 3)
            if chords else 0.0}
    return chords, info


def to_degrees(midi: int, tonic_pc: int) -> dict[str, int]:
    """Degré chromatique depuis la tonique + octave (non-ambigu, sans mode)."""
    return {"semitones": (midi - tonic_pc) % 12, "octave": midi // 12 - 1}


def notes_to_degrees(notes: list[dict[str, Any]], tonic_pc: int) -> list[dict[str, Any]]:
    return [{**n, "name": f"{NAMES[n['midi'] % 12]}{n['midi'] // 12 - 1}",
             "degree": to_degrees(n["midi"], tonic_pc)} for n in notes]


def clip_notes(notes: list[dict[str, Any]], lo_16th: int, hi_16th: int) -> list[dict[str, Any]]:
    """Notes recadrées sur la fenêtre [lo_16th, hi_16th) (inclut les tenues)."""
    out = []
    for n in notes:
        s, e = max(n["start_16th"], lo_16th), min(n["start_16th"] + n["len_16th"], hi_16th)
        if e > s:
            out.append({"midi": n["midi"], "start_16th": s, "len_16th": e - s})
    return out

def write_loop_midi(parts: dict[str, tuple[list[dict[str, Any]], int]],
                    grid: Grid, path: Path, bars: tuple[int, int],
                    tempo_qpm: float | None = None) -> Path:
    """Écrit une boucle (mesures `bars`, fin exclue) : une piste MIDI par
    partie `(événements, programme GM)`. Événements : notes
    {midi, start_16th, len_16th} ou coups {class, pos_16th} (canal 10,
    kick=36/snare=38/hat=42)."""
    import pretty_midi

    start_bar, end_bar = bars
    step = sixteenth_s(grid)
    t0 = grid.bar_start(start_bar)
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo_qpm or grid.quarter_bpm)
    ts_num, ts_den = int(grid.meter.split("/")[0]), int(grid.meter.split("/")[1])
    for name, (events, program) in parts.items():
        if name == "drums":
            inst = pretty_midi.Instrument(program=0, is_drum=True, name=name)
            pitch_of = {"kick": 36, "snare": 38, "hat": 42}
            for e in events:
                if not (t0 <= grid.origin_s + e["pos_16th"] * step < grid.bar_start(end_bar)):
                    continue
                t = e["pos_16th"] * step + grid.origin_s - t0
                inst.notes.append(pretty_midi.Note(
                    velocity=100, pitch=pitch_of.get(e["class"], 38),
                    start=t, end=t + step * 0.9))
        else:
            inst = pretty_midi.Instrument(program=program, name=name)
            dur = (end_bar - start_bar) * grid.bar_s
            for e in events:
                s = e["start_16th"] * step + grid.origin_s - t0
                end = min(dur, s + e["len_16th"] * step)
                s = max(0.0, s)
                if end <= s:
                    continue
                inst.notes.append(pretty_midi.Note(
                    velocity=90, pitch=e["midi"], start=s, end=s + (end - s) * 0.95))
        pm.instruments.append(inst)
    pm.time_signature_changes.append(
        pretty_midi.TimeSignature(ts_num, ts_den, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(path))
    return path


def write_loop_sidecar(path: Path, track_id: str, bars: tuple[int, int],
                       grid: Grid, data: dict[str, Any]) -> Path:
    """JSON d'accompagnement : minutage source, degrés, confiance."""
    start_bar, end_bar = bars
    sidecar = {"track_id": track_id, "bars": list(bars),
               "source_start_s": round(grid.bar_start(start_bar), 3),
               "source_end_s": round(grid.bar_start(end_bar), 3),
               **data}
    path.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path
