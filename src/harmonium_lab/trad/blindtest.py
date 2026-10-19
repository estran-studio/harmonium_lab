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
import shutil
import subprocess
import struct
import unicodedata
import wave
from pathlib import Path
from typing import Any, Callable

#: Durée par défaut : un air AABB de reel. Fondu par défaut (s).
DEFAULT_DURATION = 33.0
DEFAULT_FADE = 0.5


def _norm(verdict: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", verdict.strip().lower())
    return "".join(c for c in ascii_ if not unicodedata.combining(c))


def normalize_verdict(raw: str) -> str | None:
    """Normalise un verdict : 'reel', 'genere', '?' ou None si invalide."""
    norm = _norm(raw)
    if norm in ("r", "reel") or norm.startswith("reel"):
        return "reel"
    if norm in ("g", "genere") or norm.startswith("gener"):
        return "genere"
    if norm in ("?", "abstention"):
        return "?"
    if not norm:
        return ""
    return None


def load_feuille(kit_dir: Path) -> list[dict[str, str]]:
    """Lit les lignes de feuille.md en ignorant les en-têtes Markdown."""
    rows: list[dict[str, str]] = []
    path = kit_dir / "feuille.md"
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] == "fichier" or set(cells[0]) <= {"-"}:
            continue
        rows.append({"file": cells[0], "verdict": cells[1], "note": cells[2], "comment": cells[3]})
    return rows


def update_feuille(
    kit_dir: Path,
    file_name: str,
    verdict: str,
    note: str = "",
    comment: str = "",
) -> None:
    """Met à jour immédiatement la ligne correspondant à un fichier dans feuille.md."""
    path = kit_dir / "feuille.md"
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    new_lines = []
    found = False
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] == file_name:
            new_lines.append(f"| {file_name} | {verdict} | {note} | {comment} |")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"| {file_name} | {verdict} | {note} | {comment} |")
    trailing = "\n" if content.endswith("\n") else ""
    path.write_text("\n".join(new_lines) + trailing, encoding="utf-8")


def find_audio_player() -> list[str] | None:
    """Détecte automatiquement afplay (macOS) ou aplay/paplay (Linux)."""
    for cmd in ("afplay", "aplay", "paplay"):
        if shutil.which(cmd):
            return [cmd]
    return None


class AudioPlayer:
    """Lecteur audio en arrière-plan permettant d'interrompre et de rejouer."""

    def __init__(self, cmd: list[str] | None = None, print_fn: Callable[[str], None] = print):
        self.cmd = cmd if cmd is not None else find_audio_player()
        self.print_fn = print_fn
        self._proc: subprocess.Popen[bytes] | None = None

    def play(self, path: Path) -> None:
        self.stop()
        if not self.cmd:
            self.print_fn("Aucun lecteur audio détecté (afplay sur macOS, aplay/paplay sur Linux introuvable).")
            return
        try:
            self._proc = subprocess.Popen(
                self.cmd + [str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            self.print_fn(f"Erreur lors de la lecture audio ({path.name}) : {e}")

    def stop(self) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=0.2)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None


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
    rows = {e["file"]: e for e in load_feuille(kit_dir)}

    per_file = []
    for name in sorted(corrige):
        kind = corrige[name]["kind"]
        raw_verdict = rows.get(name, {}).get("verdict", "?")
        v = normalize_verdict(raw_verdict)
        judged_genere = (v == "genere")
        judged_reel = (v == "reel")
        if v in ("?", ""):
            outcome = "abstention"
        elif kind == "genere":
            outcome = "demasque" if judged_genere else "confondu" if judged_reel else "invalide"
        else:
            outcome = "reconnu" if judged_reel else "confondu" if judged_genere else "invalide"
        per_file.append({"file": name, "kind": kind, "verdict": raw_verdict, "outcome": outcome})

    judged_all = [f for f in per_file if f["outcome"] in ("demasque", "confondu", "reconnu")]
    gen_judged = [f for f in per_file if f["kind"] == "genere" and f["outcome"] in ("demasque", "confondu")]
    demasques = [f["file"] for f in per_file if f["outcome"] == "demasque"]
    top_deviations: dict[str, list[str]] = {}
    if compare_report is not None:
        by_file: dict[str, dict[str, Any]] = {}
        for p in compare_report.get("per_file", []):
            key = p.get("file", p.get("name", ""))
            by_file[key] = p
            by_file[Path(key).stem] = p  # .wav du kit vs .mid du rapport
        for name in demasques:
            src = corrige[name]["source"]
            match = by_file.get(src, by_file.get(Path(src).stem, by_file.get(name)))
            if match:
                top_deviations[name] = [d["sentence"] for d in match.get("deviations", [])[:3]]

    return {
        "n_files": len(corrige),
        "n_judged": len(judged_all),
        "n_remaining": len(corrige) - len(judged_all),
        "n_generated": sum(1 for f in per_file if f["kind"] == "genere"),
        "n_generated_judged": len(gen_judged),
        "pct_generated_recognized": round(100 * len(demasques) / len(gen_judged), 1) if gen_judged else 0.0,
        "pct_generated_confused": round(
            100 * sum(1 for f in gen_judged if f["outcome"] == "confondu") / len(gen_judged), 1
        ) if gen_judged else 0.0,
        "per_file": per_file,
        "top_deviations_unmasked": top_deviations,
    }


def print_score(
    score: dict[str, Any],
    kit_dir: Path | str | None = None,
    print_fn: Callable[[str], None] = print,
) -> None:
    """Affiche le score d'un blindtest avec gestion des feuilles vides ou partielles."""
    if score.get("n_judged", 0) == 0:
        target = str(kit_dir) if kit_dir else "<dossier>"
        print_fn(
            f"Aucune réponse dans feuille.md. Lance `harmonium-lab blindtest-play {target}` pour écouter et répondre."
        )
        return

    if score.get("n_remaining", 0) > 0:
        print_fn(
            f"Feuille partielle : il reste {score['n_remaining']} fichier(s) à juger sur {score['n_files']}."
        )

    print_fn(
        f"Générés reconnus : {score['pct_generated_recognized']} % "
        f"({score['n_generated_judged']} jugés sur {score['n_generated']})"
    )
    print_fn(f"Générés confondus (pris pour réels) : {score['pct_generated_confused']} %")
    for name, sentences in score.get("top_deviations_unmasked", {}).items():
        print_fn(f"  {name} :")
        for s in sentences:
            print_fn(f"    - {s}")


def play_kit(
    kit_dir: Path | str,
    compare_report: dict[str, Any] | None = None,
    player: Any = None,
    input_fn: Callable[[str], str] | None = None,
    print_fn: Callable[[str], None] = print,
) -> int:
    """Session d'écoute interactive pour remplir feuille.md et lancer le score."""
    _input = input_fn if input_fn is not None else input
    kit = Path(kit_dir)
    feuille_path = kit / "feuille.md"
    if not feuille_path.exists():
        print_fn(f"Erreur : feuille.md introuvable dans {kit}")
        return 1

    entries = load_feuille(kit)
    if not entries:
        print_fn(f"Erreur : aucune ligne dans feuille.md ({kit})")
        return 1

    total = len(entries)
    unjudged = [e for e in entries if normalize_verdict(e["verdict"]) not in ("reel", "genere")]
    if not unjudged:
        print_fn("Tous les fichiers sont déjà jugés dans feuille.md.")
        score = score_feuille(kit, compare_report)
        print_score(score, kit_dir=kit, print_fn=print_fn)
        return 0

    if hasattr(player, "play") and hasattr(player, "stop"):
        audio: Any = player
    elif callable(player):
        class _CallablePlayer:
            def play(self, p: Path) -> None:
                player(p)

            def stop(self) -> None:
                pass

        audio = _CallablePlayer()
    else:
        audio = AudioPlayer(print_fn=print_fn)
        if not audio.cmd:
            print_fn("Aucun lecteur audio détecté (afplay sur macOS, aplay/paplay sur Linux introuvable).")

    for idx, entry in enumerate(entries, start=1):
        name = entry["file"]
        if normalize_verdict(entry["verdict"]) in ("reel", "genere"):
            continue

        wav_path = kit / name
        print_fn(f"\n[{idx}/{total}] {name}")
        audio.play(wav_path)

        # 1) Verdict
        chosen_verdict = None
        while True:
            try:
                ans = _input("Verdict ? [r]éel / [g]énéré / [?] (p pour réécouter, q pour quitter) : ").strip()
            except (KeyboardInterrupt, EOFError):
                audio.stop()
                print_fn("\nSession interrompue. Progression sauvegardée dans feuille.md.")
                return 0

            ans_lower = ans.lower()
            if ans_lower in ("q", "quit"):
                audio.stop()
                print_fn("\nSession interrompue. Progression sauvegardée dans feuille.md.")
                print_fn(f"Reprenez avec : harmonium-lab blindtest-play {kit}")
                return 0
            if ans_lower in ("p", "play", "e", "replay"):
                audio.play(wav_path)
                continue
            v = normalize_verdict(ans)
            if v == "reel":
                chosen_verdict = "réel"
                break
            elif v == "genere":
                chosen_verdict = "généré"
                break
            elif v == "?":
                chosen_verdict = "?"
                break
            else:
                print_fn("Réponse attendue : [r]éel, [g]énéré ou [?] (p pour réécouter, q pour quitter).")

        # 2) Note
        chosen_note = ""
        while True:
            try:
                ans_note = _input("Note 1-5 (Entrée = passer) : ").strip()
            except (KeyboardInterrupt, EOFError):
                audio.stop()
                print_fn("\nSession interrompue. Progression sauvegardée dans feuille.md.")
                return 0

            if ans_note.lower() in ("q", "quit"):
                audio.stop()
                print_fn("\nSession interrompue. Progression sauvegardée dans feuille.md.")
                print_fn(f"Reprenez avec : harmonium-lab blindtest-play {kit}")
                return 0
            if ans_note == "":
                chosen_note = ""
                break
            if ans_note in ("1", "2", "3", "4", "5"):
                chosen_note = ans_note
                break
            print_fn("Note invalide : entrez un chiffre de 1 à 5, ou Entrée pour passer.")

        # 3) Commentaire
        try:
            ans_comment = _input("Commentaire (Entrée = aucun) : ").strip()
        except (KeyboardInterrupt, EOFError):
            audio.stop()
            print_fn("\nSession interrompue. Progression sauvegardée dans feuille.md.")
            return 0

        chosen_comment = ans_comment.replace("|", "-").strip()

        # Écriture immédiate dans feuille.md
        update_feuille(kit, name, chosen_verdict, chosen_note, chosen_comment)
        entry["verdict"] = chosen_verdict
        entry["note"] = chosen_note
        entry["comment"] = chosen_comment
        audio.stop()

    audio.stop()
    print_fn("\n--- Résultat du test d'écoute ---")
    score = score_feuille(kit, compare_report)
    print_score(score, kit_dir=kit, print_fn=print_fn)
    return 0
