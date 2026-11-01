"""Tests de `harmonium_lab.backing.timing` : pistes JTD SYNTHÉTIQUES seulement (aucun brut)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pytest

from harmonium_lab.backing import corpus_cache, timing
from harmonium_lab.backing.timing import PREFIX, Track

NAN_METADATA = """{
    "fname": "t1", "time_signature": 4, "tempo": 150.0, "recording_year": "1961",
    "rating_bass_audio": NaN, "rating_mix": 3.0, "rating_comments": NaN,
    "musicians": {"pianist": "P", "bassist": "B", "drummer": "D"}
}"""


def fmt(values) -> str:
    return "\n".join("" if v is None else f"{v:.4f}" for v in values)


def synthetic_files(*, tempo=150.0, ratio=0.65, n_bars=16, bass_lag=(0.02, 0.02, 0.02, 0.02), piano_lag=0.03,
                    bass_noise=0.0, drop_bass_every=0, piano_bars=None, bass_extra=False,
                    time_signature=4) -> dict[str, str]:
    """Une piste : temps réguliers, batterie sur le temps + croche retardée au rapport `ratio`,
    basse en retard de `bass_lag[temps]` s, piano en retard de `piano_lag` s."""
    beat = 60.0 / tempo
    n = 4 * n_bars + 1
    beats = [i * beat for i in range(n)]
    metre = [i % 4 + 1 for i in range(n)]
    sign = 1.0
    rows = ["" + ",beats,piano,bass,drums,metre_auto"]
    for i, t in enumerate(beats):
        sign = -sign
        bass = t + bass_lag[i % 4] + sign * bass_noise
        bass_cell = "" if drop_bass_every and i % drop_bass_every == 0 else f"{bass:.4f}"
        rows.append(f"{i},{t:.4f},{t + piano_lag:.4f},{bass_cell},{t:.4f},{metre[i]:.1f}")
    drums = []
    for i, t in enumerate(beats[:-1]):
        drums.append(t)
        if i % 2 == 1:
            drums.append(t + ratio * beat)
    bass_on = [t + bass_lag[i % 4] for i, t in enumerate(beats[:-1])]
    if bass_extra:
        bass_on += [t + 0.5 * beat for t in beats[:-1:4]]
    piano_limit = 4 * (piano_bars if piano_bars is not None else n_bars)
    piano = []
    for i, t in enumerate(beats[:-1]):
        if i < piano_limit:
            piano.append(t + piano_lag)
            if i % 2 == 1:
                piano.append(t + ratio * beat + piano_lag)
    meta = (NAN_METADATA.replace('"fname": "t1"', f'"fname": "TRACK"').replace("150.0", str(tempo))
            .replace('"time_signature": 4', f'"time_signature": {time_signature}'))
    return {"beats.csv": "\n".join(rows) + "\n", "drums_onsets.csv": fmt(drums) + "\n",
            "bass_onsets.csv": fmt(sorted(bass_on)) + "\n", "piano_onsets.csv": fmt(piano) + "\n",
            "metadata.json": meta}


def make_archive(path: Path, tracks: dict[str, dict]) -> None:
    with zipfile.ZipFile(path, "w") as z:
        for fname, kwargs in tracks.items():
            files = synthetic_files(**kwargs)
            files["metadata.json"] = files["metadata.json"].replace("TRACK", fname)
            for name, text in files.items():
                z.writestr(f"{PREFIX}{fname}/{name}", text)
            z.writestr(f"{PREFIX}{fname}/piano_midi.mid", b"MThd jamais lu")


def read_single(tmp_path: Path, **kwargs) -> Track:
    path = tmp_path / "jtd.zip"
    make_archive(path, {"t1": kwargs})
    with zipfile.ZipFile(path) as z:
        return timing.read_track(z, "t1")


# ---------------------------------------------------------------- lecture


def test_metadata_avec_nan_non_standard():
    meta = timing.parse_metadata(NAN_METADATA)
    assert meta["rating_bass_audio"] is None and meta["rating_mix"] == 3.0
    assert meta["musicians"]["drummer"] == "D"
    row = timing.manifest_row(meta, 0.8, 100)
    assert row["licence"] == "MIT" and row["year"] == 1961
    assert row["ratings"] == {"mix": 3.0}  # les NaN ne sont pas gardés
    assert row["bass_drums_paired_share"] == 0.8


def test_filtre_de_signature_et_de_tempo():
    ok = {"time_signature": 4, "tempo": 200.0}
    assert timing.keep_track(ok)
    assert not timing.keep_track({**ok, "time_signature": 3})
    assert not timing.keep_track({**ok, "tempo": 59.9})
    assert not timing.keep_track({**ok, "tempo": 330.5})
    assert not timing.keep_track({"time_signature": 4, "tempo": None})
    assert timing.keep_track({**ok, "tempo": 60.0}) and timing.keep_track({**ok, "tempo": 330.0})


def test_tranches_de_tempo():
    assert timing.tempo_bin(100.0) == "100-125"
    assert timing.tempo_bin(124.99) == "100-125"
    assert timing.tempo_bin(125.0) == "125-150"
    assert timing.tempo_bin(199.9) == "175-200"
    assert timing.tempo_bin(275.0) == "275-330"
    assert timing.tempo_bin(329.9) == "275-330"
    assert timing.tempo_bin(99.9) is None
    assert timing.BIN_LABELS[0] == "100-125" and len(timing.BIN_LABELS) == 8


def test_sha256_ou_md5_errones_refuses(tmp_path):
    bad = tmp_path / "jtd.zip"
    bad.write_bytes(b"pas la bonne archive")
    with pytest.raises(corpus_cache.DigestError, match="SHA256 différent"):
        timing.open_archive(bad)
    with pytest.raises(FileNotFoundError):
        timing.open_archive(tmp_path / "absent.zip")


# ---------------------------------------------------------------- rapport de swing


@pytest.mark.parametrize("ratio", [0.5, 0.6, 0.67, 0.75])
def test_rapport_de_swing_a_r_connu(tmp_path, ratio):
    track = read_single(tmp_path, ratio=ratio)
    for inst in ("drums",):
        ratios, n_intervals, n_with = timing.swing_observations(track.beats, track.onsets[inst])
        assert np.median(ratios) == pytest.approx(ratio, abs=1e-3)
        assert n_intervals == 64
        assert n_with == 32  # une croche retardée un temps sur deux
    stats = timing.track_stats(track)
    assert stats.drums_ratio == pytest.approx(ratio, abs=1e-3)
    block = timing.swing_block([stats], "drums")
    assert block["ratio"]["p50"] == pytest.approx(ratio, abs=1e-3)
    assert block["long_short"]["p50"] == pytest.approx(ratio / (1 - ratio), abs=0.01)
    assert block["share_intervals_with_attack"]["p50"] == pytest.approx(0.5)


def test_rapport_long_court():
    assert timing.long_short(0.5) == pytest.approx(1.0)
    assert timing.long_short(2 / 3) == pytest.approx(2.0)


def test_intervalle_irregulier_ecarte():
    beats = np.array([0.0, 0.4, 0.8, 1.2, 2.4, 2.8, 3.2, 3.6])  # trou : intervalle 1,2 s
    onsets = np.array([0.4 + 0.26, 1.2 + 0.6, 2.8 + 0.26])  # le 2ᵉ tombe dans l'intervalle écarté
    ratios, n_intervals, n_with = timing.swing_observations(beats, onsets)
    assert n_intervals == 6 and n_with == 2
    assert ratios == pytest.approx([0.65, 0.65], abs=1e-6)


# ---------------------------------------------------------------- placement


def test_ecarts_relatifs_en_ms_et_en_pas(tmp_path):
    track = read_single(tmp_path, tempo=150.0, bass_lag=(0.02,) * 4, piano_lag=0.03)
    stats = timing.track_stats(track)
    step_s = 60.0 / 150.0 / 4  # 0,1 s
    d_steps, d_ms, _ = stats.placements["rel_bass_drums"]
    assert np.allclose(d_ms, 20.0, atol=0.1) and np.allclose(d_steps, 0.2, atol=0.001)
    assert np.allclose(stats.placements["rel_piano_drums"][1], 30.0, atol=0.1)
    assert np.allclose(stats.placements["rel_piano_drums"][0], 0.3, atol=0.001)
    assert np.allclose(stats.placements["rel_bass_piano"][1], -10.0, atol=0.1)
    assert np.allclose(stats.placements["abs_drums"][1], 0.0, atol=0.1)  # batterie = temps ici
    assert step_s == pytest.approx(track.step_s)
    # Négatif = en avance : la basse devance le piano.
    assert np.allclose(stats.placements["rel_bass_piano"][0], -0.1, atol=0.001)


def test_placement_par_temps_1_3_et_2_4(tmp_path):
    track = read_single(tmp_path, bass_lag=(0.01, 0.03, 0.01, 0.03))
    stats = timing.track_stats(track)
    section = timing.placement_section([stats])["relative"]["bass_minus_drums"]["all"]
    assert section["beats_1_3"]["pooled_ms"]["p50"] == pytest.approx(10.0, abs=0.1)
    assert section["beats_2_4"]["pooled_ms"]["p50"] == pytest.approx(30.0, abs=0.1)
    assert section["beat_2"]["pooled_steps"]["p50"] == pytest.approx(0.3, abs=0.001)
    assert section["all"]["pooled_steps"]["n"] == 65  # tous les temps appariés (65 lignes)
    assert section["all"]["per_track_median_ms"]["n"] == 1
    bin_label = timing.tempo_bin(150.0)
    assert timing.placement_section([stats])["relative"]["bass_minus_drums"][bin_label]["all"]["pooled_ms"]["n"] == 65


def test_dispersion_par_piste_en_pas(tmp_path):
    track = read_single(tmp_path, bass_noise=0.01)  # basse à 0,02 ± 0,01 s en alternance
    stats = timing.track_stats(track)
    block = timing.jitter_block([stats], "rel_bass_drums")
    assert block["n_tracks"] == 1
    assert block["std_ms"]["p50"] == pytest.approx(10.0, abs=0.3)
    assert block["std_steps"]["p50"] == pytest.approx(0.1, abs=0.005)
    assert 0.0 <= block["robust_std_steps"]["p50"] <= block["std_steps"]["p50"] + 1e-9
    # Piste trop courte pour une dispersion (moins de 30 paires) : ignorée.
    short = timing.track_stats(read_single(tmp_path, n_bars=2, bass_noise=0.01))
    assert timing.jitter_block([short], "rel_bass_drums")["n_tracks"] == 0


# ---------------------------------------------------------------- rythme du piano et basse


def test_rythme_du_piano_par_mesure(tmp_path):
    track = read_single(tmp_path, ratio=0.65, piano_bars=8)  # piano muet sur les 8 dernières mesures
    stats = timing.track_stats(track)
    block = timing.piano_rhythm_block([stats], {"t1": 0.65})
    assert block["n_measures"] == 16
    prob = [s["prob"] for s in block["prob_by_step"]]
    assert prob[0] == pytest.approx(0.5) and prob[4] == pytest.approx(0.5)
    assert prob[6] == pytest.approx(0.5) and prob[14] == pytest.approx(0.5)  # croche swinguée = pas 6 et 14
    assert prob[2] == 0 and prob[1] == 0 and prob[15] == 0
    assert block["share_step_14"] == pytest.approx(0.5)
    assert block["share_step_10"] == 0
    assert block["share_silent_measures"] == pytest.approx(0.5)
    assert block["n_silent_measures"] == 8
    assert block["attacks_per_measure"]["p50"] == pytest.approx(3.0)  # moitié à 6 attaques, moitié à 0
    assert block["attacks_per_measure"]["p90"] == pytest.approx(6.0)


def test_swing_triolet_du_piano_au_pas_10_quand_le_contretemps_est_au_pas_2(tmp_path):
    # La croche retardée tombe après les temps 2 et 4 : pas 6 et 14, jamais 2 ni 10.
    track = read_single(tmp_path, ratio=2 / 3)
    block = timing.piano_rhythm_block([timing.track_stats(track)], {"t1": 2 / 3})
    probs = {s["step"]: s["prob"] for s in block["prob_by_step"]}
    assert probs[6] == probs[14] == 1.0 and probs[10] == probs[2] == 0.0


def test_mesure_irreguliere_ecartee(tmp_path):
    track = read_single(tmp_path, n_bars=4)
    track.metre[6] = 1.0  # pointage incohérent : les mesures qui contiennent ce temps tombent
    rows = timing.measure_rows(track)
    assert (rows[:4] == 0).all() and (rows[4:8] == -1).all()
    assert (rows[12:16] == 12).all()


def test_basse_hors_pulsation(tmp_path):
    track = read_single(tmp_path, bass_extra=True)  # une note à mi-temps par mesure
    block = timing.bass_offbeat_block([timing.track_stats(track)])
    assert block["n_onsets"] == 64 + 16
    assert block["n_off_beat"] == 16
    assert block["share_off_beat"] == pytest.approx(0.2)
    assert block["onsets_per_beat_per_track"]["p50"] == pytest.approx(80 / 64)
    plain = timing.bass_offbeat_block([timing.track_stats(read_single(tmp_path))])
    assert plain["n_off_beat"] == 0


# ---------------------------------------------------------------- archive complète


def tracks_for_archive() -> dict[str, dict]:
    tracks = {}
    for i in range(3):
        tracks[f"slow{i}"] = {"tempo": 110.0 + i, "ratio": 0.7}
        tracks[f"fast{i}"] = {"tempo": 260.0 + i, "ratio": 0.58, "bass_lag": (0.0, 0.0, 0.0, 0.0), "piano_lag": 0.0}
    tracks["waltz"] = {"tempo": 150.0, "time_signature": 3}
    tracks["fast_tempo_out"] = {"tempo": 400.0}
    tracks["sparse"] = {"tempo": 150.0, "drop_bass_every": 2}  # appariement basse ≈ 50 % : écartée
    return tracks


def test_pipeline_filtre_tranches_et_mapping_moteur(tmp_path):
    path = tmp_path / "jtd.zip"
    make_archive(path, tracks_for_archive())
    with zipfile.ZipFile(path) as z:
        stats, counts = timing.retained_stats(z)
        names = timing.track_names(z)
    assert len(names) == 9
    assert counts == {"total": 9, "time_signature_4": 8, "tempo_in_range": 7, "paired_ok": 6, "in_bins": 6}
    assert sorted(s.track.fname for s in stats) == ["fast0", "fast1", "fast2", "slow0", "slow1", "slow2"]
    mapping = timing.engine_mapping(stats)
    by_tempo = mapping["swing_ratio_by_tempo"]
    assert by_tempo["100-125"]["ratio"] == pytest.approx(0.7, abs=1e-3) and by_tempo["100-125"]["n_tracks"] == 3
    assert by_tempo["250-275"]["ratio"] == pytest.approx(0.58, abs=1e-3)
    assert by_tempo["150-175"]["ratio"] is None
    micro = mapping["micro_timing"]
    assert set(micro) == {"Bass", "Chords", "Drums"}
    assert micro["Bass"]["offsets"]["100-125"] == pytest.approx(0.02 / (60 / 111 / 4), abs=0.05)
    assert micro["Bass"]["offsets"]["250-275"] == pytest.approx(0.0, abs=1e-6)
    assert micro["Chords"]["offsets"]["250-275"] == pytest.approx(0.0, abs=1e-6)
    assert len(micro["Bass"]["offsets_by_beat"]["all"]) == 4
    assert micro["Drums"]["offsets"]["all"] == 0.0
    # Dispersion nulle : jitter conseillé 0.
    assert micro["Bass"]["jitter"]["250-275"] == pytest.approx(0.0, abs=1e-6)


def test_jitter_conseille_borne_au_maximum_du_moteur(tmp_path):
    track = read_single(tmp_path, bass_noise=0.03)  # écart-type 0,03 s = 0,3 pas
    mapping = timing.engine_mapping([timing.track_stats(track)])
    bass = mapping["micro_timing"]["Bass"]
    assert bass["jitter_raw"]["all"] == pytest.approx(0.3, abs=0.01)
    assert bass["jitter"]["all"] == pytest.approx(0.1)
    assert mapping["engine_jitter_bounds_steps"] == [0.0, 0.1]


def test_piano_midi_jamais_lu_et_sortie_deterministe(tmp_path):
    path = tmp_path / "jtd.zip"
    make_archive(path, tracks_for_archive())

    class Recording(zipfile.ZipFile):
        reads: list[str] = []

        def read(self, name, pwd=None):
            Recording.reads.append(name if isinstance(name, str) else name.filename)
            return super().read(name, pwd)

    outputs = []
    for _ in range(2):
        with Recording(path) as z:
            outputs.append(corpus_cache.dumps_json(timing.build_measures(z)))
    assert outputs[0] == outputs[1]
    assert Recording.reads and not any(n.endswith("piano_midi.mid") for n in Recording.reads)
    import json
    data = json.loads(outputs[0])
    prov = data["provenance"]
    assert prov["licence"] == "MIT" and prov["sha256"] == timing.SOURCE_SHA256
    assert prov["counts"]["n_tracks_retained"] == 6 and prov["counts"]["n_tracks_dropped_paired_share"] == 1
    assert data["filter"]["tracks_per_bin"]["100-125"] == 3
    assert "100-125" in data["filter"]["bins_below_min"]  # 3 pistes < 30 : déclaré
    assert data["caveats"] and "RELATIFS" in " ".join(data["caveats"])
    assert data["command"].startswith("python -m harmonium_lab.backing.timing")
    assert data["piano_rhythm"]["by_bin"]["all"]["n_measures"] > 0
