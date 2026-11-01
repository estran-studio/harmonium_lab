"""Valeurs de profil moteur dérivées des mesures agrégées (phase 018, E7).

Un seul chemin des mesures (`references/wjazzd-swing/measures-*.json`) aux paramètres d'un
profil distribué : la batterie (`percussion.toml`), les poids de la marche de basse, le tempo,
le rapport de swing et le micro-timing. Le profil du moteur n'est pas écrit à la main : ses
valeurs viennent d'ici, et le README du dossier de références les tabule.

    python -m harmonium_lab.backing.engine_values --percussion out/percussion.toml
    python -m harmonium_lab.backing.engine_values --table     # paramètres → mesure source

Règles de construction (mesures → profil) :

- **Batterie** : les patterns proposés par `drums.py` (probabilités par pas agrégées, jamais une
  mesure d'enregistrement) deviennent des `[[patterns]]` de densité 0, 1, 2 pondérés par leur
  effectif ; la vélocité de chaque rôle est portée par une voix (`[[voices]]`, médiane des
  vélocités du rôle), l'écart de chaque coup par `delta_velocity` (forme des accents du groupe de
  mesures, niveau ramené à celui de la voix). Le pattern de relance (mesures
  `fill`) n'est PAS un pattern ordinaire : le moteur tire un pattern par partie et par densité,
  un fill y jouerait toute la partie ; il devient le `[[cadence_patterns]]` de densité 2.
- **Basse** : poids d'approche = parts `none` / `chromatic` / `diatonic` du groupe `all`
  (avant un changement d'accord, toutes positions) ; poids de passage = parts `chord_tone` et
  `scale_step` (les passages chromatiques, non représentables, rejoignent `scale_step`).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .corpus_cache import REFERENCES

#: Voix de batterie du moteur : rôle de la mesure → (nom, piste du moteur).
VOICES: dict[str, tuple[str, str]] = {
    "ride": ("ride", "PercussionHigh"),
    "hat_pedal": ("pedal", "PercussionHigh"),
    "hat_closed": ("hat", "PercussionHigh"),
    "snare": ("snare", "PercussionHigh"),
    "tom": ("tom", "PercussionHigh"),
    "crash": ("crash", "PercussionHigh"),
    "kick": ("kick", "PercussionLow"),
}


#: Calage de niveau du kit de rendu (jazz de GeneralUser GS, banque 128 programme 32) : les
#: vélocités du GMD sont celles d'un kit électronique Roland ; une même vélocité donne, sur ce kit,
#: un ride plus discret que la grosse caisse, la caisse claire et les toms (mesuré hors ligne : à
#: gain 1 la densité 2 écrête, le kit joue 3 dB plus fort qu'à la densité 1). Un gain par rôle
#: ramène les rôles qui dominent au niveau du ride ; ils ne changent pas la forme des accents.
ROLE_GAIN: dict[str, float] = {"kick": 0.5, "snare": 0.6, "tom": 0.6, "hat_pedal": 0.9}


def load(name: str) -> dict[str, Any]:
    """Lit un JSON de `references/wjazzd-swing/`."""
    return json.loads((REFERENCES / name).read_text(encoding="utf-8"))


def _median(values: list[int]) -> int:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid] + 1) // 2


def voices_from(patterns: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Voix du profil : par rôle utilisé, la note GM la plus fréquente et la vélocité médiane."""
    notes: dict[str, dict[int, int]] = {}
    velocities: dict[str, list[int]] = {}
    for pattern in patterns:
        for hit in pattern["hits"]:
            role = hit["role"]
            notes.setdefault(role, {})
            notes[role][hit["note"]] = notes[role].get(hit["note"], 0) + int(pattern["weight"])
            velocities.setdefault(role, []).append(round(hit["velocity"] / hit["rel_velocity"]))
    return {
        role: {
            "note": max(sorted(counts), key=lambda n: counts[n]),
            "velocity": max(1, min(127, round(_median(velocities[role]) * ROLE_GAIN.get(role, 1.0)))),
        }
        for role, counts in notes.items()
    }


def _pattern_scale(pattern: dict[str, Any]) -> float:
    """Niveau de jeu du groupe de mesures : part moyenne de la vélocité médiane du ride.

    Les groupes viennent de fichiers différents, plus ou moins fort ; seule la FORME des accents
    (temps 2 et 4 contre croches) se garde, le niveau est ramené à celui de la voix.
    """
    rides = [h["rel_velocity"] for h in pattern["hits"] if h["role"] == "ride"]
    return sum(rides) / len(rides) if rides else 1.0


def _hit_line(hit: dict[str, Any], voices: dict[str, dict[str, int]], scale: float) -> str:
    name, _track = VOICES[hit["role"]]
    voice = voices[hit["role"]]
    level = round(voice["velocity"] * hit["rel_velocity"] / scale)
    delta = max(-127, min(127, level - voice["velocity"]))
    parts = [f"step = {hit['step']}", f'voice = "{name}"']
    if hit["note"] != voice["note"]:
        parts.append(f"note = {hit['note']}")
    if delta:
        parts.append(f"delta_velocity = {delta}")
    return "  { " + ", ".join(parts) + " },"


def percussion_toml(drums: dict[str, Any], header: str = "") -> str:
    """Le `percussion.toml` du profil, déterministe, depuis `measures-drums.json`."""
    proposed = drums["proposed_patterns"]["patterns"]
    ordinary = [p for p in proposed if not _is_fill(p)]
    fills = [p for p in proposed if _is_fill(p)]
    voices = voices_from(ordinary + fills)
    lines = [header.rstrip("\n")] if header else []
    lines.append("low_note = 36")
    lines.append("high_note = 51")
    lines.append("low_velocity = 64")
    lines.append("high_velocity = 64")
    lines.append("percussion_gain = 1.0")
    lines.append("velocity_humanize = 3")
    lines.append("")
    for role in sorted(voices, key=lambda r: (VOICES[r][1] != "PercussionLow", VOICES[r][0])):
        name, track = VOICES[role]
        voice = voices[role]
        lines += [
            "[[voices]]",
            f'name = "{name}"',
            f"note = {voice['note']}",
            f"velocity = {voice['velocity']}",
            f'track = "{track}"',
            "",
        ]
    for pattern in ordinary:
        lines += _pattern_block("patterns", pattern, voices, weight=True)
    for density in (2,):
        for pattern in fills:
            if pattern["density"] == density:
                lines += _pattern_block("cadence_patterns", pattern, voices, weight=False)
    return "\n".join(lines).rstrip("\n") + "\n"


def _is_fill(pattern: dict[str, Any]) -> bool:
    """Un pattern de relance : sans ride ni pédale (mesures `fill`, jamais un groove)."""
    return not any(h["role"] in ("ride", "hat_pedal", "hat_closed") for h in pattern["hits"])


def _pattern_block(
    table: str, pattern: dict[str, Any], voices: dict[str, dict[str, int]], *, weight: bool
) -> list[str]:
    lines = [f"[[{table}]]", f"density = {pattern['density']}"]
    if weight:
        lines.append(f"weight = {pattern['weight']}")
    lines.append("hits = [")
    for hit in sorted(pattern["hits"], key=lambda h: (h["step"], VOICES[h["role"]][1] != "PercussionLow", h["role"])):
        lines.append(_hit_line(hit, voices, _pattern_scale(pattern)))
    lines += ["]", ""]
    return lines


def bass_weights(bass: dict[str, Any], group: str = "all") -> dict[str, dict[str, int]]:
    """Poids entiers (somme 100) de l'approche et du passage depuis `measures-bass.json`.

    Approche : parts `none` / `chromatic` / `diatonic` de la pulsation qui précède une arrivée.
    Passage : parts `chord_tone` et `scale_step` des notes que le moteur tire (`passage_engine` :
    les temps ni arrivée ni approche) ; les passages chromatiques, que le moteur ne sait pas
    jouer, rejoignent `scale_step`.
    """
    data = bass["groups"][group]
    shares = data["approach"]["all"]["weights"]["shares"]
    a = [round(100 * shares[k]) for k in ("none", "chromatic", "diatonic")]
    a[0] += 100 - sum(a)
    passage = data["passage_engine"]["shares"]
    chord = passage["chord_tone"]
    c = round(100 * chord)
    return {
        "approach": {"none_weight": a[0], "chromatic_weight": a[1], "diatonic_weight": a[2]},
        "passing": {"chord_tone_weight": c, "scale_step_weight": 100 - c},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--percussion", type=Path, help="écrit le percussion.toml du profil")
    parser.add_argument("--header", type=Path, help="fichier de commentaires placé en tête")
    parser.add_argument("--table", action="store_true", help="affiche les poids de basse")
    args = parser.parse_args(argv)
    if args.percussion:
        header = args.header.read_text(encoding="utf-8") if args.header else ""
        args.percussion.write_text(percussion_toml(load("measures-drums.json"), header), encoding="utf-8")
    if args.table:
        print(json.dumps(bass_weights(load("measures-bass.json")), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
