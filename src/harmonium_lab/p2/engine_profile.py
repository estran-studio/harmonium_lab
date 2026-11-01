"""Lecture du profil moteur nécessaire à l'extraction : grille, tonique, parties, alternatives écrites.

Ne lit que `profile.toml` et ses fichiers annexes (`[files]`) : le schéma est celui du moteur
(`profiles/README.md`, E1 pour les accords de boucle). Aucune écriture : les copies enrichies
passent par `p2.enrich`.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MODE_INTERVALS = {
    "ionian": (0, 2, 4, 5, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "aeolian": (0, 2, 3, 5, 7, 8, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
}

BarChord = tuple[int, str | None]  # (fondamentale en demi-tons depuis la tonique, "" | "m" ; None = qualité libre, pédale)


def quality_class(quality: str) -> str:
    """Qualité comparable aux transcriptions (triades) : `m` si mineure, sinon majeure."""
    if quality.startswith("m") and not quality.startswith("maj"):
        return "m"
    return ""


@dataclass
class Part:
    name: str
    bars: int
    kind: str                                  # "pedal" | "chord_loop"
    degree: int = 1
    loops: list[dict[str, Any]] = field(default_factory=list)   # [{weight, chords}]


@dataclass
class EngineProfile:
    dir: Path
    id: str
    steps_per_bar: int
    steps_per_pulse: int
    steps_per_chord: int
    tonic_pc: int
    mode: str
    parts: dict[str, Part]
    bass_low: int
    bass_high: int
    motifs: list[dict[str, Any]]
    patterns: list[dict[str, Any]]
    percussion: dict[str, Any]

    def chord_root(self, chord: dict[str, Any]) -> int:
        """Fondamentale d'un accord de boucle en demi-tons depuis la tonique."""
        if "semitones" in chord:
            return int(chord["semitones"]) % 12
        scale = MODE_INTERVALS[self.mode]
        return scale[(int(chord["degree"]) - 1) % 7]

    def loop_per_bar(self, loop: dict[str, Any]) -> list[BarChord]:
        """Suite par mesure (fondamentale, qualité) d'une alternative d'accords."""
        slots: list[BarChord] = []
        for chord in loop["chords"]:
            n = int(chord.get("steps", self.steps_per_chord)) // self.steps_per_chord
            slots.extend([(self.chord_root(chord), quality_class(chord["quality"]))] * n)
        per_bar = self.steps_per_bar // self.steps_per_chord
        return [slots[i] for i in range(0, len(slots), per_bar)]

    def part_alternatives(self, part: str) -> list[list[BarChord]]:
        """Références d'une partie, par mesure : ses boucles, ou la pédale de tonique."""
        p = self.parts[part]
        if p.kind == "pedal":
            return [[(self.chord_root({"degree": p.degree}), None)] * p.bars]
        return [self.loop_per_bar(lp) for lp in p.loops]

    def place_reference(self, pc: int) -> int:
        """Hauteur MIDI de la classe `pc` dans `low..high` (fenêtre ≥ 12 : unique)."""
        for p in range(self.bass_low, self.bass_low + 12):
            if p % 12 == pc % 12:
                return p
        raise ValueError("fenêtre de basse invalide")  # inatteignable : 12 hauteurs consécutives


def load_profile(directory: Path) -> EngineProfile:
    directory = Path(directory)
    data = tomllib.loads((directory / "profile.toml").read_text(encoding="utf-8"))
    for section, name in data.get("files", {}).items():
        extra = tomllib.loads((directory / name).read_text(encoding="utf-8"))
        if section == "percussion":
            data["percussion"] = extra
    meter = data["meter"]
    tonality = data.get("fixed_tonality") or data["melody"]["key_modes"][0]
    harmony = data["harmony"]
    parts: dict[str, Part] = {}
    for fp in data["form"]["parts"]:
        hp = harmony["parts"].get(fp["name"], {})
        parts[fp["name"]] = Part(
            name=fp["name"], bars=len(fp["roles"]), kind=hp.get("kind", "pedal"),
            degree=int(hp.get("degree", 1)), loops=hp.get("loops", []))
    bass = data["accompaniment"]["bass"]
    perc = data.get("percussion", {})
    return EngineProfile(
        dir=directory, id=data["meta"]["id"],
        steps_per_bar=int(meter["steps_per_bar"]), steps_per_pulse=int(meter["steps_per_pulse"]),
        steps_per_chord=int(harmony["steps_per_chord"]),
        tonic_pc=int(tonality["key"]), mode=tonality["mode"], parts=parts,
        bass_low=int(bass["low"]), bass_high=int(bass["high"]),
        motifs=list(bass.get("motifs", [])), patterns=list(perc.get("patterns", [])),
        percussion={k: v for k, v in perc.items() if k not in ("patterns", "cadence_patterns")},
    )
