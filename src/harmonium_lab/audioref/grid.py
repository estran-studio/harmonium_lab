"""Grille rythmique d'un enregistrement : pulsation, tatum, mesure, premier temps.

Méthode (générique, aucun style supposé) :

1. *Pulsation* : `librosa.beat.beat_track` puis régression linéaire des temps
   détectés (tempo constant, typique d'une musique séquencée).
2. *Tatum* : parmi les divisions binaire (P/2, P/4) et ternaire (P/3) de la
   pulsation P, celle où les attaques se concentrent le plus (longueur du
   vecteur moyen des phases, « cohérence » R). Ternaire → mètre composé.
3. *Mesure* : pic d'autocorrélation de l'enveloppe d'attaques entre
   `bar_min_s` et `bar_max_s`, arrondi à un multiple de la pulsation.
4. *Premier temps* : décalage (en tatums) qui maximise, replié sur la
   mesure, la nouveauté harmonique (chroma) et les attaques graves.

Chaque étape expose ses scores pour que le compte rendu dise quand le choix
est ambigu ; toutes les valeurs sont remplaçables par argument.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

SR = 22050
HOP = 128


@dataclass
class Grid:
    beat_s: float            # pulsation (noire, ou noire pointée si composé)
    tatum_s: float           # plus petite division régulière (croche)
    tatums_per_beat: int     # 2 (simple) ou 3 (composé)
    beats_per_bar: int
    origin_s: float          # premier temps de la mesure 0
    duration_s: float
    scores: dict = field(default_factory=dict)

    @property
    def bar_s(self) -> float:
        return self.beat_s * self.beats_per_bar

    @property
    def tatums_per_bar(self) -> int:
        return self.tatums_per_beat * self.beats_per_bar

    @property
    def compound(self) -> bool:
        return self.tatums_per_beat == 3

    @property
    def bpm(self) -> float:
        """Pulsation par minute (noire pointée si composé)."""
        return 60.0 / self.beat_s

    @property
    def quarter_bpm(self) -> float:
        """Tempo à la noire (convention du moteur et du MIDI)."""
        return 60.0 / (self.tatum_s * 2)

    @property
    def meter(self) -> str:
        if self.compound:
            return f"{self.beats_per_bar * 3}/8"
        return f"{self.beats_per_bar}/4"

    @property
    def n_bars(self) -> int:
        return max(0, int(np.floor((self.duration_s - self.origin_s) / self.bar_s + 1e-6)))

    def bar_start(self, bar: int) -> float:
        return self.origin_s + bar * self.bar_s

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(bar_s=round(self.bar_s, 5), meter=self.meter, bpm=round(self.bpm, 3),
                 quarter_bpm=round(self.quarter_bpm, 3), n_bars=self.n_bars)
        for k in ("beat_s", "tatum_s", "origin_s", "duration_s"):
            d[k] = round(d[k], 5)
        return d


def onset_envelope(y: np.ndarray, sr: int = SR, hop: int = HOP) -> np.ndarray:
    import librosa

    return librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)


def onset_times(y: np.ndarray, sr: int = SR, hop: int = HOP) -> np.ndarray:
    import librosa

    return librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop, units="time", delta=0.03, wait=3)


def fit_beat(y: np.ndarray, sr: int = SR, hop: int = HOP, start_bpm: float = 120.0) -> tuple[float, float, float]:
    """(période de pulsation s, phase s, écart-type des résidus s) par régression."""
    import librosa

    env = onset_envelope(y, sr, hop)
    _, beats = librosa.beat.beat_track(onset_envelope=env, sr=sr, hop_length=hop,
                                       start_bpm=start_bpm, tightness=400)
    times = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
    if len(times) < 4:
        raise ValueError("pas assez de temps détectés pour estimer le tempo")
    n = np.arange(len(times))
    period, phase = np.polyfit(n, times, 1)
    resid = times - (period * n + phase)
    return float(period), float(phase % period), float(resid.std())


def coherence(onsets: np.ndarray, period: float) -> tuple[float, float]:
    """(R, phase) : concentration des attaques sur les multiples de `period`."""
    if len(onsets) == 0:
        return 0.0, 0.0
    z = np.exp(2j * np.pi * onsets / period).mean()
    return float(abs(z)), float((np.angle(z) / (2 * np.pi)) % 1.0 * period)


def choose_tatum(onsets: np.ndarray, beat_s: float) -> tuple[int, float, dict]:
    """Division de la pulsation (2, 3 ou 4) la plus cohérente → (tatums/pulsation, phase, scores).

    Une pulsation divisée en 4 est ramenée à 2 tatums de croche : le tatum
    de la grille reste la croche, la double-croche est la sous-division de
    transcription.
    """
    scores = {}
    for k in (2, 3, 4):
        r, ph = coherence(onsets, beat_s / k)
        scores[k] = (r, ph)
    best = max(scores, key=lambda k: scores[k][0])
    k = 2 if best == 4 else best
    r, ph = scores[k]
    return k, ph, {f"R_beat/{k}": round(v[0], 4) for k, v in scores.items()}


def bar_period(env: np.ndarray, beat_s: float, sr: int = SR, hop: int = HOP,
               bar_min_s: float = 1.0, bar_max_s: float = 4.5, max_beats: int = 8) -> tuple[int, dict]:
    """Nombre de pulsations par mesure : meilleur pic d'autocorrélation aux multiples de la pulsation."""
    e = env - env.mean()
    ac = np.correlate(e, e, "full")[len(e) - 1:]
    ac = ac / (ac[0] + 1e-12)
    dt = hop / sr
    scores = {}
    for n in range(2, max_beats + 1):
        lag = n * beat_s
        if not bar_min_s <= lag <= bar_max_s:
            continue
        i = int(round(lag / dt))
        lo, hi = max(0, i - 3), min(len(ac), i + 4)
        scores[n] = float(ac[lo:hi].max())
    if not scores:
        raise ValueError("aucune longueur de mesure candidate dans la plage demandée")
    best = max(scores, key=scores.get)
    # une mesure double d'une meilleure mesure courte n'est retenue que si nettement meilleure
    for n in sorted(scores):
        if best % n == 0 and n < best and scores[n] >= scores[best] - 0.05:
            best = n
            break
    return best, {f"ac_{n}_beats": round(v, 4) for n, v in scores.items()}


def downbeat_offset(tatum_s: float, tatum_phase: float, tatums_per_bar: int, tatums_per_beat: int,
                    chroma_novelty: tuple[np.ndarray, np.ndarray] | None,
                    low_onsets: tuple[np.ndarray, np.ndarray] | None) -> tuple[float, dict]:
    """Origine du premier temps : offset (multiple de pulsation) maximisant changement harmonique + graves.

    `chroma_novelty`, `low_onsets` : (temps, valeurs). Chaque courbe est
    repliée sur la mesure aux positions de pulsation puis centrée-réduite.
    """
    bar_s = tatum_s * tatums_per_bar
    n_beats = tatums_per_bar // tatums_per_beat
    total = np.zeros(n_beats)
    detail = {}
    for name, curve in (("chroma_novelty", chroma_novelty), ("low_onsets", low_onsets)):
        if curve is None:
            continue
        t, v = curve
        prof = np.zeros(n_beats)
        for b in range(n_beats):
            start = tatum_phase + b * tatums_per_beat * tatum_s
            pos = np.mod(t - start, bar_s)
            near = (pos < tatum_s * 0.5) | (pos > bar_s - tatum_s * 0.5)
            prof[b] = v[near].mean() if near.any() else 0.0
        z = (prof - prof.mean()) / (prof.std() + 1e-12)
        detail[name] = [round(float(x), 3) for x in z]
        total += z
    best = int(np.argmax(total)) if total.any() else 0
    detail["total"] = [round(float(x), 3) for x in total]
    origin = (tatum_phase + best * tatums_per_beat * tatum_s) % bar_s
    return origin, detail


def chroma_novelty(y: np.ndarray, sr: int = SR, hop: int = 512) -> tuple[np.ndarray, np.ndarray]:
    import librosa

    ch = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    ch = ch / (np.linalg.norm(ch, axis=0, keepdims=True) + 1e-9)
    # nouveauté : 1 − cos entre fenêtres de ~0,25 s avant/après
    w = max(1, int(0.25 * sr / hop))
    nov = np.zeros(ch.shape[1])
    for i in range(w, ch.shape[1] - w):
        a = ch[:, i - w:i].mean(1)
        b = ch[:, i:i + w].mean(1)
        nov[i] = 1 - float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
    return librosa.times_like(nov, sr=sr, hop_length=hop), nov


def low_onset_curve(y: np.ndarray, sr: int = SR, hop: int = HOP, fmax: float = 150.0) -> tuple[np.ndarray, np.ndarray]:
    import librosa

    X = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    fr = librosa.fft_frequencies(sr=sr, n_fft=2048)
    e = np.log1p(10 * X[fr < fmax].sum(0))
    d = np.maximum(0, np.diff(e, prepend=e[0]))
    return librosa.times_like(d, sr=sr, hop_length=hop), d


def estimate_grid(rhythm: np.ndarray, harmonic: np.ndarray | None = None, low: np.ndarray | None = None,
                  sr: int = SR, *, beat_s: float | None = None, tatums_per_beat: int | None = None,
                  beats_per_bar: int | None = None, origin_s: float | None = None,
                  start_bpm: float = 120.0) -> Grid:
    """Grille complète. `rhythm` : signal pour les attaques (mixage ou batterie) ;
    `harmonic` : signal pour la nouveauté harmonique ; `low` : signal grave (basse/grosse caisse).
    Les arguments nommés imposent une valeur au lieu de l'estimer."""
    scores: dict = {}
    duration = len(rhythm) / sr
    if beat_s is None:
        beat_s, _, resid = fit_beat(rhythm, sr, start_bpm=start_bpm)
        scores["beat_fit_resid_ms"] = round(resid * 1000, 1)
    onsets = onset_times(rhythm, sr)
    if tatums_per_beat is None:
        tatums_per_beat, phase, s = choose_tatum(onsets, beat_s)
        scores.update(s)
    else:
        _, phase = coherence(onsets, beat_s / tatums_per_beat)
    tatum_s = beat_s / tatums_per_beat
    if beats_per_bar is None:
        beats_per_bar, s = bar_period(onset_envelope(rhythm, sr), beat_s, sr)
        scores.update(s)
    if origin_s is None:
        nov = chroma_novelty(harmonic, sr) if harmonic is not None else None
        lo = low_onset_curve(low, sr) if low is not None else None
        origin_s, s = downbeat_offset(tatum_s, phase, tatums_per_beat * beats_per_bar, tatums_per_beat, nov, lo)
        scores["downbeat"] = s
    return Grid(beat_s=beat_s, tatum_s=tatum_s, tatums_per_beat=tatums_per_beat,
                beats_per_bar=beats_per_bar, origin_s=origin_s, duration_s=duration, scores=scores)
