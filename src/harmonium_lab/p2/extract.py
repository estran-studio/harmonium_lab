"""P2 — alternatives d'accords, de basse et de batterie extraites des transcriptions.

Entrée : les boucles transcrites d'un corpus (`corpus/<jeu>/transcriptions/<piste>_*.json`,
hors dépôt, principe VII) et le profil moteur écrit. Sortie : un TOML de **propositions**
dans le schéma actuel du moteur (E1/F1 : accords `{ semitones, quality, bass?, steps }`,
motifs de basse `[[accompaniment.bass.motifs]]`, patterns `[[percussion.patterns]]`) plus
des tables `[[provenance]]` (piste, mesures, minutage, confiance, soutien) et `[[gaps]]`
(ce que le schéma ne sait pas écrire). Le fichier ne contient que des **ajouts** : les
alternatives déjà au profil sont listées en provenance (`status = "présent"`), pas répétées.

Méthode, comme le minage des cellules trad (`trad/mine.py`) : observer, regrouper les
observations proches, pondérer chaque groupe par son effectif, garder le représentant le
plus central (médoïde, une observation réelle, jamais une moyenne synthétique).

1. **Observations par mesure**, dédupliquées par piste (la première boucle qui couvre une
   mesure l'emporte) : accord (triade maj/min du transcripteur, qualité lissée sur les
   mesures consécutives de même fondamentale), notes de basse, coups de batterie.
2. **Fenêtres.** Accords : longueur d'une partie `chord_loop` du profil. Basse : longueur
   (`bars`) d'un motif du profil. Fenêtres alignées sur le début de chaque plage contiguë
   de mesures observées. Batterie : une mesure.
3. **Affectation à une partie** (accords et basse) : similarité de la suite des
   fondamentales par mesure avec les références de la partie (ses boucles, sa pédale, ses
   motifs de basse à référence tonique), seuil `ASSIGN_MIN` ; en dessous, la fenêtre est
   « non assignée ». La batterie n'a pas de partie dans le schéma : le pattern prend la
   densité 0/1/2 dont les patterns écrits ont le nombre de coups moyen le plus proche.
4. **Regroupement** par partie (batterie : par densité) : clustering agglomératif à lien
   moyen sur une similarité (accords : part de mesures égales ; basse et batterie :
   Jaccard des attaques), seuils `CLUSTER_*`. Poids = effectif du groupe.
5. **Traduction au schéma** : accords en runs de mesures (`steps`), basse en motif relatif
   à la référence de la partie (`tonic` ou `chord_root`) dans le registre des motifs
   écrits, batterie par consensus du groupe (coup retenu s'il tombe dans au moins la moitié
   des mesures du groupe ; classe majoritaire à cette position).

La transcription ne porte ni vélocité ni articulation : vélocité des motifs de basse =
médiane du profil, `delta_velocity` des coups = règle fixe (voir `drum_hits`).
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Any, Callable, Sequence, TypeVar

from harmonium_lab.audioref.transcribe import NAMES
from harmonium_lab.styledist.engine import resolve_profile

from . import emit
from .engine_profile import EngineProfile, load_profile

T = TypeVar("T")

ASSIGN_MIN = 0.75         # similarité minimale d'une fenêtre avec une partie (3 mesures sur 4)
CLUSTER_CHORDS = 0.85     # part de mesures égales pour fusionner deux fenêtres d'accords (4 mesures : identiques)
CLUSTER_BASS = 0.5        # Jaccard des attaques de basse
CLUSTER_DRUMS = 0.5       # Jaccard des coups de batterie
PRESENT_BASS = 0.8        # Jaccard à partir duquel un motif est « déjà au profil »
PRESENT_DRUMS = 0.8
BASS_SLASH_SHARE = 0.7    # part de la mesure où une même classe tient la basse (accord slash)
MIN_SUPPORT = {"chords": 1, "bass": 2, "drums": 2}   # groupes plus petits écartés (bruit de transcription)

#: Sources par profil moteur : jeu (dossier de corpus) et pistes transcrites.
PROFILE_SOURCES: dict[str, dict[str, Any]] = {
    "isaac_basement": {"game": "isaac", "tracks": ["02_diptera_sonata", "21_periculum"]},
    "isaac_cellar": {"game": "isaac", "tracks": ["21_periculum"]},
    "isaac_burning": {"game": "isaac", "tracks": ["36_fundamentum"]},
    "isaac_downpour": {"game": "isaac", "tracks": ["47_river_of_despair"]},
    "nt_desert": {"game": "nuclear_throne", "tracks": ["02_flashyn", "19_a_way"]},
}

QUALITY_SUFFIX = {"maj": "", "min": "m"}
CLASS_RANK = {"kick": 0, "snare": 1, "hat": 2}


# ── Utilitaires ───────────────────────────────────────────────────────────

def fmt_time(seconds: float) -> str:
    minutes, rest = divmod(max(seconds, 0.0), 60)
    return f"{int(minutes)}:{rest:04.1f}"


def jaccard(a: frozenset, b: frozenset) -> float:
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def cluster(items: Sequence[T], sim: Callable[[T, T], float], threshold: float) -> list[list[int]]:
    """Clustering agglomératif à lien moyen : fusionne tant que la meilleure paire atteint `threshold`.
    Égalités tranchées par les plus petits indices ; retourne des listes d'indices triées."""
    clusters = [[i] for i in range(len(items))]
    while len(clusters) > 1:
        best, pair = -1.0, (0, 0)
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                s = sum(sim(items[i], items[j]) for i in clusters[a] for j in clusters[b]) / (
                    len(clusters[a]) * len(clusters[b]))
                if s > best + 1e-12:
                    best, pair = s, (a, b)
        if best < threshold:
            break
        a, b = pair
        clusters[a] = sorted(clusters[a] + clusters[b])
        del clusters[b]
    return clusters


def medoid(members: list[int], items: Sequence[T], sim: Callable[[T, T], float]) -> int:
    """Membre le plus proche des autres (égalité : le plus petit indice)."""
    return max(members, key=lambda i: (sum(sim(items[i], items[j]) for j in members if j != i), -i))


# ── Transcriptions d'une piste ────────────────────────────────────────────

@dataclass
class Track:
    id: str
    steps: int
    chords: dict[int, tuple[int, str, float]] = field(default_factory=dict)   # mesure → (fond. abs., "" | "m", score)
    bass: list[tuple[int, int, int]] = field(default_factory=list)            # (midi, début, durée) en pas
    bass_bars: set[int] = field(default_factory=set)
    bass_confidence: list[float] = field(default_factory=list)
    drums: dict[int, dict[tuple[str, int], float]] = field(default_factory=dict)  # mesure → {(classe, pas): marge}
    spans: list[tuple[int, int, float, float]] = field(default_factory=list)  # (mesure a, mesure b, début s, fin s)
    files: dict[str, list[str]] = field(default_factory=dict)                 # voix → fichiers utilisés

    def time_of(self, bar: int) -> float:
        for a, b, start, end in self.spans:
            if a <= bar <= b and b > a:
                return start + (bar - a) * (end - start) / (b - a)
        raise KeyError(f"mesure {bar} sans minutage ({self.id})")

    def when(self, first: int, last_excl: int) -> dict[str, Any]:
        """Minutage d'une plage de mesures [first, last_excl) dans le fichier de la piste."""
        return {"bars": [first, last_excl], "start": fmt_time(self.time_of(first)),
                "end": fmt_time(self.time_of(last_excl))}


def load_track(directory: Path, track_id: str, steps: int) -> Track:
    """Charge les sidecars JSON de `track_id`, dédupliqués par mesure et par voix."""
    track = Track(track_id, steps)
    covered: dict[str, set[int]] = {"chords": set(), "bass": set(), "drums": set()}
    for path in sorted(directory.glob(f"{track_id}_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("track_id") != track_id or "bars" not in data or len(data["bars"]) != 2:
            continue
        a, b = data["bars"]
        track.spans.append((a, b, float(data["source_start_s"]), float(data["source_end_s"])))
        bars = set(range(a, b))
        if "chords" in data:
            fresh = bars - covered["chords"]
            for c in data["chords"]["bars"]:
                if c["bar"] in fresh and c["quality"] in QUALITY_SUFFIX:
                    track.chords[c["bar"]] = (NAMES.index(c["root"]), QUALITY_SUFFIX[c["quality"]], float(c["score"]))
            covered["chords"] |= fresh
            track.files.setdefault("chords", []).append(path.name)
        if "bass" in data:
            fresh = bars - covered["bass"]
            for n in data["bass"]["notes"]:
                if n["start_16th"] // steps in fresh:
                    track.bass.append((int(n["midi"]), int(n["start_16th"]), int(n["len_16th"])))
            # Une mesure est « observée » même sans attaque : tenue qui la traverse.
            track.bass_bars |= fresh
            track.bass_confidence.append(float(data["bass"].get("voiced_ratio", 0.0)))
            covered["bass"] |= fresh
            track.files.setdefault("bass", []).append(path.name)
        if "drums" in data:
            fresh = bars - covered["drums"]
            for h in data["drums"]["hits"]:
                bar = h["pos_16th"] // steps
                if bar in fresh:
                    track.drums.setdefault(bar, {})[(h["class"], h["pos_16th"] % steps)] = float(h["confidence"])
            for bar in fresh:
                track.drums.setdefault(bar, {})
            covered["drums"] |= fresh
            track.files.setdefault("drums", []).append(path.name)
    track.bass.sort()
    _smooth_quality(track)
    return track


def _smooth_quality(track: Track) -> None:
    """Qualité d'une suite de mesures de même fondamentale = celle de plus grand score cumulé
    (la qualité d'une pédale oscille entre maj et min d'une mesure à l'autre)."""
    bars = sorted(track.chords)
    i = 0
    while i < len(bars):
        j = i
        while j + 1 < len(bars) and bars[j + 1] == bars[j] + 1 and track.chords[bars[j + 1]][0] == track.chords[bars[i]][0]:
            j += 1
        totals: Counter[str] = Counter()
        for b in bars[i:j + 1]:
            totals[track.chords[b][1]] += track.chords[b][2]
        best = max(totals, key=lambda q: (totals[q], q == ""))
        for b in bars[i:j + 1]:
            root, _, score = track.chords[b]
            track.chords[b] = (root, best, score)
        i = j + 1


def runs_of(bars: set[int]) -> list[list[int]]:
    """Plages de mesures consécutives."""
    out: list[list[int]] = []
    for b in sorted(bars):
        if out and out[-1][-1] == b - 1:
            out[-1].append(b)
        else:
            out.append([b])
    return out


def windows(bars: set[int], length: int) -> list[int]:
    """Débuts des fenêtres de `length` mesures, alignées sur le début de chaque plage."""
    return [run[0] + k * length for run in runs_of(bars) for k in range(len(run) // length)]


# ── Accords ───────────────────────────────────────────────────────────────

ChordBar = tuple[int, str, int | None]   # (fondamentale relative, qualité, basse relative si slash)


def bar_bass_pc(track: Track, bar: int) -> tuple[int, float] | None:
    """Classe de hauteur absolue qui tient la basse dans la mesure et sa part de durée."""
    lo, hi = bar * track.steps, (bar + 1) * track.steps
    weights: Counter[int] = Counter()
    for midi, start, length in track.bass:
        d = min(start + length, hi) - max(start, lo)
        if d > 0:
            weights[midi % 12] += d
    total = sum(weights.values())
    if not total:
        return None
    pc, w = weights.most_common(1)[0]
    return pc, w / total


def chord_window(track: Track, tonic: int, first: int, length: int) -> list[ChordBar]:
    out: list[ChordBar] = []
    for bar in range(first, first + length):
        root, quality, _ = track.chords[bar]
        bass = bar_bass_pc(track, bar)
        slash = None
        if bass and bass[1] >= BASS_SLASH_SHARE and bass[0] != root:
            slash = (bass[0] - tonic) % 12
        out.append(((root - tonic) % 12, quality, slash))
    return out


def chord_match(a: Sequence[tuple], b: Sequence[tuple]) -> float:
    """Part de mesures égales ; même fondamentale, autre qualité = demi-point. Une qualité `None`
    dans `b` (référence : pédale) vaut n'importe quelle qualité."""
    pts = 0.0
    for x, y in zip(a, b):
        if x[0] == y[0]:
            pts += 1.0 if y[1] is None or x[1] == y[1] else 0.5
    return pts / len(a) if a else 0.0


def runs_to_chords(bars: Sequence[ChordBar], steps_per_bar: int) -> list[dict[str, Any]]:
    """Mesures consécutives identiques → `{ semitones, quality, bass?, steps }`."""
    out: list[dict[str, Any]] = []
    for root, quality, slash in bars:
        if out and (out[-1]["semitones"], out[-1]["quality"], out[-1].get("bass")) == (root, quality, slash):
            out[-1]["steps"] += steps_per_bar
            continue
        chord: dict[str, Any] = {"semitones": root, "quality": quality}
        if slash is not None:
            chord["bass"] = slash
        chord["steps"] = steps_per_bar
        out.append(chord)
    return out


# ── Basse ─────────────────────────────────────────────────────────────────

def bar_roots_from_notes(notes: Sequence[tuple[int, int, int]], first: int, length: int, steps: int,
                         tonic: int) -> list[int | None]:
    """Classe dominante (durée) de la basse par mesure, relative à la tonique."""
    out: list[int | None] = []
    for bar in range(first, first + length):
        lo, hi = bar * steps, (bar + 1) * steps
        weights: Counter[int] = Counter()
        for midi, start, ln in notes:
            d = min(start + ln, hi) - max(start, lo)
            if d > 0:
                weights[midi % 12] += d
        out.append((weights.most_common(1)[0][0] - tonic) % 12 if weights else None)
    return out


def motif_bar_roots(profile: EngineProfile, motif: dict[str, Any]) -> list[int | None] | None:
    """Classe dominante par mesure d'un motif écrit à référence tonique ; None sinon."""
    if motif.get("reference", "chord_root") != "tonic":
        return None
    steps = profile.steps_per_bar
    out: list[int | None] = []
    for bar in range(int(motif.get("bars", 1))):
        weights: Counter[int] = Counter()
        for n in motif["notes"]:
            d = min(n["step"] + n["duration"], (bar + 1) * steps) - max(n["step"], bar * steps)
            if d > 0:
                weights[(n.get("semitones", 0) + 12 * n.get("octave", 0)) % 12] += d
        out.append(weights.most_common(1)[0][0] if weights else None)
    return out


def motif_signature(notes: Sequence[dict[str, Any]]) -> frozenset:
    """Attaques d'un motif écrit : (croche, classe relative à la référence)."""
    return frozenset((n["step"] // 2, (n.get("semitones", 0) + 12 * n.get("octave", 0)) % 12) for n in notes)


def root_match(a: Sequence[int | None], b: Sequence[int | None]) -> float:
    return sum(1 for x, y in zip(a, b) if x is not None and x == y) / len(a) if a else 0.0


def part_references(profile: EngineProfile, part: str, length: int) -> list[list[int | None]]:
    """Suites de classes par mesure d'une partie, découpées en fenêtres de `length` mesures :
    ses boucles ou sa pédale, et ses motifs de basse à référence tonique."""
    refs: list[list[int | None]] = []
    for alt in profile.part_alternatives(part):
        roots: list[int | None] = [root for root, _ in alt]
        refs += [roots[i:i + length] for i in range(0, len(roots) - length + 1, length)]
    for m in profile.motifs:
        if m.get("part") == part and int(m.get("bars", 1)) == length:
            r = motif_bar_roots(profile, m)
            if r:
                refs.append(r)
    return refs


def reference_register(profile: EngineProfile, part: str, length: int) -> tuple[str, float, int]:
    """(référence majoritaire, hauteur moyenne visée, vélocité médiane) des motifs écrits de la partie."""
    motifs = [m for m in profile.motifs if m.get("part") == part and int(m.get("bars", 1)) == length] or profile.motifs
    weight: Counter[str] = Counter()
    for m in motifs:
        weight[m.get("reference", "chord_root")] += int(m.get("weight", 1))
    reference = max(weight, key=lambda r: (weight[r], r == "tonic"))
    tonic_ref = profile.place_reference(profile.tonic_pc)
    pitches = [tonic_ref + n.get("semitones", 0) + 12 * n.get("octave", 0) for m in motifs for n in m["notes"]]
    velocities = [n.get("velocity", 90) for m in motifs for n in m["notes"]]
    return reference, sum(pitches) / len(pitches), int(median(velocities))


MIN_NOTE_STEPS = 2        # figures ≥ 2 pas (leçon G7h : chaque demi-ton audible)


def dejitter(notes: Sequence[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Notes (hauteur, début, durée) ordonnées, sans chevauchement, d'au moins `MIN_NOTE_STEPS` pas.
    Une note coupe la précédente ; une note trop courte est absorbée par la précédente si elle la
    prolonge sans trou, sinon écartée ; deux notes contiguës de même hauteur n'en font qu'une."""
    seq: list[tuple[int, int, int]] = []
    for midi, start, ln in sorted(notes, key=lambda n: (n[1], n[0])):
        if seq and start < seq[-1][1] + seq[-1][2]:
            pm, ps, _ = seq[-1]
            seq.pop()
            if start > ps:
                seq.append((pm, ps, start - ps))
        seq.append((midi, start, ln))
    out: list[tuple[int, int, int]] = []
    for midi, start, ln in seq:
        if ln < MIN_NOTE_STEPS:
            if out and out[-1][1] + out[-1][2] == start:
                pm, ps, pl = out[-1]
                out[-1] = (pm, ps, pl + ln)
            continue
        if out and out[-1][0] == midi and out[-1][1] + out[-1][2] == start:
            pm, ps, pl = out[-1]
            out[-1] = (pm, ps, pl + ln)
        else:
            out.append((midi, start, ln))
    return out


def bass_motif(track: Track, profile: EngineProfile, part: str, first: int, length: int,
               chord_roots: dict[int, int]) -> dict[str, Any] | None:
    """Fenêtre de basse → motif du schéma ; None si hors de portée (notes absentes ou intervalle > 48)."""
    steps = profile.steps_per_bar
    lo, hi = first * steps, (first + length) * steps
    reference, target_mean, velocity = reference_register(profile, part, length)
    notes: list[tuple[int, int, int]] = []
    for midi, start, ln in track.bass:
        s, e = max(start, lo), min(start + ln, hi)
        if e > s:
            notes.append((midi, s - lo, e - s))
    clean = dejitter(notes)
    if not clean:
        return None

    def ref_pitch(start: int) -> int:
        if reference == "tonic":
            return profile.place_reference(profile.tonic_pc)
        bar = first + start // steps
        return profile.place_reference(chord_roots.get(bar, profile.tonic_pc))

    deltas = [midi - ref_pitch(start) for midi, start, _ in clean]
    pitches = [ref_pitch(start) + d for (_, start, _), d in zip(clean, deltas)]
    shift = 12 * round((target_mean - sum(pitches) / len(pitches)) / 12)
    out_notes: list[dict[str, Any]] = []
    previous_end = None
    for (midi, start, ln), delta in zip(clean, deltas):
        d = delta + shift
        octave = int(d / 12)              # vers zéro : |semitones| < 12, lisible comme les motifs écrits
        semitones = d - 12 * octave
        if not -2 <= octave <= 2:
            return None
        note: dict[str, Any] = {"step": start, "duration": ln, "semitones": semitones}
        if octave:
            note["octave"] = octave
        note["velocity"] = velocity + (4 if start % steps == 0 else 0)
        if previous_end == start:
            note["legato"] = True
        previous_end = start + ln
        out_notes.append(note)
    return {"part": part, "bars": length, "reference": reference, "notes": out_notes}


# ── Batterie ──────────────────────────────────────────────────────────────

def drum_hits(consensus: dict[int, str], steps_per_pulse: int) -> list[dict[str, Any]]:
    """Classes consensuelles → coups du schéma. kick → PercussionLow, snare → PercussionHigh,
    hat → PercussionHigh note 42. `delta_velocity` : 0 sur la pulsation, −16 ailleurs, −40 charleston
    (règle fixe : la transcription ne porte pas de vélocité)."""
    hits = []
    for step in sorted(consensus):
        cls = consensus[step]
        on_pulse = step % steps_per_pulse == 0
        if cls == "kick":
            hits.append({"step": step, "track": "PercussionLow", "delta_velocity": 0 if on_pulse else -16})
        elif cls == "snare":
            hits.append({"step": step, "track": "PercussionHigh", "delta_velocity": 0 if on_pulse else -16})
        else:
            hits.append({"step": step, "track": "PercussionHigh", "note": 42, "delta_velocity": -40})
    return hits


def pattern_signature(profile: EngineProfile, hits: Sequence[dict[str, Any]]) -> frozenset:
    perc = profile.percussion
    defaults = {"PercussionLow": perc.get("low_note", 36), "PercussionHigh": perc.get("high_note", 38)}
    return frozenset((h["step"], h["track"], h.get("note", defaults[h.get("track", "PercussionLow")]))
                     for h in hits)


def consensus_bar(bars: Sequence[dict[tuple[str, int], float]]) -> dict[int, str]:
    """Coup retenu à une position s'il tombe dans au moins la moitié des mesures ; classe majoritaire."""
    by_pos: dict[int, Counter[str]] = {}
    for bar in bars:
        seen = {}
        for (cls, pos) in bar:
            seen.setdefault(pos, []).append(cls)
        for pos, classes in seen.items():
            by_pos.setdefault(pos, Counter()).update(set(classes))
    out = {}
    for pos, counts in by_pos.items():
        n = sum(1 for bar in bars if any(p == pos for _, p in bar))
        if n / len(bars) >= 0.5:
            out[pos] = max(counts, key=lambda c: (counts[c], -CLASS_RANK[c]))
    return out


# ── Extraction d'un profil ────────────────────────────────────────────────

def _entry(layer: str, part: str | None, track: Track, first: int, last_excl: int, **extra: Any) -> dict[str, Any]:
    return {"layer": layer, "part": part, "track": track.id, **track.when(first, last_excl), **extra}


@dataclass
class Window:
    """Fenêtre candidate : plage de mesures d'une piste, partie la plus proche et similarité."""
    track: Track
    first: int
    length: int
    sim: float
    part: str | None
    payload: Any


def non_overlapping(cands: list[Window], taken: set[tuple[str, int]]) -> list[Window]:
    """Garde les fenêtres par similarité décroissante (puis longueur décroissante) sans recouvrement ;
    `taken` accumule les mesures prises : une mesure n'alimente qu'une partie."""
    out: list[Window] = []
    for w in sorted(cands, key=lambda w: (-w.sim, -w.length, w.track.id, w.first)):
        span = {(w.track.id, b) for b in range(w.first, w.first + w.length)}
        if span & taken:
            continue
        taken |= span
        out.append(w)
    return out


def extract_profile(profile: EngineProfile, tracks: list[Track], date: str | None = None) -> dict[str, Any]:
    """Propositions d'un profil. Retour : `loops` (partie → liste), `motifs`, `patterns`,
    `provenance`, `gaps`, `stats`."""
    steps = profile.steps_per_bar
    tonic = profile.tonic_pc
    loops: dict[str, list[dict[str, Any]]] = {}
    motifs: list[dict[str, Any]] = []
    patterns: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    stats: dict[str, Any] = {"chords": {}, "bass": {}, "drums": {}}

    # ----- accords -----
    chord_cands: list[Window] = []
    for track in tracks:
        for n in sorted({p.bars for p in profile.parts.values()}):
            same_length = [p for p in profile.parts.values() if p.bars == n]
            for first in windows(set(track.chords), n):
                bars = chord_window(track, tonic, first, n)
                best, best_part = 0.0, None
                for p in same_length:
                    for ref in profile.part_alternatives(p.name):
                        s = chord_match(bars, ref)
                        if s > best + 1e-12:
                            best, best_part = s, p.name
                chord_cands.append(Window(track, first, n, best, best_part, bars))
    taken: set[tuple[str, int]] = set()
    assigned = non_overlapping([w for w in chord_cands if w.sim >= ASSIGN_MIN], taken)
    for w in non_overlapping([w for w in chord_cands if w.sim < ASSIGN_MIN], taken):
        provenance.append(_entry("chords", None, w.track, w.first, w.first + w.length,
                                 status="non-assigné", similarity=round(w.sim, 2)))
    per_part: dict[str, list[Window]] = {}
    for w in assigned:
        per_part.setdefault(w.part, []).append(w)
    for part_name, items in per_part.items():
        part = profile.parts[part_name]
        refs = profile.part_alternatives(part_name)
        groups = cluster([w.payload for w in items], chord_match, CLUSTER_CHORDS)
        stats["chords"][part_name] = {"windows": len(items), "groups": len(groups),
                                      "discarded": sum(1 for m in groups if len(m) < MIN_SUPPORT["chords"])}
        for members in groups:
            if len(members) < MIN_SUPPORT["chords"]:
                continue
            w = items[medoid(members, [x.payload for x in items], chord_match)]
            conf = round(sum(w.track.chords[b][2] for b in range(w.first, w.first + part.bars)) / part.bars, 3)
            base = dict(support=len(members), windows=len(items), confidence=conf, similarity=round(w.sim, 2))
            where = (w.track, w.first, w.first + part.bars)
            if any(chord_match(w.payload, ref) == 1.0 for ref in refs):
                provenance.append(_entry("chords", part_name, *where, status="présent", **base))
            elif part.kind == "pedal":
                provenance.append(_entry("chords", part_name, *where, status="écart", **base))
                gaps.append({"layer": "chords", "part": part_name,
                             "reason": "partie `pedal` : le schéma n'accepte pas d'alternatives pondérées "
                                       "(seules les parties `chord_loop` portent `loops`)",
                             "track": w.track.id, "bars": [w.first, w.first + part.bars]})
            else:
                loops.setdefault(part_name, []).append(
                    {"weight": len(members), "chords": runs_to_chords(w.payload, steps)})
                provenance.append(_entry("chords", part_name, *where, status="nouveau",
                                         ref=f"harmony.parts.{part_name}.loops[{len(loops[part_name]) - 1}]", **base))

    # ----- basse -----
    absolute_roots = {b: root for track in tracks for b, (root, _, _) in track.chords.items()}
    bass_cands: list[Window] = []
    for track in tracks:
        for n in sorted({int(m.get("bars", 1)) for m in profile.motifs if m.get("part")}):
            same_length = [p for p in profile.parts if any(
                m.get("part") == p and int(m.get("bars", 1)) == n for m in profile.motifs)]
            for first in windows(track.bass_bars, n):
                roots = bar_roots_from_notes(track.bass, first, n, steps, tonic)
                if all(r is None for r in roots):
                    continue
                best, best_part = 0.0, None
                for p in same_length:
                    for ref in part_references(profile, p, n):
                        s = root_match(roots, ref)
                        if s > best + 1e-12:
                            best, best_part = s, p
                bass_cands.append(Window(track, first, n, best, best_part, roots))
    taken = set()
    assigned = non_overlapping([w for w in bass_cands if w.sim >= ASSIGN_MIN], taken)
    for w in non_overlapping([w for w in bass_cands if w.sim < ASSIGN_MIN], taken):
        provenance.append(_entry("bass", None, w.track, w.first, w.first + w.length,
                                 status="non-assigné", similarity=round(w.sim, 2)))
    bass_items: dict[str, list[tuple[Window, dict[str, Any], frozenset]]] = {}
    for w in assigned:
        motif = bass_motif(w.track, profile, w.part, w.first, w.length, absolute_roots)
        if motif is None:
            gaps.append({"layer": "bass", "part": w.part, "reason": "fenêtre de basse inexprimable "
                         "(aucune note durable, ou octave hors de ±2 après recalage du registre)",
                         "track": w.track.id, "bars": [w.first, w.first + w.length]})
            continue
        bass_items.setdefault(w.part, []).append((w, motif, motif_signature(motif["notes"])))
    for part_name, items in bass_items.items():
        sigs = [s for _, _, s in items]
        groups = cluster(sigs, jaccard, CLUSTER_BASS)
        stats["bass"][part_name] = {"windows": len(items), "groups": len(groups),
                                    "discarded": sum(1 for m in groups if len(m) < MIN_SUPPORT["bass"])}
        for members in groups:
            if len(members) < MIN_SUPPORT["bass"]:
                continue
            w, motif, sig = items[medoid(members, sigs, jaccard)]
            n = motif["bars"]
            existing = [motif_signature(e["notes"]) for e in profile.motifs
                        if e.get("part") == part_name and int(e.get("bars", 1)) == n
                        and e.get("reference", "chord_root") == motif["reference"]]
            conf = sum(w.track.bass_confidence) / max(len(w.track.bass_confidence), 1)
            base = dict(support=len(members), windows=len(items), confidence=round(conf, 3), similarity=round(w.sim, 2))
            where = (w.track, w.first, w.first + n)
            if any(jaccard(sig, e) >= PRESENT_BASS for e in existing):
                provenance.append(_entry("bass", part_name, *where, status="présent", **base))
            else:
                motifs.append({**motif, "weight": len(members)})
                provenance.append(_entry("bass", part_name, *where, status="nouveau",
                                         ref=f"accompaniment.bass.motifs[{len(motifs) - 1}]", **base))

    # ----- batterie -----
    drum_bars = [(t, b, t.drums[b]) for t in tracks for b in sorted(t.drums) if t.drums[b]]
    existing_by_density: dict[int, list[dict[str, Any]]] = {}
    for p in profile.patterns:
        if "hits" in p:
            existing_by_density.setdefault(int(p["density"]), []).append(p)
    means = {d: sum(len(p["hits"]) for p in ps) / len(ps) for d, ps in existing_by_density.items()}
    bar_sigs = [frozenset(d) for _, _, d in drum_bars]
    groups = cluster(bar_sigs, jaccard, CLUSTER_DRUMS) if drum_bars else []
    stats["drums"] = {"bars": len(drum_bars), "groups": len(groups),
                      "discarded": sum(1 for m in groups if len(m) < MIN_SUPPORT["drums"])}
    for members in groups:
        if len(members) < MIN_SUPPORT["drums"]:
            continue
        cons = consensus_bar([drum_bars[i][2] for i in members])
        if not cons:
            continue
        hits = drum_hits(cons, profile.steps_per_pulse)
        density = min(means, key=lambda d: (abs(len(hits) - means[d]), d)) if means else 1
        sig = pattern_signature(profile, hits)
        by_track = Counter(drum_bars[i][0].id for i in members)
        main_track = next(t for t, _, _ in drum_bars if t.id == by_track.most_common(1)[0][0])
        bars_of = sorted(drum_bars[i][1] for i in members if drum_bars[i][0] is main_track)
        conf_values = [c for i in members for c in drum_bars[i][2].values()]
        base = dict(support=len(members), windows=len(drum_bars), density=density,
                    confidence=round(sum(conf_values) / len(conf_values), 3))
        existing = [pattern_signature(profile, p["hits"]) for p in existing_by_density.get(density, [])]
        entry = {"layer": "drums", "part": f"density{density}", "track": main_track.id, "bars_used": bars_of,
                 "times": [fmt_time(main_track.time_of(b)) for b in bars_of]}
        if any(jaccard(sig, e) >= PRESENT_DRUMS for e in existing):
            provenance.append({**entry, "status": "présent", **base})
        else:
            patterns.append({"density": density, "weight": len(members), "hits": hits})
            provenance.append({**entry, "status": "nouveau", "ref": f"percussion.patterns[{len(patterns) - 1}]", **base})
    gaps.append({"layer": "drums", "part": None,
                 "reason": "patterns de batterie par densité seulement : aucun moyen de lier un pattern à une partie "
                           "ou à un tour (le tirage est par partie et densité, mais la banque est commune)"})
    return {
        "profile": profile.id, "date": date or datetime.date.today().isoformat(),
        "loops": loops, "motifs": motifs, "patterns": patterns,
        "provenance": provenance, "gaps": gaps, "stats": stats,
        "tracks": [t.id for t in tracks],
    }


# ── Écriture du TOML de proposition ───────────────────────────────────────

def render_proposal(result: dict[str, Any], corpus_version: str | None) -> str:
    out = [
        f"# Propositions P2 pour `{result['profile']}` (phase 018) — ajouts au profil écrit, schéma moteur actuel.",
        "#",
        f"# Source : transcriptions {', '.join(result['tracks'])} (hors dépôt, principe VII)"
        + (f", corpus {corpus_version}" if corpus_version else "") + f", extraites le {result['date']}.",
        "# Aucun audio, stem ni MIDI : seuls des dérivés agrégés (accords, motifs, patterns).",
        "# Seuls `harmony.parts.*`, `accompaniment.bass.motifs` et `percussion.patterns` sont des données moteur ;",
        "# `[[provenance]]`, `[[gaps]]` et `[stats]` sont des métadonnées (le moteur les refuserait : `p2-enrich` les écarte).",
        "# `weight` = effectif du groupe de fenêtres proches (fréquence), pas un réglage d'écoute.",
        "# Confiance : accords = score moyen de la triade par mesure (0–1) ; basse = part de trames voisées ;",
        "# batterie = marge moyenne de classification des coups (peut être < 0).",
        "",
    ]
    for part, loops in result["loops"].items():
        out.append(emit.part_block(part, loops))
    for motif in result["motifs"]:
        out.append(emit.motif_block(motif))
    for pattern in result["patterns"]:
        out.append(emit.pattern_block(pattern))
    for prov in result["provenance"]:
        out.append("[[provenance]]")
        for k, v in prov.items():
            if v is not None:
                out.append(f"{k} = {emit.scalar(v)}")
        out.append("")
    for gap in result["gaps"]:
        out.append("[[gaps]]")
        for k, v in gap.items():
            if v is not None:
                out.append(f"{k} = {emit.scalar(v)}")
        out.append("")
    for layer, entries in result["stats"].items():
        if entries and all(isinstance(v, dict) for v in entries.values()):
            tables = {f"stats.{layer}.{part}": values for part, values in entries.items()}
        else:
            tables = {f"stats.{layer}": entries}
        for name, values in tables.items():
            if values:
                out.append(f"[{name}]")
                out += [f"{k} = {emit.scalar(v)}" for k, v in values.items()]
                out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


# ── CLI ───────────────────────────────────────────────────────────────────

def ref_dir_name(profile_id: str) -> str:
    return profile_id.replace("_", "-")


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="p2-extract", description=__doc__.splitlines()[0], add_help=add_help)
    p.add_argument("--profile", action="append", default=None,
                   help=f"Profil moteur (répétable ; défaut : {', '.join(PROFILE_SOURCES)})")
    p.add_argument("--engine-dir", default="../harmonium", help="Dépôt du moteur (profils)")
    p.add_argument("--corpus-root", default="corpus", help="Racine des corpus hors dépôt (<racine>/<jeu>/transcriptions)")
    p.add_argument("--refs", default="references", help="Dossier des références : <refs>/<profil-id>/proposals/")
    p.add_argument("--output", "-o", default=None, help="Fichier de sortie (un seul profil)")
    return p


def run(args: argparse.Namespace) -> int:
    engine_dir = Path(args.engine_dir).expanduser().resolve()
    corpus_root = Path(args.corpus_root).expanduser().resolve()
    ids = args.profile or list(PROFILE_SOURCES)
    if args.output and len(ids) != 1:
        raise SystemExit("--output exige un seul --profile")
    for pid in ids:
        if pid not in PROFILE_SOURCES:
            raise SystemExit(f"profil sans source de transcriptions : {pid} (connus : {', '.join(PROFILE_SOURCES)})")
        src = PROFILE_SOURCES[pid]
        profile = load_profile(resolve_profile(engine_dir, pid))
        game_dir = corpus_root / src["game"]
        tracks = [load_track(game_dir / "transcriptions", t, profile.steps_per_bar) for t in src["tracks"]]
        version_file = game_dir / "VERSION"
        version = version_file.read_text(encoding="utf-8").splitlines()[0].strip() if version_file.is_file() else None
        result = extract_profile(profile, tracks)
        dest = Path(args.output) if args.output else Path(args.refs) / ref_dir_name(pid) / "proposals" / f"{pid}.toml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_proposal(result, version), encoding="utf-8")
        n_new = {k: sum(1 for p in result["provenance"] if p["layer"] == k and p["status"] == "nouveau")
                 for k in ("chords", "bass", "drums")}
        print(f"{pid}: {n_new['chords']} boucles, {n_new['bass']} motifs de basse, {n_new['drums']} patterns → {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
