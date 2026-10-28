"""Tests audioref : mesures, structure et transcription sur signaux synthétiques."""

from __future__ import annotations

import numpy as np
import pytest

from harmonium_lab.audioref.grid import Grid, coherence
from harmonium_lab.audioref.measures import match_mode
from harmonium_lab.audioref.structure import loop_scores, self_similarity

SR = 22050


def _tone(midi: int, dur: float, amp: float = 0.4) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    return (amp * np.sin(2 * np.pi * 440.0 * 2 ** ((midi - 69) / 12) * t)).astype(np.float32)


def _click_train(period: float, dur: float) -> np.ndarray:
    y = np.zeros(int(dur * SR), dtype=np.float32)
    for t in np.arange(0.0, dur, period):
        y[int(t * SR)] = 1.0
    return y


def _grid() -> Grid:
    return Grid(beat_s=0.5, tatum_s=0.25, tatums_per_beat=2, beats_per_bar=4,
                origin_s=0.0, duration_s=8.0, scores={})


A_PHYR = [57, 58, 60, 62, 64, 65, 67]  # A phrygien une octave


def test_match_mode_phrygian():
    y = sum(_tone(m, 1.0) for m in A_PHYR)
    import librosa

    ch = librosa.feature.chroma_cqt(y=y, sr=SR).mean(axis=1)
    got = match_mode(ch, tonic_pc=9)  # tonique A : départage les relatifs
    assert got["tonic"] == "A"
    assert got["mode"] == "phrygian"


def test_match_mode_major_margin():
    y = sum(_tone(m, 1.0) for m in [60, 62, 64, 65, 67, 69, 71])  # gamme C majeur
    import librosa

    ch = librosa.feature.chroma_cqt(y=y, sr=SR).mean(axis=1)
    got = match_mode(ch)
    assert (got["tonic"], got["mode"]) == ("C", "major")
    assert got["margin"] >= 0.0  # relatifs à égalité : la marge peut être nulle


# --- structure ------------------------------------------------------------

def test_loop_scores_finds_period():
    rng = np.random.default_rng(7)
    base = rng.normal(size=(12, 4))
    base /= np.linalg.norm(base, axis=0, keepdims=True)
    mat = np.concatenate([base, base, base], axis=1)  # boucle de 4 mesures ×3
    sim = self_similarity(mat)
    scores = loop_scores(sim, range(1, 9))
    assert max(scores, key=lambda L: scores[L]["score"]) == 4
    assert scores[4]["score"] > 0.15


def test_coherence_marks_periodic_onsets():
    onsets = np.arange(0.0, 8.0, 0.5)
    r, _ = coherence(onsets, 0.5)
    r2, _ = coherence(onsets, 0.37)
    assert r > 0.9 > r2


# --- transcription ---------------------------------------------------------

def test_pitch_notes_pedal():
    from harmonium_lab.audioref.transcribe import pitch_notes, sixteenth_s

    g = _grid()
    y = _tone(33, 4.0)  # A1 tenue, 8 mesures de 0,5 s... 4 s = 2 mesures
    notes, info = pitch_notes(y, SR, g, "bass")
    assert info["voiced_ratio"] > 0.9
    assert notes and notes[0]["midi"] == 33
    assert sixteenth_s(g) == pytest.approx(0.125)


def test_drum_hits_classify_synth():
    from harmonium_lab.audioref.transcribe import drum_hits

    t = np.arange(int(0.3 * SR)) / SR
    kick = (np.sin(2 * np.pi * 55 * t) * np.exp(-t * 18)).astype(np.float32)
    y = np.zeros(2 * SR, dtype=np.float32)
    y[int(0.5 * SR): int(0.5 * SR) + len(kick)] = kick  # pas à t=0 : pas de front montant
    rng = np.random.default_rng(3)
    hat = (rng.standard_normal(int(0.05 * SR)) * np.exp(-np.arange(int(0.05 * SR)) / (0.008 * SR))).astype(np.float32)
    try:
        from scipy.signal import butter, sosfilt

        sos = butter(6, 6000, btype="high", fs=SR, output="sos")
        hat = sosfilt(sos, hat).astype(np.float32)
    except ImportError:
        pass
    y[int(1.0 * SR): int(1.0 * SR) + len(hat)] = hat * 2.0
    hits, _info = drum_hits(y, SR, _grid(), delta=0.05)
    by_time = sorted(hits, key=lambda h: h["time_s"])
    assert by_time and by_time[0]["class"] == "kick"
    assert by_time[-1]["class"] == "hat"


def test_chords_per_bar_major_triad():
    from harmonium_lab.audioref.transcribe import chords_per_bar

    g = _grid()
    bar = sum(_tone(m, 2.0) for m in [48, 52, 55])  # C3 E3 G3 simultanés
    chords, _info = chords_per_bar(bar, g)
    assert chords[0]["root"] == "C" and chords[0]["quality"] == "maj"


def test_degrees_relative_to_tonic():
    from harmonium_lab.audioref.transcribe import to_degrees

    assert to_degrees(32, 8) == {"semitones": 0, "octave": 1}  # G#1 sur tonique G#
    assert to_degrees(33, 8) == {"semitones": 1, "octave": 1}  # A1 = b2 phrygien


def test_select_accepts_alternatives():
    from harmonium_lab.audioref.manifest import parse_filters, select

    rows = [{"id": "a", "type": "zone"}, {"id": "b", "type": "zone"}, {"id": "c", "type": "boss"}]
    got = select(rows, parse_filters(["id=a|c", "type=zone"]))
    assert [r["id"] for r in got] == ["a"]


def test_audioref_loops_multi_part_spec(tmp_path, monkeypatch):
    """Une boucle « nom:début:fin:partie1,partie2 » doit écrire toutes les
    parties demandées (régression : la liste non découpée produisait un
    MIDI silencieux)."""
    import argparse
    import wave
    import json
    import numpy as np

    sr = 22050
    bar = 2.0
    t = np.arange(int(6 * bar * sr)) / sr
    bass = (0.4 * np.sin(2 * np.pi * 110.0 * t)).astype(np.float32)
    drums = np.zeros_like(bass)
    for k in range(int(6 * bar / 0.5)):
        drums[int(k * 0.5 * sr)] = 1.0
    mix = bass + drums

    def _wav(path, sig):
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes((sig * 20000).astype("<i2").tobytes())

    stems = tmp_path / "stems"
    stems.mkdir()
    _wav(stems / "bass.wav", bass)
    _wav(stems / "drums.wav", drums)
    _wav(tmp_path / "mix.wav", mix)

    from harmonium_lab.cli import cmd_audioref_loops

    args = argparse.Namespace(
        track=str(tmp_path / "mix.wav"), stems=str(stems), track_id="t",
        grid=json.dumps({"beat_s": 0.5, "tatums_per_beat": 2, "beats_per_bar": 4,
                         "origin_s": 0.0}),
        tonic="A", loop=["boucle:0:1:bass,drums"], bass_prog=32, lead_prog=81,
        pad_prog=88, parts=None, soundfont=None, no_render=True,
        out=str(tmp_path / "out"))
    assert cmd_audioref_loops(args) == 0
    import mido
    mid = mido.MidiFile(str(tmp_path / "out" / "t_boucle.mid"))
    played = sum(1 for track in mid.tracks for msg in track
                 if msg.type == "note_on" and msg.velocity > 0)
    assert played > 1, "la boucle multi-parties est vide"
