"""DS-T10 : marques écrites, positions et dénominateurs issus du parseur ABC commun.

Une occurrence par marque écrite, jamais par exécution d'une reprise. Les deux
voltas restent dans le comptage ; les levées complètent les fins si le plan le
permet. Les positions 1..8 ne sont attribuées qu'aux parties de huit mesures.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

from .abcnorm import _first_voice_lines, parse_tune
from .cells import pitch_to_degree
from .features import beat_eighths
from .form import analyze_form
from .model import mode_intervals

KINDS = (
    "grace_single", "grace_multiple", "roll", "turn", "triplet_repeated",
    "triplet_melodic", "double_stop", "chord", "trill", "fermata",
)
ARTICULATION_KINDS = ("slur", "tie", "staccato", "accent", "tenuto", "marcato")
ENGINE_KINDS = tuple(k for k in KINDS if k != "triplet_melodic")
CORPORA = {"quebecoise": "trad", "acadienne": "acadienne", "britannique_coloniale": "britannique_coloniale"}
PROFILES = {
    "reel_quebecois": ("quebecoise", "reel"),
    "gigue_quebecoise": ("quebecoise", "jig"),
    "valse_quebecoise": ("quebecoise", "waltz"),
    "reel_acadien": ("acadienne", "reel"),
    "marche_britannique_coloniale": ("britannique_coloniale", "march"),
    "gigue_britannique_coloniale": ("britannique_coloniale", "jig"),
    "hornpipe_britannique_coloniale": ("britannique_coloniale", "hornpipe"),
}
RAW = {
    "grace": r"\{[^}]*\}", "roll": r"~", "triplet": r"\(3",
    "chord": r"\[(?:[\^_=]*[A-Ga-g][,']*\d*(?:/\d*)*\s*){2,}\]",
}
BASELINE = {"quebecoise": (764, 69, 116, 204, 29), "acadienne": (270, 29, 52, 61, 2), "britannique_coloniale": (1025, 11, 3, 136, 17)}
METHOD = {
    "population": "Tous les fichiers du manifeste, toutes les notes écrites de la première voix ; reprises non multipliées, deux voltas incluses, note supérieure des doubles cordes.",
    "denominators": "Note = attaque porteuse (accord = une note, agréments hors dénominateur, triolets = trois notes). Mesures = durée écrite totale / durée nominale, fragments et levées compris. Chaque cellule contient ses opportunités, occurrences et taux par 100 notes / par mesure.",
    "positions": "Parties de huit mesures reconnues par analyze_form uniquement ; autres positions = unknown. Levée jointe à la fin complémentaire, sinon pickup sans numéro. Une source écrite vue plusieurs fois reçoit sa première position jouée. Les fins alternatives sont des opportunités distinctes.",
    "time": "Durée et onset en croches exactes (fractions). Temps métrique 1-based : blanche en 2/2, noire en 4/4 et 3/4, noire pointée en 6/8 ; phase exacte, demi-temps = floor(2*phase). Les triolets gardent leur phase 1/3 ou 2/3, sans arrondi sur la grille.",
    "context": "Intervalles signés en demi-tons avec notes voisines dans la première exécution contenant cette source (silences ignorés). Degré diatonique replié 1..7, altération séparée. Fin de phrase = mesure 4 ou 8, non preuve de cadence. Les groupes de liaison exposent longueur, contour intervalle par intervalle, répétitions et contexte de départ.",
    "types": "T/!trill!/+trill+ = trill ; ~ = roll ; !turn! = turn. . = staccato et H = fermata. Liaisons (), ties -, accents !accent!/!>!/!emphasis!/ +accent+, tenuto L/!tenuto! et marcato !marcato!/!^! sont des articulations dans la clé distincte `articulations`, jamais des agréments. Un triolet mélodique est une figure rythmique, séparée du triolet répété ; un groupe avec silence n'est pas un triolet de trois notes.",
    "limits": "Taux écrits = plancher, pas taux joués. Sources/transcripteurs confondent notation et pratique. Petits effectifs, notes corrélées : occurrences fournies, pas d'IC binomial trompeur. Changements de métrique, unité ou tonalité en cours d'air non interprétés par le parseur commun ; inline_changes compte les [M:…]/[K:…]. Positions de formes irrégulières inconnues.",
    "sparse": "Dans by_position, type absent = zéro occurrence, pas donnée manquante ; position absente = aucune opportunité. Par mesure conditionnel pour m1..8/partie/fin de phrase, par mesure totale du groupe pour temps/durée/degré/intervalles.",
}


def fraction(value: Fraction | float) -> str:
    return str(Fraction(value).limit_denominator(10000))


def _family(kind: str) -> str | None:
    if kind.startswith("grace_"):
        return "grace"
    if kind.startswith("triplet_"):
        return "triplet"
    if kind in ("double_stop", "chord"):
        return "chord"
    return "roll" if kind == "roll" else None


def extract_ornaments(text: str) -> dict[str, Any]:
    """Extraire événements et opportunités, sans réseau ni parseur musical parallèle."""
    plan = analyze_form(text)
    beat = Fraction(beat_eighths(plan.meter))
    labels: dict[int, tuple[str, int | None]] = {}
    if plan.scheme != "croche" and sum(plan.parts) == len(plan.bars):
        cursor = 0
        for label, size in zip(plan.scheme, plan.parts):
            for i in range(size):
                labels[cursor + i] = (label, i + 1 if size == 8 else None)
            cursor += size
    locations = {}
    played = [(bi, o, p) for bi, (notes, _, _, _) in enumerate(plan.bars) for o, _, p in notes if p is not None]
    neighbors = {}
    for i, (bi, onset, pitch) in enumerate(played):
        neighbors[(bi, onset, pitch)] = (
            pitch - played[i - 1][2] if i else None,
            played[i + 1][2] - pitch if i + 1 < len(played) else None,
        )
    for bi, sources in enumerate(plan.bar_sources):
        for si, shift in sources:
            locations.setdefault(si, (bi, shift))
    written = [(si, ni, p) for si, seg in enumerate(plan.segments) for ni, (_, _, p) in enumerate(seg.notes) if p is not None]
    written_neighbors = {(si, ni): (
        p - written[i - 1][2] if i else None,
        written[i + 1][2] - p if i + 1 < len(written) else None,
    ) for i, (si, ni, p) in enumerate(written)}
    # Triplets can span a barline; retain rests to reject incomplete groups.
    sequence = [(si, ni, p) for si, seg in enumerate(plan.segments) for ni, (_, _, p) in enumerate(seg.notes)]
    next_three = {(si, ni): sequence[i:i + 3] for i, (si, ni, _) in enumerate(sequence)}
    notes, events, articulation_events = [], [], []
    note_rows = {}
    bar_opportunities = defaultdict(Counter)
    for si, seg in enumerate(plan.segments):
        bi, _ = locations.get(si, (None, Fraction(0)))
        part, bar = labels.get(bi, (None, None))
        equivalents = float(seg.dur * 8 / plan.eighths_per_bar)
        bar_opportunities["bar_position"][str(bar) if bar is not None else "unknown"] += equivalents
        bar_opportunities["part_position"][f"{part}:m{bar}" if bar is not None else "unknown"] += equivalents
        bar_opportunities["phrase_end"][str(bar in (4, 8) if bar is not None else None).lower()] += equivalents
    incomplete_triplets = 0
    for si, seg in enumerate(plan.segments):
        marks = defaultdict(list)
        for ni, kind in seg.marks:
            if kind == "triplet":
                group = next_three.get((si, ni), [])
                pitches = [p for _, _, p in group]
                if len(pitches) != 3 or None in pitches:
                    incomplete_triplets += 1
                    continue
                kind = "triplet_repeated" if len(set(pitches)) == 1 else "triplet_melodic"
            marks[ni].append(kind)
        for ni, (onset, duration, pitch) in enumerate(seg.notes):
            if pitch is None:
                continue
            onset *= 8
            bi, shift = locations.get(si, (None, Fraction(0)))
            part, bar = labels.get(bi, (None, None))
            pos = onset + shift
            previous, following = neighbors.get((bi, pos, pitch), written_neighbors[(si, ni)])
            degree = pitch_to_degree(pitch, plan.key_tonic_pc, plan.mode)
            degree_index = (degree - 1 if degree > 0 else degree) % 7
            phase = pos / beat % 1
            row = {
                "part": part, "bar": bar, "pickup": si not in locations or shift > 0,
                "onset_eighths": fraction(pos), "beat": int(pos // beat) + 1,
                "beat_phase": fraction(phase), "half_beat": int(phase * 2),
                "duration_eighths": fraction(duration * 8),
                "previous_interval": previous, "next_interval": following,
                "degree": degree_index + 1, "pitch_class_relative": (pitch - plan.key_tonic_pc) % 12,
                "accidental_semitones": ((pitch - plan.key_tonic_pc - mode_intervals(plan.mode)[degree_index] + 6) % 12) - 6,
                "phrase_end": bar in (4, 8) if bar is not None else None,
            }
            notes.append(row)
            note_rows[(si, ni)] = row
            for kind in marks[ni]:
                if kind in ARTICULATION_KINDS:
                    articulation_events.append({**row, "type": kind})
                elif kind not in ("slur_open", "slur_close"):
                    events.append({**row, "type": kind})
    stack = []
    source_notes = [(si, ni, pitch) for si, seg in enumerate(plan.segments)
                    for ni, (_, _, pitch) in enumerate(seg.notes)]
    source_index = {(si, ni): i for i, (si, ni, _) in enumerate(source_notes)}
    segment_starts = {}
    source_cursor = 0
    for segment_index, segment in enumerate(plan.segments):
        segment_starts[segment_index] = source_cursor
        source_cursor += len(segment.notes)
    def slur_source_index(segment_index: int, note_index: int) -> int:
        segment = plan.segments[segment_index]
        return segment_starts[segment_index] + min(note_index, len(segment.notes))
    for si, seg in enumerate(plan.segments):
        for ni, kind in seg.marks:
            if kind == "slur_open":
                stack.append(slur_source_index(si, ni))
            elif kind == "slur_close" and stack:
                start = stack.pop()
                end = slur_source_index(si, ni)
                group = source_notes[start:end]
                pitches = [pitch for _, _, pitch in group if pitch is not None]
                first = next(((a, b) for a, b, pitch in group if pitch is not None), None)
                row = note_rows.get(first) if first else None
                if row and pitches:
                    articulation_events.append({
                        **row, "type": "slur", "note_count": len(pitches),
                        "contour": [b - a for a, b in zip(pitches, pitches[1:])],
                        "repeated_notes": len(set(pitches)) < len(pitches),
                    })
    tune = parse_tune(text)
    main = " ".join(_first_voice_lines(tune.body))
    raw = {name: bool(re.search(pattern, text)) for name, pattern in RAW.items()}
    main_raw = {name: bool(re.search(pattern, main)) for name, pattern in RAW.items()}
    families = {_family(e["type"]) for e in events}
    exclusions = {}
    for name in RAW:
        if raw[name] and name not in families:
            exclusions[name] = "hors première voix/corps (en-têtes, commentaires, voix secondaire)" if not main_raw[name] else "marque sans porteuse valide / annotation citée / groupe non constitué de trois notes"
            if name == "chord" and any(re.search(RAW["chord"], grace) for grace in re.findall(RAW["grace"], main)):
                exclusions[name] = "accord interne à un agrément {...}, pas accord de la ligne porteuse"
    return {
        "notes": notes, "events": events, "articulations": articulation_events,
        "bar_opportunities": dict(bar_opportunities),
        "bar_equivalents": float(sum((s.dur for s in plan.segments), Fraction(0)) * 8 / plan.eighths_per_bar),
        "raw_presence": raw, "main_raw_presence": main_raw,
        "exclusions": exclusions, "incomplete_triplets": incomplete_triplets,
        "transcriber": "; ".join(tune.all("Z")) or "non renseigné",
        "inline_changes": len(re.findall(r"\[(?:M|K):", main)),
    }


def _dimensions(row: dict) -> dict[str, str]:
    return {
        "bar_position": str(row["bar"]) if row["bar"] is not None else "unknown",
        "part_position": f'{row["part"]}:m{row["bar"]}' if row["bar"] is not None else "unknown",
        "beat": str(row["beat"]),
        "beat_phase": f'{row["beat"]}+{row["beat_phase"]}',
        "half_beat": f'{row["beat"]}.{row["half_beat"]}',
        "carrier_duration_eighths": row["duration_eighths"],
        "phrase_end": str(row["phrase_end"]).lower(),
        "degree": str(row["degree"]),
        "previous_interval": str(row["previous_interval"]),
        "next_interval": str(row["next_interval"]),
    }


def _rates(counts: Counter, notes: int, bars: float, sparse: bool = False) -> dict:
    return {
        "notes": notes, "bar_equivalents": round(bars, 6), "occurrences": sum(counts.values()),
        "by_type": {kind: {"count": counts[kind], "per_100_notes": round(100 * counts[kind] / notes, 6) if notes else None,
                          "per_bar": round(counts[kind] / bars, 6) if bars else None} for kind in KINDS if not sparse or counts[kind]},
    }


def aggregate(tunes: list[dict]) -> dict:
    counts, opportunities, occurrences = Counter(), defaultdict(Counter), defaultdict(lambda: defaultdict(Counter))
    articulation_counts = Counter()
    articulation_lengths, articulation_contours, articulation_contour_classes = Counter(), Counter(), Counter()
    slur_contours_by_bar = defaultdict(Counter)
    articulation_occurrences = defaultdict(lambda: defaultdict(Counter))
    bar_opportunities = defaultdict(Counter)
    for tune in tunes:
        for event in tune["articulations"]:
            if event["type"] == "slur":
                articulation_lengths[str(event["note_count"])] += 1
                contour = event["contour"]
                contour_class = "repeated" if event["repeated_notes"] else "ascending" if sum(contour) > 0 else "descending" if sum(contour) < 0 else "mixed_or_static"
                articulation_contours[",".join(map(str, contour))] += 1
                articulation_contour_classes[contour_class] += 1
                slur_contours_by_bar[str(event["bar"]) if event["bar"] is not None else "unknown"][contour_class] += 1
    total_bars = sum(t["bar_equivalents"] for t in tunes)
    for tune in tunes:
        for dim, cells in tune["bar_opportunities"].items():
            bar_opportunities[dim].update(cells)
        for note in tune["notes"]:
            for dim, key in _dimensions(note).items():
                opportunities[dim][key] += 1
        for event in tune["events"]:
            counts[event["type"]] += 1
            for dim, key in _dimensions(event).items():
                occurrences[dim][key][event["type"]] += 1
        for event in tune["articulations"]:
            articulation_counts[event["type"]] += 1
            for dim, key in _dimensions(event).items():
                articulation_occurrences[dim][key][event["type"]] += 1
    result = _rates(counts, sum(len(t["notes"]) for t in tunes), sum(t["bar_equivalents"] for t in tunes))
    articulation_by_position = {
        dim: {key: {
            "notes": n,
            "bar_equivalents": bar_opportunities[dim][key] if dim in bar_opportunities else total_bars,
            "occurrences": sum(articulation_occurrences[dim][key].values()),
            "by_type": {kind: {
                "count": articulation_occurrences[dim][key][kind],
                "per_100_notes": round(100 * articulation_occurrences[dim][key][kind] / n, 6) if n else None,
                "per_bar": round(articulation_occurrences[dim][key][kind] / (bar_opportunities[dim][key] if dim in bar_opportunities else total_bars), 6) if (bar_opportunities[dim][key] if dim in bar_opportunities else total_bars) else None,
            } for kind in ARTICULATION_KINDS if articulation_occurrences[dim][key][kind]},
        } for key, n in sorted(cells.items()) if articulation_occurrences[dim][key]} for dim, cells in sorted(opportunities.items())
    }
    slur_contour_by_bar = {}
    for bar, classes in slur_contours_by_bar.items():
        notes_in_bar = opportunities["bar_position"].get(bar, 0)
        slur_contour_by_bar[bar] = {
            name: {
                "count": count,
                "per_100_notes": round(100 * count / notes_in_bar, 6) if notes_in_bar else None,
            } for name, count in sorted(classes.items())
        }
    result["articulations"] = {
        "occurrences": sum(articulation_counts.values()),
        "by_type": {kind: {
            "count": articulation_counts[kind],
            "per_100_notes": round(100 * articulation_counts[kind] / result["notes"], 6) if result["notes"] else None,
        } for kind in ARTICULATION_KINDS},
        "by_position": articulation_by_position,
        "slur_lengths": dict(articulation_lengths),
        "slur_contours": dict(articulation_contours),
        "slur_contour_classes": dict(articulation_contour_classes),
        "slur_contour_by_bar": slur_contour_by_bar,
    }
    result.update({
        "tunes": len(tunes), "tunes_without_marks": sum(not t["events"] and not t["articulations"] for t in tunes),
        "share_without_marks": sum(not t["events"] and not t["articulations"] for t in tunes) / len(tunes) if tunes else None,
        "tunes_without_engine_ornaments": sum(not any(e["type"] in ENGINE_KINDS for e in t["events"]) for t in tunes),
        "positioned_notes": sum(n["bar"] is not None for t in tunes for n in t["notes"]),
        "incomplete_triplets": sum(t["incomplete_triplets"] for t in tunes),
        "inline_changes": sum(t["inline_changes"] for t in tunes),
        "by_position": {dim: {key: _rates(occurrences[dim][key], n, bar_opportunities[dim][key] if dim in bar_opportunities else total_bars, sparse=True) for key, n in sorted(cells.items())} for dim, cells in sorted(opportunities.items())},
        "raw_presence_tunes": {name: sum(t["raw_presence"][name] for t in tunes) for name in RAW},
        "extracted_presence_tunes": {name: sum(any(_family(e["type"]) == name for e in t["events"]) for t in tunes) for name in RAW},
        "raw_only": [{"id": t["id"], "families": t["exclusions"]} for t in tunes if t["exclusions"]],
    })
    return result


def _stratify(tunes: list[dict], field: str, positions: bool = True) -> dict:
    groups = defaultdict(list)
    for tune in tunes:
        groups[tune[field]].append(tune)
    strata = {key: aggregate(value) for key, value in sorted(groups.items())}
    if not positions:
        # Par transcripteur, les effectifs sont trop petits pour des tables par position.
        for cell in strata.values():
            cell.pop("by_position", None)
            cell["articulations"].pop("by_position", None)
    return strata


def proposal(stats: dict) -> dict:
    """Données proposées, non calibration moteur ni résultat d'écoute."""
    by_type = {}
    for kind in ENGINE_KINDS:
        durations = [Fraction(key) for key, cell in stats["by_position"].get("carrier_duration_eighths", {}).items() if kind in cell["by_type"]]
        by_type[kind] = {
            "enabled": bool(stats["by_type"][kind]["count"]),
            "written_per_100_notes": stats["by_type"][kind]["per_100_notes"],
            "occurrences": stats["by_type"][kind]["count"],
            "min_carrier_eighths_observed": fraction(min(durations)) if durations else None,
            "per_100_notes_by_bar": {str(i): (
                stats["by_position"]["bar_position"][str(i)]["by_type"].get(kind, {}).get("per_100_notes", 0.0)
                if str(i) in stats["by_position"].get("bar_position", {}) else None
            ) for i in range(1, 9)},
        }
    articulation_types = {}
    for kind in ARTICULATION_KINDS:
        cell = stats["articulations"]["by_type"][kind]
        articulation_types[kind] = {
            "enabled": bool(cell["count"]),
            "written_per_100_notes": cell["per_100_notes"],
            "occurrences": cell["count"],
            "per_100_notes_by_bar": {
                str(i): stats["articulations"]["by_position"]["bar_position"].get(str(i), {})
                .get("by_type", {}).get(kind, {}).get("per_100_notes", 0.0)
                for i in range(1, 9)
            },
        }
    return {
        "types": by_type,
        "performance": {
            "status": "Plancher écrit, à valider à l’oreille.",
            "articulations": articulation_types,
            "slur_lengths_notes": stats["articulations"]["slur_lengths"],
            "slur_contours": stats["articulations"]["slur_contours"],
            "slur_contour_classes": stats["articulations"]["slur_contour_classes"],
            "slur_probability_by_bar_and_contour": stats["articulations"]["slur_contour_by_bar"],
            "accent_by_beat": {
                beat: {
                    "count": cell["by_type"].get("accent", {}).get("count", 0),
                    "per_100_notes": cell["by_type"].get("accent", {}).get("per_100_notes", 0.0),
                    "per_bar": cell["by_type"].get("accent", {}).get("per_bar", 0.0),
                } for beat, cell in stats["articulations"]["by_position"].get("beat", {}).items()
            },
        },
        "arousal_multiplier": {"low": 1.0, "high": 1.0},
        "arousal_status": "Non mesurable dans les ABC : multiplicateurs neutres proposés, aucune corrélation revendiquée.",
        "minimum_status": "Minimum observé, pas seuil musical validé ; absent = désactiver ce type faute de données. Triolets : durée de la première note subdivisée, pas durée totale du groupe.",
    }


def run_ornaments(corpus_root: Path, output: Path, references: Path, tradition: str = "all", tune_type: str | None = None) -> Path:
    groups, all_tunes = {}, defaultdict(list)
    output.mkdir(parents=True, exist_ok=True)
    references.mkdir(parents=True, exist_ok=True)
    selected = CORPORA if tradition == "all" else {tradition: CORPORA[tradition]}
    events_path = output / "events.jsonl"
    with events_path.open("w", encoding="utf-8") as event_file:
        for name, folder in selected.items():
            root = corpus_root / folder
            entries = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines() if line.strip()]
            types = defaultdict(list)
            for entry in entries:
                if tune_type and entry["type"] != tune_type:
                    continue
                path = root / "tunes" / entry["type"] / (entry["id"] + ".abc")
                text = path.read_text(encoding="utf-8")
                measured = extract_ornaments(text)
                measured.update(id=entry["id"], source=entry.get("source", "autres"))
                types[entry["type"]].append(measured)
                all_tunes[name].append(measured)
                for event in (*measured["events"], *measured["articulations"]):
                    event_file.write(json.dumps({"id": entry["id"], "tradition": name, "tune_type": entry["type"], "source": measured["source"], "transcriber": measured["transcriber"], **event}, ensure_ascii=False) + "\n")
            for typ, tunes in sorted(types.items()):
                stats = aggregate(tunes)
                stats.update(tradition=name, tune_type=typ, schema_version=2, method=METHOD,
                             by_source=_stratify(tunes, "source", positions=False),
                             by_source_transcriber=_stratify([{**t, "source_transcriber": t["source"] + " / " + t["transcriber"]} for t in tunes], "source_transcriber", positions=False))
                stats["engine_proposal"] = proposal(stats)
                groups[(name, typ)] = stats
                (references / f"{name}-{typ}.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = render_report(groups, all_tunes)
    destination = output / "report.md"
    destination.write_text(report, encoding="utf-8")
    return destination


def render_report(groups: dict, all_tunes: dict) -> str:
    lines = ["# DS-T10 — Ornements écrits dans les corpus ABC", "", "## Méthode", ""]
    lines.extend(f"- **{key}** : {value}" for key, value in METHOD.items())
    lines += ["", "## Contrôle du comptage brut", "", "Les cellules contiennent brut observé / extraction mélodique ; le brut annoncé est indiqué séparément.", "", "| Tradition | Airs | {…} | ~ | (3 | [notes] | Annoncé (airs, agréments, rouleaux, triolets, accords) |", "|---|---:|---:|---:|---:|---:|---|"]
    raw_only = []
    for name, tunes in all_tunes.items():
        s = aggregate(tunes)
        cells = [f'{s["raw_presence_tunes"][k]}/{s["extracted_presence_tunes"][k]}' for k in RAW]
        lines.append(f'| {name} | {len(tunes)} | ' + " | ".join(cells) + " | " + str(BASELINE[name]) + " |")
        raw_only.extend(s["raw_only"])
    lines += ["", "### Écarts et exclusions", "", "Le comptage initial des accords (29/2/17) n'est pas reproduit par une reconnaissance de deux notes ABC complètes : les durées, octaves et altérations internes comptent aussi, par exemple `[G,2D2]`, `[d2f2]`, `[^db]`. Une regex limitée aux lettres adjacentes manque ces formes ; la regex complète utilisée est conservée dans `ornaments.RAW`. Les symboles d'accompagnement entre guillemets et les champs `[V:…]` ne sont pas des accords mélodiques. Les marques présentes seulement dans les en-têtes/commentaires/voix secondaires sont exclues ci-dessous."]
    for row in raw_only:
        lines.append(f'- `{row["id"]}` : ' + "; ".join(f"{k} : {v}" for k, v in row["families"].items()))
    lines += ["", "## Combinaisons présentes", "", "| Tradition-type | Airs | Notes | Mesures équiv. | Marques | Sans marque | Notes positionnées |", "|---|---:|---:|---:|---:|---:|---:|"]
    for (trad, typ), s in groups.items():
        lines.append(f'| {trad}-{typ} | {s["tunes"]} | {s["notes"]} | {s["bar_equivalents"]:.2f} | {s["occurrences"]} | {100*s["share_without_marks"]:.1f}% | {s["positioned_notes"]} |')
    lines += ["", "## Sept profils distribués", "", "Taux par 100 attaques porteuses ; n entre parenthèses = occurrences écrites. Les articulations et triolets mélodiques sont mesurés mais ne sont pas proposés comme agréments à générer.", ""]
    for profile, key in PROFILES.items():
        if key not in groups:
            continue
        s = groups[key]
        lines += [f"### {profile}", "", f'{s["tunes"]} airs, {s["notes"]} notes, {s["bar_equivalents"]:.2f} mesures équivalentes ; {100*s["share_without_marks"]:.1f}% sans marque.', "", "| Type | Taux/100 notes (n) | Porteuse min. observée (croches) | m1 | m2 | m3 | m4 | m5 | m6 | m7 | m8 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for kind in KINDS:
            total = s["by_type"][kind]
            durations = [Fraction(d) for d, cell in s["by_position"]["carrier_duration_eighths"].items() if kind in cell["by_type"]]
            cells = []
            for i in range(1, 9):
                cell = s["by_position"]["bar_position"].get(str(i))
                rate = cell["by_type"].get(kind, {"per_100_notes": 0.0, "count": 0}) if cell else None
                cells.append(f'{rate["per_100_notes"]:.3f} ({rate["count"]})' if rate else "—")
            lines.append(f'| {kind} | {total["per_100_notes"]:.3f} ({total["count"]}) | {fraction(min(durations)) if durations else "—"} | ' + " | ".join(cells) + " |")
        lines += ["", "| Source | Airs | Notes | Marques | Sans marque |", "|---|---:|---:|---:|---:|"]
        for source, cell in s["by_source"].items():
            lines.append(f'| {source} | {cell["tunes"]} | {cell["notes"]} | {cell["occurrences"]} | {100*cell["share_without_marks"]:.1f}% |')
    lines += ["", "## DS-T10b — articulations écrites", "",
              "Les articulations sont isolées de `events` dans `articulations` ; le staccato n’est compté qu’ici. Les taux sont un plancher de notation, à valider à l’oreille.", "",
              "| Profil | Liens /100 (n) | Liaisons, longueur moyenne (notes) | Liaisons répétées (n) | Ties /100 (n) | Staccato /100 (n) | Accents /100 (n) | Tenuto /100 (n) | Marcato /100 (n) |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for profile, key in PROFILES.items():
        if key not in groups:
            continue
        a = groups[key]["articulations"]
        slur = a["by_type"]["slur"]
        lengths = a["slur_lengths"]
        mean_length = (sum(int(n) * count for n, count in lengths.items()) / sum(lengths.values())) if lengths else None
        cells = [f'{a["by_type"][kind]["per_100_notes"]:.3f} ({a["by_type"][kind]["count"]})'
                 for kind in ARTICULATION_KINDS if kind != "slur"]
        lines.append(f'| {profile} | {slur["per_100_notes"]:.3f} ({slur["count"]}) | {mean_length:.2f}' if mean_length is not None else f'| {profile} | {slur["per_100_notes"]:.3f} ({slur["count"]}) | —')
        lines[-1] += " | " + str(a["slur_contour_classes"].get("repeated", 0)) + " | " + " | ".join(cells) + " |"
    lines += ["", "La proposition `[performance]` des références contient les taux par mesure, temps, demi-temps, durée, contour et longueur. Les agrégats par source/transcripteur sont totaux uniquement ; aucune table positionnelle par transcripteur.", ""]
    sample_key = ("quebecoise", "reel") if ("quebecoise", "reel") in groups else next(iter(groups), None)
    lines += ["", "## Schéma proposé pour les profils moteur", ""]
    if sample_key:
        sample = groups[sample_key]["engine_proposal"]["types"]["grace_single"]
        positions = ", ".join(f'"{i}" = {v}' for i, v in sample["per_100_notes_by_bar"].items() if v is not None)
        lines += [
            f"Exemple mesuré : {sample_key[0]}-{sample_key[1]}, agrément simple.",
            "", "```toml", "[ornaments]",
            f'reference = "references/ornaments/{sample_key[0]}-{sample_key[1]}.json"',
            'rate_unit = "per_100_carrier_notes"',
            "arousal_low_multiplier = 1.0", "arousal_high_multiplier = 1.0",
            "", "[ornaments.types.grace_single]",
            f'enabled = {str(bool(sample["occurrences"])).lower()}',
            f'written_per_100_notes = {sample["written_per_100_notes"]}',
            f'occurrences = {sample["occurrences"]} # effectif, pas réglage',
            f"per_100_notes_by_bar = {{ {positions} }}",
        ]
        if sample["min_carrier_eighths_observed"] is not None:
            lines.append(f'min_carrier_eighths = {float(Fraction(sample["min_carrier_eighths_observed"]))}')
        lines += ["```", ""]
    lines += [
        "Même sous-table pour chaque type de `engine_proposal.types` des sept JSON. Type sans occurrence : désactivé, minimum non inférable (null JSON, champ TOML omis). Position absente : aucune opportunité, ne pas inventer un taux. Les taux sont non exclusifs ; ce schéma décrit une proposition de dosage, pas une calibration validée.",
        "", "Aucun lien ABC/arousal mesuré : conserver 1→1 avant une décision d'écoute. Les minima sont observés, pas des seuils musicaux validés ; ne pas transformer la durée subdivisée d'un triolet en durée minimale avant subdivision. Aucun changement au moteur.",
        "", "Les taux par temps, demi-temps exact, durée, degré et intervalles et par source/transcripteur sont dans les références ; les événements individuels dérivés sont dans `events.jsonl`, sans copie d'ABC.", "",
    ]
    return "\n".join(lines)
