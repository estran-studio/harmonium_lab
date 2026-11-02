"""Groove MIDI Dataset complet (L2, phase 019) : batterie de TOUS les styles, ramenée à la grille du feel.

Source : Gillick, Roberts, Engel, Eck, Bamman, « Learning to Groove with Inverse Sequence
Transformations », ICML 2019 ; Groove MIDI Dataset v1.0.0 (archive MIDI seule), CC BY 4.0,
https://magenta.withgoogle.com/datasets/groove. Les bruts restent en cache gitignoré
(`corpus/gmd/raw/`), le SHA256 est vérifié avant toute lecture (`drums.open_archive`) ; ne sortent
que des agrégats : probabilités par pas, vélocités, micro-timing, patterns vus dans plusieurs
fichiers, patterns proposés construits sur des probabilités (jamais une mesure d'un enregistrement).

## Ce que ce module ajoute à `drums.py` (E7, jazz seul)

- **Tous les styles** d'`info.csv` (18 familles, 76 styles), `beat` et `fill` séparés, métriques
  4/4, 3/4 et 6/8 (un fichier 5/4 et un 5/8 : listés, jamais mesurés, `rejects`).
- **Rôles fins** : la table Roland TD-11 → GM de `drums.ROLAND_TABLE` est conservée pour les notes,
  mais les rôles passent de 8 à 12 : le cross-stick (37) devient `sidestick`, la cloche de ride (53)
  `ride_bell`, les trois toms `tom_high` / `tom_mid` / `tom_low`. Le GMD ne contient AUCUNE
  percussion latine (le TD-11 n'a que les pads d'un kit) : les styles latins sont joués au kit, avec
  le cross-stick, la cloche de ride et les toms ; `LATIN_STAND_IN` note les équivalents GM possibles
  pour un rendu, à l'oreille, jamais mesurés.
- **Grille selon le feel**, décidé par fichier (`classify_feel`) :
  - `straight` : 16 pas par pulsation à 4 pas (doubles croches), 16 pas en 4/4, 12 en 3/4 et en 6/8 ;
  - `swing` : même grille, pas 2 de chaque pulsation retardé au rapport `r` mesuré (0,56 ≤ r < 0,62) ;
  - `ternary` : grille de triolets, 3 pas par pulsation (12 pas en 4/4, 9 en 3/4), shuffle, 12/8 et swing
    appuyé (r ≥ 0,62). 6/8 : toujours `straight` (la pulsation de croche y est le pas 2).
  Le feel vient des contretemps du ride et du charleston fermé : fractions de pulsation autour de 1/4 et 3/4
  (doubles croches droites) contre r médian dans [0,45 ; 0,73]. Un fichier sans contretemps de timekeeper
  est jugé sur les autres rôles (sauf la grosse caisse) ; sans preuve il reste `straight`.
- **Micro-timing par rôle** : écart de chaque attaque à sa position nominale de grille, en pas et en ms
  (au tempo du fichier). Les ticks du MIDI suivent le métronome : l'écart est absolu.
- **Fills** : les fichiers `fill` sont décrits par leur position (pas de la première et de la dernière
  attaque, durée en temps, nombre de mesures touchées) en plus des probabilités par pas.
- **Fiabilité** par groupe, seuils écrits dans `RELIABILITY` (assez / juste / trop peu).

Usage : `python -m harmonium_lab.backing.gmd_styles [--fetch] [--manifest] [--measures] [--summary]`
(sans drapeau d'étape : tout). Sorties : `references/gmd-<famille>/` (une par famille) et
`references/gmd-<famille>-<style>/` (une par style secondaire assez fourni, `OWN_FOLDER`), chacune avec
`measures-drums.json` et `README.md`, plus `references/gmd-inventory.json` (tous styles, effectifs).
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import mido
import numpy as np

from . import drums
from .corpus_cache import ROOT, describe, fetch, percentiles, write_json

REFERENCES_ROOT = ROOT / "references"
COMMAND = "python -m harmonium_lab.backing.gmd_styles --measures"

# ---------------------------------------------------------------------------------------
# Rôles fins et table Roland → rôle → GM

PITCH_ROLE: dict[int, str] = {
    36: "kick",
    38: "snare", 40: "snare",
    37: "sidestick",
    48: "tom_high", 50: "tom_high",
    45: "tom_mid", 47: "tom_mid",
    43: "tom_low", 58: "tom_low",
    46: "hat_open", 26: "hat_open",
    42: "hat_closed", 22: "hat_closed",
    44: "hat_pedal",
    49: "crash", 55: "crash", 57: "crash", 52: "crash",
    51: "ride", 59: "ride",
    53: "ride_bell",
}
"""Hauteur Roland TD-11 → rôle fin. Les notes GM viennent de `drums.ROLAND_TABLE` (colonne « Paper Mapping »
de la page officielle) ; tête et rimshot de caisse claire, arc et bord de ride, arc et bord de crash,
bord de tom partagent le rôle de leur pad."""

ROLES = ("kick", "snare", "sidestick", "hat_closed", "hat_pedal", "hat_open", "ride", "ride_bell", "crash",
         "tom_high", "tom_mid", "tom_low")
TIMEKEEPERS = ("ride", "hat_closed", "hat_open", "ride_bell")
"""Rôles qui peuvent porter la pulsation d'une mesure (celui qui a le plus de coups l'emporte)."""
FILL_ROLES = ("kick", "snare", "sidestick", "tom_high", "tom_mid", "tom_low", "crash")

LATIN_STAND_IN: dict[str, dict[str, Any]] = {
    "sidestick": {"gm": 37, "latin": "clave / bois (GM 75 claves, 76-77 wood blocks)"},
    "ride_bell": {"gm": 53, "latin": "cloche, campana (GM 56 cowbell)"},
    "tom_high": {"gm": 50, "latin": "conga / timbale aiguë (GM 63 open hi conga, 65 high timbale)"},
    "tom_mid": {"gm": 47, "latin": "conga médium (GM 62 mute hi conga)"},
    "tom_low": {"gm": 43, "latin": "tumbadora grave (GM 64 low conga)"},
}
"""Équivalents latins POSSIBLES pour un rendu. Hypothèse d'écoute : le GMD ne mesure aucun instrument latin."""


def fine_role(pitch: int) -> str | None:
    return PITCH_ROLE.get(pitch)


def role_table() -> dict[str, Any]:
    """Table de correspondance documentée : hauteur Roland → nom Roland, rôle fin, note GM."""
    return {
        "source": f"{drums.SOURCE_PAGE}, section « Drum Mapping » (Roland TD-11 → GM), consultée le 2026-11-01",
        "pitches": {str(p): {"roland": drums.ROLAND_TABLE[p][0], "role": PITCH_ROLE[p], "gm": drums.ROLAND_TABLE[p][2]}
                    for p in sorted(PITCH_ROLE)},
        "latin_stand_in": LATIN_STAND_IN,
        "note": "aucune percussion latine dans le GMD ; les stand-ins sont des hypothèses de rendu",
    }


# ---------------------------------------------------------------------------------------
# Métriques, feels et grilles

SUPPORTED_METERS = {"4-4": 4.0, "3-4": 3.0, "6-8": 3.0}
"""Signature d'`info.csv` → longueur de la mesure en pulsations (noires, comme les ticks du MIDI)."""
COMPOUND_METERS = ("6-8",)

FEELS = ("straight", "swing", "ternary")
SWING_CUTS = (0.56, 0.62)
"""r < 0,56 : droit ; 0,56 ≤ r < 0,62 : swing léger ; ≥ 0,62 : ternaire (triolets)."""
OFFBEAT_WINDOW = (0.45, 0.73)
SIXTEENTH_TOLERANCE = 0.07
MIN_EVIDENCE = 8
SIXTEENTH_SHARE = 0.25

GRID_POSITIONS: dict[str, tuple[float, ...]] = {
    "straight": (0.0, 0.25, 0.5, 0.75),
    "ternary": (0.0, 1 / 3, 2 / 3),
}
STEP_BEATS = {"straight": 0.25, "swing": 0.25, "ternary": 1 / 3}
"""Durée nominale d'un pas, en pulsations (sert à exprimer le micro-timing en pas)."""


def steps_per_beat(feel: str) -> int:
    return 3 if feel == "ternary" else 4


def positions_for(feel: str, ratio: float) -> tuple[float, ...]:
    if feel == "swing":
        return drums.nominal_positions(ratio)
    return GRID_POSITIONS[feel]


def classify_feel(hits: Sequence[drums.Hit], signature: str) -> dict[str, Any]:
    """Feel d'un fichier : `{feel, ratio, evidence, n_evidence}`.

    Contretemps des timekeepers (ride, charleston fermé et ouvert, cloche), fractions de pulsation hors des
    abords du temps (< 0,08, > 0,92). Si au moins 25 % d'entre eux sont près de 1/4 ou 3/4 (±0,07) et plus
    nombreux que ceux près de 1/3 ou 2/3 : doubles croches droites. Sinon `r` = médiane des fractions dans
    [0,45 ; 0,73] et `feel` suit `SWING_CUTS`. Moins de `MIN_EVIDENCE` contretemps : les autres rôles sauf
    la grosse caisse servent de preuve. Aucune preuve : `straight`.
    """
    if signature in COMPOUND_METERS:
        return {"feel": "straight", "ratio": 0.5, "evidence": "compound_meter", "n_evidence": 0}

    def fractions(roles: Iterable[str]) -> list[float]:
        wanted = set(roles)
        out = []
        for h in hits:
            if fine_role(h.pitch) in wanted:
                f = h.beat % 1.0
                if 0.08 <= f <= 0.92:
                    out.append(f)
        return out

    for label, roles in (("timekeeper", TIMEKEEPERS),
                         ("other_roles", tuple(r for r in ROLES if r != "kick" and r not in TIMEKEEPERS))):
        fr = fractions(roles)
        if len(fr) < MIN_EVIDENCE:
            continue
        n16 = sum(1 for f in fr if abs(f - 0.25) <= SIXTEENTH_TOLERANCE or abs(f - 0.75) <= SIXTEENTH_TOLERANCE)
        n3 = sum(1 for f in fr if abs(f - 1 / 3) <= SIXTEENTH_TOLERANCE or abs(f - 2 / 3) <= SIXTEENTH_TOLERANCE)
        if n16 >= SIXTEENTH_SHARE * len(fr) and n16 > n3:
            return {"feel": "straight", "ratio": 0.5, "evidence": f"{label}:sixteenths", "n_evidence": len(fr)}
        low, high = OFFBEAT_WINDOW
        inside = [f for f in fr if low <= f <= high]
        if len(inside) < MIN_EVIDENCE:
            continue
        r = float(np.median(inside))
        if r < SWING_CUTS[0]:
            feel = "straight"
        elif r < SWING_CUTS[1]:
            feel = "swing"
        else:
            feel = "ternary"
        return {"feel": feel, "ratio": r, "evidence": f"{label}:ratio", "n_evidence": len(inside)}
    return {"feel": "straight", "ratio": 0.5, "evidence": "none", "n_evidence": 0}


def quantize(beat: float, feel: str, ratio: float) -> tuple[int, int, float]:
    """Position en pulsations → `(pulsation, pas dans la pulsation, écart en pulsations)`.

    Plus proche position nominale de la pulsation courante ou de la suivante (position 1) ; l'écart est
    `attaque − position nominale` (négatif : en avance).
    """
    positions = positions_for(feel, ratio)
    base = int(np.floor(beat + 1e-9))
    frac = beat - base
    best = min(((abs(frac - pos), s) for s, pos in enumerate(positions)), default=(1.0, 0))
    if abs(1.0 - frac) < best[0]:
        return base + 1, 0, frac - 1.0
    return base, best[1], frac - positions[best[1]]


# ---------------------------------------------------------------------------------------
# Lecture et mesures


@dataclass(frozen=True)
class Performance:
    hits: tuple[drums.Hit, ...]
    end_beat: float
    unmapped: int = 0


def read_performance(data: bytes) -> Performance:
    """Attaques d'un MIDI de batterie en pulsations (`tick / résolution`). La métrique vient d'`info.csv`."""
    midi = mido.MidiFile(file=io.BytesIO(data))
    ppq = midi.ticks_per_beat
    hits: list[drums.Hit] = []
    unmapped = 0
    end_tick = 0
    for track in midi.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type in ("note_on", "note_off"):
                end_tick = max(end_tick, tick)
            if msg.type == "note_on" and msg.velocity > 0:
                if msg.note not in PITCH_ROLE:
                    unmapped += 1
                    continue
                hits.append(drums.Hit(tick / ppq, msg.note, msg.velocity))
    hits.sort(key=lambda h: (h.beat, h.pitch))
    return Performance(tuple(hits), end_tick / ppq, unmapped)


@dataclass
class Measure:
    """Une mesure ramenée à la grille : `steps[rôle][pas] = (vélocité max, note GM, écart en pulsations)`."""
    file: str
    style: str
    beat_type: str
    feel: str
    ratio: float
    bpm: int
    bar_beats: float
    steps: dict[str, dict[int, tuple[int, int, float]]] = field(default_factory=dict)

    @property
    def steps_per_bar(self) -> int:
        return int(round(self.bar_beats * steps_per_beat(self.feel)))

    def role_steps(self, role: str) -> tuple[int, ...]:
        return tuple(sorted(self.steps.get(role, {})))


def measures_of(perf: Performance, row: drums.FileRow, feel: str, ratio: float) -> list[Measure]:
    """Mesures entières d'un fichier (mêmes règles qu'E7 : fin de la mesure dans le fichier à une demi-pulsation
    près ; première mesure gardée si sa première attaque tombe avant 0,9 pulsation ; fill : 70 % de couverture)."""
    bar_beats = SUPPORTED_METERS[row.time_signature]
    spb = steps_per_beat(feel)
    by_bar: dict[int, Measure] = {}
    first_attack: dict[int, float] = {}
    for hit in perf.hits:
        beat_index, sub, off = quantize(hit.beat, feel, ratio)
        bar, beat_in_bar = divmod(beat_index, int(bar_beats))
        step = beat_in_bar * spb + sub
        role = fine_role(hit.pitch)
        assert role is not None
        measure = by_bar.setdefault(bar, Measure(row.path, row.style, row.beat_type, feel, ratio, row.bpm, bar_beats))
        first_attack.setdefault(bar, hit.beat)
        slot = measure.steps.setdefault(role, {})
        previous = slot.get(step)
        note = drums.gm_note(hit.pitch)
        assert note is not None
        if previous is None or hit.velocity > previous[0]:
            slot[step] = (hit.velocity, note, off)
    kept: list[Measure] = []
    first_bar = min(by_bar) if by_bar else None
    for bar in sorted(by_bar):
        start = bar * bar_beats
        if row.beat_type == "fill":
            complete = perf.end_beat >= start + drums.FILL_MIN_COVERAGE * bar_beats
        else:
            complete = start + bar_beats <= perf.end_beat + drums.BAR_TOLERANCE_BEATS
            if bar == first_bar and first_attack[bar] - start > drums.FIRST_BAR_LATEST_ATTACK_BEATS:
                complete = False
        if complete:
            kept.append(by_bar[bar])
    return kept


@dataclass
class FileResult:
    row: drums.FileRow
    feel: str = "straight"
    ratio: float = 0.5
    evidence: str = "none"
    n_evidence: int = 0
    measures: list[Measure] = field(default_factory=list)
    fill_position: dict[str, Any] | None = None
    unmapped: int = 0
    reject: str | None = None


def fill_position(perf: Performance, row: drums.FileRow, feel: str, ratio: float) -> dict[str, Any] | None:
    """Position d'un fichier `fill` : pas (dans sa mesure) et temps de la première et de la dernière attaque,
    durée en pulsations, mesures touchées."""
    if not perf.hits:
        return None
    bar_beats = SUPPORTED_METERS[row.time_signature]
    spb = steps_per_beat(feel)

    def locate(h: drums.Hit) -> tuple[int, int]:
        idx, sub, _ = quantize(h.beat, feel, ratio)
        bar, b = divmod(idx, int(bar_beats))
        return bar, b * spb + sub

    first_bar, first_step = locate(perf.hits[0])
    last_bar, last_step = locate(perf.hits[-1])
    return {
        "first_step": first_step, "last_step": last_step,
        "first_beat_in_bar": first_step // spb + 1,
        "span_beats": float(perf.hits[-1].beat - perf.hits[0].beat),
        "bars_touched": last_bar - first_bar + 1,
        "first_bar_index": first_bar,
        "n_hits": len(perf.hits),
    }


def analyse_archive(archive: zipfile.ZipFile, rows: Sequence[drums.FileRow]) -> list[FileResult]:
    """Lit chaque MIDI : feel, quantification, mesures. Métriques non prises en charge : `reject`."""
    results: list[FileResult] = []
    for row in rows:
        if row.time_signature not in SUPPORTED_METERS:
            results.append(FileResult(row, reject=f"métrique {row.time_signature} : un seul fichier, non mesurée"))
            continue
        perf = read_performance(archive.read(f"groove/{row.path}"))
        info = classify_feel(perf.hits, row.time_signature)
        res = FileResult(row, info["feel"], info["ratio"], info["evidence"], info["n_evidence"], unmapped=perf.unmapped)
        res.measures = measures_of(perf, row, res.feel, res.ratio)
        if row.beat_type == "fill":
            res.fill_position = fill_position(perf, row, res.feel, res.ratio)
        results.append(res)
    return results


# ---------------------------------------------------------------------------------------
# Agrégation d'un groupe de mesures


RELIABILITY = {
    "beat": {"assez": {"files": 8, "drummers": 3, "measures": 200}, "juste": {"files": 3, "drummers": 1, "measures": 60}},
    "fill": {"assez": {"files": 30, "drummers": 3, "measures": 30}, "juste": {"files": 10, "drummers": 1, "measures": 10}},
}
"""Seuils : `assez` si tous les minima sont atteints, sinon `juste` si ceux de `juste` le sont, sinon `trop peu`.
Un fichier `beat` dure ~1 min (30 à 40 mesures) : 8 fichiers de 3 batteurs au moins donnent 200+ mesures et un
motif qui ne tient pas à un seul batteur ; 3 fichiers donnent de quoi proposer un pattern (seuil d'E7). Un
`fill` est une mesure : il en faut trente pour parler d'un répertoire."""


def reliability(kind: str, n_files: int, n_drummers: int, n_measures: int) -> str:
    spec = RELIABILITY[kind]
    for level in ("assez", "juste"):
        need = spec[level]
        if n_files >= need["files"] and n_drummers >= need["drummers"] and n_measures >= need["measures"]:
            return level
    return "trop peu"


def _share(n: int, total: int) -> float:
    return n / total if total else 0.0


def role_velocity_medians(measures: Sequence[Measure]) -> dict[str, float]:
    pool: dict[str, list[int]] = defaultdict(list)
    for m in measures:
        for role, slots in m.steps.items():
            pool[role].extend(v for v, _, _ in slots.values())
    return {role: float(np.median(v)) for role, v in pool.items()}


def per_step(measures: Sequence[Measure], medians: dict[str, float], steps: int) -> dict[str, list[list[float]]]:
    """Par rôle : lignes `[pas, n, probabilité, vélocité médiane, vélocité relative médiane, écart médian en pas]`
    des seuls pas où le rôle joue (la probabilité est rapportée au nombre total de mesures)."""
    total = len(measures)
    out: dict[str, list[list[float]]] = {}
    for role in ROLES:
        rows = []
        for step in range(steps):
            present = [(m.steps[role][step], m) for m in measures if step in m.steps.get(role, {})]
            if not present:
                continue
            vels = [h[0] for h, _ in present]
            offs = [h[2] / STEP_BEATS[m.feel] for h, m in present]
            rows.append([step, len(present), _share(len(present), total), float(np.median(vels)),
                         float(np.median(vels) / medians[role]) if medians.get(role) else 0.0,
                         float(np.median(offs))])
        if rows:
            out[role] = rows
    return out


def micro_timing(measures: Sequence[Measure]) -> dict[str, Any]:
    """Écart à la grille par rôle, en pas et en ms : sur les pulsations (pas % pas par pulsation = 0) et hors
    pulsation. Centiles 10/50/90, moyenne et écart-type ; `n` = nombre d'attaques."""
    pools: dict[tuple[str, str], tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    for m in measures:
        spb = steps_per_beat(m.feel)
        for role, slots in m.steps.items():
            for step, (_, _, off) in slots.items():
                where = "on_beat" if step % spb == 0 else "off_beat"
                steps_list, ms_list = pools[(role, where)]
                steps_list.append(off / STEP_BEATS[m.feel])
                ms_list.append(off * 60000.0 / m.bpm)
    out: dict[str, Any] = {}
    for (role, where), (s, ms) in sorted(pools.items()):
        if len(s) < 5:
            continue
        out.setdefault(role, {})[where] = {
            "n": len(s),
            "steps": {"mean": float(np.mean(s)), "std": float(np.std(s, ddof=1)), **percentiles(s, (10, 50, 90))},
            "ms": {"mean": float(np.mean(ms)), "std": float(np.std(ms, ddof=1)), **percentiles(ms, (10, 50, 90))},
        }
    return out


def grid_fit(measures: Sequence[Measure]) -> dict[str, Any]:
    """Part des attaques à moins d'un quart de pas de leur position de grille (fidélité de la grille)."""
    offs = [abs(off) / STEP_BEATS[m.feel] for m in measures for slots in m.steps.values() for _, _, off in slots.values()]
    close = sum(1 for o in offs if o <= 0.25)
    return {"n_hits": len(offs), "within_quarter_step": _share(close, len(offs)),
            "mean_abs_offset_steps": float(np.mean(offs)) if offs else None}


def timekeeper_of(m: Measure) -> str:
    counts = {r: len(m.steps.get(r, {})) for r in TIMEKEEPERS}
    best = max(counts.values())
    if best == 0:
        return "none"
    return next(r for r in TIMEKEEPERS if counts[r] == best)


FIGURES = ("none", "quarters", "eighths", "sixteenths", "spang", "quarters_plus", "sparse", "other")


def figure_of(m: Measure) -> str:
    """Figure du timekeeper de la mesure, par sous-pas occupés de chaque pulsation.

    - `quarters` : chaque pulsation sur le temps seulement ; `eighths` : temps et contretemps (swing, shuffle ou croches
      droites selon le feel) à chaque pulsation ; `sixteenths` : tous les sous-pas (doubles croches droites ou triolets)
      sur trois pulsations au moins ; `spang` : mesure de 4 pulsations où les pulsations 1 et 3 n'ont que le temps et
      les pulsations 2 et 4 temps et contretemps (figure du ride jazz) ; `quarters_plus` : tous les temps plus d'autres
      pas ; `sparse` : moins de la moitié des pulsations ; `other` : le reste.
    """
    role = timekeeper_of(m)
    if role == "none":
        return "none"
    spb = steps_per_beat(m.feel)
    n_beats = int(m.bar_beats)
    subs = [{s % spb for s in m.steps[role] if s // spb == b} for b in range(n_beats)]
    on = [0 in s for s in subs]
    if sum(on) < max(2, n_beats // 2 + 1) and not any(len(s) > 1 for s in subs):
        return "sparse"
    full = set(range(spb))
    if all(s == {0} for s in subs):
        return "quarters"
    if sum(1 for s in subs if s == full) >= 3:
        return "sixteenths"
    if n_beats == 4 and subs[0] == {0} and subs[2] == {0} and subs[1] == {0, 2} and subs[3] == {0, 2}:
        return "spang"
    if all(s >= {0, 2} and s <= {0, 2} for s in subs):
        return "eighths"
    if all(0 in s for s in subs):
        return "quarters_plus"
    if sum(on) <= n_beats // 2:
        return "sparse"
    return "other"


def top_patterns(measures: Sequence[Measure], top_n: int = 8, min_files: int = 2) -> dict[str, Any]:
    """Patterns de mesure les plus fréquents (pas occupés) par rôle, et kick+snare ; seuls ceux vus dans au moins
    `min_files` fichiers sont listés (aucun motif propre à un enregistrement)."""
    total = len(measures)

    def rank(keyed: list[tuple[Any, str]]) -> list[dict[str, Any]]:
        counts: Counter = Counter(k for k, _ in keyed)
        files: dict[Any, set[str]] = defaultdict(set)
        for k, f in keyed:
            files[k].add(f)
        listed = sorted((k for k in counts if len(files[k]) >= min_files and k != ()),
                        key=lambda k: (-counts[k], str(k)))[:top_n]
        return [{"key": k, "n": counts[k], "share": _share(counts[k], total), "n_files": len(files[k])} for k in listed]

    out: dict[str, Any] = {}
    for role in ("ride", "hat_closed", "hat_pedal", "kick", "snare", "sidestick", "ride_bell", "tom_low"):
        ranked = rank([(m.role_steps(role), m.file) for m in measures])
        if ranked:
            out[role] = [{"steps": list(r["key"]), "n": r["n"], "share": r["share"], "n_files": r["n_files"]}
                         for r in ranked]
    combined = rank([((m.role_steps("kick"), m.role_steps("snare")), m.file) for m in measures
                     if m.role_steps("kick") and m.role_steps("snare")])
    out["kick_snare"] = [{"kick": list(r["key"][0]), "snare": list(r["key"][1]), "n": r["n"], "share": r["share"],
                          "n_files": r["n_files"]} for r in combined]
    return out


def densities(measures: Sequence[Measure]) -> dict[str, Any]:
    counts = {role: [len(m.steps.get(role, {})) for m in measures] for role in ROLES}
    return {role: {**describe(v), "share_with": _share(sum(1 for x in v if x), len(v))}
            for role, v in counts.items() if any(v)}


def gm_notes(measures: Sequence[Measure]) -> dict[str, dict[str, int]]:
    out: dict[str, Counter] = defaultdict(Counter)
    for m in measures:
        for role, slots in m.steps.items():
            for _, note, _ in slots.values():
                out[role][note] += 1
    return {role: {str(n): c for n, c in sorted(counter.items())} for role, counter in sorted(out.items())}


def group_stats(measures: Sequence[Measure], results: Sequence[FileResult]) -> dict[str, Any]:
    """Toutes les mesures agrégées d'un groupe (un style, un feel, `beat` ou `fill`)."""
    files = Counter(m.file for m in measures)
    total = len(measures)
    medians = role_velocity_medians(measures)
    steps = measures[0].steps_per_bar if measures else 0
    tk = Counter(timekeeper_of(m) for m in measures)
    fig = Counter(figure_of(m) for m in measures)
    drummers = {r.row.drummer for r in results}
    kind = results[0].row.beat_type if results else "beat"
    return {
        "n_measures": total,
        "n_files": len(files),
        "n_drummers": len(drummers),
        "max_file_share": _share(max(files.values()), total) if files else 0.0,
        "minutes": sum(r.row.duration for r in results) / 60.0,
        "bpm": describe([r.row.bpm for r in results]),
        "swing_ratio": describe([r.ratio for r in results]),
        "steps_per_bar": steps,
        "n_hits": sum(len(s) for m in measures for s in m.steps.values()),
        "grid_fit": grid_fit(measures),
        "reliability": reliability(kind, len(files), len(drummers), total),
        "velocity_median_by_role": medians,
        "per_step_columns": ["step", "n", "prob", "velocity_p50", "rel_velocity_p50", "offset_p50_steps"],
        "per_step": per_step(measures, medians, steps),
        "densities": densities(measures),
        "timekeeper": {"roles": {r: {"n": n, "share": _share(n, total)} for r, n in sorted(tk.items())},
                       "figures": {f: {"n": fig.get(f, 0), "share": _share(fig.get(f, 0), total)} for f in FIGURES}},
        "micro_timing": micro_timing(measures),
        "top_patterns": top_patterns(measures),
        "gm_notes": gm_notes(measures),
    }


# ---------------------------------------------------------------------------------------
# Patterns proposés (mappables sur `[[patterns]]`, comme E7)

MIN_FILES_FOR_PROPOSAL = drums.MIN_FILES_FOR_PROPOSAL
MIN_MEASURES_FOR_PROPOSAL = drums.MIN_MEASURES_FOR_PROPOSAL
MAX_FILE_SHARE_FOR_PROPOSAL = drums.MAX_FILE_SHARE_FOR_PROPOSAL
FILL_THRESHOLD = drums.FILL_THRESHOLD
LEVELS = {
    0: {"timekeeper": 0.5},
    1: {"timekeeper": 0.5, "hat_pedal": 0.5, "kick": 0.5, "snare": 0.5, "sidestick": 0.5},
    2: {"timekeeper": 0.5, "hat_pedal": 0.5, "kick": 0.25, "snare": 0.25, "sidestick": 0.25},
}


def eligible(measures: Sequence[Measure]) -> bool:
    files = Counter(m.file for m in measures)
    return (len(measures) >= MIN_MEASURES_FOR_PROPOSAL and len(files) >= MIN_FILES_FOR_PROPOSAL
            and max(files.values()) / len(measures) <= MAX_FILE_SHARE_FOR_PROPOSAL)


def _subset_hits(measures: Sequence[Measure], thresholds: dict[str, float], medians: dict[str, float],
                 steps: int) -> list[dict[str, Any]]:
    total = len(measures)
    hits = []
    for role, threshold in thresholds.items():
        for step in range(steps):
            present = [m.steps[role][step] for m in measures if step in m.steps.get(role, {})]
            if total and len(present) / total >= threshold:
                note = sorted(Counter(n for _, n, _ in present).items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                vels = [v for v, _, _ in present]
                hits.append({"step": step, "role": role, "note": note,
                             "rel_velocity": float(np.mean([v / medians[role] for v in vels])) if medians.get(role) else 0.0,
                             "velocity": float(np.median(vels))})
    hits.sort(key=lambda h: (h["step"], h["role"]))
    return hits


def proposed_patterns(beats: Sequence[Measure], fills: Sequence[Measure]) -> dict[str, Any]:
    """Patterns de densité 0, 1, 2 par (timekeeper, figure), construits sur les probabilités par pas.

    Mesures `beat` groupées par (rôle du timekeeper, figure) ; groupe éligible : ≥ 20 mesures, ≥ 3 fichiers, aucun
    fichier au-delà de 60 %. Densité 0 : timekeeper seul (probabilité ≥ 0,5) ; 1 : plus pédale de charleston,
    grosse caisse, caisse claire et cross-stick ≥ 0,5 ; 2 : grosse caisse, caisse claire et cross-stick dès 0,25.
    Le poids est l'effectif de mesures du groupe. S'y ajoute en densité 2 un pattern de relance sur les `fill`
    (kick, caisse claire, cross-stick, toms, crash ≥ 0,25) si l'ensemble est éligible. Les figures `none`,
    `sparse` et `other` ne sont pas proposées : pas d'ossature commune.
    """
    out: dict[str, Any] = {"patterns": [], "skipped": []}
    if not beats:
        return out
    steps = beats[0].steps_per_bar
    medians = role_velocity_medians(beats)
    groups: dict[tuple[str, str], list[Measure]] = defaultdict(list)
    for m in beats:
        groups[(timekeeper_of(m), figure_of(m))].append(m)
    proposals = []
    for (role, fig), subset in sorted(groups.items()):
        if role == "none" or fig in ("none", "sparse", "other"):
            continue
        if not eligible(subset):
            out["skipped"].append({"group": f"{role}:{fig}", "n_measures": len(subset),
                                   "n_files": len({m.file for m in subset}),
                                   "reason": f"< {MIN_MEASURES_FOR_PROPOSAL} mesures, < {MIN_FILES_FOR_PROPOSAL} "
                                             f"fichiers ou un fichier > {MAX_FILE_SHARE_FOR_PROPOSAL:.0%} du groupe"})
            continue
        for density, thr in LEVELS.items():
            thresholds = {(role if k == "timekeeper" else k): v for k, v in thr.items()}
            hits = _subset_hits(subset, thresholds, medians, steps)
            if hits:
                proposals.append({"density": density, "weight": len(subset), "source": f"beat:{role}:{fig}",
                                  "n_files": len({m.file for m in subset}), "hits": hits})
    if fills and eligible(fills):
        fill_steps = fills[0].steps_per_bar
        hits = _subset_hits(fills, {r: FILL_THRESHOLD for r in FILL_ROLES}, role_velocity_medians(fills), fill_steps)
        if hits:
            proposals.append({"density": 2, "weight": len(fills), "source": "fill:all",
                              "n_files": len({m.file for m in fills}), "hits": hits})
    elif fills:
        out["skipped"].append({"group": "fill:all", "n_measures": len(fills), "n_files": len({m.file for m in fills}),
                               "reason": "groupe non éligible"})
    proposals.sort(key=lambda p: (p["density"], -p["weight"], p["source"]))
    out["patterns"] = proposals
    out["construction"] = ("chaque coup = (rôle, pas) dont la probabilité par pas dans le groupe atteint le seuil de "
                           "la densité ; jamais une mesure d'un enregistrement")
    out["thresholds"] = {str(d): t for d, t in LEVELS.items()}
    return out


def fill_summary(results: Sequence[FileResult]) -> dict[str, Any]:
    """Description des fichiers `fill` d'un groupe : position de la première et de la dernière attaque."""
    placed = [r.fill_position for r in results if r.fill_position]
    if not placed:
        return {"n_files": 0}
    first = Counter(p["first_beat_in_bar"] for p in placed)
    return {
        "n_files": len(placed),
        "first_beat_in_bar": {str(k): v for k, v in sorted(first.items())},
        "first_step": describe([p["first_step"] for p in placed]),
        "last_step": describe([p["last_step"] for p in placed]),
        "span_beats": describe([p["span_beats"] for p in placed]),
        "bars_touched": {str(k): v for k, v in sorted(Counter(p["bars_touched"] for p in placed).items())},
        "n_hits": describe([p["n_hits"] for p in placed]),
        "note": "`first_beat_in_bar` : temps (1 à 4) de la mesure où tombe la première attaque ; `first_step` / `last_step` : "
                "pas de la première et de la dernière attaque dans leur mesure ; `bars_touched` : mesures couvertes",
    }


# ---------------------------------------------------------------------------------------
# Passe complète


def slug(style: str) -> str:
    return "gmd-" + style.replace("/", "-")


def inventory(results: Sequence[FileResult]) -> list[dict[str, Any]]:
    """Une ligne par (style, type) : fichiers, mesures, minutes, feels, métriques, batteurs, fiabilité."""
    table: dict[tuple[str, str], list[FileResult]] = defaultdict(list)
    for r in results:
        table[(r.row.style, r.row.beat_type)].append(r)
    rows = []
    for (style, kind), items in sorted(table.items()):
        measured = [r for r in items if not r.reject]
        n_meas = sum(len(r.measures) for r in measured)
        drummers = {r.row.drummer for r in measured if r.measures}
        rows.append({
            "style": style, "family": style.split("/", 1)[0], "beat_type": kind,
            "n_files": len(items), "n_files_with_measures": sum(1 for r in measured if r.measures),
            "n_measures": n_meas, "minutes": sum(r.row.duration for r in items) / 60.0,
            "n_drummers": len(drummers),
            "meters": dict(sorted(Counter(r.row.time_signature for r in items).items())),
            "feels": dict(sorted(Counter(r.feel for r in measured).items())),
            "n_rejected": sum(1 for r in items if r.reject),
            "reliability": reliability(kind, len(measured), len(drummers), n_meas),
        })
    return rows


def style_block(style: str, items: Sequence[FileResult]) -> dict[str, Any]:
    """Un style : un groupe par (métrique, feel), `beat` et `fill` (statistiques, patterns proposés, position des fills).
    Clé de groupe : `4-4:straight`, `4-4:ternary`, `3-4:swing`…"""
    measured = [r for r in items if not r.reject]
    out: dict[str, Any] = {
        "n_files": len(items), "n_rejected": len(items) - len(measured),
        "rejected": [{"path": r.row.path, "reason": r.reject} for r in items if r.reject],
        "meters": dict(sorted(Counter(r.row.time_signature for r in items).items())),
        "minutes": sum(r.row.duration for r in items) / 60.0,
        "feel_by_file": {f"{k[0]}:{k[1]}:{k[2]}": v for k, v in sorted(
            Counter((r.row.beat_type, r.row.time_signature, r.feel) for r in measured).items())},
        "groups": {},
    }
    for meter, feel in sorted({(r.row.time_signature, r.feel) for r in measured}):
        pool = [r for r in measured if r.row.time_signature == meter and r.feel == feel]
        block: dict[str, Any] = {"meter": meter, "feel": feel}
        for kind in ("beat", "fill"):
            members = [r for r in pool if r.row.beat_type == kind]
            meas = [m for r in members for m in r.measures]
            if members:
                block[kind] = group_stats(meas, members) if meas else {"n_files": len(members), "n_measures": 0}
        beats = [m for r in pool if r.row.beat_type == "beat" for m in r.measures]
        fills = [m for r in pool if r.row.beat_type == "fill" for m in r.measures]
        if beats or fills:
            block["proposed_patterns"] = proposed_patterns(beats, fills)
            block["fill_position"] = fill_summary([r for r in pool if r.row.beat_type == "fill"])
            out["groups"][f"{meter}:{feel}"] = block
    return out


OWN_FOLDER_RULES = {"files_a": 3, "measures_a": 150, "files_b": 2, "measures_b": 300}
ALWAYS_OWN = frozenset({
    "latin/samba", "latin/brazilian-bossa", "blues/shuffle", "funk/purdieshuffle", "rock/shuffle",
    "afrocuban/bembe", "neworleans/secondline", "jazz/swing",
})
"""Styles secondaires nommés par le brief L2 (samba, bossa, shuffles, afro-cubain, second line) ou ternaires : dossier
propre même sous les seuils (leur fiabilité reste écrite)."""


def own_folder(style: str, items: Sequence[FileResult]) -> bool:
    """Un style secondaire a son dossier s'il est dans `ALWAYS_OWN`, ou a ≥ 3 fichiers `beat` et ≥ 150 mesures,
    ou ≥ 2 fichiers et ≥ 300 mesures (`OWN_FOLDER_RULES`). Les autres restent dans le dossier de leur famille."""
    if "/" not in style:
        return False
    beats = [r for r in items if r.row.beat_type == "beat" and r.measures]
    n = sum(len(r.measures) for r in beats)
    rules = OWN_FOLDER_RULES
    return (style in ALWAYS_OWN or (len(beats) >= rules["files_a"] and n >= rules["measures_a"])
            or (len(beats) >= rules["files_b"] and n >= rules["measures_b"]))


def provenance(results: Sequence[FileResult]) -> dict[str, Any]:
    return {
        "source": drums.SOURCE_NAME, "version": drums.SOURCE_VERSION, "url": drums.SOURCE_URL,
        "sha256": drums.SOURCE_SHA256, "licence": drums.SOURCE_LICENCE, "attribution": drums.ATTRIBUTION,
        "mention": "Groove MIDI Dataset v1.0.0, CC BY 4.0 (Google LLC) : " + drums.ATTRIBUTION,
        "counts": {
            "n_files": len(results),
            "n_files_measured": sum(1 for r in results if not r.reject),
            "n_files_rejected": sum(1 for r in results if r.reject),
            "n_measures": sum(len(r.measures) for r in results),
            "n_hits_unmapped_ignored": sum(r.unmapped for r in results),
        },
    }


GRID_DOC = {
    "straight": "16 pas en 4/4 (4 par pulsation, doubles croches) ; 12 en 3/4 et en 6/8",
    "swing": "même grille, pas 2 de chaque pulsation retardé au rapport r du fichier (0,56 ≤ r < 0,62)",
    "ternary": "triolets : 3 pas par pulsation, 12 pas en 4/4, 9 en 3/4 (shuffle, 12/8, swing appuyé r ≥ 0,62)",
}


def build_all(archive: zipfile.ZipFile, rows: Sequence[drums.FileRow]) -> dict[str, Any]:
    """Résultats de tous les fichiers + blocs par style, prêts à écrire."""
    results = analyse_archive(archive, rows)
    settle(results, archive)
    by_style: dict[str, list[FileResult]] = defaultdict(list)
    for r in results:
        by_style[r.row.style].append(r)
    blocks = {style: style_block(style, items) for style, items in sorted(by_style.items())}
    return {"results": results, "by_style": by_style, "blocks": blocks}


def settle(results: list[FileResult], archive: zipfile.ZipFile) -> None:
    """Un fichier `fill` sans preuve de feel (`evidence == none`) prend le feel majoritaire des fichiers `beat` de
    son style (à défaut, de sa famille) et ses mesures sont recalculées sur cette grille."""
    def dominant(pool: Iterable[FileResult]) -> str | None:
        c = Counter(r.feel for r in pool if r.row.beat_type == "beat" and not r.reject and r.evidence != "none")
        return c.most_common(1)[0][0] if c else None

    for r in results:
        if r.reject or r.row.beat_type != "fill" or r.evidence != "none":
            continue
        feel = dominant(x for x in results if x.row.style == r.row.style) or dominant(
            x for x in results if x.row.family == r.row.family)
        if feel and feel != r.feel:
            ratio = {"straight": 0.5, "ternary": 2 / 3}.get(feel, 0.6)
            perf = read_performance(archive.read(f"groove/{r.row.path}"))
            r.feel, r.ratio, r.evidence = feel, ratio, "inherited_from_beats"
            r.measures = measures_of(perf, r.row, feel, ratio)
            r.fill_position = fill_position(perf, r.row, feel, ratio)


def output_plan(built: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Dossier → contenu : une famille par dossier (`gmd-<famille>`) ; un style secondaire fourni a le sien."""
    by_style: dict[str, list[FileResult]] = built["by_style"]
    own = {s for s, items in by_style.items() if own_folder(s, items)}
    plan: dict[str, dict[str, Any]] = {}
    families = sorted({s.split("/", 1)[0] for s in by_style})
    for fam in families:
        styles = {s: built["blocks"][s] for s in sorted(by_style) if s.split("/", 1)[0] == fam}
        pointers = {s: slug(s) for s in styles if s in own}
        plan[slug(fam)] = {"scope": f"famille {fam}", "styles": {s: b for s, b in styles.items() if s not in own},
                           "own_folders": pointers,
                           "summary_of_own": {s: _compact(b) for s, b in styles.items() if s in own},
                           "files": [r for s in styles for r in by_style[s]]}
    for s in sorted(own):
        plan[slug(s)] = {"scope": f"style {s}", "styles": {s: built["blocks"][s]}, "own_folders": {},
                         "summary_of_own": {}, "files": by_style[s]}
    return plan


def _compact(block: dict[str, Any]) -> dict[str, Any]:
    """Résumé d'un style qui a son dossier : effectifs et groupes seulement."""
    out = {k: block[k] for k in ("n_files", "minutes", "meters", "feel_by_file")}
    out["groups"] = {g: {kind: {k: v[k] for k in ("n_files", "n_measures", "reliability") if k in v}
                         for kind, v in gb.items() if kind in ("beat", "fill")} for g, gb in block["groups"].items()}
    return out


def document(folder: str, content: dict[str, Any]) -> dict[str, Any]:
    results: list[FileResult] = content["files"]
    return {
        "command": COMMAND,
        "scope": content["scope"],
        "provenance": provenance(results),
        "role_table": role_table(),
        "grids": GRID_DOC,
        "feel_rules": {"swing_cuts": list(SWING_CUTS), "offbeat_window": list(OFFBEAT_WINDOW),
                       "sixteenth_tolerance": SIXTEENTH_TOLERANCE, "sixteenth_share": SIXTEENTH_SHARE,
                       "min_evidence": MIN_EVIDENCE},
        "reliability_thresholds": RELIABILITY,
        "inventory": inventory(results),
        "styles": content["styles"],
        "styles_with_own_folder": content["own_folders"],
        "styles_with_own_folder_summary": content["summary_of_own"],
    }


# ---------------------------------------------------------------------------------------
# README de chaque dossier


def _fmt(x: float | None, digits: int = 2) -> str:
    return "—" if x is None else f"{x:.{digits}f}"


def readme(folder: str, content: dict[str, Any]) -> str:
    results: list[FileResult] = content["files"]
    inv = inventory(results)
    prov = provenance(results)
    lines = [
        f"# `{folder}` — {content['scope']} (Groove MIDI Dataset, phase 019, L2)",
        "",
        "Mesures agrégées de la batterie d'un style du Groove MIDI Dataset v1.0.0 (Gillick et al., ICML 2019), ramenées à la",
        "grille du feel : probabilités par pas, vélocités, micro-timing par rôle, patterns par rôle, patterns proposés,",
        "fills et leur position. **Aucune mesure d'un enregistrement n'est copiée** : agrégats seulement (principe VII).",
        "",
        "## Licence et mention requise",
        "",
        f"- Source : {drums.SOURCE_NAME} {drums.SOURCE_VERSION}, <{drums.SOURCE_PAGE}>.",
        f"- Licence : **{drums.SOURCE_LICENCE}** (<https://creativecommons.org/licenses/by/4.0/>).",
        f"- SHA256 de l'archive, vérifié avant toute lecture : `{drums.SOURCE_SHA256}` (identique à `corpus/sources-jazz.md`).",
        f"- Mention à reprendre : « {drums.ATTRIBUTION} ».",
        "",
        "## Reproduire",
        "",
        "```sh",
        "make backing-gmd        # télécharge et vérifie l'archive, écrit corpus/gmd/manifest.jsonl, references/gmd-*",
        "```",
        "",
        f"Fichiers : `measures-drums.json` (ce dossier). Brut : `corpus/gmd/raw/` (cache gitignoré).",
        "",
        "## Effectifs",
        "",
        "| Style | Type | Fichiers | Mesures | Minutes | Batteurs | Métriques | Feel (fichiers) | Fiabilité |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for e in inv:
        feels = ", ".join(f"{k} {v}" for k, v in e["feels"].items()) or "—"
        meters = ", ".join(f"{k} {v}" for k, v in e["meters"].items())
        lines.append(f"| {e['style']} | {e['beat_type']} | {e['n_files']} | {e['n_measures']} | {e['minutes']:.1f} | "
                     f"{e['n_drummers']} | {meters} | {feels} | {e['reliability']} |")
    lines += [
        "",
        f"Total : {prov['counts']['n_files']} fichiers, {prov['counts']['n_measures']} mesures entières"
        + (f" ; {prov['counts']['n_files_rejected']} fichier(s) non mesuré(s) (métrique à un seul fichier : 5/4, 5/8)."
           if prov["counts"]["n_files_rejected"] else "."),
        "",
        "Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; "
        "**juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; "
        "**juste** ≥ 10 fichiers.",
        "",
        "## Ce que disent les mesures",
        "",
    ]
    for style, block in content["styles"].items():
        for key, group in block["groups"].items():
            beat = group.get("beat")
            if not beat or not beat.get("n_measures"):
                continue
            tk = beat["timekeeper"]
            main_tk = max(tk["roles"].items(), key=lambda kv: kv[1]["n"])[0]
            fig = max(tk["figures"].items(), key=lambda kv: kv[1]["n"])
            kick = beat["top_patterns"].get("kick", [])
            snare = beat["top_patterns"].get("snare", [])
            lines.append(f"- **{style}**, groupe `{key}` ({beat['n_files']} fichiers, {beat['n_measures']} mesures, "
                         f"{beat['bpm']['p50']:.0f} BPM médian, fiabilité {beat['reliability']}) : timekeeper `{main_tk}` "
                         f"({tk['roles'][main_tk]['share']:.0%}), figure `{fig[0]}` ({fig[1]['share']:.0%}) ; "
                         + (f"kick le plus fréquent {kick[0]['steps']} ({kick[0]['share']:.0%}) ; " if kick else "")
                         + (f"caisse claire {snare[0]['steps']} ({snare[0]['share']:.0%}) ; " if snare else "")
                         + f"{len(group['proposed_patterns']['patterns'])} patterns proposés.")
    if content["own_folders"]:
        lines += ["", "Styles secondaires détaillés dans leur propre dossier : "
                  + ", ".join(f"`{v}`" for v in content["own_folders"].values()) + "."]
    lines += [
        "",
        "## Grille et rôles",
        "",
        *(f"- `{k}` : {v}." for k, v in GRID_DOC.items()),
        "- Rôles : kick, snare, sidestick (cross-stick), hat_closed, hat_pedal, hat_open, ride, ride_bell, crash, tom_high, tom_mid, "
        "tom_low ; table Roland → GM dans le JSON (`role_table`).",
        "- Le GMD ne contient aucune percussion latine : les styles latins sont joués au kit (cross-stick, cloche de ride, toms).",
        "",
        "## Limites",
        "",
        "- Jeu sur kit électronique Roland TD-11 avec métronome : les vélocités et le micro-timing sont ceux de ce kit.",
        "- Dix batteurs au total ; un style à un ou deux fichiers décrit un batteur, pas un style (fiabilité `trop peu`).",
        "- Un fichier a un seul feel, décidé sur ses contretemps ; un fichier à feel mixte est classé sur sa majorité.",
        "- Le feel ternaire quantifie sur des triolets : une double croche y est ramenée au pas le plus proche ; la fidélité "
        "est dans `grid_fit.within_quarter_step`.",
        "- Les fills sont des fichiers isolés d'une à quatre mesures : `fill_position` donne leur début et leur fin dans la mesure.",
        "",
        "Jamais de fichier MIDI du GMD dans le dépôt (`corpus/gmd/raw/` gitignoré).",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------
# Résumé et CLI


def summary(inv: Sequence[dict[str, Any]]) -> str:
    out = [f"{'style':<28}{'type':<5}{'files':>6}{'meas':>7}{'min':>7}{'drum':>5}  {'feels':<28}fiabilité"]
    for e in inv:
        feels = ",".join(f"{k}:{v}" for k, v in e["feels"].items())
        out.append(f"{e['style']:<28}{e['beat_type']:<5}{e['n_files']:>6}{e['n_measures']:>7}{e['minutes']:>7.1f}"
                   f"{e['n_drummers']:>5}  {feels:<28}{e['reliability']}")
    return "\n".join(out)


def write_all(built: dict[str, Any], out_root: Path = REFERENCES_ROOT) -> list[str]:
    """Écrit un dossier par famille / style fourni et `gmd-inventory.json` ; renvoie les noms de dossier."""
    plan = output_plan(built)
    for folder, content in plan.items():
        write_json(out_root / folder / "measures-drums.json", document(folder, content))
        (out_root / folder / "README.md").write_text(readme(folder, content), encoding="utf-8")
    write_json(out_root / "gmd-inventory.json", {
        "command": COMMAND,
        "provenance": provenance(built["results"]),
        "folders": sorted(plan),
        "inventory": inventory(built["results"]),
    })
    return sorted(plan)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fetch", action="store_true", help="télécharge l'archive (SHA256 vérifié)")
    parser.add_argument("--manifest", action="store_true", help="écrit corpus/gmd/manifest.jsonl (tous les fichiers) et VERSION")
    parser.add_argument("--measures", action="store_true", help="écrit references/gmd-*/")
    parser.add_argument("--summary", action="store_true", help="affiche l'inventaire lisible (references/gmd-inventory.json)")
    parser.add_argument("--out-root", type=Path, default=REFERENCES_ROOT)
    args = parser.parse_args(argv)
    steps = args.fetch or args.manifest or args.measures or args.summary
    do_fetch = args.fetch or not steps
    do_manifest = args.manifest or not steps
    do_measures = args.measures or not steps
    try:
        if do_fetch:
            fetch(drums.SOURCE_URL, drums.ARCHIVE, drums.SOURCE_SHA256)
            print(f"archive vérifiée : {drums.ARCHIVE}")
        if do_manifest or do_measures:
            archive = drums.open_archive()
            if do_manifest:
                drums.write_manifest(archive)
                print(f"manifeste → {drums.MANIFEST}")
            if do_measures:
                rows = drums.parse_rows(drums.read_info_rows(archive))
                built = build_all(archive, rows)
                folders = write_all(built, args.out_root)
                print(f"{len(folders)} dossiers → {args.out_root}/gmd-*")
        if args.summary:
            path = args.out_root / "gmd-inventory.json"
            if not path.is_file():
                print(f"{path} absent : lancer --measures", file=sys.stderr)
                return 1
            print(summary(json.loads(path.read_text(encoding="utf-8"))["inventory"]))
    except (ValueError, FileNotFoundError, RuntimeError) as err:
        print(f"erreur : {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
