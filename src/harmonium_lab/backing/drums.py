"""Batterie de référence : Groove MIDI Dataset (GMD) ramené à la grille du profil moteur.

Source : Gillick, Roberts, Engel, Eck, Bamman, « Learning to Groove with Inverse Sequence
Transformations », ICML 2019 ; Groove MIDI Dataset v1.0.0 (archive MIDI seule), CC BY 4.0,
https://magenta.withgoogle.com/datasets/groove. Batteurs engagés, jeu sur Roland TD-11 avec
métronome (les ticks du MIDI sont alignés sur le métronome : la position en pulsations est
`tick / résolution`, quel que soit le tempo déclaré).

Sous-ensemble (4/4 seulement) :
- `core` : styles `jazz` et `jazz/swing` (cœur du profil) ;
- `jazz_other` : les autres `jazz/*` (funk, fusion, march, fast, linear…), hors cœur ;
- `neworleans` : `neworleans/*`, pour information ;
- `blues_shuffle` : `blues/shuffle`, variante blues.

Chaque mesure entière est un échantillon, `beat` et `fill` séparés. Une mesure est ramenée aux
16 pas du profil : 4 pulsations de 4 pas, le pas 2 de chaque pulsation retardé par le swing r.
r est mesuré PAR FICHIER (médiane de la position des attaques de ride/charleston fermé comprises
entre 0,45 et 0,85 de la pulsation), puis chaque attaque va à la position nominale swinguée la
plus proche parmi {0, r/2, r, r + (1 − r)/2} (et 1 = pulsation suivante).

Mesures retenues (« entières ») :
- `beat` : mesure dont la fin tombe dans le fichier (tolérance d'une demi-pulsation : la note éteinte prolonge la fin du fichier) ; la première
  mesure non vide n'est gardée que si sa première attaque tombe avant 0,9 pulsation (sinon le
  batteur est entré en cours de mesure) ; une mesure sans attaque est ignorée ;
- `fill` : les fichiers de relance s'arrêtent à la dernière attaque (durée 0,73–1,03 mesure) ;
  une mesure est gardée si le fichier la couvre à 70 % au moins, le reste étant silence.

Les sorties sont des agrégats : probabilités par pas, vélocités, patterns de mesure vus dans au
moins deux fichiers, patterns proposés construits à partir de probabilités par pas (jamais copiés
d'une mesure précise).

Usage : `python -m harmonium_lab.backing.drums [--fetch] [--manifest] [--measures] [--summary]`
(aucun drapeau d'étape : tout, dans l'ordre ; `--summary` relit/affiche le JSON).
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import mido
import numpy as np

from .corpus_cache import (
    REFERENCES,
    ROOT,
    describe,
    fetch,
    open_verified,
    percentiles,
    write_json,
    write_jsonl,
    write_version,
)

SOURCE_NAME = "Groove MIDI Dataset"
SOURCE_VERSION = "v1.0.0 (groove-v1.0.0-midionly.zip)"
SOURCE_URL = "https://storage.googleapis.com/magentadata/datasets/groove/groove-v1.0.0-midionly.zip"
SOURCE_SHA256 = "651cbc524ffb891be1a3e46d89dc82a1cecb09a57c748c7b45b844c4841dcc1e"
SOURCE_LICENCE = "CC-BY-4.0"
SOURCE_PAGE = "https://magenta.withgoogle.com/datasets/groove"
ATTRIBUTION = (
    "Gillick, Roberts, Engel, Eck, Bamman, Learning to Groove with Inverse Sequence "
    "Transformations, ICML 2019 ; Groove MIDI Dataset v1.0.0, Google LLC, CC BY 4.0 "
    "(https://creativecommons.org/licenses/by/4.0/)"
)
ARCHIVE = ROOT / "corpus" / "gmd" / "raw" / "groove-v1.0.0-midionly.zip"
MANIFEST = ROOT / "corpus" / "gmd" / "manifest.jsonl"
VERSION_FILE = ROOT / "corpus" / "gmd" / "VERSION"
OUTPUT = REFERENCES / "measures-drums.json"
COMMAND = "python -m harmonium_lab.backing.drums --measures"

STEPS = 16
STEPS_PER_BEAT = 4
BEATS_PER_BAR = 4

# Table Roland TD-11 → rôle et note GM équivalente. Source : page officielle du jeu, section
# « Drum Mapping » (colonnes Roland Mapping / GM Mapping / Paper Mapping), consultée le
# 2026-11-01. `gm` suit la colonne « Paper Mapping » pour les toms, les cymbales crash et la
# caisse claire (tête 38, rimshot 40 → 38) ; le cross-stick 37 et la cloche de ride 53 gardent
# leur note GM propre ; ride arc et bord (51, 59) → 51.
ROLAND_TABLE: dict[int, tuple[str, str, int]] = {
    # pitch: (nom Roland, rôle, note GM)
    36: ("Kick", "kick", 36),
    38: ("Snare (Head)", "snare", 38),
    40: ("Snare (Rim)", "snare", 38),
    37: ("Snare X-Stick", "snare", 37),
    48: ("Tom 1", "tom", 50),
    50: ("Tom 1 (Rim)", "tom", 50),
    45: ("Tom 2", "tom", 47),
    47: ("Tom 2 (Rim)", "tom", 47),
    43: ("Tom 3 (Head)", "tom", 43),
    58: ("Tom 3 (Rim)", "tom", 43),
    46: ("HH Open (Bow)", "hat_open", 46),
    26: ("HH Open (Edge)", "hat_open", 46),
    42: ("HH Closed (Bow)", "hat_closed", 42),
    22: ("HH Closed (Edge)", "hat_closed", 42),
    44: ("HH Pedal", "hat_pedal", 44),
    49: ("Crash 1 (Bow)", "crash", 49),
    55: ("Crash 1 (Edge)", "crash", 49),
    57: ("Crash 2 (Bow)", "crash", 49),
    52: ("Crash 2 (Edge)", "crash", 49),
    51: ("Ride (Bow)", "ride", 51),
    59: ("Ride (Edge)", "ride", 51),
    53: ("Ride (Bell)", "ride", 53),
}
ROLES = ("kick", "snare", "ride", "hat_closed", "hat_open", "hat_pedal", "crash", "tom")
TIMEKEEPER_ROLES = ("ride", "hat_closed")
"""Rôles dont les contretemps donnent le rapport de swing d'un fichier (par ordre de priorité)."""

# Groupes de styles (sous-ensemble 4/4).
CORE_STYLES = ("jazz", "jazz/swing")
SWING_WINDOW = (0.45, 0.85)
SWING_MIN_HITS = 8
SWING_FALLBACK = 2 / 3
SWING_BOUNDS = (0.5, 0.8)
FILL_MIN_COVERAGE = 0.7
BAR_TOLERANCE_BEATS = 0.5
FIRST_BAR_LATEST_ATTACK_BEATS = 0.9
TOP_N = 8
MIN_FILES_PER_PATTERN = 2
FILL_ROLES = ("kick", "snare", "tom", "crash")
FILL_THRESHOLD = 0.25
MIN_FILES_FOR_PROPOSAL = 3
MIN_MEASURES_FOR_PROPOSAL = 20
MAX_FILE_SHARE_FOR_PROPOSAL = 0.6

SPANG = (0, 4, 6, 8, 12, 14)
QUARTERS = (0, 4, 8, 12)
EIGHTHS = (0, 2, 4, 6, 8, 10, 12, 14)
OFFBEAT_STEPS = (2, 6, 10, 14)
DOTTED_STEPS = (3, 7, 11, 15)
RIDE_CLASSES = (
    "none", "quarters", "spang_a_lang", "spang_a_lang_ornamented", "eighths", "quarters_plus",
    "spang_partial", "other",
)


def role_of(pitch: int) -> str | None:
    """Rôle d'une hauteur Roland TD-11 (`None` si hors table)."""
    entry = ROLAND_TABLE.get(pitch)
    return entry[1] if entry else None


def gm_note(pitch: int) -> int | None:
    """Note GM équivalente d'une hauteur Roland TD-11 (`None` si hors table)."""
    entry = ROLAND_TABLE.get(pitch)
    return entry[2] if entry else None


def group_of(style: str) -> str | None:
    """Groupe d'un style GMD : `core`, `jazz_other`, `neworleans`, `blues_shuffle` ou `None`."""
    if style in CORE_STYLES:
        return "core"
    if style.startswith("jazz"):
        return "jazz_other"
    if style.startswith("neworleans"):
        return "neworleans"
    if style == "blues/shuffle":
        return "blues_shuffle"
    return None


# --------------------------------------------------------------------------------------
# Manifeste


@dataclass(frozen=True)
class FileRow:
    """Ligne de `info.csv` retenue."""
    path: str
    drummer: str
    session: str
    ident: str
    style: str
    bpm: int
    beat_type: str
    time_signature: str
    duration: float
    split: str

    @property
    def group(self) -> str | None:
        """Groupe E7 du style (`None` hors du sous-ensemble jazz / New Orleans / blues-shuffle)."""
        return group_of(self.style)

    @property
    def family(self) -> str:
        """Famille du style (`latin/brazilian-samba` → `latin`)."""
        return self.style.split("/", 1)[0]


def open_archive(path: Path = ARCHIVE) -> zipfile.ZipFile:
    """Ouvre l'archive GMD après vérification du SHA256."""
    return zipfile.ZipFile(open_verified(path, SOURCE_SHA256))


def read_info_rows(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    """Toutes les lignes brutes d'`info.csv`."""
    with archive.open("groove/info.csv") as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8")))


def parse_rows(rows: Iterable[dict[str, str]]) -> list[FileRow]:
    """Lignes d'`info.csv` → `FileRow` (tous styles, toutes métriques), triées par chemin."""
    return sorted((FileRow(
        path=row["midi_filename"], drummer=row["drummer"], session=row["session"],
        ident=row["id"], style=row["style"], bpm=int(row["bpm"]), beat_type=row["beat_type"],
        time_signature=row["time_signature"], duration=float(row["duration"]), split=row["split"],
    ) for row in rows), key=lambda r: r.path)


def read_info(archive: zipfile.ZipFile) -> list[FileRow]:
    """Lignes `info.csv` du sous-ensemble E7 : styles jazz*, neworleans*, blues/shuffle, en 4/4."""
    return select_rows(read_info_rows(archive))


def select_rows(rows: Iterable[dict[str, str]]) -> list[FileRow]:
    """Filtre les lignes d'`info.csv` du sous-ensemble E7 (4/4 ; styles du sous-ensemble)."""
    return [r for r in parse_rows(rows) if r.group is not None and r.time_signature == "4-4"]


def manifest_rows(rows: Sequence[FileRow]) -> list[dict[str, Any]]:
    """Une ligne de manifeste par fichier MIDI : faits d'`info.csv`, aucune note. `group` : groupe
    du sous-ensemble E7 (`null` hors sous-ensemble) ; `family` : premier élément du style."""
    return [{
        "path": r.path, "id": r.ident, "drummer": r.drummer, "session": r.session,
        "style": r.style, "family": r.family, "group": r.group, "bpm": r.bpm, "beat_type": r.beat_type,
        "time_signature": r.time_signature, "duration": r.duration, "split": r.split,
        "licence": SOURCE_LICENCE,
    } for r in rows]


def write_manifest(archive: zipfile.ZipFile) -> list[FileRow]:
    """Écrit `corpus/gmd/manifest.jsonl` (TOUS les fichiers : phase 019, L2) et `VERSION` ; renvoie
    les lignes du sous-ensemble E7 (jazz*, neworleans*, blues/shuffle en 4/4)."""
    info = parse_rows(read_info_rows(archive))
    text = write_jsonl(MANIFEST, manifest_rows(info))
    write_version(VERSION_FILE, {
        "version": SOURCE_VERSION,
        "source": SOURCE_NAME,
        "url": SOURCE_URL,
        "sha256": SOURCE_SHA256,
        "licence": SOURCE_LICENCE,
        "attribution": ATTRIBUTION,
        "date_source": "2019-05-01",
        "subset": f"tous les styles d'info.csv ; {len(info)} fichiers MIDI (4/4, 3/4, 6/8, 5/4, 5/8) ; "
                  "le champ `group` marque le sous-ensemble E7 (jazz*, neworleans*, blues/shuffle en 4/4)",
    }, text)
    return select_rows(read_info_rows(archive))


# --------------------------------------------------------------------------------------
# Lecture MIDI et quantification


@dataclass(frozen=True)
class Hit:
    """Attaque : position en pulsations (noires) depuis le début du fichier, hauteur, vélocité."""
    beat: float
    pitch: int
    velocity: int


@dataclass(frozen=True)
class Performance:
    """Attaques d'un fichier et fin du fichier (en pulsations, dernière note éteinte comprise)."""
    hits: tuple[Hit, ...]
    end_beat: float
    unmapped: int = 0


def read_performance(data: bytes) -> Performance | None:
    """Lit un MIDI de batterie : attaques (note_on de vélocité > 0) en pulsations.

    La position est `tick / résolution` : indépendante du tempo (le fichier suit le métronome,
    y compris avec des changements de tempo). Renvoie `None` si la métrique n'est pas 4/4 de
    bout en bout (mesure variable) ; une absence de métrique signifie 4/4 (valeur par défaut MIDI).
    """
    midi = mido.MidiFile(file=io.BytesIO(data))
    ppq = midi.ticks_per_beat
    hits: list[Hit] = []
    unmapped = 0
    end_tick = 0
    for track in midi.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == "time_signature" and (msg.numerator, msg.denominator) != (4, 4):
                return None
            if msg.type in ("note_on", "note_off"):
                end_tick = max(end_tick, tick)
            if msg.type == "note_on" and msg.velocity > 0:
                if role_of(msg.note) is None:
                    unmapped += 1
                    continue
                hits.append(Hit(tick / ppq, msg.note, msg.velocity))
    hits.sort(key=lambda h: (h.beat, h.pitch))
    return Performance(tuple(hits), end_tick / ppq, unmapped)


def swing_ratio(hits: Sequence[Hit]) -> tuple[float | None, int]:
    """Rapport de swing d'un fichier : médiane de la position (fraction de pulsation) des attaques
    comprises dans `SWING_WINDOW`, au ride d'abord, sinon au charleston fermé (les rôles de
    `TIMEKEEPER_ROLES`, dans l'ordre : un charleston droit ne dilue pas un ride swingué).
    Renvoie `(rapport, effectif)` ; rapport `None` s'il y a moins de `SWING_MIN_HITS` attaques
    de contretemps pour tous les rôles (l'effectif est alors celui du dernier rôle essayé)."""
    low, high = SWING_WINDOW
    inside: list[float] = []
    for role in TIMEKEEPER_ROLES:
        fractions = [h.beat % 1.0 for h in hits if role_of(h.pitch) == role]
        inside = [f for f in fractions if low <= f <= high]
        if len(inside) >= SWING_MIN_HITS:
            return float(np.median(inside)), len(inside)
    return None, len(inside)


def effective_ratio(measured: float | None) -> float:
    """Rapport employé pour quantifier : mesuré (borné) ou repli triolet sans contretemps."""
    if measured is None:
        return SWING_FALLBACK
    return min(max(measured, SWING_BOUNDS[0]), SWING_BOUNDS[1])


def nominal_positions(ratio: float) -> tuple[float, float, float, float]:
    """Positions nominales (fraction de pulsation) des 4 pas d'une pulsation swinguée."""
    return (0.0, ratio / 2, ratio, ratio + (1 - ratio) / 2)


def quantize(beat: float, ratio: float) -> tuple[int, int]:
    """Position en pulsations → `(index de pulsation, pas dans la pulsation 0..3)`.

    Plus proche position nominale swinguée de la pulsation courante, ou de la pulsation suivante
    (position 1) ; une attaque juste avant le temps passe donc au pas 0 de la pulsation suivante.
    """
    base = int(np.floor(beat + 1e-9))
    frac = beat - base
    candidates = [(abs(frac - pos), s) for s, pos in enumerate(nominal_positions(ratio))]
    candidates.append((abs(1.0 - frac), 4))
    _, step = min(candidates)
    if step == 4:
        return base + 1, 0
    return base, step


@dataclass
class Measure:
    """Une mesure ramenée aux 16 pas : `steps[rôle][pas] = (vélocité max, note GM)`."""
    file: str
    style: str
    beat_type: str
    ratio: float
    steps: dict[str, dict[int, tuple[int, int]]] = field(default_factory=dict)

    def role_steps(self, role: str) -> tuple[int, ...]:
        return tuple(sorted(self.steps.get(role, {})))


def measures_of(perf: Performance, row: FileRow, ratio: float) -> list[Measure]:
    """Mesures entières d'un fichier, quantifiées avec le rapport `ratio` (règles du module)."""
    bar_beats = BEATS_PER_BAR
    by_bar: dict[int, Measure] = {}
    first_attack: dict[int, float] = {}
    for hit in perf.hits:
        beat_index, sub = quantize(hit.beat, ratio)
        bar, step = divmod(beat_index, BEATS_PER_BAR)
        step = step * STEPS_PER_BEAT + sub
        role = role_of(hit.pitch)
        assert role is not None
        measure = by_bar.setdefault(bar, Measure(row.path, row.style, row.beat_type, ratio))
        first_attack.setdefault(bar, hit.beat)
        slot = measure.steps.setdefault(role, {})
        previous = slot.get(step)
        note = gm_note(hit.pitch)
        assert note is not None
        if previous is None or hit.velocity > previous[0]:
            slot[step] = (hit.velocity, note)
    kept: list[Measure] = []
    first_bar = min(by_bar) if by_bar else None
    for bar in sorted(by_bar):
        start = bar * bar_beats
        if row.beat_type == "fill":
            complete = perf.end_beat >= start + FILL_MIN_COVERAGE * bar_beats
        else:
            complete = start + bar_beats <= perf.end_beat + BAR_TOLERANCE_BEATS
            if bar == first_bar and first_attack[bar] - start > FIRST_BAR_LATEST_ATTACK_BEATS:
                complete = False
        if complete:
            kept.append(by_bar[bar])
    return kept


# --------------------------------------------------------------------------------------
# Agrégation


def ride_class(measure: Measure) -> str:
    """Classe de la figure de ride d'une mesure (ensemble de pas exact ou inclusion)."""
    steps = set(measure.role_steps("ride"))
    if not steps:
        return "none"
    if steps == set(QUARTERS):
        return "quarters"
    if steps == set(SPANG):
        return "spang_a_lang"
    if set(SPANG) < steps:
        return "spang_a_lang_ornamented"
    if set(EIGHTHS) <= steps:
        return "eighths"
    if set(QUARTERS) <= steps:
        return "quarters_plus"
    if len(steps & set(SPANG)) >= 4:
        return "spang_partial"
    return "other"


def _share(n: int, total: int) -> float:
    return n / total if total else 0.0


def _rel(velocity: int, median: float) -> float:
    return velocity / median if median else 0.0


def role_velocity_medians(measures: Sequence[Measure]) -> dict[str, float]:
    """Vélocité médiane de chaque rôle sur tous ses coups du groupe."""
    pool: dict[str, list[int]] = defaultdict(list)
    for m in measures:
        for role, slots in m.steps.items():
            pool[role].extend(v for v, _ in slots.values())
    return {role: float(np.median(v)) for role, v in pool.items()}


def per_step(measures: Sequence[Measure], medians: dict[str, float]) -> dict[str, list[dict[str, Any]]]:
    """Par rôle et par pas : effectif, probabilité, vélocité absolue et relative (part de la
    vélocité médiane du rôle)."""
    total = len(measures)
    out: dict[str, list[dict[str, Any]]] = {}
    for role in ROLES:
        rows = []
        for step in range(STEPS):
            vels = [m.steps[role][step][0] for m in measures if step in m.steps.get(role, {})]
            entry: dict[str, Any] = {"step": step, "n": len(vels), "prob": _share(len(vels), total)}
            if vels:
                rels = [_rel(v, medians[role]) for v in vels]
                entry["velocity"] = {"mean": float(np.mean(vels)), **percentiles(vels, (10, 50, 90))}
                entry["rel_velocity"] = {"mean": float(np.mean(rels)), **percentiles(rels, (10, 50, 90))}
            rows.append(entry)
        out[role] = rows
    return out


def top_patterns(measures: Sequence[Measure]) -> dict[str, Any]:
    """Patterns de mesure les plus fréquents : par rôle (ride, kick, snare, hat_pedal) et
    combinés kick + snare. Seuls les patterns vus dans au moins `MIN_FILES_PER_PATTERN`
    fichiers sont listés (aucun motif propre à un enregistrement)."""
    total = len(measures)

    def rank(keyed: list[tuple[Any, str]]) -> list[dict[str, Any]]:
        counts: Counter = Counter(k for k, _ in keyed)
        files: dict[Any, set[str]] = defaultdict(set)
        for k, f in keyed:
            files[k].add(f)
        listed = sorted(
            (k for k in counts if len(files[k]) >= MIN_FILES_PER_PATTERN),
            key=lambda k: (-counts[k], str(k)),
        )[:TOP_N]
        return [{"key": k, "n": counts[k], "share": _share(counts[k], total), "n_files": len(files[k])}
                for k in listed]

    out: dict[str, Any] = {}
    for role in ("ride", "kick", "snare", "hat_pedal"):
        ranked = rank([(m.role_steps(role), m.file) for m in measures])
        out[role] = [{"steps": list(r["key"]), "n": r["n"], "share": r["share"], "n_files": r["n_files"]}
                     for r in ranked]
    combined = rank([((m.role_steps("kick"), m.role_steps("snare")), m.file) for m in measures])
    out["kick_snare"] = [{"kick": list(r["key"][0]), "snare": list(r["key"][1]), "n": r["n"],
                          "share": r["share"], "n_files": r["n_files"]} for r in combined]
    return out


def ride_figures(measures: Sequence[Measure]) -> dict[str, Any]:
    """Parts des figures de ride (classes exclusives) et indicateurs complémentaires."""
    total = len(measures)
    classes = Counter(ride_class(m) for m in measures)
    with_ride = [m for m in measures if m.steps.get("ride")]
    dotted = sum(1 for m in with_ride if set(m.role_steps("ride")) & set(DOTTED_STEPS))
    return {
        "definitions": {
            "none": "aucune attaque de ride (charleston en croches, balais, etc.)",
            "quarters": "pas 0, 4, 8, 12 exactement (pulsation à la noire seule)",
            "spang_a_lang": "pas 0, 4, 6, 8, 12, 14 exactement (figure classique)",
            "spang_a_lang_ornamented": "contient la figure classique plus d'autres pas",
            "eighths": "contient les 8 pas pairs (croches swinguées continues)",
            "quarters_plus": "contient les 4 pulsations plus d'autres pas, hors figures ci-dessus",
            "spang_partial": "au moins 4 des 6 pas de la figure classique, sans les 4 pulsations complètes",
            "other": "toute autre mesure avec ride (figures éparses, ghost, cloche seule)",
        },
        "classes": {c: {"n": classes.get(c, 0), "share": _share(classes.get(c, 0), total)}
                    for c in RIDE_CLASSES},
        "with_dotted_eighth_steps": {"n": dotted, "share": _share(dotted, total),
                                     "note": "au moins une attaque de ride aux pas 3, 7, 11 ou 15"},
        "n_measures_with_ride": len(with_ride),
    }


def densities(measures: Sequence[Measure]) -> dict[str, Any]:
    """Coups par mesure et par rôle ; kick au 1ᵉʳ temps ; caisse claire en contretemps."""
    total = len(measures)
    counts = {role: [len(m.steps.get(role, {})) for m in measures] for role in ROLES}
    snare_off = [sum(1 for s in m.steps.get("snare", {}) if s in OFFBEAT_STEPS) for m in measures]
    snare_dot = [sum(1 for s in m.steps.get("snare", {}) if s in DOTTED_STEPS) for m in measures]
    snare_any = [len(m.steps.get("snare", {})) for m in measures]
    kick_one = sum(1 for m in measures if 0 in m.steps.get("kick", {}))
    pedal24 = sum(1 for m in measures if 4 in m.steps.get("hat_pedal", {}) and 12 in m.steps["hat_pedal"])
    pedal_any = sum(1 for m in measures if m.steps.get("hat_pedal"))
    pedal_steps = Counter()
    for m in measures:
        pedal_steps.update(m.steps.get("hat_pedal", {}).keys())
    return {
        "hits_per_measure": {role: describe(counts[role]) for role in ROLES},
        "kick_on_beat_1": {"n": kick_one, "share": _share(kick_one, total)},
        "snare_offbeat_steps_2_6_10_14": {
            "n_measures": sum(1 for c in snare_off if c), "share": _share(sum(1 for c in snare_off if c), total),
            "hits_per_measure": describe(snare_off)},
        "snare_steps_3_7_11_15": {
            "n_measures": sum(1 for c in snare_dot if c), "share": _share(sum(1 for c in snare_dot if c), total),
            "hits_per_measure": describe(snare_dot)},
        "snare_any": {"n_measures": sum(1 for c in snare_any if c),
                      "share": _share(sum(1 for c in snare_any if c), total)},
        "hat_pedal_beats_2_4": {
            "n_both_steps_4_and_12": pedal24, "share_both": _share(pedal24, total),
            "n_measures_with_pedal": pedal_any, "share_with_pedal": _share(pedal_any, total),
            "n_step_4": pedal_steps.get(4, 0), "n_step_12": pedal_steps.get(12, 0),
        },
    }


def ride_accent(measures: Sequence[Measure]) -> dict[str, Any]:
    """Vélocité du ride sur la pulsation (pas 0 mod 4) et sur le contretemps (pas 2 mod 4), en
    absolu et en part de la médiane du ride ; rapport contretemps / pulsation par fichier."""
    on, off = defaultdict(list), defaultdict(list)
    for m in measures:
        for step, (vel, _) in m.steps.get("ride", {}).items():
            if step % STEPS_PER_BEAT == 0:
                on[m.file].append(vel)
            elif step % STEPS_PER_BEAT == 2:
                off[m.file].append(vel)
    all_on = [v for f in on.values() for v in f]
    all_off = [v for f in off.values() for v in f]
    ratios = [float(np.median(off[f]) / np.median(on[f])) for f in on
              if len(on[f]) >= 20 and len(off.get(f, ())) >= 20]
    return {
        "on_beat_steps_0_4_8_12": describe(all_on, (10, 50, 90)),
        "offbeat_steps_2_6_10_14": describe(all_off, (10, 50, 90)),
        "offbeat_over_on_beat_mean": (float(np.mean(all_off) / np.mean(all_on)) if all_on and all_off else None),
        "per_file_median_ratio": describe(ratios),
    }


def note_shares(measures: Sequence[Measure]) -> dict[str, dict[str, int]]:
    """Effectifs des notes GM par rôle (sans position)."""
    out: dict[str, Counter] = defaultdict(Counter)
    for m in measures:
        for role, slots in m.steps.items():
            for _, note in slots.values():
                out[role][note] += 1
    return {role: {str(n): c for n, c in sorted(counter.items())} for role, counter in sorted(out.items())}


def group_stats(measures: Sequence[Measure]) -> dict[str, Any]:
    """Toutes les mesures agrégées d'un groupe (`core`/`beat`, etc.)."""
    files = Counter(m.file for m in measures)
    total = len(measures)
    medians = role_velocity_medians(measures)
    return {
        "n_measures": total,
        "n_files": len(files),
        "max_file_share": _share(max(files.values()), total) if files else 0.0,
        "n_hits": sum(len(s) for m in measures for s in m.steps.values()),
        "velocity_median_by_role": medians,
        "per_step": per_step(measures, medians),
        "top_patterns": top_patterns(measures),
        "ride_figures": ride_figures(measures),
        "densities": densities(measures),
        "ride_accent": ride_accent(measures),
        "gm_notes": note_shares(measures),
    }


# --------------------------------------------------------------------------------------
# Patterns proposés (mappables sur `[[patterns]]`)


def _subset_hits(measures: Sequence[Measure], role_thresholds: dict[str, float],
                 medians: dict[str, float]) -> list[dict[str, Any]]:
    """Coups d'un pattern construit à partir des probabilités par pas du sous-ensemble : pour
    chaque rôle et chaque pas, un coup si la part des mesures avec attaque ≥ seuil du rôle ;
    note GM dominante du (rôle, pas) ; vélocité relative moyenne."""
    total = len(measures)
    hits = []
    for role, threshold in role_thresholds.items():
        for step in range(STEPS):
            present = [m.steps[role][step] for m in measures if step in m.steps.get(role, {})]
            if total and len(present) / total >= threshold:
                notes = Counter(n for _, n in present)
                note = sorted(notes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                vels = [v for v, _ in present]
                hits.append({
                    "step": step, "role": role, "note": note,
                    "rel_velocity": float(np.mean([_rel(v, medians[role]) for v in vels])),
                    "velocity": float(np.median(vels)),
                })
    hits.sort(key=lambda h: (h["step"], h["role"]))
    return hits


def _eligible(measures: Sequence[Measure]) -> bool:
    files = Counter(m.file for m in measures)
    return (len(measures) >= MIN_MEASURES_FOR_PROPOSAL and len(files) >= MIN_FILES_FOR_PROPOSAL
            and max(files.values()) / len(measures) <= MAX_FILE_SHARE_FOR_PROPOSAL)


def _merge(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fusionne les patterns de même densité et mêmes (pas, rôle, note) : poids additionnés."""
    merged: dict[tuple, dict[str, Any]] = {}
    for p in proposals:
        key = (p["density"], tuple((h["step"], h["role"], h["note"]) for h in p["hits"]))
        if key in merged:
            merged[key]["weight"] += p["weight"]
            merged[key]["sources"] = sorted(set(merged[key]["sources"]) | set(p["sources"]))
        else:
            merged[key] = {**p, "sources": sorted(p["sources"])}
    return sorted(merged.values(), key=lambda p: (p["density"], -p["weight"], str([h["step"] for h in p["hits"]])))


def proposed_patterns(beats: Sequence[Measure], fills: Sequence[Measure]) -> dict[str, Any]:
    """Patterns de densité 0, 1, 2 construits à partir des probabilités par pas, par figure de ride.

    Les mesures `beat` sont groupées par classe de ride (≥ 20 mesures, ≥ 3 fichiers, aucun
    fichier au-delà de 60 % du groupe) ; dans chaque groupe :
    - densité 0 (ossature) : ride seul, pas de probabilité ≥ 0,5 ;
    - densité 1 (principal) : ride et pédale de charleston ≥ 0,5, kick et caisse claire ≥ 0,5 ;
    - densité 2 (relances) : comme la densité 1, kick et caisse claire (comping) dès 0,25.
    Le poids est l'effectif de mesures du groupe. S'y ajoute, en densité 2, un pattern de
    relance construit sur l'ensemble des mesures `fill` (kick, caisse claire, toms, crash ≥ 0,25) quand il est éligible.
    Les groupes `none` (pas de ride) et `other` (figures éparses) ne sont pas proposés : sans
    ossature de ride commune, leurs probabilités par pas ne forment pas un pattern.
    """
    medians = role_velocity_medians(beats)
    fill_medians = role_velocity_medians(fills)
    classes: dict[str, list[Measure]] = defaultdict(list)
    for m in beats:
        classes[ride_class(m)].append(m)
    proposals: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    levels = {
        0: {"ride": 0.5},
        1: {"ride": 0.5, "hat_pedal": 0.5, "kick": 0.5, "snare": 0.5},
        2: {"ride": 0.5, "hat_pedal": 0.5, "kick": 0.25, "snare": 0.25},
    }
    for cls in RIDE_CLASSES:
        subset = classes.get(cls, [])
        if cls in ("none", "other") or not subset:
            continue
        if not _eligible(subset):
            skipped.append({"class": cls, "n_measures": len(subset),
                            "n_files": len({m.file for m in subset}),
                            "reason": f"< {MIN_MEASURES_FOR_PROPOSAL} mesures, < {MIN_FILES_FOR_PROPOSAL} fichiers "
                                      f"ou un fichier > {MAX_FILE_SHARE_FOR_PROPOSAL:.0%} du groupe"})
            continue
        for density, thresholds in levels.items():
            hits = _subset_hits(subset, thresholds, medians)
            if hits:
                proposals.append({"density": density, "weight": len(subset), "sources": [f"beat:{cls}"],
                                  "n_files": len({m.file for m in subset}), "hits": hits})
    if _eligible(fills):
        hits = _subset_hits(fills, {role: FILL_THRESHOLD for role in FILL_ROLES}, fill_medians)
        if hits:
            proposals.append({"density": 2, "weight": len(fills), "sources": ["fill:all"],
                              "n_files": len({m.file for m in fills}), "hits": hits})
    else:
        skipped.append({"class": "fill:all", "n_measures": len(fills), "n_files": len({m.file for m in fills}),
                        "reason": "groupe non éligible"})
    return {
        "construction": "chaque coup = (rôle, pas) dont la probabilité par pas dans le groupe de mesures "
                        "atteint le seuil de la densité ; jamais une mesure d'un enregistrement",
        "thresholds": {str(d): t for d, t in levels.items()},
        "fill_threshold": FILL_THRESHOLD,
        "fill_roles": list(FILL_ROLES),
        "note": "note = note GM dominante du (rôle, pas) ; rel_velocity = part de la vélocité médiane du "
                "rôle (moyenne sur les coups du pas) ; velocity = médiane absolue (0..127)",
        "patterns": _merge(proposals),
        "skipped": skipped,
    }


# --------------------------------------------------------------------------------------
# Passe complète


@dataclass
class FileResult:
    row: FileRow
    ratio: float | None
    n_offbeat: int
    measures: list[Measure]
    unmapped: int
    metre_skipped: bool = False


def analyse_archive(archive: zipfile.ZipFile, rows: Sequence[FileRow]) -> list[FileResult]:
    """Lit chaque MIDI du sous-ensemble : rapport de swing, quantification, mesures entières."""
    results = []
    for row in rows:
        perf = read_performance(archive.read(f"groove/{row.path}"))
        if perf is None:
            results.append(FileResult(row, None, 0, [], 0, metre_skipped=True))
            continue
        measured, n_off = swing_ratio(perf.hits)
        results.append(FileResult(row, measured, n_off, measures_of(perf, row, effective_ratio(measured)),
                                  perf.unmapped))
    return results


def swing_distribution(results: Sequence[FileResult]) -> dict[str, Any]:
    """Distribution des rapports de swing par fichier, par style et par groupe."""
    def block(items: Sequence[FileResult]) -> dict[str, Any]:
        measured = [r.ratio for r in items if r.ratio is not None]
        return {"n_files": len(items), "n_files_measured": len(measured),
                "n_files_fallback": len(items) - len(measured),
                **{k: v for k, v in describe(measured).items() if k != "n"}}
    by_style: dict[str, list[FileResult]] = defaultdict(list)
    by_group: dict[str, list[FileResult]] = defaultdict(list)
    by_type: dict[str, list[FileResult]] = defaultdict(list)
    for r in results:
        if r.row.beat_type == "beat":
            by_style[r.row.style].append(r)
            by_group[r.row.group].append(r)
        if r.row.group == "core":
            by_type[r.row.beat_type].append(r)
    core_files = sorted(
        ({"bpm": r.row.bpm, "beat_type": r.row.beat_type, "style": r.row.style, "n_offbeat_hits": r.n_offbeat,
          "ratio": r.ratio} for r in results if r.row.group == "core" and r.row.beat_type == "beat"),
        key=lambda d: (d["bpm"], d["style"], d["n_offbeat_hits"]))
    return {
        "definition": f"médiane par fichier des positions (fraction de pulsation) des attaques de ride et de "
                      f"charleston fermé entre {SWING_WINDOW[0]} et {SWING_WINDOW[1]} ; au moins "
                      f"{SWING_MIN_HITS} attaques, sinon repli {SWING_FALLBACK:.3f} ; borné à "
                      f"{SWING_BOUNDS[0]}..{SWING_BOUNDS[1]} pour la quantification",
        "scope": "by_style et by_group : fichiers `beat` (un fichier de relance ne dure que ~1 mesure : "
                 "peu de contretemps, repli fréquent) ; core_by_beat_type : cœur, beat et fill séparés",
        "by_style": {s: block(v) for s, v in sorted(by_style.items())},
        "by_group": {g: block(v) for g, v in sorted(by_group.items())},
        "core_by_beat_type": {t: block(v) for t, v in sorted(by_type.items())},
        "core_beat_files": core_files,
    }


def inventory(results: Sequence[FileResult]) -> list[dict[str, Any]]:
    """Comptes par style et type : fichiers du manifeste, fichiers donnant des mesures, mesures."""
    table: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"n_files": 0, "n_files_with_measures": 0,
                                                                        "n_measures": 0})
    for r in results:
        entry = table[(r.row.style, r.row.beat_type)]
        entry["n_files"] += 1
        entry["n_measures"] += len(r.measures)
        entry["n_files_with_measures"] += 1 if r.measures else 0
    return [{"style": s, "beat_type": t, "group": group_of(s), **v} for (s, t), v in sorted(table.items())]


def build_measures(archive: zipfile.ZipFile, rows: Sequence[FileRow]) -> dict[str, Any]:
    """JSON complet de `references/wjazzd-swing/measures-drums.json`."""
    results = analyse_archive(archive, rows)
    core = [r for r in results if r.row.group == "core"]
    beats = [m for r in core if r.row.beat_type == "beat" for m in r.measures]
    fills = [m for r in core if r.row.beat_type == "fill" for m in r.measures]
    blues = [m for r in results if r.row.group == "blues_shuffle" for m in r.measures]
    other = [m for r in results if r.row.group == "jazz_other" and r.row.beat_type == "beat" for m in r.measures]
    swing_only = [m for r in core if r.row.style == "jazz/swing" for m in r.measures]
    nola = [m for r in results if r.row.group == "neworleans" and r.row.beat_type == "beat" for m in r.measures]
    return {
        "command": COMMAND,
        "provenance": {
            "source": SOURCE_NAME,
            "version": SOURCE_VERSION,
            "url": SOURCE_URL,
            "sha256": SOURCE_SHA256,
            "licence": SOURCE_LICENCE,
            "attribution": ATTRIBUTION,
            "subset": "styles jazz, jazz/swing (cœur) ; jazz/* autres, neworleans/*, blues/shuffle (séparés) ; "
                      "4/4 seulement ; mesures entières (règles dans le module drums.py)",
            "counts": {
                "n_files": len(results),
                "n_files_core": len(core),
                "n_measures": sum(len(r.measures) for r in results),
                "n_measures_core_beat": len(beats),
                "n_measures_core_fill": len(fills),
                "n_hits_mapped": sum(len(s) for r in results for m in r.measures for s in m.steps.values()),
                "n_unmapped_pitches_ignored": sum(r.unmapped for r in results),
                "n_files_variable_metre_skipped": sum(1 for r in results if r.metre_skipped),
            },
        },
        "role_table": {
            "source": f"{SOURCE_PAGE}, section « Drum Mapping » (Roland TD-11 → GM), consultée le 2026-11-01",
            "pitches": {str(p): {"roland": v[0], "role": v[1], "gm": v[2]} for p, v in sorted(ROLAND_TABLE.items())},
        },
        "grid": {"steps_per_measure": STEPS, "steps_per_beat": STEPS_PER_BEAT,
                 "nominal_positions": "{0, r/2, r, r + (1-r)/2} par pulsation, r = rapport du fichier"},
        "inventory": inventory(results),
        "swing_ratio": swing_distribution(results),
        "core": {"beat": group_stats(beats), "fill": group_stats(fills)},
        "swing_only_beat_and_fill": group_stats(swing_only),
        "blues_shuffle": group_stats(blues),
        "jazz_other_beat": group_stats(other),
        "neworleans_beat": group_stats(nola),
        "proposed_patterns": proposed_patterns(beats, fills),
    }


# --------------------------------------------------------------------------------------
# Résumé lisible


def summary(data: dict[str, Any]) -> str:
    """Résumé texte du JSON de mesures."""
    out = []
    prov = data["provenance"]
    out.append(f"{prov['source']} {prov['version']} — {prov['licence']}")
    out.append(f"fichiers {prov['counts']['n_files']} (cœur {prov['counts']['n_files_core']}), "
               f"mesures cœur beat {prov['counts']['n_measures_core_beat']} / fill {prov['counts']['n_measures_core_fill']}")
    out.append("\nInventaire (style, type : fichiers / avec mesures / mesures)")
    for e in data["inventory"]:
        out.append(f"  {e['style']:<22}{e['beat_type']:<5} {e['n_files']:>3} / {e['n_files_with_measures']:>3} / {e['n_measures']:>5}")
    out.append("\nRapport de swing par fichier (n mesurés, p10 p50 p90)")
    for s, b in data["swing_ratio"]["by_style"].items():
        if b["n_files_measured"]:
            out.append(f"  {s:<22} {b['n_files_measured']:>3}/{b['n_files']:<3} "
                       f"{b['p10']:.3f} {b['p50']:.3f} {b['p90']:.3f}")
    for label, key in (("beat", "beat"), ("fill", "fill")):
        g = data["core"][key]
        out.append(f"\nCœur {label} : {g['n_measures']} mesures, {g['n_files']} fichiers (fichier max {g['max_file_share']:.0%})")
        for role in ("ride", "hat_pedal", "kick", "snare"):
            probs = " ".join(f"{s['prob']:.2f}" for s in g["per_step"][role])
            out.append(f"  P({role:<9}) {probs}")
        if key == "beat":
            figs = g["ride_figures"]["classes"]
            out.append("  ride : " + ", ".join(f"{c} {v['share']:.0%}" for c, v in figs.items()))
            for role in ("ride", "kick", "snare"):
                top = g["top_patterns"][role][:3]
                out.append(f"  top {role} : " + " | ".join(f"{p['steps']} {p['share']:.0%}" for p in top))
    out.append("\nPatterns proposés")
    for p in data["proposed_patterns"]["patterns"]:
        desc = " ".join(f"{h['step']}{h['role'][0]}{h['note']}" for h in p["hits"])
        out.append(f"  d{p['density']} w={p['weight']} {p['sources']} : {desc}")
    return "\n".join(out)


# --------------------------------------------------------------------------------------
# CLI


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fetch", action="store_true", help="télécharge l'archive (SHA256 vérifié)")
    parser.add_argument("--manifest", action="store_true", help="écrit corpus/gmd/manifest.jsonl et VERSION")
    parser.add_argument("--measures", action="store_true", help="écrit references/wjazzd-swing/measures-drums.json")
    parser.add_argument("--summary", action="store_true", help="affiche un résumé lisible")
    parser.add_argument("--out", type=Path, default=OUTPUT, help="sortie JSON des mesures")
    args = parser.parse_args(argv)
    steps = args.fetch or args.manifest or args.measures or args.summary
    do_fetch = args.fetch or not steps
    do_manifest = args.manifest or not steps
    do_measures = args.measures or not steps
    try:
        if do_fetch:
            fetch(SOURCE_URL, ARCHIVE, SOURCE_SHA256)
            print(f"archive vérifiée : {ARCHIVE}")
        if do_manifest or do_measures:
            archive = open_archive()
            rows = write_manifest(archive) if do_manifest else read_info(archive)
            if do_manifest:
                print(f"manifeste : {len(rows)} fichiers → {MANIFEST}")
            if do_measures:
                data = build_measures(archive, rows)
                write_json(args.out, data)
                print(f"mesures → {args.out}")
        if args.summary:
            if args.out.is_file():
                import json
                print(summary(json.loads(args.out.read_text(encoding="utf-8"))))
            else:
                print(f"{args.out} absent : lancer --measures", file=sys.stderr)
                return 1
    except (ValueError, FileNotFoundError, RuntimeError) as err:
        print(f"erreur : {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
