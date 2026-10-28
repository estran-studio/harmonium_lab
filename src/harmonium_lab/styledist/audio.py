"""Distance audio d'un rendu à une piste de référence.

Mesures (toutes insensibles au niveau : le signal est normalisé au pic) :

| groupe      | mesures                                                              |
|-------------|----------------------------------------------------------------------|
| tempo       | `tempo_log2` (log2 de la pulsation, voir `midi_pulse_log2`)             |
| tonalité    | `chroma_cos` (1 − cosinus des chromas moyens), `key_strength`,        |
|             | `chroma_entropy`                                                      |
| brillance   | `centroid_hz`, `rolloff_hz`, `flatness_log10`                         |
| percussif   | `percussive_ratio` (part percussive de l'énergie, HPSS)               |
| attaques    | `onset_rate` (attaques par seconde)                                   |
| dynamique   | `rms_db_mean` (niveau moyen sous le pic RMS), `dynamic_spread_db`     |
|             | (écart percentiles 95 − 5 du niveau RMS en dB)                        |
| bandes      | part d'énergie en dB par bande : 20–80, 80–250, 250–1000, 1–4 k,      |
|             | > 4 kHz                                                               |

Normalisation (écart z, sans unité) :

- mesure scalaire : `z = |g − r| / σ`, σ = écart-type de la mesure sur le corpus
  de contexte (pistes du même genre, p. ex. toutes les zones d'un jeu) ;
- `chroma_cos` : `z = d / médiane`, médiane des `1 − cos` entre paires de pistes
  du contexte (la distance habituelle entre deux pistes différentes) ;
- `tempo_log2` : pulsation du rendu (MIDI, vérité terrain : `midi_pulse_log2`)
  contre pulsation de la grille G0 de la référence (champ `bpm` ; à défaut,
  tempo `beat_track` brut) ; repliée à l'octave (`beat_track` tombe sur ÷2
  ou ×2), tolérance fixe de 1/12 d'octave (≈ 6 %), car le contexte mélange
  nappes sans pulsation et pistes rythmées (σ non significatif).

Score d'une mesure : `100 · max(0, 1 − z / 3)` (0 σ → 100, 1 σ → 67, ≥ 3 σ → 0).
Score d'un groupe : moyenne de ses mesures ; score global : moyenne des groupes
(chaque groupe pèse autant, quel que soit son nombre de mesures).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

SR = 22050
#: z au-delà duquel le score d'une mesure tombe à 0.
Z_ZERO = 3.0
#: Tolérance de tempo (octaves) : 1 σ.
TEMPO_TOL_OCT = 1.0 / 12.0
BANDS_HZ: tuple[tuple[float, float | None], ...] = (
    (20, 80), (80, 250), (250, 1000), (1000, 4000), (4000, None))

def _band_name(lo: float, hi: float | None) -> str:
    return f"band_db_{lo:g}_{'max' if hi is None else format(hi, 'g')}"


GROUPS: dict[str, tuple[str, ...]] = {
    "tempo": ("tempo_log2",),
    "tonalite": ("chroma_cos", "key_strength", "chroma_entropy"),
    "brillance": ("centroid_hz", "rolloff_hz", "flatness_log10"),
    "percussif": ("percussive_ratio",),
    "attaques": ("onset_rate",),
    "dynamique": ("rms_db_mean", "dynamic_spread_db"),
    "bandes": tuple(_band_name(lo, hi) for lo, hi in BANDS_HZ),
}
SCALAR_METRICS = tuple(m for g in GROUPS.values() for m in g if m != "chroma_cos")
CHROMA_METRIC = "chroma_cos"


def extract_features(y: np.ndarray, sr: int = SR) -> dict[str, Any]:
    """Mesures d'un signal mono : `scalars` (par nom), `chroma` (12), `tonal`."""
    import librosa

    from harmonium_lab.audioref.measures import measure_track

    y = np.asarray(y, dtype=np.float32)
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    if peak <= 0:
        raise ValueError("signal silencieux")
    y = y * (0.9 / peak)

    m = measure_track(y, sr)
    spec = np.abs(librosa.stft(y, n_fft=2048, hop_length=512)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    total = float(spec.sum()) + 1e-12
    scalars: dict[str, float] = {
        "tempo_log2": float(np.log2(max(m["rhythm"]["detected_tempo"], 1.0))),
        "key_strength": m["tonal"]["key_strength"],
        "chroma_entropy": m["tonal"]["chroma_entropy"],
        "centroid_hz": m["spectral"]["spectral_centroid_mean"],
        "rolloff_hz": m["spectral"]["spectral_rolloff_mean"],
        "flatness_log10": float(np.log10(max(m["spectral"]["spectral_flatness_mean"], 1e-9))),
        "percussive_ratio": m["dissonance"]["percussive_ratio"],
        "onset_rate": m["rhythm"]["onset_rate"],
    }
    rms_db = librosa.amplitude_to_db(librosa.feature.rms(y=y)[0], ref=np.max, top_db=80.0)
    scalars["rms_db_mean"] = float(np.mean(rms_db))
    scalars["dynamic_spread_db"] = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))
    for lo, hi in BANDS_HZ:
        mask = (freqs >= lo) & ((freqs < hi) if hi is not None else np.ones_like(freqs, bool))
        share = float(spec[mask].sum()) / total
        scalars[_band_name(lo, hi)] = 10.0 * float(np.log10(share + 1e-9))
    return {"scalars": {k: round(v, 5) for k, v in scalars.items()},
            "chroma": m["chroma_mean"],
            "tonal": {"tonic": m["tonal"]["mode"]["tonic"], "mode": m["tonal"]["mode"]["mode"],
                      "mode_margin": m["tonal"]["mode"]["margin"],
                      "estimated_key": m["tonal"]["estimated_key"]},
            "duration_s": round(len(y) / sr, 2)}


def features_for_file(path: Path, cache_dir: Path | None = None, sr: int = SR) -> dict[str, Any]:
    """`extract_features` d'un fichier audio, mis en cache (clé : nom, taille, date)."""
    cache = None
    if cache_dir is not None:
        st = path.stat()
        key = hashlib.sha1(f"{path.resolve()}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:16]
        cache = cache_dir / f"{path.stem}-{key}.json"
        if cache.is_file():
            return json.loads(cache.read_text(encoding="utf-8"))
    import librosa

    y, _ = librosa.load(str(path), sr=sr, mono=True)
    feats = extract_features(y, sr)
    if cache is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(feats), encoding="utf-8")
    return feats

def midi_pulse_log2(path: Path) -> float:
    """log2 de la pulsation d'un MIDI moteur : tempo à la noire divisé par la
    pulsation en noires (noire pointée = 1,5 en mètre composé x/8, noire = 1
    sinon). Évite les artefacts de `beat_track`, qui compare des niveaux
    métriques différents (69,8 détecté contre 140 joué, ×3 non repliable)."""
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(str(path))
    qpm = float(pm.get_tempo_changes()[1][0])
    den = pm.time_signature_changes[0].denominator if pm.time_signature_changes else 4
    pulse_quarters = 1.5 if den == 8 else 1.0
    return float(np.log2(qpm / pulse_quarters))


def chroma_distance(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, float), np.asarray(b, float)
    return float(1.0 - va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-12))


def compute_scales(context: list[dict[str, Any]]) -> dict[str, float]:
    """σ de chaque mesure scalaire + médiane des distances de chroma entre paires."""
    if len(context) < 3:
        raise ValueError(f"contexte trop petit ({len(context)} pistes) : au moins 3 pour une échelle")
    scales = {m: float(np.std([c["scalars"][m] for c in context])) for m in SCALAR_METRICS
              if m != "tempo_log2"}
    pairs = [chroma_distance(context[i]["chroma"], context[j]["chroma"])
             for i in range(len(context)) for j in range(i + 1, len(context))]
    scales[CHROMA_METRIC] = float(np.median(pairs))
    scales["tempo_log2"] = TEMPO_TOL_OCT
    for m, s in scales.items():
        if s <= 0:
            raise ValueError(f"échelle nulle pour {m} : contexte sans dispersion")
    return {m: round(s, 5) for m, s in scales.items()}


def fold_octave(delta_log2: float) -> float:
    """Écart de tempo en octaves, replié : 140 contre 70 ou 280 vaut 0."""
    return abs(delta_log2 - round(delta_log2))


def score_from_z(z: float) -> float:
    return 100.0 * max(0.0, 1.0 - z / Z_ZERO)


def metric_z(metric: str, gen: dict[str, Any], ref: dict[str, Any], scales: dict[str, float]) -> float:
    if metric == CHROMA_METRIC:
        return chroma_distance(gen["chroma"], ref["chroma"]) / scales[metric]
    g, r = gen["scalars"][metric], ref["scalars"][metric]
    if metric == "tempo_log2":
        return fold_octave(g - r) / scales[metric]
    return abs(g - r) / scales[metric]


def compare(gen: dict[str, Any], ref: dict[str, Any], scales: dict[str, float]) -> dict[str, float]:
    """z de chaque mesure entre un rendu et une référence."""
    return {m: metric_z(m, gen, ref, scales) for g in GROUPS.values() for m in g}


def summarize(per_seed_z: list[dict[str, float]]) -> dict[str, Any]:
    """Score par mesure (moyenne des scores des graines), par groupe et global."""
    scores = {m: float(np.mean([score_from_z(z[m]) for z in per_seed_z])) for m in per_seed_z[0]}
    groups = {g: float(np.mean([scores[m] for m in ms])) for g, ms in GROUPS.items()}
    return {"scores": {m: round(s, 1) for m, s in scores.items()},
            "z_mean": {m: round(float(np.mean([z[m] for z in per_seed_z])), 3) for m in per_seed_z[0]},
            "groups": {g: round(s, 1) for g, s in groups.items()},
            "score": round(float(np.mean(list(groups.values()))), 1)}
