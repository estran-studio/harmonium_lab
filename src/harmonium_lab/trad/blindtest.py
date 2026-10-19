"""Kit d'écoute en aveugle (specs/001-trad-dataset D6, ``blindtest``).

Mélange des WAV réels (rendus ``trad-render``, mêmes instruments) et
des WAV du moteur, tous ramenés à la même durée (découpe ou silence,
fondu de 0,5 s), sous des noms aléatoires ``01.wav … NN.wav``.
``feuille.md`` à remplir, ``corrige.json`` séparé, et ``score_feuille``
pour dépouiller la feuille remplie.

WAV PCM via le stdlib ``wave`` uniquement (pas de dépendance audio) ;
déterministe par seed ; écrit uniquement dans le dossier cible.
"""

from __future__ import annotations

import json
import random
import struct
import unicodedata
import wave
from pathlib import Path
from typing import Any

#: Durée par défaut : un air AABB de reel. Fondu par défaut (s).
DEFAULT_DURATION = 33.0
DEFAULT_FADE = 0.5


def _norm(verdict: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", verdict.strip().lower())
    return "".join(c for c in ascii_ if not unicodedata.combining(c))


def _decode_samples(fmt: int, bits: int, chans: int, data: bytes) -> list[float]:
    """Octets audio -> échantillons mono flottants (-1..1)."""
    frames: list[float] = []
    if fmt == 3:  # float32 (sortie du moteur)
        n = len(data) // 4
        vals = struct.unpack(f"<{n}f", data[: n * 4])
        frames = [sum(vals[i * chans:(i + 1) * chans]) / chans for i in range(n // chans)]
    elif bits == 16:
        n = len(data) // 2
        vals = struct.unpack(f"<{n}h", data[: n * 2])
        frames = [sum(vals[i * chans:(i + 1) * chans]) / (chans * 32768.0) for i in range(n // chans)]
    elif bits == 8:
        frames = [(b - 128) / 128.0 for b in data[::chans]]
    elif bits == 24:
        n = len(data) // 3
        vals = [
            int.from_bytes(data[i * 3:(i + 1) * 3], "little", signed=True) / 8388608.0
            for i in range(n)
        ]
        frames = [sum(vals[i * chans:(i + 1) * chans]) / chans for i in range(n // chans)]
    elif bits == 32:
        n = len(data) // 4
        vals = [v / 2147483648.0 for v in struct.unpack(f"<{n}i", data[: n * 4])]
        frames = [sum(vals[i * chans:(i + 1) * chans]) / chans for i in range(n // chans)]
    return frames


def read_wav_mono(path: Path) -> tuple[int, list[float]]:
    """Lit un WAV (PCM entier ou float32) -> (taux, échantillons mono flottants)."""
    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError(f"{path.name} : pas un WAV RIFF")
    pos, fmt, chans, rate, bits, data = 12, None, None, None, None, None
    while pos + 8 <= len(raw):
        tag, size = raw[pos:pos + 4], int.from_bytes(raw[pos + 4:pos + 8], "little")
        body = raw[pos + 8:pos + 8 + size]
        if tag == b"fmt " and len(body) >= 16:
            fmt, chans, rate = struct.unpack("<HHI", body[:8])
            bits = struct.unpack("<H", body[14:16])[0]
            if fmt == 65534 and len(body) >= 40:  # WAVE_FORMAT_EXTENSIBLE
                fmt = struct.unpack("<H", body[24:26])[0]
        elif tag == b"data" and data is None:
            data = body
        pos += 8 + size + (size % 2)
    if fmt not in (1, 3) or data is None or not chans or not rate or not bits:
        raise ValueError(f"{path.name} : format WAV non supporté (fmt={fmt})")
    if (fmt, bits) not in ((1, 8), (1, 16), (1, 24), (1, 32), (3, 32)):
        raise ValueError(f"{path.name} : {bits} bits fmt={fmt} non supportés")
    return rate, _decode_samples(fmt, bits, chans, data)

def write_wav_mono(path: Path, samples: list[float], framerate: int) -> None:
    """Écrit un WAV mono PCM 16 bits."""
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(framerate)
        w.writeframes(struct.pack(f"<{len(samples)}h", *(int(max(-1.0, min(1.0, s)) * 32767) for s in samples)))


def fit_duration(samples: list[float], target: int, fade: int) -> list[float]:
    """Découpe ou bourre (silence) à ``target`` échantillons + fondus linéaires."""
    if len(samples) > target:
        out = samples[:target]
    else:
        out = samples + [0.0] * (target - len(samples))
    f = min(fade, target // 2)
    for i in range(f):
        ramp = (i + 1) / (f + 1)
        out[i] *= ramp
        out[target - 1 - i] *= ramp
    return out


def build_kit(
    real_pool: list[Path],
    gen_pool: list[Path],
    out_dir: Path,
    n_real: int,
    n_gen: int,
    seed: int,
    duration: float = DEFAULT_DURATION,
    fade: float = DEFAULT_FADE,
) -> dict[str, Any]:
    """Construit le kit : échantillonne, normalise, mélange, écrit feuille + corrigé."""
    rng = random.Random(seed)
    if len(real_pool) < n_real:
        raise ValueError(f"pas assez de WAV réels ({len(real_pool)} < {n_real})")
    if len(gen_pool) < n_gen:
        raise ValueError(f"pas assez de WAV générés ({len(gen_pool)} < {n_gen})")
    chosen = [("reel", p) for p in rng.sample(sorted(real_pool), n_real)]
    chosen += [("genere", p) for p in rng.sample(sorted(gen_pool), n_gen)]

    # Taux commun exigé : sinon « même durée » ne veut rien dire.
    rates = {read_wav_mono(p)[0] for _, p in chosen}
    if len(rates) > 1:
        raise ValueError(f"taux d'échantillonnage hétérogènes : {sorted(rates)}")
    rate = rates.pop()

    out_dir.mkdir(parents=True, exist_ok=False)
    order = rng.sample(range(len(chosen)), len(chosen))
    corrige: dict[str, dict[str, str]] = {}
    names: list[str] = []
    for rank, idx in enumerate(order, start=1):
        kind, src = chosen[idx]
        name = f"{rank:02d}.wav"
        _, mono = read_wav_mono(src)
        target = int(duration * rate)
        out = fit_duration(mono, target, int(fade * rate))
        write_wav_mono(out_dir / name, out, rate)
        corrige[name] = {"kind": kind, "source": src.name}
        names.append(name)

    feuille = (
        "# Feuille d'écoute en aveugle\n\n"
        "Pour chaque fichier : verdict (`réel` / `généré` / `?`), "
        "note de 1 (pas trad) à 5 (on dirait un vrai), commentaire libre.\n\n"
        "| fichier | verdict | note | commentaire |\n"
        "|---|---|---|---|\n"
        + "".join(f"| {n} | ? |  |  |\n" for n in sorted(names))
    )
    (out_dir / "feuille.md").write_text(feuille, encoding="utf-8")
    (out_dir / "corrige.json").write_text(
        json.dumps(corrige, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {"files": sorted(names), "corrige": corrige, "seed": seed}


def score_feuille(
    kit_dir: Path, compare_report: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Dépouille ``feuille.md`` remplie vs ``corrige.json``.

    Retourne les % de générés reconnus / confondus (sur les générés
    jugés, ``?`` exclus) + le détail par fichier ; avec ``compare_report``
    (``report.json`` de ``trad-compare``), les 3 écarts les plus forts
    de chaque généré démasqué.
    """
    corrige = json.loads((kit_dir / "corrige.json").read_text(encoding="utf-8"))
    rows: dict[str, dict[str, str]] = {}
    for line in (kit_dir / "feuille.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] == "fichier" or set(cells[0]) <= {"-"}:
            continue
        rows[cells[0]] = {"verdict": _norm(cells[1]), "note": cells[2], "comment": cells[3]}

    per_file = []
    for name in sorted(corrige):
        kind = corrige[name]["kind"]
        verdict = rows.get(name, {}).get("verdict", "?")
        judged_genere = verdict.startswith("gener")
        judged_reel = verdict == "reel" or verdict.startswith("reel")
        if verdict in ("?", ""):
            outcome = "abstention"
        elif kind == "genere":
            outcome = "demasque" if judged_genere else "confondu" if judged_reel else "invalide"
        else:
            outcome = "reconnu" if judged_reel else "confondu" if judged_genere else "invalide"
        per_file.append({"file": name, "kind": kind, "verdict": verdict, "outcome": outcome})

    gen_judged = [f for f in per_file if f["kind"] == "genere" and f["outcome"] in ("demasque", "confondu")]
    demasques = [f["file"] for f in per_file if f["outcome"] == "demasque"]
    top_deviations: dict[str, list[str]] = {}
    if compare_report is not None:
        by_file = {p.get("file", p.get("name", "")): p for p in compare_report.get("per_file", [])}
        for name in demasques:
            src = corrige[name]["source"]
            match = by_file.get(src, by_file.get(name))
            if match:
                top_deviations[name] = [d["sentence"] for d in match.get("deviations", [])[:3]]

    return {
        "n_files": len(corrige),
        "n_generated": sum(1 for f in per_file if f["kind"] == "genere"),
        "n_generated_judged": len(gen_judged),
        "pct_generated_recognized": round(100 * len(demasques) / len(gen_judged), 1) if gen_judged else 0.0,
        "pct_generated_confused": round(
            100 * sum(1 for f in gen_judged if f["outcome"] == "confondu") / len(gen_judged), 1
        ) if gen_judged else 0.0,
        "per_file": per_file,
        "top_deviations_unmasked": top_deviations,
    }
