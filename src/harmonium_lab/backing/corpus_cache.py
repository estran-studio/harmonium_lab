"""Outils communs des sources d'accompagnement (GMD, JTD) : cache vérifié et écritures déterministes.

Principe VII : les bruts restent en cache local gitignoré (`corpus/<source>/raw/`) ; seuls
`manifest.jsonl`, `VERSION` et les dérivés agrégés sont versionnés. Aucun brut n'est lu sans que
son SHA256 ait été vérifié (`open_verified`) ; un fichier absent est téléchargé (`fetch`) puis
vérifié, un fichier à l'empreinte différente est refusé (jamais lu, jamais réparé en silence).

Les écritures sont déterministes : clés triées, listes dans l'ordre fourni, flottants arrondis
(`ROUND`), aucun horodatage dans les JSON. La date de récupération n'est écrite que dans
`VERSION` et y est conservée d'une exécution à l'autre.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from ..trad.download import Fetcher

ROUND = 4
"""Décimales conservées dans les JSON versionnés."""

PERCENTILES = (10, 25, 50, 75, 90)

ROOT = Path(__file__).resolve().parents[3]
"""Racine du labo (`src/harmonium_lab/backing/` → 3 niveaux)."""

REFERENCES = ROOT / "references" / "wjazzd-swing"


class DigestError(ValueError):
    """Empreinte SHA256 d'un brut différente de l'empreinte attendue."""


def sha256_file(path: Path) -> str:
    """SHA256 hexadécimal d'un fichier, lu par blocs."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def open_verified(path: Path, expected_sha256: str) -> Path:
    """Renvoie `path` si son SHA256 est `expected_sha256` ; sinon lève `DigestError`.

    Appelée avant TOUTE lecture d'un brut : un fichier non vérifié n'est jamais lu.
    """
    if not path.is_file():
        raise FileNotFoundError(f"brut absent : {path} (relancer avec --fetch)")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise DigestError(
            f"SHA256 différent pour {path} : attendu {expected_sha256}, obtenu {actual}. "
            "Fichier refusé (ne pas le lire) ; le supprimer puis relancer avec --fetch."
        )
    return path


def fetch(url: str, dest: Path, expected_sha256: str, *, fetcher: Fetcher | None = None) -> Path:
    """Télécharge `url` vers `dest` s'il est absent, puis vérifie le SHA256.

    Un téléchargement à l'empreinte erronée est supprimé et signalé par `DigestError`.
    """
    fetcher = fetcher or Fetcher()
    fresh = not dest.exists()
    fetcher.get(url, dest)
    try:
        return open_verified(dest, expected_sha256)
    except DigestError:
        if fresh:
            dest.unlink(missing_ok=True)
        raise


def round_floats(value: Any, digits: int = ROUND) -> Any:
    """Arrondit récursivement les flottants (et convertit les types numpy en types JSON)."""
    if isinstance(value, dict):
        return {str(k): round_floats(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [round_floats(v, digits) for v in value]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if number != number:
            return None
        return round(number, digits)
    if isinstance(value, np.integer):
        return int(value)
    return value


def dumps_json(data: Any) -> str:
    """JSON déterministe : clés triées, indentation 2, flottants arrondis, fin de ligne finale."""
    return json.dumps(round_floats(data), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_json(path: Path, data: Any) -> str:
    """Écrit `data` en JSON déterministe ; renvoie le texte écrit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = dumps_json(data)
    path.write_text(text, encoding="utf-8")
    return text


def write_jsonl(path: Path, rows: Iterable[dict]) -> str:
    """Écrit un JSON par ligne (clés triées) ; renvoie le texte écrit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(round_floats(row), sort_keys=True, ensure_ascii=False) for row in rows]
    text = "".join(line + "\n" for line in lines)
    path.write_text(text, encoding="utf-8")
    return text


def write_version(path: Path, fields: dict[str, str], manifest_text: str) -> None:
    """Écrit `VERSION` : une ligne `clé: valeur` par champ, plus l'empreinte du manifeste.

    La date de récupération (`retrieved`) est celle du premier appel : elle est relue dans le
    `VERSION` existant tant que l'empreinte de la source est la même, pour que deux exécutions
    produisent un fichier identique.
    """
    retrieved = datetime.date.today().isoformat()
    if path.is_file():
        old = parse_version(path)
        if old.get("sha256") == fields.get("sha256") and "retrieved" in old:
            retrieved = old["retrieved"]
    lines = {**fields, "retrieved": retrieved, "manifest_sha256": sha256_bytes(manifest_text.encode())}
    path.write_text("".join(f"{key}: {value}\n" for key, value in lines.items()), encoding="utf-8")


def parse_version(path: Path) -> dict[str, str]:
    """Relit un `VERSION` (lignes `clé: valeur`)."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            out[key] = value
    return out


def percentiles(values: Sequence[float], qs: Sequence[int] = PERCENTILES) -> dict[str, float | None]:
    """Centiles (interpolation linéaire) sous la forme `{"p10": …}` ; `None` si aucune valeur."""
    if len(values) == 0:
        return {f"p{q}": None for q in qs}
    data = np.asarray(values, dtype=float)
    return {f"p{q}": float(np.percentile(data, q)) for q in qs}


def describe(values: Sequence[float], qs: Sequence[int] = PERCENTILES) -> dict[str, Any]:
    """Effectif, moyenne et centiles d'une série."""
    if len(values) == 0:
        return {"n": 0, "mean": None, **percentiles(values, qs)}
    return {"n": len(values), "mean": float(np.mean(values)), **percentiles(values, qs)}
