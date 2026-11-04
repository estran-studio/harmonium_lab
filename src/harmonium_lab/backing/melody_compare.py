"""Mélodie générée par le moteur contre les solos swing de WJazzD (E12).

    python -m harmonium_lab.backing.melody_compare \\
        --truth a1.json --truth a2.json --label bouche_trou \\
        --truth b1.json --truth b2.json --label banque_swing \\
        -o references/wjazzd-melodie/compare-melody.json --markdown

Entrées : des fichiers `harmonium-cli --export --record-truth` (premier air, piste `Melody`). Chaque
`--label` nomme les `--truth` qui le précèdent depuis le label précédent (comme `bass_compare`).
Les mesures du généré passent par `melody_measures.measure`, l'unique chemin de calcul du corpus
comme du généré ; la distance de chaque critère est celle de `bass_compare` (`tv`, `share`,
`semitones` : écart de centiles / 12, plafonné à 1). La distance agrégée est la moyenne des critères
disponibles ; `by_family` en donne la moyenne par famille.

Familles : `intervals` (histogramme des demi-tons, d'une mesure à l'autre, répétitions, saut maximal),
`rhythm` (attaques par mesure, part d'attaque de chaque croche, durées, anticipation au créneau 7),
`chord` (relation à l'accord des attaques : temps forts, quatre temps, croches), `register`
(hauteurs, ambitus) et `phrasing` (longueur des phrases en temps, part de temps muets). Les
cellules n'ont pas de silence : la famille `phrasing` du généré s'écarte du corpus par
construction (écart de schéma, pas de banque).

`--levels` rend aussi, pour chaque étiquette, la conformité aux bornes de difficulté E10 (saut,
attaques par mesure, plus petite durée, ambitus), lues sur la même vérité terrain.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from ._util import ROUND, write_json
from .bass_compare import Criterion, _LabelAction, _display, _fmt, criterion_distance, labels_from_events
from .melody_cells import LEVELS
from .melody_measures import MBar, OUTPUT as REFERENCE, SLOTS, measure, truth_solos

DEFAULT_OUTPUT = REFERENCE.with_name("compare-melody.json")

CRITERIA: tuple[Criterion, ...] = (
    Criterion("intervals", "interval_histogram", "tv", "total.intervals_semitones.counts"),
    Criterion("intervals", "cross_bar_interval_histogram", "tv", "cross_bar_intervals.counts"),
    Criterion("intervals", "interval_repeat_share", "share", "total.intervals_semitones.shares.0",
              "total.intervals_semitones"),
    Criterion("intervals", "interval_keep_direction_share", "share", "keep_direction", "total.intervals_semitones"),
    Criterion("intervals", "biggest_leap_percentiles", "semitones", "total.biggest_leap"),
    Criterion("rhythm", "attacks_per_bar", "tv", "total.attacks_per_bar.counts"),
    Criterion("rhythm", "slot_attack_shares", "tv", "slot_attack_share"),
    Criterion("rhythm", "legato_duration", "tv", "total.legato_duration.counts"),
    Criterion("rhythm", "anticipation_share", "share", "anticipation.bars_with_attack_7_share", "bars"),
    Criterion("chord", "strong_beat_relations", "tv", "targets.strong.counts"),
    Criterion("chord", "beat_relations", "tv", "targets.beats.counts"),
    Criterion("chord", "offbeat_relations", "tv", "targets.offbeat.counts"),
    Criterion("chord", "strong_beat_chord_share", "share", "strong_chord_share", "targets.strong"),
    Criterion("chord", "offbeat_chord_share", "share", "offbeat_chord_share", "targets.offbeat"),
    Criterion("register", "register_percentiles", "semitones", "register"),
    Criterion("register", "ambitus_percentiles", "semitones", "total.ambitus"),
    Criterion("phrasing", "phrase_length_beats", "semitones", "phrases.length_beats"),
    Criterion("phrasing", "silent_beats_share", "share", "silence.beats_without_sound_share", "bars"),
)


def compare(reference: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    """Distances par critère, par famille et agrégée (moyenne des critères disponibles)."""
    criteria = {c.name: criterion_distance(c, reference, generated) for c in CRITERIA}
    available = {n: v["distance"] for n, v in criteria.items() if v["distance"] is not None}
    families: dict[str, list[float]] = {}
    for c in CRITERIA:
        if c.name in available:
            families.setdefault(c.family, []).append(available[c.name])
    return {
        "criteria": criteria,
        "distance": round(sum(available.values()) / len(available), ROUND) if available else None,
        "by_family": {f: round(sum(v) / len(v), ROUND) for f, v in sorted(families.items())},
        "missing": sorted(c.name for c in CRITERIA if c.name not in available),
    }


def compliance(solos: Sequence[Sequence[MBar]], level: int) -> dict[str, Any]:
    """Conformité des mesures générées aux bornes E10 du niveau (1 à 3) : parts de mesures et pires valeurs.

    Le saut est celui d'une attaque à la suivante, d'une mesure à l'autre comprise (comme le filtre).
    La mesure de clôture de l'air (la dernière du fichier) est écartée : le filtre ne la touche pas (E10,
    « mesure de clôture non touchée »), son saut d'arrivée est celui de la cellule tirée.
    """
    leap_max, attacks_max, dur_min, ambitus_max = LEVELS[level]
    bars = bad = 0
    worst = {"leap": 0, "attacks": 0, "ambitus": 0, "min_dur": SLOTS}
    violations = {"leap": 0, "attacks": 0, "min_dur": 0, "ambitus": 0}
    for full in solos:
        solo = full[:-1]
        previous = None
        for bar in solo:
            if not bar.notes:
                previous = None if previous is not None and previous.bar + 1 != bar.bar else previous
                continue
            bars += 1
            pitches = [n.pitch for n in bar.notes]
            leaps = [abs(b - a) for a, b in zip(pitches, pitches[1:])]
            if previous is not None and previous.bar + 1 == bar.bar:
                leaps.append(abs(pitches[0] - previous.notes[-1].pitch))
            ends = [n.slot for n in bar.notes[1:]] + [SLOTS]
            min_dur = min(e - n.slot for n, e in zip(bar.notes, ends))
            values = {"leap": max(leaps, default=0), "attacks": len(bar.notes),
                      "ambitus": max(pitches) - min(pitches), "min_dur": min_dur}
            worst["leap"] = max(worst["leap"], values["leap"])
            worst["attacks"] = max(worst["attacks"], values["attacks"])
            worst["ambitus"] = max(worst["ambitus"], values["ambitus"])
            worst["min_dur"] = min(worst["min_dur"], min_dur)
            broken = [k for k, ok in (("leap", values["leap"] <= leap_max), ("attacks", values["attacks"] <= attacks_max),
                                      ("min_dur", min_dur >= dur_min), ("ambitus", values["ambitus"] <= ambitus_max))
                      if not ok]
            for k in broken:
                violations[k] += 1
            bad += bool(broken)
            previous = bar
    return {"level": level, "bounds": {"leap": leap_max, "attacks": attacks_max, "min_dur": dur_min,
                                       "ambitus": ambitus_max},
            "bars": bars, "bars_out_of_bounds": bad, "violations": violations, "worst": worst}


def build(reference_doc: dict[str, Any], labels: dict[str, list[Path]], command: str, reference_path: str,
          levels: dict[str, int] | None = None) -> dict[str, Any]:
    measured: dict[str, Any] = {}
    comparisons: dict[str, Any] = {}
    for label, paths in labels.items():
        solos, stats = truth_solos(paths)
        doc = measure(solos)
        measured[label] = {"provenance": {"truth_files": [p.name for p in paths], **stats}, "measures": doc}
        comparisons[label] = compare(reference_doc, doc)
        if levels and label in levels:
            measured[label]["compliance"] = compliance(solos, levels[label])
    return {"command": command,
            "reference": {"file": reference_path, "provenance": reference_doc["provenance"]},
            "labels": measured, "comparisons": comparisons}


def markdown(doc: dict[str, Any]) -> str:
    prov = doc["reference"]["provenance"]
    labels = list(doc["labels"])
    out = ["# Distance de la mélodie générée à WJazzD (swing)", "",
           f"Référence : {prov['source']} ({doc['reference']['file']}), {prov['n_solos']} solos, "
           f"{prov['n_bars']} mesures, {prov['n_notes']} attaques.", "",
           f"Licence : {prov['licence']}. {prov['attribution']}", "",
           f"Commande : `{doc['command']}`", "", "Généré :"]
    for label, m in doc["labels"].items():
        p = m["provenance"]
        out.append(f"- `{label}` : {p.get('files', 0)} fichier(s), {p.get('bars', 0)} mesures, "
                   f"{p.get('notes', 0)} attaques ({p.get('dropped', 0)} sur un pas impair ou un créneau pris)")
    out += ["", "| famille | critère | " + " | ".join(f"d({lb})" for lb in labels) + " |",
            "|---|---|" + "---|" * len(labels)]
    for c in CRITERIA:
        out.append(f"| {c.family} | {c.name} | "
                   + " | ".join(_fmt(doc["comparisons"][lb]["criteria"][c.name]["distance"]) for lb in labels) + " |")
    out.append("| **agrégée** | moyenne des critères | "
               + " | ".join(f"**{_fmt(doc['comparisons'][lb]['distance'])}**" for lb in labels) + " |")
    out += ["", "Par famille : " + " ; ".join(
        f"`{lb}` : " + ", ".join(f"{f} {v:.3f}" for f, v in doc["comparisons"][lb]["by_family"].items())
        for lb in labels), "",
        "Valeurs comparées (référence puis étiquettes) :", "",
        "| critère | référence | " + " | ".join(labels) + " |", "|---|---|" + "---|" * len(labels)]
    for c in CRITERIA:
        ref_value = doc["comparisons"][labels[0]]["criteria"][c.name]["reference"]
        out.append(f"| {c.name} | {_fmt(ref_value)} | "
                   + " | ".join(_fmt(doc["comparisons"][lb]["criteria"][c.name]["generated"]) for lb in labels) + " |")
    shown = [(lb, m["compliance"]) for lb, m in doc["labels"].items() if "compliance" in m]
    if shown:
        out += ["", "Conformité aux bornes de difficulté E10 :", "",
                "| étiquette | niveau | mesures | hors bornes | saut | attaques | durée | ambitus | pires (saut / attaques / durée / ambitus) |",
                "|---|---|---|---|---|---|---|---|---|"]
        for lb, c in shown:
            v, w = c["violations"], c["worst"]
            out.append(f"| {lb} | {c['level']} | {c['bars']} | {c['bars_out_of_bounds']} | {v['leap']} | {v['attacks']} "
                       f"| {v['min_dur']} | {v['ambitus']} | {w['leap']} / {w['attacks']} / {w['min_dur']} / {w['ambitus']} |")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--truth", action=_LabelAction, help="fichier --record-truth (répétable)")
    ap.add_argument("--label", action=_LabelAction, help="nom des --truth qui précèdent (répétable)")
    ap.add_argument("--level", action="append", default=[], metavar="LABEL=N",
                    help="conformité E10 de l'étiquette au niveau N (1 à 3), répétable")
    ap.add_argument("--reference", type=Path, default=REFERENCE)
    ap.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args(argv)
    events = getattr(args, "events", None)
    if not events:
        ap.error("au moins un --truth est requis")
    try:
        labels = labels_from_events(events)
        levels = {k: int(v) for k, v in (item.split("=", 1) for item in args.level)}
        reference_doc = json.loads(args.reference.read_text(encoding="utf-8"))
        command = "python -m harmonium_lab.backing.melody_compare " + " ".join(argv if argv is not None else sys.argv[1:])
        doc = build(reference_doc, labels, command, _display(args.reference), levels)
    except (ValueError, OSError, KeyError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    write_json(args.output, doc)
    for label, result in doc["comparisons"].items():
        print(f"{label:<24} distance agrégée = {result['distance']}  par famille {result['by_family']}")
    if args.markdown:
        args.output.with_suffix(".md").write_text(markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
