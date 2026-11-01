"""Les mêmes mesures de basse sur le généré du moteur, et leur distance à WJazzD.

    python -m harmonium_lab.backing.bass_compare \\
        --truth a1.json --truth a2.json --label grille_accompagnee \\
        --truth b1.json --label wjazzd_swing \\
        --reference references/wjazzd-swing/measures-bass.json \\
        --group all --group blues -o references/wjazzd-swing/compare-bass.json --markdown

Entrées : des fichiers `harmonium-cli --export --record-truth` (lus par
`seedvariety.bar_from_entry`). Chaque `--label` nomme les `--truth` qui le précèdent
(depuis le label précédent) : plusieurs graines d'un même profil sont regroupées, plusieurs
étiquettes (profil, ligne de base) sont comparées dans un même rapport. Seul le premier air
(`tune_index = 0`) est lu.

## Mesures sur le généré

La piste 2 est la basse (une note par pulsation) ; les accords viennent de `chord_changes`
(`root_pc`, `bass_pc`, `quality`, `is_minor`, lus par `chords.from_engine`) : l'accord d'une
pulsation est le dernier changement dont `start_step` ≤ 4 × pulsation. Une mesure est
**valide** si elle a exactement une note de basse à chacun des pas 0, 4, 8, 12 et si ses accords
sont analysables ; une mesure écartée coupe la suite (comme une mesure sans basse du corpus).
Les hauteurs de la vérité terrain sont relatives à la tonique (`pitch − key`) : la hauteur absolue
est restituée avec `position.key`. Les `BassBar` obtenus passent par `bass_measures.measure_runs`,
l'unique chemin de calcul du corpus comme du généré.

## Distance

Chaque critère donne une distance dans [0, 1] entre le généré et un groupe du corpus :

- `tv` : distance de variation totale entre deux distributions de comptes
  (½ Σ |p − q|) ;
- `share` : écart absolu de deux parts ;
- `semitones` : écart moyen de centiles (ou bornes de fenêtre), en demi-tons, divisé par 12 et
  plafonné à 1 (une octave d'écart vaut 1).

La distance agrégée est la moyenne des distances de critères disponibles (un critère sans
donnée d'un côté est omis et listé dans `missing`) ; `by_family` donne la moyenne par famille
(arrivée, approche, passage, intervalles, registre, rythme harmonique). Aucune valeur n'est
tirée de WJazzD pour juger le « bien » : la distance mesure seulement l'écart à ce corpus.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

from ..seedvariety import BASS_TRACK, bar_from_entry
from ._util import ROUND, write_json
from .bass_measures import BEATS, OUTPUT as REFERENCE, BassBar, BassRun, Beat, measure_runs
from .wjazzd import REPO
from .chords import Chord, ChordParseError, from_engine

DEFAULT_OUTPUT = REFERENCE.with_name("compare-bass.json")
STEPS_PER_BEAT = 4
OCTAVE = 12


# ── Vérité terrain → mesures ─────────────────────────────────────────────

class TruthStats(NamedTuple):
    """Comptes de lecture d'un ensemble de vérités terrain."""
    files: int
    bars: int
    bars_valid: int
    bars_no_bass: int
    bars_unparsed_chord: int
    runs: int


def _chord_at(changes: list[tuple[int, Chord]], step: int) -> Chord:
    """Dernier accord dont le pas de départ est ≤ `step`."""
    return [chord for start, chord in changes if start <= step][-1]


def runs_from_truth(paths: list[Path]) -> tuple[list[BassRun], TruthStats]:
    """Suites de mesures valides de fichiers `--record-truth` (premier air, une suite par trou)."""
    runs: list[BassRun] = []
    total = valid = no_bass = unparsed = 0
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        run: BassRun | None = None
        last_chord: Chord | None = None
        last_index: int | None = None
        for entry in data["measures"]:
            pos = entry["measure"]["position"]
            if pos["tune_index"] != 0:
                continue
            bar = bar_from_entry(entry)
            key = int(pos["key"])
            total += 1
            try:
                changes = [(start, from_engine((root + key) % 12, (bass + key) % 12, quality, is_minor))
                           for start, root, quality, is_minor, bass in bar.sigs["chords"]]
            except ChordParseError:
                unparsed += 1
                run = None
                continue
            notes: dict[int, list[int]] = {}
            for start, rel_pitch, _duration in bar.sigs["bass"]:
                notes.setdefault(start, []).append(rel_pitch + key)
            steps = [b * STEPS_PER_BEAT for b in range(BEATS)]
            complete = (all(len(notes.get(s, ())) == 1 for s in steps) and set(notes) <= set(steps))
            beat_chords = [_chord_at(changes, s) for s in steps]
            if not complete:
                no_bass += 1
                run = None
            else:
                mesure = BassBar([Beat(c, notes[s][0]) for c, s in zip(beat_chords, steps)], prev_chord=last_chord)
                contiguous = last_index is not None and bar.index == last_index + 1
                if run is None or not contiguous or run.key != key:
                    run = BassRun([], key=key)
                    runs.append(run)
                run.bars.append(mesure)
                valid += 1
            last_chord = beat_chords[-1]
            last_index = bar.index
    return runs, TruthStats(len(paths), total, valid, no_bass, unparsed, len(runs))


# ── Critères et distances ────────────────────────────────────────────────

def tv_distance(a: dict[str, int], b: dict[str, int]) -> float | None:
    """Distance de variation totale entre deux dictionnaires de comptes ; `None` si l'un est vide."""
    ta, tb = sum(a.values()), sum(b.values())
    if not ta or not tb:
        return None
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0) / ta - b.get(k, 0) / tb) for k in keys) / 2


def _get(doc: dict[str, Any], path: str) -> Any:
    node: Any = doc
    for part in path.split("."):
        node = node[part]
    return node


class Criterion(NamedTuple):
    """Un critère : famille, nom, type (`tv`, `share`, `semitones`), chemin dans les mesures et,
    pour une part, chemin du bloc dont `n` dit si la part existe."""
    family: str
    name: str
    kind: str
    path: str
    n_path: str = ""


def _folded_beats(counts: dict[str, int]) -> dict[str, int]:
    """Temps du changement d'accord replié en `beat1` / `beat3` / `other`."""
    return {"beat1": counts["1"], "beat3": counts["3"], "other": counts["2"] + counts["4"]}


CRITERIA: tuple[Criterion, ...] = (
    Criterion("arrival", "arrival_classes_at_change", "tv", "arrival.change.counts"),
    Criterion("arrival", "arrival_bass_share_at_change", "share", "arrival.change.shares.bass", "arrival.change"),
    Criterion("arrival", "bar_start_no_change_classes", "tv", "arrival.bar_start_no_change.counts"),
    Criterion("arrival", "bar_start_no_change_bass_share", "share", "arrival.bar_start_no_change.shares.bass", "arrival.bar_start_no_change"),
    Criterion("approach", "approach_weights", "tv", "approach.all.weights.counts"),
    Criterion("approach", "approach_weights_bar_change", "tv", "approach.bar_change.weights.counts"),
    Criterion("approach", "approach_weights_mid_change", "tv", "approach.mid_change.weights.counts"),
    Criterion("approach", "approach_classes", "tv", "approach.all.counts"),
    Criterion("approach", "approach_distance", "tv", "approach.all.distance.counts"),
    Criterion("approach", "approach_above_share", "share", "approach.all.moving.above_below.shares.above", "approach.all.moving.above_below"),
    Criterion("approach", "approach_same_side_share", "share", "approach.all.moving.side.shares.same_side_as_arrival", "approach.all.moving.side"),
    Criterion("passage", "passage_classes", "tv", "passage.counts"),
    Criterion("passage", "passage_engine_classes", "tv", "passage_engine.counts"),
    Criterion("intervals", "interval_histogram", "tv", "intervals.counts"),
    Criterion("intervals", "interval_repeat_share", "share", "intervals.repeat_share", "intervals"),
    Criterion("intervals", "interval_keep_direction_share", "share", "intervals.keep_direction.share", "intervals.keep_direction"),
    Criterion("intervals", "interval_toward_target_share", "share", "intervals.toward_target.share", "intervals.toward_target"),
    Criterion("intervals", "interval_percentiles", "semitones", "intervals.percentiles"),
    Criterion("register", "register_percentiles", "semitones", "register.pitch"),
    Criterion("register", "register_percentiles_relative_to_tonic", "semitones", "register.relative_to_tonic"),
    Criterion("register", "walk_window", "semitones", "register.walk_window"),
    Criterion("register", "arrival_window", "semitones", "register.arrival_window"),
    Criterion("harmonic_rhythm", "chords_per_bar", "tv", "harmonic_rhythm.chords_per_bar.counts"),
    Criterion("harmonic_rhythm", "chord_duration", "tv", "harmonic_rhythm.chord_duration_beats.counts"),
    Criterion("harmonic_rhythm", "change_beat", "tv", "harmonic_rhythm.change_beat.counts"),
)


def _numeric(block: dict[str, Any]) -> dict[str, float]:
    """Valeurs numériques d'un bloc de centiles (clés `pNN`, `low`, `high`) ; ignore `n` et le reste."""
    return {k: v for k, v in block.items()
            if (k.startswith("p") and k[1:].isdigit() or k in ("low", "high")) and v is not None}


def criterion_distance(criterion: Criterion, ref: dict[str, Any], gen: dict[str, Any]) -> dict[str, Any]:
    """Distance d'un critère (`None` si l'un des deux côtés n'a pas de donnée) et valeurs comparées."""
    a, b = _get(ref, criterion.path), _get(gen, criterion.path)
    distance: float | None
    if criterion.kind == "tv":
        if criterion.name == "change_beat":
            a, b = _folded_beats(a), _folded_beats(b)
        distance = tv_distance(a, b)
        shown = [_normalise(a), _normalise(b)]
    elif criterion.kind == "share":
        distance = abs(a - b) if _get(ref, criterion.n_path)["n"] and _get(gen, criterion.n_path)["n"] else None
        shown = [a, b]
    else:
        na, nb = _numeric(a), _numeric(b)
        keys = sorted(set(na) & set(nb))
        distance = (sum(min(1.0, abs(na[k] - nb[k]) / OCTAVE) for k in keys) / len(keys)) if keys else None
        shown = [na, nb]
    return {
        "distance": None if distance is None else round(distance, ROUND),
        "generated": shown[1],
        "kind": criterion.kind,
        "reference": shown[0],
    }


def _normalise(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    return {k: round(v / total, ROUND) for k, v in counts.items()} if total else {}


def compare(reference: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    """Distances par critère, par famille et agrégée (moyenne des critères disponibles)."""
    criteria = {c.name: criterion_distance(c, reference, generated) for c in CRITERIA}
    available = {c.name: criteria[c.name]["distance"] for c in CRITERIA if criteria[c.name]["distance"] is not None}
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


def build(reference_doc: dict[str, Any], labels: dict[str, list[Path]], groups: list[str],
          command: str, reference_path: str) -> dict[str, Any]:
    """Document de comparaison : mesures du généré par étiquette, distances par groupe de référence."""
    measured: dict[str, dict[str, Any]] = {}
    for label, paths in labels.items():
        runs, stats = runs_from_truth(paths)
        measured[label] = {"provenance": {"truth_files": [p.name for p in paths], **stats._asdict()},
                           "measures": measure_runs(runs)}
    comparisons: dict[str, dict[str, Any]] = {}
    for group in groups:
        ref = reference_doc["groups"][group]
        comparisons[group] = {label: compare(ref, m["measures"]) for label, m in measured.items()}
    return {
        "command": command,
        "reference": {"file": reference_path, "provenance": reference_doc["provenance"],
                      "groups": {g: reference_doc["groups"][g]["counts"] for g in groups}},
        "labels": measured,
        "comparisons": comparisons,
    }


# ── Rapport Markdown ─────────────────────────────────────────────────────

def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, dict):
        return " ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in value.items())
    return f"{value:.3f}" if isinstance(value, float) else str(value)


def markdown(doc: dict[str, Any]) -> str:
    """Rapport lisible : une section par groupe de référence, une colonne de distance par étiquette."""
    prov = doc["reference"]["provenance"]
    labels = list(doc["labels"])
    out = ["# Distance de la basse générée à WJazzD (swing)", "",
           f"Référence : {prov['source']} — {prov['version']} ({doc['reference']['file']}), "
           f"{prov['n_solos']} solos, {prov['n_bars_valid']} mesures valides.", "",
           f"Licence : {prov['licence']}. {prov['attribution']}", "",
           f"Commande : `{doc['command']}`", ""]
    out.append("Généré :")
    for label, m in doc["labels"].items():
        p = m["provenance"]
        out.append(f"- `{label}` : {p['files']} fichier(s), {p['bars_valid']} mesures valides sur {p['bars']} "
                   f"(sans basse complète : {p['bars_no_bass']}, accord non analysé : {p['bars_unparsed_chord']})")
    for group, per_label in doc["comparisons"].items():
        counts = doc["reference"]["groups"][group]
        out += ["", f"## Groupe de référence `{group}` ({counts['solos']} solos, {counts['bars_valid']} mesures valides)", "",
                "| famille | critère | " + " | ".join(f"d({lb})" for lb in labels) + " |",
                "|---|---|" + "---|" * len(labels)]
        for c in CRITERIA:
            cells = " | ".join(_fmt(per_label[lb]["criteria"][c.name]["distance"]) for lb in labels)
            out.append(f"| {c.family} | {c.name} | {cells} |")
        out.append("| **agrégée** | moyenne des critères | "
                   + " | ".join(f"**{_fmt(per_label[lb]['distance'])}**" for lb in labels) + " |")
        out += ["", "Par famille : " + " ; ".join(
            f"`{lb}` : " + ", ".join(f"{f} {v:.3f}" for f, v in per_label[lb]["by_family"].items()) for lb in labels), ""]
        out += ["Valeurs comparées (référence puis étiquettes) :", "",
                "| critère | référence | " + " | ".join(labels) + " |", "|---|---|" + "---|" * len(labels)]
        for c in CRITERIA:
            ref_value = per_label[labels[0]]["criteria"][c.name]["reference"]
            cells = " | ".join(_fmt(per_label[lb]["criteria"][c.name]["generated"]) for lb in labels)
            out.append(f"| {c.name} | {_fmt(ref_value)} | {cells} |")
    return "\n".join(out) + "\n"


def _display(path: Path) -> str:
    """Chemin lisible et stable : relatif au dépôt du labo s'il y est."""
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


class _LabelAction(argparse.Action):
    """`--truth` empile des fichiers ; `--label` nomme ceux qui précèdent depuis le dernier label."""

    def __call__(self, parser, namespace, values, option_string=None):  # noqa: ANN001
        events = getattr(namespace, "events", None) or []
        events.append((self.dest, values))
        namespace.events = events


def labels_from_events(events: list[tuple[str, Any]]) -> dict[str, list[Path]]:
    """Regroupe les événements `--truth` / `--label` en `{étiquette: fichiers}`."""
    labels: dict[str, list[Path]] = {}
    pending: list[Path] = []
    for kind, value in events:
        if kind == "truth":
            pending.append(Path(value))
        else:
            if not pending:
                raise ValueError(f"--label {value} sans --truth avant lui")
            labels.setdefault(value, []).extend(pending)
            pending = []
    if pending:
        labels.setdefault("genere", []).extend(pending)
    return labels


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--truth", action=_LabelAction, help="fichier --record-truth (répétable)")
    ap.add_argument("--label", action=_LabelAction, help="nom des --truth qui précèdent (répétable)")
    ap.add_argument("--reference", type=Path, default=REFERENCE)
    ap.add_argument("--group", action="append", help="groupe(s) de référence (défaut : all)")
    ap.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--markdown", action="store_true", help="écrit aussi le rapport .md à côté du JSON")
    args = ap.parse_args(argv)
    events = getattr(args, "events", None)
    if not events:
        ap.error("au moins un --truth est requis")
    try:
        labels = labels_from_events(events)
        reference_doc = json.loads(args.reference.read_text(encoding="utf-8"))
        command = "python -m harmonium_lab.backing.bass_compare " + " ".join(argv if argv is not None else sys.argv[1:])
        doc = build(reference_doc, labels, args.group or ["all"], command, _display(args.reference))
    except (ValueError, OSError, KeyError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    write_json(args.output, doc)
    for group, per_label in doc["comparisons"].items():
        for label, result in per_label.items():
            print(f"{group:<12} {label:<24} distance agrégée = {result['distance']}")
    if args.markdown:
        args.output.with_suffix(".md").write_text(markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
