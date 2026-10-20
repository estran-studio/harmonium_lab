"""Préparation des frappes de pieds (chantier SK1).

Pour chaque frappe listée dans `samples/feet/selection.json`
(`{role: [{src, t}]}`) : découpe autour de l'attaque `t`, coupe le
silence, fondu de sortie court, normalisation ; écrit
`samples/feet/prepared/{heel,toe}/NN.wav` (16 bits mono 44,1 kHz).

Classification talon/pointe : rapport d'énergie grave/aigu calculé par
frappe (suggestion), rôle final fixé par la revue manuelle
(`samples/feet/review.md`, figé dans `selection.json`).

Point d'entrée des enregistrements du propriétaire : si
`samples/feet/own/{heel,toe}/*.wav` contient des fichiers, ils
remplacent les libres pour ce rôle (même normalisation, ordre
alphabétique).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample

from harmonium_lab.feet import SAMPLE_RATE, feet_dir

#: Pic cible après normalisation (−1 dBFS).
PEAK = 0.89
#: Durée maximale d'une frappe (s) : pas de débordement sur le pas voisin.
MAX_S = 0.25
#: Fondu de sortie (s).
FADE_S = 0.02
#: Seuil de silence relatif au pic (−40 dB).
SILENCE = 0.01
#: Seuil second transitoire : rejet au-delà de cette fraction du pic après 25 ms.
ECHO_RATIO = 0.3
#: Le pic doit arriver dans les 20 premières ms.
PEAK_MS = 20.0
#: Suggestion talon si énergie grave/aigu ≥ ce seuil.
HEEL_RATIO = 1.5


def load_mono_44k(path: Path) -> np.ndarray:
    """Décode (mp3/wav/…) en mono 44,1 kHz flottant."""
    data, sr = sf.read(str(path), always_2d=True)
    mono = data.mean(axis=1).astype(np.float64)
    if sr != SAMPLE_RATE:
        mono = resample(mono, int(len(mono) * SAMPLE_RATE / sr))
    return mono


def spectral_features(hit: np.ndarray) -> tuple[float, float]:
    """(centroïde spectral Hz, énergie 70–400 Hz / 2–9 kHz)."""
    if len(hit) < 16:
        return 0.0, 0.0
    spec = np.abs(np.fft.rfft(hit * np.hanning(len(hit))))
    freqs = np.fft.rfftfreq(len(hit), 1 / SAMPLE_RATE)
    total = spec.sum()
    centroid = float((spec * freqs).sum() / total) if total > 0 else 0.0
    low = spec[(freqs >= 70) & (freqs < 400)].sum()
    high = spec[(freqs >= 2000) & (freqs < 9000)].sum()
    return centroid, float(low / high) if high > 0 else float("inf")


def suggest_role(hit: np.ndarray) -> str:
    """talon si grave dominant, sinon pointe (revue manuelle : review.md)."""
    _, ratio = spectral_features(hit)
    return "heel" if ratio >= HEEL_RATIO else "toe"


def cut_hit(audio: np.ndarray, at: float, end_limit: float | None = None) -> np.ndarray:
    """Découpe UNE frappe : début ≤ 5 ms avant l'attaque `at` (s).

    Fin = premier silence (< −40 dB du pic), sans dépasser `end_limit`
    (frappe suivante de la source) ni `MAX_S`. Fondu de sortie `FADE_S`,
    pic normalisé à `PEAK`.
    """
    sr = SAMPLE_RATE
    start = max(0, int((at - 0.005) * sr))
    stop = len(audio) if end_limit is None else min(len(audio), int(end_limit * sr))
    window = audio[start:stop]
    if window.size == 0:
        raise ValueError(f"attaque {at:.2f}s hors audio")
    peak = np.abs(window).max()
    if peak <= 0:
        raise ValueError(f"silence à {at:.2f}s")
    loud = np.nonzero(np.abs(window) >= SILENCE * peak)[0]
    end = min(loud[-1] + int(0.01 * sr), len(window), int(MAX_S * sr))
    hit = window[:end].copy()
    fade = min(int(FADE_S * sr), len(hit))
    hit[-fade:] *= 0.5 * (1 + np.cos(np.pi * np.arange(fade) / fade))
    hit *= PEAK / np.abs(hit).max()
    return hit


def late_transients(hit: np.ndarray) -> list[float]:
    """Positions (ms) des remontées > 30 % du pic après 25 ms.

    Détection par proéminence (`scipy`) : la décroissance naturelle
    (ondulation basse fréquence) ne compte pas, un vrai second coup si.
    """
    from scipy.signal import find_peaks
    sr = SAMPLE_RATE
    k = max(1, int(0.008 * sr))
    env = np.convolve(np.abs(hit), np.ones(k) / k, mode="same")
    peak = env.max()
    if peak <= 0:
        return []
    seg = env[int(0.025 * sr):]
    idx, _ = find_peaks(seg, prominence=ECHO_RATIO * peak,
                         distance=int(0.015 * sr))
    return [(i + int(0.025 * sr)) / sr * 1000 for i in idx]


def validate_hit(hit: np.ndarray, label: str) -> dict:
    """Une seule frappe : pic < 20 ms, durée ≤ 250 ms, pas d'écho > 30 %.

    Lève `ValueError` en nommant le fichier et la raison (dont les
    enregistrements du propriétaire, cf. `prepare_own`).
    """
    sr = SAMPLE_RATE
    peak_ms = float(np.argmax(np.abs(hit)) / sr * 1000)
    dur_ms = len(hit) / sr * 1000
    echoes = late_transients(hit)
    problems = []
    if peak_ms >= PEAK_MS:
        problems.append(f"pic à {peak_ms:.0f} ms (≥ {PEAK_MS:.0f} ms : attaque tardive)")
    if dur_ms > MAX_S * 1000:
        problems.append(f"durée {dur_ms:.0f} ms (> {MAX_S * 1000:.0f} ms)")
    if echoes:
        problems.append("2ᵉ transitoire > 30 % à "
                        + ", ".join(f"{e:.0f} ms" for e in echoes[:4]))
    if problems:
        raise ValueError(f"{label} rejetée : " + " ; ".join(problems))
    return {"peak_ms": round(peak_ms, 1), "dur_ms": round(dur_ms, 1), "echoes": []}


def write_wav(path: Path, hit: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(hit, -1.0, 1.0)
    sf.write(str(path), (pcm * 32767).astype(np.int16), SAMPLE_RATE)


def source_onsets(audio: np.ndarray) -> list[float]:
    """Attaques (s) de la source : borne de fin anti-débordement."""
    import librosa
    onsets = librosa.onset.onset_detect(y=audio.astype(np.float32), sr=SAMPLE_RATE,
                                        units="time", backtrack=True,
                                        delta=0.2, wait=int(0.15 * SAMPLE_RATE / 512))
    return [float(t) for t in onsets]


def prepare_libre(root: Path, selection: dict) -> list[dict]:
    """Applique `selection.json` → prepared/. Retourne la table de revue."""
    manifest = {e["id"]: e for e in
                (json.loads(line) for line in (root / "manifest.jsonl")
                 .read_text(encoding="utf-8").splitlines() if line.strip())}
    cache: dict[str, tuple[np.ndarray, list[float]]] = {}
    table = []
    for role, hits in selection.items():
        if role not in ("heel", "toe"):
            continue  # ex. "_comment"
        for i, h in enumerate(hits, start=1):
            src = h["src"]
            if src not in cache:
                audio = load_mono_44k(root / "raw" / f"{src}.mp3")
                cache[src] = (audio, source_onsets(audio))
            audio, onsets = cache[src]
            nxt = min([o for o in onsets if o > h["t"] + 0.02], default=None)
            end_limit = h["t"] + MAX_S if nxt is None else min(h["t"] + MAX_S, nxt - 0.005)
            label = f"{src} t={h['t']}s"
            hit = cut_hit(audio, h["t"], end_limit)
            info = validate_hit(hit, label)  # lève si double frappe / attaque tardive
            centroid, ratio = spectral_features(hit)
            suggested = suggest_role(hit)
            dest = root / "prepared" / role / f"{i:02d}.wav"
            write_wav(dest, hit)
            table.append({"role": role, "file": dest.name, "src": src,
                          "title": manifest[src]["title"], "t": h["t"],
                          "centroid_hz": round(centroid),
                          "lowhi": round(ratio, 2) if ratio != float("inf") else None,
                          "suggested": suggested,
                          "avertissement": suggested != role,
                          **info})
    return table


def prepare_own(root: Path) -> dict[str, list[str]]:
    """Normalise `own/{heel,toe}/*.wav` → prepared/. Retourne les rôles remplacés."""
    replaced: dict[str, list[str]] = {}
    for role in ("heel", "toe"):
        wavs = sorted((root / "own" / role).glob("*.wav")) if (root / "own" / role).is_dir() else []
        if not wavs:
            continue
        outdir = root / "prepared" / role
        for old in outdir.glob("*.wav"):
            old.unlink()
        names = []
        for i, wav in enumerate(wavs, start=1):
            label = f"own/{role}/{wav.name}"
            audio = load_mono_44k(wav)
            if np.abs(audio).max() <= 0:
                raise ValueError(f"{label} rejeté : fichier silencieux")
            onsets = source_onsets(audio)
            at = onsets[0] if onsets else 0.0
            nxt = min([o for o in onsets if o > at + 0.02], default=None)
            end_limit = at + MAX_S if nxt is None else min(at + MAX_S, nxt - 0.005)
            hit = cut_hit(audio, at, end_limit)
            validate_hit(hit, label)  # lève en nommant le fichier et la raison
            dest = outdir / f"{i:02d}.wav"
            write_wav(dest, hit)
            names.append(wav.name)
        replaced[role] = names
    return replaced


def prepare(root: Path, selection: dict) -> tuple[list[dict], dict[str, list[str]]]:
    table = prepare_libre(root, selection)
    replaced = prepare_own(root)
    return table, replaced


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="feet-prepare",
                                 description="Découpe/normalise les frappes (raw/ → prepared/)")
    ap.add_argument("--root", type=Path, default=feet_dir(), help="dossier samples/feet")
    args = ap.parse_args(argv)
    try:
        selection = json.loads((args.root / "selection.json").read_text(encoding="utf-8"))
        table, replaced = prepare(args.root, selection)
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    for row in table:
        flag = "  ← SUGGESTION CONTRAIRE" if row["avertissement"] else ""
        print(f"{row['role']:>4} {row['file']} src={row['src']} t={row['t']}s "
              f"centroide={row['centroid_hz']}Hz grave/aigu={row['lowhi']}{flag}")
    for role, names in replaced.items():
        print(f"{role} : {len(names)} enregistrement(s) du propriétaire "
              f"remplacent les libres ({', '.join(names)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
