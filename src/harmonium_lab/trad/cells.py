"""Vocabulaire de cellules : une mesure en notation du moteur (D5).

Notation (identique à ``harmonium_core::trad::cells``) :
- ``1..7`` : degrés de l'octave principale (``1`` = tonique) ;
- ``8..`` : octave supérieure (``8`` = tonique + 1 octave) ;
- ``k,`` : octave inférieure (``5,`` = quinte grave) ;
- ``-`` : prolongation de la note précédente (tient aussi lieu de silence :
  les pauses et les tenues partagent ``-``, voir ``bar_to_cell``).

Quantisation (déterministe) :
- l'attaque est arrondie à la croche la plus proche ;
- une note non diatonique (chromatisme) est ramenée au degré le plus proche
  en demi-tons, égalité -> le plus grave (documenté, le moteur n'admet aucun
  chromatisme dans sa banque) ;
- une case sans attaque ni tenue (pause) émet ``-`` ;
- mesure en trop (« croche », plus de croches que ``eighths_per_bar``) : les
  jetons surnuméraires sont conservés tels quels (cellule plus longue),
  c'est ``features()`` qui marque la mesure, jamais une erreur ;
- mesure trop courte : complétée par ``-`` (tenue implicite) ;
- liaison à cheval sur une barre de mesure : la mesure suivante commence par
  ``-`` (exception documentée à l'invariant moteur « jamais `-` en premier »).
"""

from __future__ import annotations

from .model import Note, mode_intervals


def pitch_to_degree(midi: int, tonic_pc: int, mode: str) -> int:
    """Degré moteur d'une hauteur MIDI (``1`` = tonique, ``8`` = octave, ``-3`` = ``5,``).

    Convention identique à ``harmonium_core::trad::mode`` :
    pas diatoniques ``0..`` -> degrés ``1..``, pas ``< 0`` -> degrés ``-1..``.
    La tonique est ancrée en octave 4 (ex. D4 = 62) : les degrés ``1..7``
    couvrent l'octave de la tonique, ``8..`` l'aigu, ``k,`` le grave.
    """
    intervals = mode_intervals(mode)
    anchor = tonic_pc + 60
    best_step = 0
    best_dist = abs(midi - (anchor + intervals[0]))
    for octave in range(-3, 9):
        for i, semis in enumerate(intervals):
            pitch = anchor + 12 * octave + semis
            dist = abs(midi - pitch)
            # "<" strict : à égalité on garde le degré le plus grave.
            if dist < best_dist:
                best_dist = dist
                best_step = 7 * octave + i
    return best_step + 1 if best_step >= 0 else best_step


def degree_to_notation(degree: int) -> str:
    """Formate un degré en notation moteur (``-3`` -> ``"5,"``, ``8`` -> ``"8"``)."""
    if degree < 0:
        return f"{degree + 8},"
    return str(degree)


def bar_to_cell(
    notes: list[Note],
    tonic_pc: int,
    mode: str,
    eighths_per_bar: int,
) -> str:
    """Rend une mesure en cellule moteur (``"1 3 5 3 1 3 5 3"`` en reel)."""
    notes = sorted(notes, key=lambda n: (n.onset, n.pitch))
    attacks: dict[int, int] = {}
    for n in notes:
        slot = int(round(n.onset))
        if slot < 0:
            continue
        if slot not in attacks:
            attacks[slot] = pitch_to_degree(n.pitch, tonic_pc, mode)

    tokens: list[str] = []
    last_slot = max([eighths_per_bar] + [s + 1 for s in attacks])
    for slot in range(last_slot):
        if slot in attacks:
            tokens.append(degree_to_notation(attacks[slot]))
        else:
            # Tenue ("-") ou pause (même jeton, voir doc du module).
            tokens.append("-")
    return " ".join(tokens)
