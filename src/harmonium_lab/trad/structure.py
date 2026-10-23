"""DS-T9 : motifs, phrases et rythmes, sans confondre reprises et composition.

Les mesures et levées ABC viennent du plan de forme existant. Une seule
passe de chaque partie écrite est retenue (première fin). Les formes croches
ne contribuent pas aux positions 1..8 ; leurs mesures pleines restent dans
le vocabulaire rythmique. Aucun air ni incipit n'est écrit dans les références.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from .cells import pitch_to_degree
from .features import beat_eighths
from .form import analyze_form
from .loaders import load_engine_midi
from .model import Note, mode_intervals, normalize_mode

TRANSFORMS = ("exact", "sequence", "varied_ending", "inversion", "rhythmic_variation")
PROFILES = {
    "reel_quebecois": ("quebecoise", "reel"),
    "gigue_quebecoise": ("quebecoise", "jig"),
    "valse_quebecoise": ("quebecoise", "waltz"),
    "reel_acadien": ("acadienne", "reel"),
    "marche_britannique_coloniale": ("britannique_coloniale", "march"),
}
METHOD = {
    "parts": "Première passe de chaque lettre ABC, première fin ; parties de 8 mesures seulement pour les positions. Formes croches : mesures pleines jouées pour le rythme, sans positions ni lien A/B.",
    "pitch": "Pas diatoniques relatifs à la tonique, octaves conservées ; altération chromatique conservée séparément (aucun chromatisme fusionné).",
    "similarity": "Proportion de jetons identiques au même rang, divisée par le nombre maximal de notes ; matrices moyennes sur les parties, pas sur les reprises.",
    "transformations": "Tests non exclusifs ; exact = hauteurs/attaques/durées ; séquence = décalage diatonique constant non nul, rythme égal ; inversion = intervalles diatoniques opposés (au moins deux, dont un non nul), rythme égal ; fin variée = première moitié temporelle identique et non vide, suite différente ; variation rythmique = hauteurs identiques et rythme différent.",
    "letters": "Quatre paires de mesures : même lettre si identique ; apostrophe si transformation d'un prototype antérieur, sinon nouvelle lettre. Parts d'airs : présence au moins une fois, non exclusive entre structures.",
    "phrase": "Indice 4+4, pas une preuve musicologique : m1-2 = m5-6, dernière note de m4 non tonique, dernière note de m8 tonique tenue au moins un temps. Repos = note finale >= un temps ; cadence tonique = repos sur tonique.",
    "rhythm": "Durées exactes en croches (fractions), silences explicites reconstruits entre notes ; entropie Shannon en bits par mesure. Croches continues = grille pleine de notes de durée 1, sans silence.",
    "syncopation": "Note attaquée hors temps métrique et tenue au-delà du prochain temps (2 croches en 4/4 et 3/4, 4 en 2/2, 3 en 6/8). Pas une mesure du swing ni de la qualité des pieds.",
    "engine": "MIDI canal 0 ; attaques absolues ramenées à la croche puis redécoupées en mesures (banques moteur en croches ; swing et petite dérive d'horloge neutralisés), durées jusqu'à l'attaque suivante ou la barre : gate exclu, silences internes assimilés à des tenues. Début AABB recherché parmi les décalages 0..4 par identité A/A et B/B (au moins 14 mesures sur 16) ; meilleur score, premier candidat en cas d'égalité explicitement comptée. Intros et queue exclues, première passe A et B. Tonalité/mode : record-truth si renseigné, sinon journal .log du même export, sinon estimation signalée.",
    "accents": "Seulement !accent!, !emphasis!, !marcato!, !>! et leurs formes +...+ ; positions notées, pas d'accent métrique inventé. Absence de marque ≠ absence d'accent joué. MIDI non comparable sur cette annotation.",
    "limits": "Ornements et voix secondaires exclus par le parseur existant ; doubles-cordes : note supérieure. Changements de métrique non gérés. Résultats descriptifs de transcriptions, ni indépendance des sources ni inférence historique garanties.",
}


@dataclass(frozen=True)
class Motif:
    pitches: tuple[tuple[int, int], ...]
    rhythm: tuple[tuple[float, float], ...]
    span: float


def motif(bars: list[list[Note]], tonic: int, mode: str, length: float) -> Motif:
    pitches, rhythm = [], []
    intervals = mode_intervals(mode)
    for bi, bar in enumerate(bars):
        for n in bar:
            degree = pitch_to_degree(n.pitch, tonic, mode)
            step = degree - 1 if degree > 0 else degree
            octave, index = divmod(step, 7)
            accidental = n.pitch - (60 + tonic + 12 * octave + intervals[index])
            pitches.append((step, accidental))
            rhythm.append((round(bi * length + n.onset, 3), round(n.duration, 3)))
    return Motif(tuple(pitches), tuple(rhythm), length * len(bars))


def transformations(a: Motif, b: Motif) -> list[str]:
    if not a.pitches or not b.pitches or a.span != b.span:
        return []
    same_pitch, same_rhythm = a.pitches == b.pitches, a.rhythm == b.rhythm
    found = []
    if same_pitch and same_rhythm:
        return ["exact"]
    if len(a.pitches) == len(b.pitches) and len(a.pitches) >= 2 and same_rhythm:
        shifts = {y[0] - x[0] for x, y in zip(a.pitches, b.pitches)}
        same_acc = all(x[1] == y[1] for x, y in zip(a.pitches, b.pitches))
        if len(shifts) == 1 and 0 not in shifts and same_acc:
            found.append("sequence")
        da = [y[0] - x[0] for x, y in zip(a.pitches, a.pitches[1:])]
        db = [y[0] - x[0] for x, y in zip(b.pitches, b.pitches[1:])]
        if len(da) >= 2 and any(da) and da == [-d for d in db] and same_acc:
            found.append("inversion")
    def opening(m: Motif) -> tuple:
        return tuple((p, o, min(d, m.span / 2 - o)) for p, (o, d) in zip(m.pitches, m.rhythm) if o < m.span / 2)
    if opening(a) and opening(a) == opening(b):
        found.append("varied_ending")
    if same_pitch and not same_rhythm:
        found.append("rhythmic_variation")
    return found


def letter_structure(pairs: list[Motif]) -> str:
    prototypes: list[Motif] = []
    labels = []
    for pair in pairs:
        exact = next((i for i, p in enumerate(prototypes) if pair == p), None)
        related = next((i for i, p in enumerate(prototypes) if transformations(p, pair)), None)
        if exact is not None:
            labels.append(chr(97 + exact))
        elif related is not None:
            labels.append(chr(97 + related) + "'")
        else:
            labels.append(chr(97 + len(prototypes)))
            prototypes.append(pair)
    return " ".join(labels)


@dataclass
class Material:
    parts: list[tuple[str, list[list[Note]]]]
    rhythm_bars: list[list[Note]]
    tonic: int
    mode: str
    meter: str
    length: int
    accents: list[tuple[float, str]] = field(default_factory=list)
    excluded_parts: int = 0
    tail_bars: int = 0
    key_source: str = "abc"
    intro_bars: int = 0
    alignment_score: int | None = None
    alignment_candidates: int = 0


_ACCENT = re.compile(r"!((?:accent|emphasis|marcato|>))!|\+((?:accent|emphasis|marcato|>))\+")


def abc_material(text: str) -> Material:
    plan = analyze_form(text)
    # Les marqueurs deviennent des annotations d'accords sur une seconde lecture,
    # donc bénéficient exactement des mêmes reprises, levées, triolets et voltas.
    accent_plan = None
    if _ACCENT.search(text):
        marked = re.sub(r'"[^"\n]*"', '', text)
        marked = _ACCENT.sub('"C"', marked)
        accent_plan = analyze_form(marked)
    parts, rhythms, accents = [], [], []
    excluded = 0
    def notes_at(ids: list[int]) -> list[list[Note]]:
        return [[Note(p, round(float(o), 3), round(float(d), 3)) for o, d, p in plan.bars[i][0] if p is not None] for i in ids]
    if plan.scheme != "croche" and sum(plan.parts) == len(plan.bars):
        cursor, seen = 0, set()
        for label, size in zip(plan.scheme, plan.parts):
            ids = list(range(cursor, cursor + size))
            cursor += size
            if label in seen:
                continue
            seen.add(label)
            bars = notes_at(ids)
            rhythms.extend(bars)
            if size == 8:
                parts.append((label, bars))
            else:
                excluded += 1
            if accent_plan:
                accents.extend((float(o), s) for i in ids for o, s in accent_plan.bars[i][1])
    else:
        ids = [i for i, b in enumerate(plan.bars) if b[3]]
        rhythms = notes_at(ids)
        excluded = len(plan.passes)
        if accent_plan:
            accents.extend((float(o), s) for i in ids for o, s in accent_plan.bars[i][1])
    return Material(parts, rhythms, plan.key_tonic_pc, plan.mode, plan.meter, plan.eighths_per_bar, accents, excluded)


def engine_material(path: Path, tune_type: str) -> Material:
    tune = load_engine_midi(path, tune_type=tune_type)
    key_source = "estimated"
    key, mode = "", ""
    truth_path = path.with_suffix(".json")
    if truth_path.exists():
        truth = json.loads(truth_path.read_text())
        rows = truth.get("reports", []) if isinstance(truth, dict) else truth
        first = next((row for row in rows if row.get("session_key") and row.get("session_scale")), None)
        if first:
            key, mode = first["session_key"], first["session_scale"]
            key_source = "record-truth"
    log = path.with_suffix(".log")
    if not key and log.exists():
        match = re.search(r"Tune 1 \(bars \d+\.\.=\d+\): ([A-G][#b]?) (\w+)", log.read_text())
        if match:
            key, mode = match.groups()
            key_source = "export-log"
    match = re.fullmatch(r"([A-G])([#b]?)", key)
    if match:
        tune.key_tonic_pc = ({"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[match[1]] + {"": 0, "#": 1, "b": -1}[match[2]]) % 12
        tune.mode = normalize_mode(mode)
    if len(tune.bars) < 32:
        raise ValueError(f"{path.name}: export AABB incomplet ({len(tune.bars)} mesures, 32 requises)")
    # Quantifier AVANT de redécouper : une attaque légèrement avant une barre
    # (dérive de l'horloge MIDI) appartient à la mesure suivante, pas à la fin
    # de la précédente. Les banques distribuées sont sur une grille de croches.
    attacks_by_bar = defaultdict(dict)
    for bi, bar in enumerate(tune.bars):
        for n in bar:
            absolute = round(bi * tune.eighths_per_bar + n.onset)
            target, onset = divmod(absolute, tune.eighths_per_bar)
            attacks_by_bar[target][float(onset)] = n.pitch
    bars = []
    for bi in range(max(len(tune.bars), max(attacks_by_bar, default=0) + 1)):
        attacks = attacks_by_bar[bi]
        starts = sorted(attacks)
        bars.append([Note(attacks[o], o, end - o) for o, end in zip(starts, starts[1:] + [float(tune.eighths_per_bar)])])
    # Alignement sur les reprises jouées, jamais sur la copie m.1-2 -> m.5-6
    # que l'on cherche justement à mesurer. Une intro « tail » contient des
    # notes : supprimer seulement les mesures silencieuses serait faux.
    scores = {}
    for offset in range(min(4, len(bars) - 32) + 1):
        body = bars[offset:offset + 32]
        scores[offset] = sum(bool(body[i]) and body[i] == body[i + 8] for i in list(range(8)) + list(range(16, 24)))
    best = max(scores.values())
    if best < 14:
        raise ValueError(f"{path.name}: alignement AABB incertain (meilleur score {best}/16)")
    candidates = [offset for offset, score in scores.items() if score == best]
    offset = candidates[0]
    body = bars[offset:offset + 32]
    parts = [("A", body[:8]), ("B", body[16:24])]
    return Material(parts, body[:8] + body[16:24], tune.key_tonic_pc, tune.mode, tune.meter, tune.eighths_per_bar, tail_bars=len(bars) - offset - 32, key_source=key_source, intro_bars=offset, alignment_score=best, alignment_candidates=len(candidates))


def _rate(n: int | float, d: int) -> float | None:
    return round(n / d, 6) if d else None


def _distribution(counts: Counter, denominator: int) -> list[dict]:
    return [{"pattern": p, "count": n, "share": _rate(n, denominator)} for p, n in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _fraction(value: float) -> str:
    return str(Fraction(value).limit_denominator(96))


def rhythm_cell(bar: list[Note], length: int) -> str:
    tokens, end = [], 0.0
    for n in bar:
        if n.onset > end + .01:
            tokens.append("z" + _fraction(n.onset - end))
        tokens.append(_fraction(n.duration))
        end = max(end, n.onset + n.duration)
    if end < length - .01:
        tokens.append("z" + _fraction(length - end))
    return " ".join(tokens)


def _similarity(a: tuple, b: tuple) -> float:
    return sum(x == y for x, y in zip(a, b)) / max(len(a), len(b)) if a or b else 1.0


def analyze_materials(materials: list[Material]) -> dict[str, Any]:
    matrices = defaultdict(lambda: {k: [[0.0] * 8 for _ in range(8)] for k in ("pitch", "rhythm", "joint")})
    part_counts, structures, structure_tunes = Counter(), Counter(), Counter()
    positions = defaultdict(Counter)
    sequence_shifts = defaultdict(Counter)
    opportunities = Counter()
    phrase = Counter()
    rest_positions = defaultdict(Counter)
    rhythm_counts, long_positions, accent_positions = Counter(), Counter(), Counter()
    rhythm_totals = Counter()
    key_sources = Counter()

    def compare(key: str, a: Motif, b: Motif) -> None:
        opportunities[key] += 1
        found = transformations(a, b)
        positions[key].update(found)
        if "sequence" in found:
            sequence_shifts[key][str(b.pitches[0][0] - a.pitches[0][0])] += 1

    for material in materials:
        m = material
        key_sources[m.key_source] += 1
        present = set()
        by_label = {}
        beat = beat_eighths(m.meter)
        for label, bars in m.parts:
            by_label[label] = bars
            ms = [motif([b], m.tonic, m.mode, m.length) for b in bars]
            pairs = [motif(bars[i:i + 2], m.tonic, m.mode, m.length) for i in range(0, 8, 2)]
            pattern = letter_structure(pairs)
            structures[pattern] += 1
            present.add(pattern)
            for group in ("all", label):
                part_counts[group] += 1
                for i, a in enumerate(ms):
                    for j, b in enumerate(ms):
                        for channel, x, y in (("pitch", a.pitches, b.pitches), ("rhythm", a.rhythm, b.rhythm), ("joint", tuple(zip(a.pitches, a.rhythm)), tuple(zip(b.pitches, b.rhythm)))):
                            matrices[group][channel][i][j] += _similarity(x, y)
            for i in range(8):
                for j in range(i + 1, 8):
                    compare(f"{label}:m{j + 1}/m{i + 1}", ms[i], ms[j])
            for i in range(4):
                for j in range(i + 1, 4):
                    compare(f"{label}:m{j * 2 + 1}-{j * 2 + 2}/m{i * 2 + 1}-{i * 2 + 2}", pairs[i], pairs[j])
            phrase["parts"] += 1
            copied_opening = pairs[0] == pairs[2] and bool(pairs[0].pitches)
            phrase["opening_reprise"] += copied_opening
            end4 = bars[3][-1] if bars[3] else None
            end8 = bars[7][-1] if bars[7] else None
            tonic8 = end8 is not None and end8.pitch % 12 == m.tonic
            phrase["antecedent_consequent"] += bool(copied_opening and end4 and end4.pitch % 12 != m.tonic and tonic8 and end8.duration >= beat - .01)
            for i, bar in enumerate(bars, 1):
                rest = rest_positions[f"{label}:m{i}"]
                rest["bars"] += 1
                if bar:
                    last = bar[-1]
                    rest["long_final"] += last.duration >= beat - .01
                    rest["tonic_final"] += last.pitch % 12 == m.tonic
                    rest["tonic_cadence"] += last.pitch % 12 == m.tonic and last.duration >= beat - .01
                    rest["rest_after_final"] += last.onset + last.duration < m.length - .01
        structure_tunes.update(present)
        if "A" in by_label and "B" in by_label:
            a, b = by_label["A"], by_label["B"]
            phrase["ab_pairs"] += 1
            for i in range(8):
                compare(f"B:m{i + 1}/A:m{i + 1}", motif([a[i]], m.tonic, m.mode, m.length), motif([b[i]], m.tonic, m.mode, m.length))
            for i in range(0, 8, 2):
                compare(f"B:m{i + 1}-{i + 2}/A:m{i + 1}-{i + 2}", motif(a[i:i + 2], m.tonic, m.mode, m.length), motif(b[i:i + 2], m.tonic, m.mode, m.length))
            ending, opening = motif(a[6:8], m.tonic, m.mode, m.length), motif(b[:2], m.tonic, m.mode, m.length)
            compare("B:m1-2/A:m7-8", ending, opening)
            phrase["b_reuses_a_ending"] += bool(transformations(ending, opening))
        for bar in m.rhythm_bars:
            rhythm_totals["bars"] += 1
            rhythm_counts[rhythm_cell(bar, m.length)] += 1
            rhythm_totals["continuous_eighth_bars"] += len(bar) == m.length and all(abs(n.onset - i) < .01 and abs(n.duration - 1) < .01 for i, n in enumerate(bar))
            sync = 0
            for n in bar:
                if n.duration >= beat - .01:
                    long_positions[_fraction(n.onset)] += 1
                next_beat = (math.floor((n.onset + .001) / beat) + 1) * beat
                sync += abs(n.onset / beat - round(n.onset / beat)) > .01 and n.onset + n.duration > next_beat + .01
            rhythm_totals["syncopated_notes"] += sync
            rhythm_totals["syncopated_bars"] += bool(sync)
            rhythm_totals["notes"] += len(bar)
            rhythm_totals["adjacent_pairs"] += max(0, len(bar) - 1)
            rhythm_totals["repeated_notes"] += sum(a.pitch == b.pitch for a, b in zip(bar, bar[1:]))
            rhythm_totals["repeated_triplets"] += sum(a.pitch == b.pitch == c.pitch and all(abs(n.duration - 2 / 3) < .01 for n in (a, b, c)) for a, b, c in zip(bar, bar[1:], bar[2:]))
        accent_positions.update(_fraction(o) for o, _ in m.accents)
        rhythm_totals["tunes_with_accents"] += bool(m.accents)
    n_bars = rhythm_totals["bars"]
    positional_tunes = sum(bool(m.parts) for m in materials)
    entropy = -sum((n / n_bars) * math.log2(n / n_bars) for n in rhythm_counts.values()) if n_bars else None
    return {
        "engine_intro_bars": dict(sorted(Counter(str(m.intro_bars) for m in materials if m.alignment_score is not None).items())),
        "engine_alignment_scores": dict(sorted(Counter(str(m.alignment_score) for m in materials if m.alignment_score is not None).items())),
        "engine_ambiguous_alignments": sum(m.alignment_candidates > 1 for m in materials),
        "tunes": len(materials),
        "positional_tunes": positional_tunes,
        "parts": dict(sorted(part_counts.items())),
        "excluded_non8_parts": sum(m.excluded_parts for m in materials),
        "excluded_engine_tail_bars": sum(m.tail_bars for m in materials),
        "key_sources": dict(sorted(key_sources.items())),
        "similarity": {g: {k: [[round(v / part_counts[g], 6) for v in row] for row in matrix] for k, matrix in channels.items()} for g, channels in sorted(matrices.items())},
        "structures": [{**row, "tune_count": structure_tunes[row["pattern"]], "tune_share": _rate(structure_tunes[row["pattern"]], positional_tunes)} for row in _distribution(structures, part_counts["all"])],
        "transformations": {key: {"opportunities": opportunities[key], "counts": {t: counts[t] for t in TRANSFORMS}, "rates": {t: _rate(counts[t], opportunities[key]) for t in TRANSFORMS}} for key, counts in sorted(positions.items())},
        "sequence_shifts": {key: _distribution(counts, sum(counts.values())) for key, counts in sorted(sequence_shifts.items())},
        "phrases": {"parts": phrase["parts"], "opening_reprise_count": phrase["opening_reprise"], "opening_reprise_rate": _rate(phrase["opening_reprise"], phrase["parts"]), "antecedent_consequent_count": phrase["antecedent_consequent"], "antecedent_consequent_rate": _rate(phrase["antecedent_consequent"], phrase["parts"]), "ab_pairs": phrase["ab_pairs"], "b_reuses_a_ending_rate": _rate(phrase["b_reuses_a_ending"], phrase["ab_pairs"]), "rest_by_position": {p: {"bars": c["bars"], **{k + "_rate": _rate(c[k], c["bars"]) for k in ("long_final", "tonic_final", "tonic_cadence", "rest_after_final")}} for p, c in sorted(rest_positions.items())}},
        "rhythm": {
            "counts": dict(sorted(rhythm_totals.items())),
            "cells": _distribution(rhythm_counts, n_bars),
            "top20": _distribution(rhythm_counts, n_bars)[:20],
            "vocabulary_size": len(rhythm_counts),
            "entropy_bits": round(entropy, 6) if entropy is not None else None,
            "continuous_eighth_rate": _rate(rhythm_totals["continuous_eighth_bars"], n_bars),
            "syncopated_bar_rate": _rate(rhythm_totals["syncopated_bars"], n_bars),
            "repeated_note_rate": _rate(rhythm_totals["repeated_notes"], rhythm_totals["adjacent_pairs"]),
            "long_note_onsets": _distribution(long_positions, sum(long_positions.values())),
            "accents": {
                "count": sum(accent_positions.values()),
                "tunes_with_marks": rhythm_totals["tunes_with_accents"],
                "onsets": _distribution(accent_positions, sum(accent_positions.values())),
            },
        },
    }


def analyze_paths(paths: list[Path], tune_type: str, engine: bool = False) -> dict:
    materials, errors = [], Counter()
    for path in paths:
        try:
            m = engine_material(path, tune_type) if engine else abc_material(path.read_text(encoding="utf-8", errors="replace"))
            if not m.rhythm_bars:
                raise ValueError("aucune mesure pleine")
            materials.append(m)
        except (ValueError, KeyError, IndexError, TypeError, ZeroDivisionError) as exc:
            errors[type(exc).__name__ + ": " + str(exc)] += 1
    stats = analyze_materials(materials)
    stats["input_files"] = len(paths)
    stats["errors"] = dict(sorted(errors.items()))
    return stats
