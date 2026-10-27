"""Synthèse procédurale générique et déterministe en numpy (sans licence tierce).

Fournit des recettes paramétrées pour instruments mélodiques/harmoniques
bouclés à tenue (`detuned_saw`, `warm_pad`, `whistle_lead`) et percussions
one-shot (`drum_kick`, `drum_snare`, `drum_stick`, `drum_hat`, `drum_tom`,
`drum_cymbal`). Aucun nom de jeu ou de style n'est codé en dur.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from harmonium_lab.bank import SAMPLE_RATE


def midi_to_hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))


def _fft_filter(
    signal: np.ndarray,
    sr: int = SAMPLE_RATE,
    *,
    hp_hz: float | None = None,
    lp_hz: float | None = None,
    peaking: list[tuple[float, float, float]] | None = None,
) -> np.ndarray:
    """Filtrage fréquentiel déterministe à phase nulle (passe-haut, passe-bas, cloches)."""
    n = len(signal)
    freqs = np.fft.rfftfreq(n, d=1.0 / sr)
    spec = np.fft.rfft(signal)
    gain = np.ones_like(freqs)

    if hp_hz is not None and hp_hz > 0:
        ratio = np.maximum(freqs, 1e-3) / float(hp_hz)
        gain *= (ratio**4) / (1.0 + ratio**4)

    if lp_hz is not None and lp_hz > 0:
        ratio = freqs / float(lp_hz)
        gain *= 1.0 / np.sqrt(1.0 + ratio**8)

    if peaking:
        for center_hz, q, gain_db in peaking:
            if center_hz <= 0 or abs(gain_db) < 1e-6:
                continue
            bw = center_hz / max(q, 0.1)
            bell = np.exp(-0.5 * ((freqs - center_hz) / bw) ** 2)
            lin = 10.0 ** (gain_db / 20.0)
            gain *= 1.0 + (lin - 1.0) * bell

    filtered = np.fft.irfft(spec * gain, n=n)
    return filtered.astype(np.float64)


def _bandlimited_saw(phase_rad: np.ndarray, f0_hz: float, max_harmonics: int = 48, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Dent-de-scie additive limitée en bande (sans repliement spectral)."""
    nyquist = 0.45 * sr
    n_harm = min(max_harmonics, max(1, int(nyquist // max(f0_hz, 1.0))))
    out = np.zeros_like(phase_rad, dtype=np.float64)
    for k in range(1, n_harm + 1):
        # Atténuation de Gibbs douce sur les harmoniques hautes
        sigma = math.sin(math.pi * k / (n_harm + 1)) / (math.pi * k / (n_harm + 1))
        out += ((-1.0) ** (k + 1)) * (sigma / k) * np.sin(k * phase_rad)
    return out * (2.0 / math.pi)




def crossfade_loop(
    audio: np.ndarray,
    loop_start: int,
    loop_end: int,
    fade_s: float = 0.05,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Fondu linéaire de `fade_s` avant `loop_end` vers la fenêtre précédant `loop_start`."""
    fade = round(fade_s * sr)
    if loop_start < fade or loop_end - loop_start < 4 * fade or loop_end > len(audio):
        raise ValueError("fenêtre de boucle trop courte pour le fondu")
    result = audio.copy()
    w = np.linspace(0.0, 1.0, fade, dtype=np.float64)
    result[loop_end - fade : loop_end] = (
        (1.0 - w) * audio[loop_end - fade : loop_end]
        + w * audio[loop_start - fade : loop_start]
    )
    return result


def compute_period_aligned_loop(
    n_samples: int,
    f0_hz: float,
    start_s: float = 0.35,
    end_margin_s: float = 0.15,
    sr: int = SAMPLE_RATE,
) -> tuple[int, int]:
    """Calcule `(loop_start, loop_end)` alignés sur un nombre entier de périodes de `f0_hz`."""
    period = sr / max(f0_hz, 10.0)
    loop_start = max(round(0.08 * sr), round(start_s * sr))
    raw_end = n_samples - max(round(0.05 * sr), round(end_margin_s * sr))
    n_cycles = max(8, round((raw_end - loop_start) / period))
    loop_end = min(n_samples - 16, loop_start + round(n_cycles * period))
    if loop_end <= loop_start + round(0.25 * sr):
        loop_end = n_samples - 16
    return int(loop_start), int(loop_end)


def normalize_peak(audio: np.ndarray, peak_target: float = 0.89, fade_in_ms: float = 1.5, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Supprime la composante continue, applique un micro-fondu d'entrée et normalise le pic."""
    y = np.asarray(audio, dtype=np.float64) - float(np.mean(audio))
    fade_in = max(1, round(fade_in_ms * 0.001 * sr))
    if len(y) > fade_in:
        y[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
        y[0] = 0.0
    peak = float(np.max(np.abs(y)))
    if peak < 1e-8:
        raise ValueError("signal synthétisé silencieux")
    return np.clip(y * (peak_target / peak), -0.999, 0.999)


def synth_detuned_saw(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Scie synthé désaccordée à tenue (pédale grave, basse fuzz ou lead).

    Chœur de dent-de-scie désaccordées + sub-octave, saturation légère et
    présence : amplitude constante, la note tient sans décroissance tant
    que la note MIDI dure (échantillon bouclé, sustain plein).
    """
    midi = int(params["midi"])
    f0 = midi_to_hz(midi)
    dur_s = float(params.get("duration_s", 2.2))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr

    sub_level = float(params.get("sub_level", 0.32))
    sub_oct = float(params.get("sub_oct", -12.0))
    detune_cents = float(params.get("detune_cents", 9.0))
    max_harmonics = int(params.get("max_harmonics", 64))
    drive = float(params.get("drive", 2.1))
    bite_hz = float(params.get("bite_hz", 1200.0))
    bite_db = float(params.get("bite_db", 4.5))
    lowpass_hz = float(params.get("lowpass_hz", 4600.0))
    hp_hz = float(params.get("hp_hz", 30.0))
    vibrato_hz = float(params.get("vibrato_hz", 0.0))
    vibrato_cents = float(params.get("vibrato_cents", 0.0))

    # Vibrato progressif commun à toutes les voix (en cycles de phase)
    vib_mod = np.zeros(n, dtype=np.float64)
    if vibrato_hz > 0 and vibrato_cents != 0:
        vib_env = 1.0 - np.exp(-t / 0.20)
        vib_peak = f0 * ((2.0 ** (abs(vibrato_cents) / 1200.0)) - 1.0) / (2.0 * math.pi * vibrato_hz)
        vib_mod = np.sign(vibrato_cents) * vib_env * vib_peak * np.sin(2.0 * math.pi * vibrato_hz * t)

    # Centre dominant : le désaccord colore sans creux de battement en tenue.
    offsets = (-detune_cents, -0.45 * detune_cents, 0.0, 0.42 * detune_cents, detune_cents)
    phases = (0.7, 1.9, 0.0, 0.9, 2.4)
    weights = (0.025, 0.025, 0.9, 0.025, 0.025)
    saw = np.zeros(n, dtype=np.float64)
    for cents, phi, weight in zip(offsets, phases, weights):
        f_v = f0 * (2.0 ** (cents / 1200.0))
        saw += weight * _bandlimited_saw(
            2.0 * math.pi * (f_v * t + vib_mod) + phi, f_v, max_harmonics=max_harmonics, sr=sr
        )

    # Sub-octave sinusoidale (corps grave, suit le vibrato)
    f_sub = f0 * (2.0 ** (sub_oct / 12.0))
    sub = np.sin(2.0 * math.pi * (f_sub * t + vib_mod))

    raw = saw + sub_level * sub
    sat = np.tanh(drive * raw)
    sat -= np.mean(sat)
    filtered = _fft_filter(
        sat,
        sr=sr,
        hp_hz=hp_hz,
        lp_hz=lowpass_hz,
        peaking=[
            (bite_hz, 1.1, bite_db),
            (bite_hz * 1.6, 1.3, bite_db * 0.55),
        ],
    )
    loop_start, loop_end = compute_period_aligned_loop(n, f0, start_s=0.35, end_margin_s=0.15, sr=sr)
    looped = crossfade_loop(filtered, loop_start, loop_end, fade_s=0.05, sr=sr)
    norm = normalize_peak(looped, peak_target=float(params.get("peak", 0.90)), fade_in_ms=1.5, sr=sr)
    return norm, loop_start, loop_end


def synth_warm_pad(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Nappe synthé analogique chaude avec chœur multi-oscillateurs et brillance contrôlée."""
    midi = int(params["midi"])
    f0 = midi_to_hz(midi)
    dur_s = float(params.get("duration_s", 3.6))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 101 + midi))))

    detune_cents = float(params.get("detune_cents", 11.0))
    fifth_level = float(params.get("fifth_level", 0.22))
    octave_level = float(params.get("octave_level", 0.38))
    sub_level = float(params.get("sub_level", 0.20))
    shimmer_level = float(params.get("shimmer_level", 0.24))
    warm_drive = float(params.get("warm_drive", 1.65))
    lowpass_hz = float(params.get("lowpass_hz", 3100.0))
    air_hz = float(params.get("air_hz", 1650.0))
    air_gain_db = float(params.get("air_gain_db", 5.5))
    breath_level = float(params.get("breath_level", 0.025))

    # Ensemble de 5 oscillateurs désaccordés (dent-de-scie + triangle)
    offsets_cents = (-detune_cents, -0.45 * detune_cents, 0.0, 0.48 * detune_cents, detune_cents)
    pad = np.zeros(n, dtype=np.float64)
    for idx, c in enumerate(offsets_cents):
        f_v = f0 * (2.0 ** (c / 1200.0))
        phi0 = float(rng.uniform(0.0, 2.0 * math.pi))
        lfo = 0.0018 * np.sin(2.0 * math.pi * (0.55 + 0.12 * idx) * t + phi0)
        phase = 2.0 * math.pi * f_v * (t + lfo) + phi0
        pad += _bandlimited_saw(phase, f_v, max_harmonics=36, sr=sr)

    pad /= len(offsets_cents)

    # Fondamentale grave, octave supérieure et quinte douce (texture bourdon désertique)
    phase_main = 2.0 * math.pi * f0 * t
    sub_osc = np.sin(0.5 * phase_main) + 0.5 * np.sin(phase_main)
    oct_osc = _bandlimited_saw(2.0 * phase_main + 0.4, 2.0 * f0, max_harmonics=28, sr=sr)
    fifth_osc = _bandlimited_saw(1.5 * phase_main + 1.1, 1.5 * f0, max_harmonics=24, sr=sr)
    shimmer_osc = np.sin(3.0 * phase_main) + 0.6 * np.sin(4.0 * phase_main) + 0.35 * np.sin(5.0 * phase_main)

    # Texture de souffle chaud filtré
    noise = rng.standard_normal(n)
    breath = _fft_filter(noise, sr=sr, hp_hz=500.0, lp_hz=2600.0, peaking=[(air_hz, 1.5, 6.0)])

    combined = (
        pad
        + sub_level * sub_osc
        + octave_level * oct_osc
        + fifth_level * fifth_osc
        + shimmer_level * shimmer_osc
        + breath_level * breath
    )
    saturated = np.tanh(warm_drive * combined + 0.12 * (combined**2))
    filtered = _fft_filter(
        saturated,
        sr=sr,
        hp_hz=45.0,
        lp_hz=lowpass_hz,
        peaking=[
            (320.0, 1.0, 2.0),
            (air_hz, 1.1, air_gain_db),
            (air_hz * 1.55, 1.4, air_gain_db * 0.6),
        ],
    )
    loop_start, loop_end = compute_period_aligned_loop(n, f0, start_s=0.55, end_margin_s=0.20, sr=sr)
    looped = crossfade_loop(filtered, loop_start, loop_end, fade_s=0.08, sr=sr)
    norm = normalize_peak(looped, peak_target=float(params.get("peak", 0.86)), fade_in_ms=12.0, sr=sr)
    return norm, loop_start, loop_end


def synth_whistle_lead(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Sifflement western / flûte de Pan soufflée avec transitoire d'air et vibrato."""
    midi = int(params["midi"])
    f0 = midi_to_hz(midi)
    dur_s = float(params.get("duration_s", 2.4))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 303 + midi))))

    harm2_level = float(params.get("harm2_level", 0.18))
    harm3_level = float(params.get("harm3_level", 0.09))
    breath_level = float(params.get("breath_level", 0.08))
    chiff_level = float(params.get("chiff_level", 0.14))
    vibrato_hz = float(params.get("vibrato_hz", 5.5))
    vibrato_cents = float(params.get("vibrato_cents", 18.0))
    scoop_ms = float(params.get("scoop_ms", 35.0))
    scoop_cents = float(params.get("scoop_cents", -45.0))
    lowpass_hz = float(params.get("lowpass_hz", 3600.0))

    # Léger portamento ascendant à l'attaque (signature sifflement western)
    scoop_ratio = (2.0 ** (scoop_cents / 1200.0) - 1.0) * np.exp(-t / max(scoop_ms * 0.001, 0.005))
    vib_env = 1.0 - np.exp(-t / 0.20)
    vib_ratio = vib_env * (2.0 ** (vibrato_cents / 1200.0) - 1.0) * np.sin(2.0 * math.pi * vibrato_hz * t)
    inst_freq = f0 * (1.0 + scoop_ratio + vib_ratio)
    phase = 2.0 * math.pi * np.cumsum(inst_freq) / sr

    tone = np.sin(phase) + harm2_level * np.sin(2.0 * phase + 0.3) + harm3_level * np.sin(3.0 * phase + 0.8)

    noise = rng.standard_normal(n)
    breath_band = _fft_filter(
        noise,
        sr=sr,
        hp_hz=max(200.0, 0.7 * f0),
        lp_hz=min(6000.0, 3.2 * f0),
        peaking=[(f0, 4.0, 12.0), (2.0 * f0, 3.0, 6.0)],
    )
    breath_band /= max(float(np.std(breath_band)), 1e-6)
    chiff_env = np.exp(-t / 0.028)
    air = (breath_level + chiff_level * chiff_env) * breath_band * 0.25

    mixed = np.tanh(1.25 * (tone + air))
    filtered = _fft_filter(mixed, sr=sr, hp_hz=120.0, lp_hz=lowpass_hz)
    # Boucle alignée sur le vibrato (courte : périodique par construction)
    loop_start, loop_end = compute_period_aligned_loop(n, vibrato_hz, start_s=0.45, end_margin_s=0.18, sr=sr)
    looped = crossfade_loop(filtered, loop_start, loop_end, fade_s=0.06, sr=sr)
    norm = normalize_peak(looped, peak_target=float(params.get("peak", 0.88)), fade_in_ms=6.0, sr=sr)
    return norm, loop_start, loop_end

def synth_drum_kick(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Grosse caisse rock sèche et compressée : impact grave < 80 Hz + clic de batte."""
    dur_s = float(params.get("duration_s", 0.32))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 501))))

    f_end = float(params.get("f_end_hz", 50.0))
    f_drop1 = float(params.get("f_drop1_hz", 145.0))
    tau_drop1 = float(params.get("pitch_decay_ms", 16.0)) * 0.001
    f_drop2 = float(params.get("f_drop2_hz", 42.0))
    tau_drop2 = float(params.get("punch_decay_ms", 55.0)) * 0.001
    body_decay = float(params.get("body_decay_ms", 145.0)) * 0.001
    click_hz = float(params.get("click_hz", 2400.0))
    click_level = float(params.get("click_level", 0.42))
    drive = float(params.get("drive", 2.4))

    freq = f_end + f_drop1 * np.exp(-t / tau_drop1) + f_drop2 * np.exp(-t / tau_drop2)
    phase = 2.0 * math.pi * np.cumsum(freq) / sr
    body_env = np.exp(-t / body_decay) * (1.0 - np.exp(-t / 0.0008))
    body = (np.sin(phase) + 0.28 * np.sin(2.0 * phase)) * body_env

    # Clic de batte sec (transitoire 1.8–4 kHz sur ~8 ms)
    click_noise = _fft_filter(rng.standard_normal(n), sr=sr, hp_hz=900.0, lp_hz=5200.0, peaking=[(click_hz, 1.5, 9.0)])
    click_noise /= max(float(np.max(np.abs(click_noise))), 1e-6)
    click_env = np.exp(-t / 0.0065)
    click = click_level * (0.6 * np.sin(2.0 * math.pi * click_hz * t) + 0.4 * click_noise) * click_env

    kick = np.tanh(drive * (body + click))
    # Fondu de fin propre sur les 20 dernières ms
    fade = round(0.02 * sr)
    kick[-fade:] *= np.linspace(1.0, 0.0, fade)
    norm = normalize_peak(kick, peak_target=float(params.get("peak", 0.94)), fade_in_ms=0.4, sr=sr)
    return norm, 0, 0


def synth_drum_snare(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Caisse claire rock sèche et claquante (fût modal 185/330 Hz + timbre brillant)."""
    dur_s = float(params.get("duration_s", 0.28))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 601))))

    f1 = float(params.get("f_body1_hz", 186.0))
    f2 = float(params.get("f_body2_hz", 332.0))
    body_decay = float(params.get("body_decay_ms", 68.0)) * 0.001
    wire_level = float(params.get("wire_level", 1.15))
    wire_decay = float(params.get("wire_decay_ms", 125.0)) * 0.001
    wire_hp_hz = float(params.get("wire_hp_hz", 1100.0))
    wire_lp_hz = float(params.get("wire_lp_hz", 9200.0))
    snap_hz = float(params.get("snap_hz", 3400.0))
    drive = float(params.get("drive", 2.2))

    # Modes de fût avec léger glissement d'attaque
    p1 = 2.0 * math.pi * np.cumsum(f1 * (1.0 + 0.45 * np.exp(-t / 0.010))) / sr
    p2 = 2.0 * math.pi * np.cumsum(f2 * (1.0 + 0.30 * np.exp(-t / 0.008))) / sr
    shell = (0.65 * np.sin(p1) + 0.35 * np.sin(p2)) * np.exp(-t / body_decay)

    # Timbre métallique (wires) + claquement d'attaque (rim/stick snap)
    noise = rng.standard_normal(n)
    wires = _fft_filter(
        noise,
        sr=sr,
        hp_hz=wire_hp_hz,
        lp_hz=wire_lp_hz,
        peaking=[(2200.0, 1.1, 5.5), (snap_hz, 1.2, 7.5), (6200.0, 1.3, 6.0)],
    )
    wires /= max(float(np.max(np.abs(wires))), 1e-6)
    wire_env = 0.75 * np.exp(-t / wire_decay) + 0.25 * np.exp(-t / (wire_decay * 0.35))

    snap = np.sin(2.0 * math.pi * 1150.0 * t) * np.exp(-t / 0.0045) * 0.45
    snare = np.tanh(drive * (0.75 * shell + wire_level * wires * wire_env + snap))
    fade = round(0.02 * sr)
    snare[-fade:] *= np.linspace(1.0, 0.0, fade)
    norm = normalize_peak(snare, peak_target=float(params.get("peak", 0.92)), fade_in_ms=0.3, sr=sr)
    return norm, 0, 0


def synth_drum_stick(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Coup de cercle (side stick / rimshot court)."""
    dur_s = float(params.get("duration_s", 0.12))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 650))))

    f1 = float(params.get("f1_hz", 820.0))
    f2 = float(params.get("f2_hz", 2150.0))
    decay = float(params.get("decay_ms", 28.0)) * 0.001
    drive = float(params.get("drive", 2.0))

    modes = (0.55 * np.sin(2.0 * math.pi * f1 * t) + 0.45 * np.sin(2.0 * math.pi * f2 * t)) * np.exp(-t / decay)
    click = _fft_filter(rng.standard_normal(n), sr=sr, hp_hz=1500.0, lp_hz=7000.0) * np.exp(-t / 0.005)
    stick = np.tanh(drive * (modes + 0.35 * click))
    fade = round(0.015 * sr)
    stick[-fade:] *= np.linspace(1.0, 0.0, fade)
    norm = normalize_peak(stick, peak_target=float(params.get("peak", 0.88)), fade_in_ms=0.2, sr=sr)
    return norm, 0, 0


def _metallic_cymbal_matrix(t: np.ndarray, base_freqs: tuple[float, ...]) -> np.ndarray:
    """Matrice d'oscillateurs carrés inharmoniques modulés en anneau (cymbales/charleston)."""
    acc = np.zeros_like(t, dtype=np.float64)
    for idx, f in enumerate(base_freqs):
        sq = np.tanh(4.5 * np.sin(2.0 * math.pi * f * t + idx * 0.73))
        fm = np.sin(2.0 * math.pi * (f * 1.4142) * t + idx * 1.19)
        acc += sq * (0.65 + 0.35 * fm)
    return acc / len(base_freqs)


def synth_drum_hat(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Charleston rock très brillant (> 5 kHz), fermé, au pied ou ouvert."""
    dur_s = float(params.get("duration_s", 0.16))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 701))))

    decay = float(params.get("decay_ms", 48.0)) * 0.001
    hp_hz = float(params.get("hp_hz", 5200.0))
    lp_hz = float(params.get("lp_hz", 10400.0))
    ping_hz = float(params.get("ping_hz", 6800.0))
    drive = float(params.get("drive", 1.9))

    metal = _metallic_cymbal_matrix(t, (317.0, 463.0, 628.0, 839.0, 1103.0, 1489.0))
    noise = rng.standard_normal(n)
    raw = 0.45 * metal + 0.55 * noise
    bright = _fft_filter(
        raw,
        sr=sr,
        hp_hz=hp_hz,
        lp_hz=lp_hz,
        peaking=[(ping_hz, 1.3, 8.0), (8600.0, 1.5, 6.5)],
    )
    bright /= max(float(np.max(np.abs(bright))), 1e-6)
    env = 0.72 * np.exp(-t / decay) + 0.28 * np.exp(-t / max(decay * 0.25, 0.004))
    hat = np.tanh(drive * bright * env)
    fade = min(round(0.015 * sr), n // 4)
    hat[-fade:] *= np.linspace(1.0, 0.0, fade)
    norm = normalize_peak(hat, peak_target=float(params.get("peak", 0.88)), fade_in_ms=0.2, sr=sr)
    return norm, 0, 0


def synth_drum_tom(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Tom rock sec et percutant (grave, médium ou aigu)."""
    dur_s = float(params.get("duration_s", 0.34))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 801))))

    f_end = float(params.get("f_end_hz", 110.0))
    f_drop = float(params.get("f_drop_hz", 65.0))
    pitch_decay = float(params.get("pitch_decay_ms", 24.0)) * 0.001
    body_decay = float(params.get("body_decay_ms", 165.0)) * 0.001
    overtone_ratio = float(params.get("overtone_ratio", 1.58))
    overtone_level = float(params.get("overtone_level", 0.26))
    click_level = float(params.get("click_level", 0.28))
    drive = float(params.get("drive", 2.0))

    freq = f_end + f_drop * np.exp(-t / pitch_decay)
    phase = 2.0 * math.pi * np.cumsum(freq) / sr
    fundamental = np.sin(phase) * np.exp(-t / body_decay)
    overtone = np.sin(overtone_ratio * phase + 0.4) * np.exp(-t / (body_decay * 0.55)) * overtone_level

    stick = _fft_filter(rng.standard_normal(n), sr=sr, hp_hz=600.0, lp_hz=4200.0)
    stick /= max(float(np.max(np.abs(stick))), 1e-6)
    click = click_level * stick * np.exp(-t / 0.007)

    tom = np.tanh(drive * (fundamental + overtone + click))
    fade = round(0.02 * sr)
    tom[-fade:] *= np.linspace(1.0, 0.0, fade)
    norm = normalize_peak(tom, peak_target=float(params.get("peak", 0.90)), fade_in_ms=0.3, sr=sr)
    return norm, 0, 0


def synth_drum_cymbal(params: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Cymbale crash ou ride rock brillante."""
    dur_s = float(params.get("duration_s", 1.15))
    n = round(dur_s * sr)
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.Generator(np.random.PCG64(int(params.get("seed", 901))))

    decay = float(params.get("decay_ms", 420.0)) * 0.001
    bell_hz = float(params.get("bell_hz", 2650.0))
    bell_level = float(params.get("bell_level", 0.25))
    bell_decay = float(params.get("bell_decay_ms", 180.0)) * 0.001
    hp_hz = float(params.get("hp_hz", 3200.0))
    lp_hz = float(params.get("lp_hz", 10200.0))
    shimmer_hz = float(params.get("shimmer_hz", 6200.0))
    drive = float(params.get("drive", 1.85))

    metal = _metallic_cymbal_matrix(t, (271.0, 389.0, 541.0, 733.0, 997.0, 1361.0, 1847.0))
    noise = rng.standard_normal(n)
    wash = _fft_filter(
        0.50 * metal + 0.50 * noise,
        sr=sr,
        hp_hz=hp_hz,
        lp_hz=lp_hz,
        peaking=[(bell_hz, 1.6, 5.5), (shimmer_hz, 1.2, 7.5), (8400.0, 1.4, 5.0)],
    )
    wash /= max(float(np.max(np.abs(wash))), 1e-6)
    wash_env = 0.65 * np.exp(-t / decay) + 0.35 * np.exp(-t / (decay * 0.28))

    bell = (
        np.sin(2.0 * math.pi * bell_hz * t) + 0.5 * np.sin(2.0 * math.pi * (bell_hz * 1.47) * t)
    ) * np.exp(-t / bell_decay)

    cym = np.tanh(drive * (wash * wash_env + bell_level * bell))
    fade = round(0.04 * sr)
    cym[-fade:] *= np.linspace(1.0, 0.0, fade)
    norm = normalize_peak(cym, peak_target=float(params.get("peak", 0.89)), fade_in_ms=0.3, sr=sr)
    return norm, 0, 0


RECIPES = {
    "detuned_saw": synth_detuned_saw,
    "warm_pad": synth_warm_pad,
    "whistle_lead": synth_whistle_lead,
    "drum_kick": synth_drum_kick,
    "drum_snare": synth_drum_snare,
    "drum_stick": synth_drum_stick,
    "drum_hat": synth_drum_hat,
    "drum_tom": synth_drum_tom,
    "drum_cymbal": synth_drum_cymbal,
}


def synthesize_entry(entry: dict[str, Any], sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int, int]:
    """Exécute la recette procédurale déclarée dans `entry['source']`."""
    source = str(entry.get("source", ""))
    if not source.startswith("procedural:numpy:"):
        raise ValueError(f"{entry.get('id')} : source non procédurale ({source!r})")
    recipe_name = source.split(":", 2)[2]
    if recipe_name not in RECIPES:
        raise ValueError(
            f"{entry.get('id')} : recette inconnue {recipe_name!r} "
            f"(attendu l'une de {sorted(RECIPES)})"
        )
    params = dict(entry.get("synth", {}))
    params.setdefault("midi", entry.get("root_key", 60))
    return RECIPES[recipe_name](params, sr=sr)
