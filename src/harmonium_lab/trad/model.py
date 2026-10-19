"""Représentation commune des airs trad (D5).

Un air est une mélodie découpée en mesures, reprises jouées (AABB développé),
avec les accords échantillonnés par mesure. Deux chargeurs produisent cette
représentation : depuis l'ABC du corpus (voix principale, ``expandRepeats``)
et depuis un MIDI du moteur (canal 0 = mélodie, canaux 1/2 = accords/basse).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Note:
    """Une note de la mélodie, positionnée dans sa mesure."""

    pitch: int  # MIDI 0-127
    onset: float  # en croches depuis le début de la mesure
    duration: float  # en croches


@dataclass(slots=True)
class TradTune:
    """Un air trad sous forme analysable (reprises développées)."""

    tune_id: str
    key_tonic_pc: int  # classe de hauteur de la tonique (0-11, C=0)
    key_name: str  # ex. "D"
    mode: str  # ex. "ionian", "mixolydian", "dorian", "aeolian"
    meter: str  # ex. "2/2", "6/8", "3/4"
    eighths_per_bar: int  # croches par mesure (reel 8, gigue 6, valse 6)
    bars: list[list[Note]] = field(default_factory=list)  # mélodie
    # accords par mesure : liste de (position en croches, symbole ex. "D", "Am")
    chords: list[list[tuple[float, str]]] = field(default_factory=list)
    source: str = ""  # "abc" ou "engine-midi"
    # Forme analysée (scheme, parts, is_aabb, pickup, cause, source) ; vide
    # pour le MIDI moteur (calculée dans features() depuis les mesures).
    form: dict = field(default_factory=dict)


# Intervalles (demi-tons) des degrés 1..7 pour chaque mode.
MODE_INTERVALS: dict[str, list[int]] = {
    "ionian": [0, 2, 4, 5, 7, 9, 11],
    "major": [0, 2, 4, 5, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
}

# Normalisation des noms de modes (music21, ABC) vers le vocabulaire moteur.
MODE_ALIASES: dict[str, str] = {
    "major": "ionian",
    "minor": "aeolian",
    "ionian": "ionian",
    "mixolydian": "mixolydian",
    "dorian": "dorian",
    "aeolian": "aeolian",
    "phrygian": "phrygian",
    "lydian": "lydian",
    "locrian": "locrian",
    "majeur": "ionian",
    "mineur": "aeolian",
    "dorien": "dorian",
    "mixolydien": "mixolydian",
    "lydien": "lydian",
    "phrygien": "phrygian",
    "locrien": "locrian",
}


# Noms de notes (dièses) pour la sortie déterministe des degrés d'accords.
PC_NAMES: list[str] = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Degrés candidats par mode pour l'harmonisation (cf. harmonium trad/harmony.rs).
CANDIDATE_CHORDS: dict[str, list[str]] = {
    "ionian": ["I", "IV", "V", "vi"],
    "mixolydian": ["I", "IV", "bVII", "v"],
    "dorian": ["i", "v", "IV", "bVII"],
    "aeolian": ["i", "iv", "v", "bVII", "bVI"],
}


def normalize_mode(name: str) -> str:
    """Normalise un nom de mode ; inconnu -> "ionian" (documenté)."""
    return MODE_ALIASES.get(name.strip().lower(), "ionian")


def mode_intervals(mode: str) -> list[int]:
    """Intervalles du mode ; inconnu -> ionien (documenté)."""
    return MODE_INTERVALS.get(normalize_mode(mode), MODE_INTERVALS["ionian"])


def eighths_per_bar(numerator: int, denominator: int) -> int:
    """Nombre de croches par mesure : reel 2/2 -> 8, gigue 6/8 -> 6, valse 3/4 -> 6."""
    return numerator * 8 // denominator
