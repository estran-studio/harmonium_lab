"""Rapports français DS-T9 et propositions de règles, jamais appliquées au moteur."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .structure import METHOD, PROFILES, analyze_paths


def _percent(value: float | None) -> str:
    return "non mesuré" if value is None else f"{100 * value:.1f} %"


def deviations(real: dict, generated: dict) -> list[dict]:
    """Écarts de taux en points ; au moins un par domaine si observable."""
    candidates = []
    def add(domain: str, label: str, r: float | None, g: float | None, rule: dict, denominator: int) -> None:
        if r is not None and g is not None:
            candidates.append({"domain": domain, "label": label, "real": r, "engine": g, "gap_points": round(100 * (g - r), 4), "real_opportunities": denominator, "proposed_rule": rule})
    for key, label, domain in (
        ("opening_reprise_rate", "m.5-6 reprennent exactement m.1-2", "répétition"),
        ("antecedent_consequent_rate", "question-réponse 4+4 avec repos tonique final", "phrases"),
        ("b_reuses_a_ending_rate", "le début de B reprend ou transforme la fin de A", "phrases"),
    ):
        r = real["phrases"][key]
        add(domain, label, r, generated["phrases"][key], {"operation": key.removesuffix("_rate"), "probability": r}, real["phrases"]["ab_pairs" if key.startswith("b_") else "parts"])
    real_structures = {row["pattern"]: row["share"] for row in real["structures"]}
    engine_structures = {row["pattern"]: row["share"] for row in generated["structures"]}
    for pattern in sorted(real_structures.keys() | engine_structures.keys()):
        r = real_structures.get(pattern, 0.0)
        add("répétition", f"structure de paires « {pattern} »", r, engine_structures.get(pattern, 0.0), {"operation": "pair_structure", "letters": pattern, "probability": r}, real["parts"].get("all", 0))
    for position in sorted(real["transformations"].keys() & generated["transformations"].keys()):
        r, g = real["transformations"].get(position), generated["transformations"].get(position)
        if not r or not g:
            continue
        for transform, label in (("exact", "répétition exacte"), ("sequence", "séquence diatonique"), ("varied_ending", "fin variée"), ("inversion", "inversion"), ("rhythmic_variation", "variation rythmique")):
            # Les trois vues de la même copie sont déjà représentées par
            # opening_reprise : éviter trois recommandations redondantes.
            if transform == "exact" and position.split(":")[-1] in ("m5/m1", "m6/m2", "m5-6/m1-2"):
                continue
            add("répétition", f"{position} : {label}", r["rates"][transform], g["rates"][transform], {"position": position, "operation": transform, "probability": r["rates"][transform]}, r["opportunities"])
    for position, r in real["phrases"]["rest_by_position"].items():
        # Toutes les positions, pas seulement les cadences attendues m.4/8.
        g = generated["phrases"]["rest_by_position"].get(position)
        if g:
            for key, label in (("long_final_rate", "note finale tenue au moins un temps"), ("tonic_cadence_rate", "repos final sur la tonique")):
                add("phrases", f"{position} : {label}", r[key], g[key], {"position": position, "operation": key.removesuffix("_rate"), "probability": r[key]}, r["bars"])
    rr, gr = real["rhythm"], generated["rhythm"]
    for key, label in (("continuous_eighth_rate", "mesures à croches continues"), ("syncopated_bar_rate", "mesures avec une syncope notée"), ("repeated_note_rate", "notes successives de même hauteur")):
        add("rythme", label, rr[key], gr[key], {"operation": key.removesuffix("_rate"), "probability": rr[key]}, rr["counts"].get("adjacent_pairs" if key == "repeated_note_rate" else "bars", 0))
    # Comparer au vocabulaire complet, pas au seul top20 : absent vaut
    # réellement zéro, et non « hors du tableau ».
    real_cells = {c["pattern"]: c["share"] for c in rr["cells"]}
    generated_cells = {c["pattern"]: c["share"] for c in gr["cells"]}
    for pattern in sorted(real_cells.keys() | generated_cells.keys()):
        r = real_cells.get(pattern, 0.0)
        add("rythme", f"cellule en croches « {pattern} »", r, generated_cells.get(pattern, 0.0), {"operation": "rhythm_cell", "durations_eighths": pattern, "probability": r}, rr["counts"]["bars"])
    candidates.sort(key=lambda c: (-abs(c["gap_points"]), c["label"]))
    chosen = []
    for domain in ("répétition", "phrases", "rythme"):
        best = next((c for c in candidates if c["domain"] == domain), None)
        if best:
            chosen.append(best)
    for c in candidates:
        if len(chosen) == 5:
            break
        if c not in chosen:
            chosen.append(c)
    return sorted(chosen, key=lambda c: (-abs(c["gap_points"]), c["label"]))


def render_report(report: dict) -> str:
    lines = [f"# Structure — {report['tradition']} / {report['type']}", "", "## Périmètre", ""]
    for label, stats in (("Réel", report["real"]), ("Moteur", report.get("generated"))):
        if stats is None:
            continue
        lines.append(f"- {label} : {stats['tunes']} airs analysés sur {stats['input_files']}, {stats['positional_tunes']} avec partie de 8 mesures ; {stats['parts'].get('all', 0)} parties, {stats['rhythm']['counts'].get('bars', 0)} mesures rythmiques ; {sum(stats['errors'].values())} rejets.")
        lines.append(f"- {label} : {stats['excluded_non8_parts']} parties non positionnées ; {stats['excluded_engine_tail_bars']} mesures de queue moteur exclues ; tonalités : `{json.dumps(stats['key_sources'], ensure_ascii=False)}`.")
        if stats["engine_intro_bars"]:
            lines.append(f"- Intros exclues (mesures → nombre d'exports) : `{stats['engine_intro_bars']}` ; scores d'alignement sur 16 : `{stats['engine_alignment_scores']}` ; alignements ambigus : {stats['engine_ambiguous_alignments']}.")
    lines += ["", "## Définitions et limites", ""]
    lines += [f"- **{key}** : {value}" for key, value in METHOD.items()]
    for label, stats in (("Réel", report["real"]), ("Moteur", report.get("generated"))):
        if stats is None:
            continue
        lines += ["", f"## {label} — carte de répétition", ""]
        for part, matrices in stats["similarity"].items():
            if part == "all":
                continue
            for channel, matrix in matrices.items():
                lines += [f"### Partie {part} — {channel}", "", "| Mesure | " + " | ".join(map(str, range(1, 9))) + " |", "|---|" + "---|" * 8]
                lines += [f"| {i} | " + " | ".join(f"{v:.2f}" for v in row) + " |" for i, row in enumerate(matrix, 1)]
                lines.append("")
        lines += ["### Structures de paires de mesures", "", "| Structure | Parties | Part des parties | Airs concernés | Part des airs positionnables |", "|---|---:|---:|---:|---:|"]
        lines += [f"| `{r['pattern']}` | {r['count']} | {_percent(r['share'])} | {r['tune_count']} | {_percent(r['tune_share'])} |" for r in stats["structures"][:20]]
        lines += ["", "## " + label + " — transformations par position", "", "Chaque dénominateur est le nombre de comparaisons disponibles. Les catégories peuvent se chevaucher.", "", "| Position (cible/source) | n | Exacte | Séquence | Fin variée | Inversion | Rythme varié |", "|---|---:|---:|---:|---:|---:|---:|"]
        for position, entry in stats["transformations"].items():
            lines.append(f"| {position} | {entry['opportunities']} | " + " | ".join(_percent(entry["rates"][k]) for k in ("exact", "sequence", "varied_ending", "inversion", "rhythmic_variation")) + " |")
        phrase = stats["phrases"]
        lines += ["", f"## {label} — phrases et repos", "", f"- Début repris en m.5-6 : {_percent(phrase['opening_reprise_rate'])} des {phrase['parts']} parties.", f"- Indice antécédent/conséquent : {_percent(phrase['antecedent_consequent_rate'])} des parties.", f"- Début de B lié à la fin de A : {_percent(phrase['b_reuses_a_ending_rate'])} des {phrase['ab_pairs']} liens A/B.", "", "| Position | n | Finale longue | Finale tonique | Repos tonique | Silence final |", "|---|---:|---:|---:|---:|---:|"]
        for position, r in phrase["rest_by_position"].items():
            lines.append(f"| {position} | {r['bars']} | " + " | ".join(_percent(r[k + "_rate"]) for k in ("long_final", "tonic_final", "tonic_cadence", "rest_after_final")) + " |")
        rhythm = stats["rhythm"]
        lines += ["", f"## {label} — rythmes", "", f"- Entropie : {rhythm['entropy_bits']} bits ; {rhythm['vocabulary_size']} cellules distinctes. Estimation descriptive sensible au nombre d'airs (20 côté moteur).", f"- Croches continues : {_percent(rhythm['continuous_eighth_rate'])} des mesures ; syncope : {_percent(rhythm['syncopated_bar_rate'])} des mesures ; notes répétées : {_percent(rhythm['repeated_note_rate'])} des paires successives dans une mesure.", f"- Groupes de trois notes répétées en triolets : {rhythm['counts'].get('repeated_triplets', 0)} (fenêtres de trois notes, recouvrement possible).", "", "### Top 20 des cellules (durées en croches ; z = silence)", "", "| Cellule | Mesures | Part |", "|---|---:|---:|"]
        lines += [f"| `{r['pattern']}` | {r['count']} | {_percent(r['share'])} |" for r in rhythm["top20"]]
        lines += ["", "### Position des notes longues (dans la mesure, origine 0)", "", "| Attaque en croches | Notes | Part des notes longues |", "|---|---:|---:|"]
        lines += [f"| {r['pattern']} | {r['count']} | {_percent(r['share'])} |" for r in rhythm["long_note_onsets"]]
        accents = rhythm["accents"]
        lines += ["", f"Accents ABC explicites : {accents['count']} sur {accents['tunes_with_marks']} airs ; leur absence ne mesure pas l'accentuation réelle."]
        if accents["onsets"]:
            lines += ["", "| Attaque en croches | Marques |", "|---|---:|"]
            lines += [f"| {r['pattern']} | {r['count']} |" for r in accents["onsets"]]
        if stats["errors"]:
            lines += ["", "### Rejets", "", "```json", json.dumps(stats["errors"], ensure_ascii=False, indent=2), "```"]
    if report.get("deviations"):
        lines += ["", "## Cinq écarts et règles proposées", ""] + _deviation_lines(report["deviations"])
    return "\n".join(lines) + "\n"


def _deviation_lines(rows: list[dict]) -> list[str]:
    lines = ["| Observation | Réel | Moteur | Écart (points) | Occasions réelles |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {r['label']} | {_percent(r['real'])} | {_percent(r['engine'])} | {r['gap_points']:+.1f} | {r['real_opportunities']} |" for r in rows]
    lines += ["", "Règles en données proposées (probabilités entre 0 et 1 ; cibles à écouter, pas des décisions appliquées) :", ""]
    lines += [f"{i}. **{r['label']}** : viser {_percent(r['real'])} des occasions ; `{json.dumps(r['proposed_rule'], ensure_ascii=False, sort_keys=True)}`." for i, r in enumerate(rows, 1)]
    return lines


def write_synthesis(output: Path) -> Path:
    reports = {}
    for path in sorted(output.glob("*/stats.json")):
        report = json.loads(path.read_text())
        if report.get("engine_profile") in PROFILES and report.get("deviations"):
            reports[report["engine_profile"]] = report
    lines = [
        "# Phrases, motifs et rythmes : vrais airs et moteur", "",
        "Ces chiffres décrivent les transcriptions, pas toute une tradition. Les propositions sont des paramètres à essayer puis écouter : le moteur n'a pas été modifié.", "",
        "Écarts absolus de taux, en points ; on retient au moins un écart par domaine (répétition, phrases, rythme), puis les plus grands restants. Les mesures d'un air sont liées : pas de test de significativité ni de classement de qualité. Les attaques MIDI absolues sont ramenées à la croche avant de redécouper les mesures : le swing, le gate et la petite dérive d'horloge de l'export sont exclus. Les banques distribuées du moteur sont en croches ; les triolets réels restent en fractions exactes. On compare donc des rythmes écrits estimés, pas les beats audio.", "",
        "Les exports incluent des intros de 1 ou 2 mesures selon le profil et le seed. On repère le corps AABB par l'identité des reprises A/A et B/B, sans utiliser la copie m.1-2 vers m.5-6 comme critère. Seules les premières passes A et B du corps comptent. Les ambiguïtés d'alignement sont signalées. L'indice question-réponse est une règle descriptive stricte, pas une reconnaissance musicologique universelle.",
    ]
    for profile in PROFILES:
        lines += ["", f"## {profile}", ""]
        report = reports.get(profile)
        if not report:
            lines += ["Comparaison non disponible : lancer trad-structure avec les exports de ce profil."]
            continue
        real, engine = report["real"], report["generated"]
        lines += [f"Corpus {report['tradition']} / {report['type']} : {real['tunes']} airs, dont {real['positional_tunes']} positionnables ; moteur : {engine['tunes']} seeds, {engine['parts'].get('all', 0)} parties A/B.", ""]
        lines += [f"Intros repérées (mesures → nombre d'exports) : `{engine['engine_intro_bars']}` ; scores d'identité des reprises sur 16 : `{engine['engine_alignment_scores']}` ; alignements ambigus : {engine['engine_ambiguous_alignments']}. Tonalités/modes : `{engine['key_sources']}`.", ""]
        lines += _deviation_lines(report["deviations"])
        lines += ["", f"Variété rythmique (entropie descriptive, sensible à la taille du lot) : réel {real['rhythm']['entropy_bits']} bits, moteur {engine['rhythm']['entropy_bits']} bits."]
    lines += [
        "", "## Avant toute modification du moteur", "",
        "1. Écouter des exemples réels et générés avec le même violon et le même accompagnement, notamment les m.3, 4, 5 et 8.",
        "2. Essayer une seule règle à la fois ; garder la tonalité, la tessiture et les cadences valides. Les règles de séquence doivent aussi choisir le déplacement dans la distribution mesurée par position (sequence_shifts dans stats.json).",
        "3. Recalculer et refaire une écoute en aveugle. Réduire un écart statistique n'est pas une preuve d'amélioration musicale.", "",
        "Le résultat antérieur « 52 % contre 0 % » n'est pas effacé : il portait sur les mesures d'export non réalignées. Ici les intros sont exclues avant de comparer les positions dans A et B ; le taux obtenu mesure donc une autre fenêtre. Les champs session_key/session_scale de la vérité peuvent être vides : le journal du même export fournit alors la tonalité réellement annoncée par le moteur, plutôt qu'une estimation ambiguë entre majeur et relatif mineur.",
    ]
    path = output / "synthese.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_structure(corpus: Path, tune_type: str, generated: Path | None, output: Path, references: Path) -> Path:
    tradition = "quebecoise" if corpus.name == "trad" else corpus.name
    paths = sorted((corpus / "tunes" / tune_type).glob("*.abc"))
    if not paths:
        raise ValueError(f"Aucun ABC dans {corpus / 'tunes' / tune_type}")
    real = analyze_paths(paths, tune_type)
    if not real["tunes"]:
        raise ValueError(f"Aucun air analysable : {real['errors']}")
    version = corpus / "VERSION"
    manifest = corpus / "manifest.jsonl"
    report = {"schema_version": 1, "tradition": tradition, "type": tune_type, "method": METHOD, "corpus_version": version.read_text().strip() if version.exists() else None, "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest() if manifest.exists() else None, "real": real}
    if generated is not None:
        midis = sorted(generated.glob("*.mid")) + sorted(generated.glob("*.midi"))
        if not midis:
            raise ValueError(f"Aucun MIDI dans {generated}")
        engine = analyze_paths(midis, tune_type, engine=True)
        if engine["tunes"] != len(midis):
            raise ValueError(f"Exports incomplets ou illisibles : {engine['errors']}")
        profile = generated.name
        if profile in PROFILES and PROFILES[profile] != (tradition, tune_type):
            raise ValueError(f"Profil {profile} incompatible avec {tradition}/{tune_type}")
        report.update(generated=engine, engine_profile=profile, deviations=deviations(real, engine))
    destination = output / f"{tradition}-{tune_type}"
    destination.mkdir(parents=True, exist_ok=True)
    references.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (destination / "stats.json").write_text(encoded, encoding="utf-8")
    (destination / "report.md").write_text(render_report(report), encoding="utf-8")
    (references / f"{tradition}-{tune_type}.json").write_text(encoded, encoding="utf-8")
    write_synthesis(output)
    return destination
