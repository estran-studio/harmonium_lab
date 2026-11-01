"""Écriture TOML (sous-ensemble du schéma moteur) : accords de boucle, motifs de basse, patterns.

Sans dépendance d'écriture : les valeurs sont des entiers, flottants, booléens ou textes simples.
Les clés suivent l'ordre du dictionnaire (l'ordre des exemples de `profiles/README.md`).
"""

from __future__ import annotations

from typing import Any


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(scalar(v) for v in value) + "]"
    raise TypeError(f"valeur TOML non gérée : {value!r}")


def inline(table: dict[str, Any]) -> str:
    return "{ " + ", ".join(f"{k} = {scalar(v)}" for k, v in table.items()) + " }"


def loop_lines(loop: dict[str, Any], indent: str = "  ") -> list[str]:
    """`{ weight = 1, chords = [ {..}, .. ] }` sur plusieurs lignes (un accord par ligne)."""
    lines = [f"{indent}{{ weight = {loop['weight']}, chords = ["]
    lines += [f"{indent}  {inline(c)}," for c in loop["chords"]]
    lines.append(f"{indent}] }},")
    return lines


def part_block(name: str, loops: list[dict[str, Any]], kind: str | None = "chord_loop") -> str:
    """Section `[harmony.parts.<name>]` portant `loops` (et `kind` si fourni)."""
    lines = [f"[harmony.parts.{name}]"]
    if kind:
        lines.append(f"kind = {scalar(kind)}")
    lines.append("loops = [")
    for loop in loops:
        lines += loop_lines(loop)
    lines.append("]")
    return "\n".join(lines) + "\n"


def motif_block(motif: dict[str, Any], table: str = "accompaniment.bass.motifs") -> str:
    head = {k: motif[k] for k in ("part", "bars", "weight", "reference") if k in motif}
    lines = [f"[[{table}]]"] + [f"{k} = {scalar(v)}" for k, v in head.items()]
    lines.append("notes = [")
    lines += [f"  {inline(n)}," for n in motif["notes"]]
    lines.append("]")
    return "\n".join(lines) + "\n"


def pattern_block(pattern: dict[str, Any], table: str = "percussion.patterns") -> str:
    lines = [f"[[{table}]]", f"density = {pattern['density']}", f"weight = {pattern['weight']}", "hits = ["]
    lines += [f"  {inline(h)}," for h in pattern["hits"]]
    lines.append("]")
    return "\n".join(lines) + "\n"
