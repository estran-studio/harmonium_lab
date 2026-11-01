"""Tests styledist : normalisation audio, mesures symboliques, rôles MIDI."""

from __future__ import annotations

import numpy as np
import pytest

from harmonium_lab.styledist import audio as aud
from harmonium_lab.styledist import symbolic as sym
from harmonium_lab.styledist.engine import parse_bank

STEPS = 24


def test_fold_octave_ignores_half_and_double_tempo():
    # 140 contre 70 ou 280 BPM : même pulsation, à l'octave près
    assert aud.fold_octave(np.log2(70 / 140)) == pytest.approx(0.0)
    assert aud.fold_octave(np.log2(280 / 140)) == pytest.approx(0.0)
    assert aud.fold_octave(np.log2(2 ** (1 / 12))) == pytest.approx(1 / 12)


def test_score_from_z_bounds():
    assert aud.score_from_z(0.0) == 100.0
    assert aud.score_from_z(1.0) == pytest.approx(200 / 3)
    assert aud.score_from_z(3.0) == 0.0
    assert aud.score_from_z(9.0) == 0.0


def _feat(value: float, chroma_pc: int) -> dict:
    scalars = {m: value for m in aud.SCALAR_METRICS}
    chroma = [0.1] * 12
    chroma[chroma_pc] = 1.0
    return {"scalars": scalars, "chroma": chroma}


def test_scales_need_a_dispersed_context():
    with pytest.raises(ValueError, match="contexte trop petit"):
        aud.compute_scales([_feat(1, 0), _feat(2, 1)])
    with pytest.raises(ValueError, match="échelle nulle"):
        aud.compute_scales([_feat(1, 0), _feat(1, 1), _feat(1, 2)])


def test_audio_distance_is_zero_on_identity_and_grows_with_gap():
    ctx = [_feat(v, i) for i, v in enumerate((0.0, 1.0, 2.0, 3.0))]
    scales = aud.compute_scales(ctx)
    same = aud.summarize([aud.compare(ctx[0], ctx[0], scales)])
    assert same["score"] == 100.0
    near = aud.summarize([aud.compare(_feat(0.2, 0), ctx[0], scales)])["score"]
    far = aud.summarize([aud.compare(_feat(2.5, 5), ctx[0], scales)])["score"]
    assert 100.0 > near > far


def test_bc_is_total_variation_on_histograms():
    a = np.array([0.5, 0.5, 0.0])
    b = np.array([0.5, 0.0, 0.5])
    assert sym.bc(a, a) == 0.0
    assert sym.bc(a, b) == pytest.approx(0.5)
    assert sym.bc(a, np.array([0.0, 0.0, 1.0])) == pytest.approx(1.0)


def test_repeat_share_detects_the_loop_length_not_a_multiple_mismatch():
    # boucle de 4 mesures A B C D répétée : se répète à la période 4, pas à 3
    bars = {b: frozenset({"ABCD"[b % 4]}) for b in range(16)}
    assert sym.repeat_share(bars, 4) == 1.0
    assert sym.repeat_share(bars, 3) == 0.0
    assert sym.detected_period(bars) == 4
    # pas assez de mesures pour une fenêtre de 2×16
    assert sym.repeat_share(bars, 16) is None


def _write_midi(path, tempo: float = 120.0) -> None:
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    pm.time_signature_changes.append(pretty_midi.TimeSignature(12, 8, 0))
    bar = 12 / 8 * 4 * 60 / tempo  # 12/8 = 12 croches = 6 noires
    step = bar / STEPS
    drums = pretty_midi.Instrument(program=0, is_drum=True)
    for b in range(4):
        for pos, pitch in ((0, 36), (2, 38), (6, 42)):
            t = b * bar + pos * step
            drums.notes.append(pretty_midi.Note(100, pitch, t, t + step))
    pad = pretty_midi.Instrument(program=89)
    bass = pretty_midi.Instrument(program=81)
    for b in range(4):
        for pitch in (56, 60, 63):  # G# mineur sur 4 mesures, 3 voix
            pad.notes.append(pretty_midi.Note(90, pitch, b * bar, (b + 1) * bar))
        bass.notes.append(pretty_midi.Note(90, 32, b * bar, (b + 1) * bar))
    pm.instruments.extend([pad, drums, bass])
    pm.write(str(path))


def test_read_midi_assigns_roles_by_register_and_polyphony(tmp_path):
    midi = tmp_path / "t.mid"
    _write_midi(midi)
    v = sym.read_midi(midi, STEPS)
    assert {m for m, _, _ in v.bass} == {32}  # la voix la plus grave, pas la nappe
    assert set(v.chords) == {0, 1, 2, 3}
    assert set(v.chords.values()) == {8}  # G#
    assert {c for c, _ in v.drums} == {"kick", "snare", "hat"}
    grid = sym.drum_grid(v, "kick")
    assert grid[0] == 1.0 and grid.sum() == 1.0
    assert sym.drum_grid(v, "snare")[2] == 1.0


def test_symbolic_distance_zero_against_itself_and_positive_on_shift(tmp_path):
    midi = tmp_path / "t.mid"
    _write_midi(midi)
    v = sym.read_midi(midi, STEPS)
    loops = {"bass": [], "drums": [], "chords": []}
    same = sym.generated_metrics(v, v, loops)["d"]
    assert same["bass_pc"] == 0.0 and same["drums_any"] == 0.0 and same["chord_roots"] == 0.0
    assert same["loop_bass"] is None  # pas de boucle de référence : non scoré
    shifted = sym.Voices(STEPS, [(m + 1, s, n) for m, s, n in v.bass],
                         [(c, p + 1) for c, p in v.drums], {b: (r + 1) % 12 for b, r in v.chords.items()})
    d = sym.generated_metrics(shifted, v, loops)["d"]
    assert d["bass_pc"] == 1.0 and d["drums_any"] == 1.0 and d["chord_roots"] == 1.0


def test_parse_bank_defaults_percussion_to_main_bank():
    b = parse_bank("x=/tmp/a.sf2")
    assert b.label == "x" and b.percussion_soundfont == b.soundfont
    assert parse_bank("x=/tmp/a.sf2,/tmp/f.sf2").percussion_soundfont.name == "f.sf2"
    with pytest.raises(ValueError):
        parse_bank("sans-egal")
