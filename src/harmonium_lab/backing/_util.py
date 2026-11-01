"""Outils communs des mesures d'accompagnement : SHA256, JSON déterministe, centiles, parts.

Les JSON versionnés sont déterministes : clés triées, arrondis fixes (`ROUND`), aucun
horodatage. Les comptes bruts (`n`) accompagnent toujours les parts.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROUND = 4  # décimales des parts et des distances
PCT_ROUND = 2  # décimales des centiles


def sha256_file(path: Path) -> str:
    """SHA256 hexadécimal d'un fichier (lu par blocs)."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def dump_json(obj: Any) -> str:
    """JSON canonique : clés triées, indentation fixe, fin de ligne, caractères non ASCII conservés."""
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_json(path: Path, obj: Any) -> None:
    """Écrit `obj` en JSON canonique (crée le dossier parent)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_json(obj), encoding="utf-8")


def share(part: int | float, total: int | float) -> float:
    """Part `part / total` arrondie (0.0 si `total` est nul)."""
    return round(part / total, ROUND) if total else 0.0


def percentile(values: Sequence[float], q: float) -> float:
    """Centile `q` (0..100) par interpolation linéaire entre rangs (comme numpy, sans numpy)."""
    if not values:
        raise ValueError("centile d'une série vide")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q / 100.0
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def percentiles(values: Sequence[float], qs: Iterable[int]) -> dict[str, float | None]:
    """Centiles `{"p50": …}` arrondis ; `None` partout si la série est vide."""
    if not values:
        return {f"p{q}": None for q in qs}
    return {f"p{q}": round(percentile(values, q), PCT_ROUND) for q in qs}


def counts_and_shares(counter: Mapping[str, int], keys: Sequence[str]) -> dict[str, Any]:
    """`{"n", "counts", "shares"}` sur un jeu de clés fixe (les clés absentes valent 0)."""
    total = sum(counter.get(k, 0) for k in keys)
    return {
        "n": total,
        "counts": {k: int(counter.get(k, 0)) for k in keys},
        "shares": {k: share(counter.get(k, 0), total) for k in keys},
    }
