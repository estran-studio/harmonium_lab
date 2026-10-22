"""Brouillon de profil de style à partir du corpus ABC trad.

Les fichiers sont volontairement simples et restent indépendants du format final
que définira le moteur.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .form import analyze_form
from .mine import mine_cells, mine_harmony, mine_tempo


def build_profile_draft(corpus_root: Path | str, tune_type: str) -> dict[str, Any]:
    """Construit les données du profil et ses sources de données."""
    root = Path(corpus_root)
    tune_files = sorted((root / "tunes" / tune_type).glob("*.abc"))
    if not tune_files:
        raise FileNotFoundError(f"Aucun ABC pour le type {tune_type}: {root / 'tunes' / tune_type}")

    forms: list[dict[str, Any]] = []
    for path in tune_files:
        plan = analyze_form(path.read_text(encoding="utf-8", errors="replace"))
        forms.append({
            "id": path.stem,
            "scheme": plan.scheme,
            "parts": plan.parts,
            "pickup_eighths": float(plan.pickup),
            "meter": plan.meter,
            "eighths_per_bar": plan.eighths_per_bar,
        })
    schemes = Counter(row["scheme"] for row in forms)
    parts = Counter(tuple(row["parts"]) for row in forms)
    meters = Counter(row["meter"] for row in forms)
    pickups = Counter(str(row["pickup_eighths"]) for row in forms)
    cells, cell_stats = mine_cells(root, tune_type, top_per_role=30)
    harmony = mine_harmony(root, tune_type)
    tempo = mine_tempo(root, tune_type)["types"][tune_type]
    return {
        "type": tune_type,
        "source": str(root / "tunes" / tune_type),
        "tunes": len(tune_files),
        "cells": cells,
        "cell_stats": cell_stats,
        "harmony": harmony,
        "tempo": tempo,
        "meter": dict(sorted(meters.items())),
        "form": {
            "schemes": dict(sorted(schemes.items())),
            "part_lengths_measures": {"/".join(map(str, key)): n for key, n in sorted(parts.items())},
            "pickups_eighths": dict(sorted(pickups.items(), key=lambda item: float(item[0]))),
            "tunes": forms,
        },
    }


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_profile_draft(profile: dict[str, Any], output: Path | str) -> Path:
    """Écrit un profil TOML ainsi que les statistiques détaillées en JSON."""
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    harmony = profile["harmony"]
    tempo = profile["tempo"]
    accompaniment = harmony["accompagnement"]
    meter = max(profile["meter"], key=lambda item: (profile["meter"][item], item)) if profile["meter"] else ""
    eighths_per_bar = 6 if meter in {"3/4", "6/8"} else 0
    steps_per_pulse = 2 if meter == "3/4" else 3 if meter == "6/8" else 0
    q = tempo["tempo_q"]
    lines = [
        f"# Brouillon P2-T2 — {profile['type']}; voir README.md.",
        "[meta]",
        f"name = {_toml_string(profile['type'])}",
        f"tradition = {_toml_string('trad québécois')}",
        f"corpus = {_toml_string(profile['source'])}",
        f"tunes = {profile['tunes']}",
        "",
        "[meter]",
        f"signature = {_toml_string(meter)}",
        f"signature_counts = {_toml_string(json.dumps(profile['meter'], ensure_ascii=False))}",
        f"steps_per_bar = {eighths_per_bar}",
        f"steps_per_cell = {eighths_per_bar}",
        f"steps_per_pulse = {steps_per_pulse}",
        f"pulses_per_bar = {eighths_per_bar // steps_per_pulse if steps_per_pulse else 0}",
        f"default_tempo = {q['mediane'] if q else 0}",
        f"min_tempo = {q['min'] if q else 0}",
        f"max_tempo = {q['max'] if q else 0}",
        f"tempo_missing = {str(q is None).lower()}",
        "",
        "[form]",
        f"schemes = {_toml_string(json.dumps(profile['form']['schemes'], ensure_ascii=False))}",
        f"part_lengths_measures = {_toml_string(json.dumps(profile['form']['part_lengths_measures'], ensure_ascii=False))}",
        f"pickups_eighths = {_toml_string(json.dumps(profile['form']['pickups_eighths'], ensure_ascii=False))}",
        "positional_roles = \"1:open, 4:cad_half, 8:cad_full; other positions: interval role\"",
        "",
        "[melody]",
        f"cell_length = {eighths_per_bar}",
        "cell_unit = \"eighth_note\"",
        "",
    ]
    for cell in profile["cells"]:
        lines.append("[[melody.cells]]")
        lines.extend([
            f"role = {_toml_string(cell['role'])}",
            f"notes = {_toml_string(cell['notes'])}",
            f"weight = {cell['count']}",
            "",
        ])
    lines.extend([
        "[harmony]",
        'model = "trad_functional"',
        f"rhythm_dominant_chords_per_bar = {harmony['rythme_harmonique_dominant'] or 0}",
        f"rhythm_per_bar = {_toml_string(json.dumps(harmony['rythme_harmonique_par_mesure']))}",
        f"rhythm_per_half_bar = {_toml_string(json.dumps(harmony['rythme_harmonique_par_demi_mesure'], ensure_ascii=False))}",
        f"degrees_by_position = {_toml_string(json.dumps(harmony['par_position'], ensure_ascii=False))}",
        f"bigrams = {_toml_string(json.dumps(harmony['bigrammes'], ensure_ascii=False))}",
        "",
        "[accompaniment]",
        f"source = {_toml_string(accompaniment['source'])}",
        f"waltz_bass_beats = {json.dumps(accompaniment['mesure_3_4']['basse'])}",
        f"waltz_chord_beats = {json.dumps(accompaniment['mesure_3_4']['accord'])}",
        f"jig_bass_eighths = {json.dumps(accompaniment['mesure_6_8']['basse_croche'])}",
        f"jig_chord_eighths = {json.dumps(accompaniment['mesure_6_8']['accord_croche'])}",
        "",
        "[percussion]",
        'source = "convention métrique; pas mesuré dans les ABC"',
        "waltz_accent_beats = [1, 2, 3]",
        "jig_accent_eighths = [1, 4]",
        "",
    ])
    (out / "profile.toml").write_text("\n".join(lines), encoding="utf-8")
    for filename, key in (("harmony.json", "harmony"), ("tempo.json", "tempo"),
                          ("form.json", "form"), ("cell-stats.json", "cell_stats")):
        (out / filename).write_text(
            json.dumps(profile[key], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    (out / "README.md").write_text(
        "# Profil de style — brouillon\n\n"
        f"Type : `{profile['type']}`. Source ABC : `{profile['source']}` "
        f"({profile['tunes']} airs analysés). Ce n’est pas le format final du moteur.\n\n"
        "## Sources des valeurs\n\n"
        "- `profile.toml` — métrique et forme calculées sur les en-têtes/corps ABC; "
        "cellules quantifiées par mesure, validées avec les invariants Python du moteur "
        "(degrés, ambitus, sauts; longueur lue dans la métrique); `weight` = fréquence observée.\n"
        "- `harmony.json` — symboles d’accords ABC convertis en degrés relatifs à la tonique; "
        "rythme harmonique observé par mesure et positions dans les parties. Les motifs "
        "d’accompagnement sont des conventions métriques (pas mesurés dans l’ABC).\n"
        "- `tempo.json` — `Q:` et `M:` tels que fournis par les fichiers ABC; `tempo_q: null` "
        "signale les tempos manquants.\n"
        "- `form.json` — schémas, longueurs de parties et levées calculés par l’analyseur ABC.\n"
        "- `cell-stats.json` — rejets de validation et statistiques d’extraction.\n",
        encoding="utf-8",
    )
    return out
