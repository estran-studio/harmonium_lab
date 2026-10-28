"""Distance symbolique d'un MIDI moteur aux boucles transcrites du corpus.

Les transcriptions (`audioref-loops`, hors dépôt) donnent, par boucle, des
notes de basse, des coups de batterie (kick/snare/charleston) et un accord par
mesure, positionnés en sous-divisions (`pos_16th`, comptées depuis la mesure 0).
Le MIDI moteur est ramené à la même représentation : mesure = durée de la
signature rythmique du MIDI, position = `round(fraction de mesure × pas)` avec
`pas` = nombre de pas par mesure de la référence (24 en 12/8).

Rôles dans le MIDI : batterie = piste `is_drum` (GM : 35–36 kick, 37–40 snare,
42/44/46 charleston) ; basse = piste non percussive de hauteur médiane la plus
grave ; accords = piste non percussive la plus polyphonique parmi les autres.

Toutes les distances sont dans [0, 1] (0 = identique) ; score = 100 · (1 − d).
`bc(a, b) = Σ|a − b| / Σ(a + b)` (Bray-Curtis ; sur des histogrammes
normalisés c'est la distance en variation totale). Mesures :

- `bass_pc` : `bc` des histogrammes de classes de hauteur de la basse
  (pondérés par la durée) ;
- `drums_any`, `drums_kick`, `drums_snare`, `drums_hat` : `bc` des grilles
  d'attaques (fréquence, par position dans la mesure, des mesures où un coup
  tombe ; calculée sur les mesures où la batterie joue) ;
- `chord_roots` : `bc` des histogrammes de fondamentales des accords par
  mesure ; `chord_pedal_share` : écart de la part de la fondamentale la plus
  fréquente (pédale) ; `chord_change_rate` : écart de la part de mesures dont
  la fondamentale change. La qualité (maj/min) d'une pédale est ambiguë : non
  scorée ;
- `loop_bass`, `loop_drums`, `loop_chords` : pour chaque boucle de référence
  de `L` mesures, `1 − part des paires de mesures actives (b, b+L) de la voix
  générée qui se ressemblent` (Jaccard par mesure ≥ 0,75 ; ≥ 2 paires
  requises), moyennée sur les boucles de la voix. « La voix se répète-t-elle à
  la longueur de boucle de la référence ? » — exigeant pour une harmonie qui
  évolue par section (le pont de 8 mesures de *Fläshyn* ne se répète pas
  non plus à ce décalage) ; sans paires (voix absente ou trop courte) : non
  scoré. Une voix absente de la transcription (ex. pas de batterie dans un
  bourdon) donne la distance maximale contre une référence vide, listée dans
  `reference_empty_voices`.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from harmonium_lab.audioref.transcribe import CHORD_QUALITIES, NAMES

KICK, SNARE, HAT = {35, 36}, {37, 38, 39, 40}, {42, 44, 46}
REPEAT_MIN = 0.75
MAX_PERIOD = 16

GROUPS: dict[str, tuple[str, ...]] = {
    "basse": ("bass_pc",),
    "batterie": ("drums_any", "drums_kick", "drums_snare", "drums_hat"),
    "accords": ("chord_roots", "chord_pedal_share", "chord_change_rate"),
    "boucles": ("loop_bass", "loop_drums", "loop_chords"),
}


def bc(a: np.ndarray, b: np.ndarray) -> float:
    den = float(np.sum(a) + np.sum(b))
    return 0.0 if den == 0 else float(np.sum(np.abs(a - b)) / den)


# ── Représentation commune ────────────────────────────────────────────────

class Voices:
    """Voix quantifiées sur une grille de `steps` pas par mesure."""

    def __init__(self, steps: int, bass: list[tuple[int, int, int]],
                 drums: list[tuple[str, int]], chords: dict[int, int]):
        self.steps = steps
        self.bass = bass          # (midi, début en pas, durée en pas)
        self.drums = drums        # (classe, position en pas depuis la mesure 0)
        self.chords = chords      # mesure → fondamentale (classe de hauteur)

    def bass_bars(self) -> dict[int, frozenset]:
        """Signature de basse par mesure : attaques (pos, pc) + notes tenues d'avant (−1, pc)."""
        sigs: dict[int, set] = {}
        for midi, start, length in self.bass:
            pc = midi % 12
            sigs.setdefault(start // self.steps, set()).add((start % self.steps, pc))
            for bar in range(start // self.steps + 1, (start + length - 1) // self.steps + 1):
                sigs.setdefault(bar, set()).add((-1, pc))
        return {b: frozenset(s) for b, s in sigs.items()}

    def drum_bars(self) -> dict[int, frozenset]:
        sigs: dict[int, set] = {}
        for cls, pos in self.drums:
            sigs.setdefault(pos // self.steps, set()).add((cls, pos % self.steps))
        return {b: frozenset(s) for b, s in sigs.items()}

    def chord_bars(self) -> dict[int, frozenset]:
        return {b: frozenset({r}) for b, r in self.chords.items()}


def _chord_templates() -> dict[str, np.ndarray]:
    out = {}
    for q, iv in CHORD_QUALITIES.items():
        t = np.full(12, 0.2)
        t[list(iv)] = 1.0
        out[q] = t / np.linalg.norm(t)
    return out


def chord_root(pc_weights: np.ndarray) -> int | None:
    """Fondamentale de la triade (maj/min) la plus proche d'un profil de classes de hauteur."""
    if pc_weights.sum() <= 0:
        return None
    v = pc_weights / (np.linalg.norm(pc_weights) + 1e-12)
    templ = _chord_templates()
    best = max(((float(v @ np.roll(t, r)), r) for r in range(12) for t in templ.values()))
    return best[1]


# ── Référence : transcriptions JSON ───────────────────────────────────────

def steps_per_bar(grid: dict[str, Any]) -> int:
    """Doubles-croches par mesure d'une grille G0 : 2 tatums/croche × tatums/pulsation × pulsations."""
    return 2 * int(grid["tatums_per_beat"]) * int(grid["beats_per_bar"])


def load_transcriptions(directory: Path, track_id: str) -> list[dict[str, Any]]:
    """Sidecars JSON d'une piste, ordre alphabétique (les doublons de voix sont écartés
    par `reference_voices`)."""
    out = []
    for path in sorted(directory.glob(f"{track_id}_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("track_id") == track_id:
            data["_file"] = path.name
            out.append(data)
    return out


def _loops(files: list[dict[str, Any]], voice: str) -> list[dict[str, Any]]:
    """Boucles d'une voix (`bass`, `drums`, `chords`), une par plage de mesures
    (la boucle complète qui répète une voix déjà transcrite est écartée)."""
    seen, out = set(), []
    for f in files:
        if voice not in f:
            continue
        key = tuple(f["bars"])
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def reference_voices(files: list[dict[str, Any]], steps: int) -> tuple[Voices, dict[str, list[dict[str, Any]]]]:
    """Voix de référence (union dédupliquée des boucles) + boucles par voix."""
    loops = {v: _loops(files, v) for v in ("bass", "drums", "chords")}
    bass, seen = [], set()
    for f in loops["bass"]:
        for n in f["bass"]["notes"]:
            k = (n["midi"], n["start_16th"], n["len_16th"])
            if k not in seen:
                seen.add(k)
                bass.append(k)
    drums, seen_d = [], set()
    for f in loops["drums"]:
        for h in f["drums"]["hits"]:
            k = (h["class"], h["pos_16th"])
            if k not in seen_d:
                seen_d.add(k)
                drums.append(k)
    chords: dict[int, int] = {}
    for f in loops["chords"]:
        for c in f["chords"]["bars"]:
            chords.setdefault(c["bar"], NAMES.index(c["root"]))
    return Voices(steps, bass, drums, chords), loops


# ── Génération : MIDI moteur ──────────────────────────────────────────────

def read_midi(path: Path, steps: int) -> Voices:
    """MIDI moteur → voix quantifiées sur `steps` pas par mesure (signature rythmique constante)."""
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(str(path))
    ts = pm.time_signature_changes[0] if pm.time_signature_changes else None
    num, den = (ts.numerator, ts.denominator) if ts else (4, 4)
    bar_ticks = num * 4 / den * pm.resolution
    step_ticks = bar_ticks / steps

    def q(t: float) -> int:
        return int(round(pm.time_to_tick(t) / step_ticks))

    drums: list[tuple[str, int]] = []
    pitched = []
    for inst in pm.instruments:
        if inst.is_drum:
            for n in inst.notes:
                cls = ("kick" if n.pitch in KICK else "snare" if n.pitch in SNARE
                       else "hat" if n.pitch in HAT else None)
                if cls:
                    drums.append((cls, q(n.start)))
        elif inst.notes:
            pitched.append(inst)
    bass_inst, chord_inst = None, None
    if pitched:
        bass_inst = min(pitched, key=lambda i: float(np.median([n.pitch for n in i.notes])))
        rest = [i for i in pitched if i is not bass_inst]
        if rest:
            chord_inst = max(rest, key=lambda i: _polyphony(i, q))
    bass = []
    if bass_inst is not None:
        bass = [(n.pitch, q(n.start), max(1, q(n.end) - q(n.start))) for n in bass_inst.notes]
    chords: dict[int, int] = {}
    if chord_inst is not None:
        weights: dict[int, np.ndarray] = {}
        for n in chord_inst.notes:
            s, e = q(n.start), max(q(n.start) + 1, q(n.end))
            for bar in range(s // steps, (e - 1) // steps + 1):
                lo, hi = max(s, bar * steps), min(e, (bar + 1) * steps)
                if hi > lo:
                    weights.setdefault(bar, np.zeros(12))[n.pitch % 12] += hi - lo
        for bar, w in weights.items():
            root = chord_root(w)
            if root is not None:
                chords[bar] = root
    return Voices(steps, bass, drums, chords)


def _polyphony(inst, q) -> float:
    """Nombre moyen de notes simultanées aux attaques de la piste."""
    spans = [(q(n.start), q(n.end)) for n in inst.notes]
    starts = sorted({s for s, _ in spans})
    return float(np.mean([sum(1 for s, e in spans if s <= t < e) for t in starts])) if starts else 0.0


# ── Mesures ───────────────────────────────────────────────────────────────

def bass_histogram(v: Voices) -> np.ndarray:
    h = np.zeros(12)
    for midi, _s, length in v.bass:
        h[midi % 12] += length
    return h / h.sum() if h.sum() else h


def drum_grid(v: Voices, cls: str | None) -> np.ndarray:
    """Fréquence par position des mesures (où la batterie joue) contenant un coup de `cls`
    (`None` : toute classe)."""
    bars: dict[int, set[int]] = {}
    active: set[int] = set()
    for c, pos in v.drums:
        active.add(pos // v.steps)
        if cls is None or c == cls:
            bars.setdefault(pos // v.steps, set()).add(pos % v.steps)
    grid = np.zeros(v.steps)
    for positions in bars.values():
        for p in positions:
            grid[p] += 1
    return grid / len(active) if active else grid


def chord_stats(v: Voices) -> dict[str, Any]:
    roots = [r for _, r in sorted(v.chords.items())]
    hist = np.bincount(roots, minlength=12).astype(float) if roots else np.zeros(12)
    stats: dict[str, Any] = {"hist": hist / hist.sum() if hist.sum() else hist}
    stats["pedal_share"] = float(hist.max() / hist.sum()) if hist.sum() else 0.0
    bars = sorted(v.chords)
    pairs = [(a, b) for a, b in zip(bars, bars[1:]) if b == a + 1]
    stats["change_rate"] = (float(np.mean([v.chords[a] != v.chords[b] for a, b in pairs]))
                            if pairs else 0.0)
    return stats


def jaccard(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def repeat_share(sigs: dict[int, frozenset], lag: int) -> float | None:
    """Part des paires de mesures actives (b, b+lag) qui se ressemblent
    (Jaccard ≥ `REPEAT_MIN`). `None` : moins de 2 paires."""
    sims = [jaccard(sigs[b], sigs[b + lag]) for b in sigs if b + lag in sigs]
    if len(sims) < 2:
        return None
    return float(np.mean([s >= REPEAT_MIN for s in sims]))


def detected_period(sigs: dict[int, frozenset]) -> int | None:
    """Plus petite période (mesures) ≤ 16 à laquelle ≥ 75 % des paires de mesures actives se répètent."""
    for p in range(1, MAX_PERIOD + 1):
        sims = [jaccard(sigs[b], sigs[b + p]) for b in sigs if b + p in sigs]
        if len(sims) >= 2 and float(np.mean(sims)) >= REPEAT_MIN:
            return p
    return None


def generated_metrics(gen: Voices, ref: Voices, loops: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Distances (clé → d) et valeurs mesurées d'un MIDI contre les voix de référence."""
    d: dict[str, float | None] = {}
    d["bass_pc"] = bc(bass_histogram(gen), bass_histogram(ref))
    d["drums_any"] = bc(drum_grid(gen, None), drum_grid(ref, None))
    for cls in ("kick", "snare", "hat"):
        d[f"drums_{cls}"] = bc(drum_grid(gen, cls), drum_grid(ref, cls))
    gs, rs = chord_stats(gen), chord_stats(ref)
    d["chord_roots"] = bc(gs["hist"], rs["hist"])
    d["chord_pedal_share"] = abs(gs["pedal_share"] - rs["pedal_share"])
    d["chord_change_rate"] = abs(gs["change_rate"] - rs["change_rate"])
    sig_of = {"bass": gen.bass_bars(), "drums": gen.drum_bars(), "chords": gen.chord_bars()}
    loop_detail: dict[str, dict[str, Any]] = {}
    for voice in ("bass", "drums", "chords"):
        shares = []
        for f in loops[voice]:
            length = f["bars"][1] - f["bars"][0]
            share = repeat_share(sig_of[voice], length)
            loop_detail[f"{voice}:{f['loop']}"] = {
                "bars": length,
                "generated_lag_match_share": None if share is None else round(share, 3)}
            if share is not None:
                shares.append(share)
        d[f"loop_{voice}"] = float(1.0 - np.mean(shares)) if shares else None
    values = {
        "bass_pc_hist": [round(float(x), 3) for x in bass_histogram(gen)],
        "bass_median_midi": float(np.median([n[0] for n in gen.bass])) if gen.bass else None,
        "drum_hits_per_bar": round(len(gen.drums) / max(1, len({p // gen.steps for _, p in gen.drums})), 2),
        "chord_pedal_share": round(gs["pedal_share"], 3),
        "chord_change_rate": round(gs["change_rate"], 3),
        "chord_roots": [NAMES[r] for _, r in sorted(gen.chords.items())],
        "detected_period_bars": {v: detected_period(sig_of[v]) for v in sig_of},
        "loops": loop_detail,
    }
    return {"d": d, "values": values}


def reference_values(ref: Voices, loops: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    cs = chord_stats(ref)
    empty = [v for v, present in (("bass", ref.bass), ("drums", ref.drums), ("chords", ref.chords)) if not present]
    return {
        "bass_pc_hist": [round(float(x), 3) for x in bass_histogram(ref)],
        "bass_median_midi": float(np.median([n[0] for n in ref.bass])) if ref.bass else None,
        "drum_hits_per_bar": round(len(ref.drums) / max(1, len({p // ref.steps for _, p in ref.drums})), 2),
        "drum_grid_any": [round(float(x), 3) for x in drum_grid(ref, None)],
        "chord_pedal_share": round(cs["pedal_share"], 3),
        "chord_change_rate": round(cs["change_rate"], 3),
        "chord_roots": dict(Counter(NAMES[r] for _, r in sorted(ref.chords.items()))),
        "reference_empty_voices": empty,
        "loops": {f"{v}:{f['loop']}": {"bars": f["bars"][1] - f["bars"][0], "source_bars": f["bars"]}
                  for v in loops for f in loops[v]},
    }


def summarize(per_seed: list[dict[str, float | None]]) -> dict[str, Any]:
    """Distance moyenne (sur les graines), scores, groupes ; mesures absentes ignorées."""
    dist: dict[str, float | None] = {}
    for key in per_seed[0]:
        vals = [s[key] for s in per_seed if s[key] is not None]
        dist[key] = round(float(np.mean(vals)), 4) if vals else None
    scores = {k: (None if v is None else round(100.0 * (1.0 - v), 1)) for k, v in dist.items()}
    groups: dict[str, float | None] = {}
    for g, keys in GROUPS.items():
        vals = [scores[k] for k in keys if scores.get(k) is not None]
        groups[g] = round(float(np.mean(vals)), 1) if vals else None
    valid = [v for v in groups.values() if v is not None]
    return {"distance": dist, "scores": scores, "groups": groups,
            "score": round(float(np.mean(valid)), 1) if valid else None}
