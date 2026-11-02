"""Tests de `harmonium_lab.backing.swing_tempo` : pistes JTD SYNTHÉTIQUES seulement (aucun brut)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from harmonium_lab.backing import corpus_cache, swing_tempo as st, timing
from harmonium_lab.backing.timing import PREFIX


FULL_RESAMPLES = (st.BOOTSTRAP_MEDIAN, st.BOOTSTRAP_CURVE)


@pytest.fixture(autouse=True)
def fewer_resamples(monkeypatch):
    """Rééchantillons réduits (vitesse) ; les tests qui vérifient le déterminisme complet restaurent les vrais."""
    monkeypatch.setattr(st, "BOOTSTRAP_MEDIAN", 300)
    monkeypatch.setattr(st, "BOOTSTRAP_CURVE", 200)


def fmt(values) -> str:
    return "\n".join(f"{v:.6f}" for v in values)


def synthetic_files(*, tempo=150.0, ratio=0.65, n_bars=16, bass_lag=(0.02,) * 4, piano_lag=0.03, bass_ratio=None,
                    drummer="D0", bassist="B0", pianist="P0", time_signature=4, drop_bass_every=0) -> dict[str, str]:
    """Une piste : temps réguliers, batterie sur le temps + croche retardée au rapport `ratio` (une fois
    sur deux), basse en retard de `bass_lag[temps]` s (croche au rapport `bass_ratio` si donné), piano
    en retard de `piano_lag` s au même rapport que la batterie."""
    beat = 60.0 / tempo
    n = 4 * n_bars + 1
    beats = [i * beat for i in range(n)]
    rows = [",beats,piano,bass,drums,metre_auto"]
    for i, t in enumerate(beats):
        bass = "" if drop_bass_every and i % drop_bass_every == 0 else f"{t + bass_lag[i % 4]:.6f}"
        rows.append(f"{i},{t:.6f},{t + piano_lag:.6f},{bass},{t:.6f},{i % 4 + 1:.1f}")
    drums, bass_on, piano = [], [], []
    for i, t in enumerate(beats[:-1]):
        drums.append(t)
        piano.append(t + piano_lag)
        bass_on.append(t + bass_lag[i % 4])
        if i % 2 == 1:
            drums.append(t + ratio * beat)
            piano.append(t + ratio * beat + piano_lag)
            if bass_ratio is not None:
                bass_on.append(t + bass_ratio * beat + bass_lag[i % 4])
    meta = {"fname": "TRACK", "time_signature": time_signature, "tempo": tempo, "recording_year": "1961",
            "musicians": {"pianist": pianist, "bassist": bassist, "drummer": drummer}}
    return {"beats.csv": "\n".join(rows) + "\n", "drums_onsets.csv": fmt(drums) + "\n",
            "bass_onsets.csv": fmt(sorted(bass_on)) + "\n", "piano_onsets.csv": fmt(piano) + "\n",
            "metadata.json": json.dumps(meta)}


def make_archive(path: Path, tracks: dict[str, dict]) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        for fname, kwargs in tracks.items():
            files = synthetic_files(**kwargs)
            files["metadata.json"] = files["metadata.json"].replace("TRACK", fname)
            for name, text in files.items():
                z.writestr(f"{PREFIX}{fname}/{name}", text)
            z.writestr(f"{PREFIX}{fname}/piano_midi.mid", b"MThd jamais lu")
    return path


def sweep(ratio_of_tempo, n=100, lo=110.0, hi=290.0, n_drummers=20, **kwargs) -> dict[str, dict]:
    """`n` pistes de tempos régulièrement répartis, rapport de swing `ratio_of_tempo(tempo)`, batteurs en rotation."""
    tracks = {}
    for i, tempo in enumerate(np.linspace(lo, hi, n)):
        tracks[f"t{i:03d}"] = {"tempo": float(tempo), "ratio": float(ratio_of_tempo(tempo)), "drummer": f"D{i % n_drummers}",
                               "bassist": f"B{i % 12}", "pianist": f"P{i % 9}", **kwargs}
    return tracks


def measures(tmp_path: Path, tracks: dict[str, dict]) -> dict:
    path = make_archive(tmp_path / "jtd.zip", tracks)
    with zipfile.ZipFile(path) as z:
        return json.loads(corpus_cache.dumps_json(st.build_measures(z)))


def stats_of(tmp_path: Path, tracks: dict[str, dict]):
    path = make_archive(tmp_path / "jtd.zip", tracks)
    with zipfile.ZipFile(path) as z:
        return st.read_stats(z)


# ---------------------------------------------------------------- classes et filtre


def test_bornes_des_classes_de_tempo():
    assert st.tempo_class(60.0) == "60-120" and st.tempo_class(119.99) == "60-120"
    assert st.tempo_class(120.0) == "120-180" and st.tempo_class(179.9) == "120-180"
    assert st.tempo_class(180.0) == "180-240" and st.tempo_class(240.0) == "240-330"
    assert st.tempo_class(330.0) == "240-330"  # `keep_track` accepte 330 BPM
    assert st.tempo_class(59.9) is None and st.tempo_class(330.1) is None
    assert st.CLASS_IDS == ("60-120", "120-180", "180-240", "240-330")


def test_pistes_de_60_a_100_bpm_gardees_la_ou_e7_les_ecarte(tmp_path):
    tracks = {"lent0": {"tempo": 80.0}, "lent1": {"tempo": 99.0}, "moyen": {"tempo": 150.0}}
    stats, counts = stats_of(tmp_path, tracks)
    assert counts["retained"] == 3
    assert sorted(s.bin for s in stats) == ["120-180", "60-120", "60-120"]
    with zipfile.ZipFile(tmp_path / "jtd.zip") as z:
        _, e7 = timing.retained_stats(z)
    assert e7["in_bins"] == 1  # E7 écarte les tempos < 100 : sa boucle ne convient pas ici


def test_comptes_du_filtre(tmp_path):
    tracks = {"ok": {"tempo": 150.0}, "valse": {"tempo": 150.0, "time_signature": 3}, "trop_vite": {"tempo": 400.0},
              "trop_lent": {"tempo": 40.0}, "creuse": {"tempo": 150.0, "drop_bass_every": 2}}
    stats, counts = stats_of(tmp_path, tracks)
    assert [s.track.fname for s in stats] == ["ok"]
    assert (counts["total"], counts["time_signature_4"], counts["tempo_in_range"], counts["paired_ok"]) == (5, 4, 2, 1)
    assert counts["tempo_min_archive"] == 40.0 and counts["tempo_max_archive"] == 400.0


def test_mediane_par_piste_exige_20_contretemps(tmp_path):
    stats, _ = stats_of(tmp_path, {"court": {"n_bars": 4, "ratio": 0.7},  # 8 contretemps < 20
                                   "long": {"n_bars": 16, "ratio": 0.7}})
    block = st.swing_class_block(stats, "drums", "120-180")
    assert block["n_tracks"] == 2 and block["n_tracks_measured"] == 1
    assert block["median"] == pytest.approx(0.7, abs=1e-3)


@pytest.mark.parametrize("ratio", [0.55, 0.667, 0.75])
def test_rapport_de_swing_de_la_classe(tmp_path, ratio):
    stats, _ = stats_of(tmp_path, {f"t{i}": {"tempo": 200.0 + i, "ratio": ratio, "drummer": f"D{i}"} for i in range(6)})
    block = st.swing_class_block(st.by_class(stats)["180-240"], "drums", "180-240")
    assert block["median"] == pytest.approx(ratio, abs=2e-3)
    assert block["median_long_short"] == pytest.approx(ratio / (1 - ratio), rel=1e-2)
    assert block["ci95_tracks"][0] <= ratio + 2e-3 and block["ci95_tracks"][1] >= ratio - 2e-3


# ---------------------------------------------------------------- bootstrap


def test_bootstrap_par_musicien_plus_large_que_par_piste():
    # Six musiciens, chacun a son niveau ; 20 pistes chacun, sans bruit intra-musicien.
    levels = [0.60, 0.64, 0.68, 0.72, 0.76, 0.80]
    values = np.repeat(levels, 20) + np.tile(np.linspace(-0.002, 0.002, 20), 6)
    groups = [f"m{i}" for i in range(6) for _ in range(20)]
    tracks = st.bootstrap_ci(values, st._rng("t"), 1000)
    musicians = st.bootstrap_ci_clustered(values, groups, st._rng("t"), 1000)
    assert (musicians[1] - musicians[0]) > 2.5 * (tracks[1] - tracks[0])


def test_bootstrap_degenere_et_deterministe():
    assert st.bootstrap_ci([0.7], st._rng("x"), 100) is None
    assert st.bootstrap_ci_clustered([0.7, 0.6, 0.8], ["a", "a", "a"], st._rng("x"), 100) is None  # un seul groupe
    assert st.bootstrap_ci_clustered([], [], st._rng("x"), 100) is None
    values = np.random.default_rng(0).normal(0.7, 0.03, 50)
    assert st.bootstrap_ci(values, st._rng("a"), 500) == st.bootstrap_ci(values, st._rng("a"), 500)
    assert st.bootstrap_ci(values, st._rng("a"), 500) != st.bootstrap_ci(values, st._rng("b"), 500)
    ci = st.bootstrap_ci(values, st._rng("a"), 2000)
    assert ci[0] < float(np.median(values)) < ci[1]


def test_nombre_de_reechantillons_minimal():
    assert FULL_RESAMPLES[0] >= 1000 and FULL_RESAMPLES[1] >= 1000


def test_moyenne_tronquee_ignore_les_valeurs_aberrantes():
    values = np.concatenate([np.full(48, 10.0), [500.0, -500.0]])
    ci = st.bootstrap_ci(values, st._rng("m"), 500, stat="trimmed_mean")
    assert ci[0] == pytest.approx(10.0) and ci[1] < 12.0


# ---------------------------------------------------------------- régression robuste


def test_huber_resiste_aux_valeurs_aberrantes_mieux_que_les_moindres_carres():
    x = np.linspace(100, 300, 100)
    y = 0.84 - 0.0009 * x
    y[::10] = 0.2  # 10 % d'aberrantes
    ls_slope = np.polyfit(x, y, 1)[0]
    scale = st.robust_scale("linear", x, y)
    a, b, _, _ = st.fit_model("linear", x, y, np.ones((1, 100)), scale)
    assert abs(b[0] + 0.0009) < 0.02 * 0.0009
    assert abs(ls_slope + 0.0009) > 0.1 * 0.0009  # les moindres carrés sont tirés
    assert a[0] == pytest.approx(0.84, abs=0.005)


def test_plateau_cherche_la_charniere():
    x = np.linspace(100, 300, 120)
    y = 0.72 - 0.001 * np.maximum(x - 170, 0)
    scale = st.robust_scale("plateau_linear", x, y)
    a, b, h, _ = st.fit_model("plateau_linear", x, y, np.ones((1, 120)), scale)
    assert h[0] == 170.0 and a[0] == pytest.approx(0.72, abs=1e-3) and b[0] == pytest.approx(-0.001, rel=0.02)
    assert st.hinge_candidates(np.array([100.0, 110.0, 200.0])) == []  # pas assez de pistes de chaque côté


def test_courbe_lineaire_retrouvee_avec_bornes_de_validite(tmp_path):
    data = measures(tmp_path, sweep(lambda t: 0.74 - 0.0008 * (t - 100)))
    curve = data["curve"]["drums"]
    assert curve["available"] and curve["chosen_model"] == "linear"
    assert curve["fit"]["params"]["slope_per_100_bpm"] == pytest.approx(-0.08, abs=2e-3)
    by_tempo = {p["tempo"]: p for p in curve["points"]}
    assert by_tempo[200.0]["swing_ratio"] == pytest.approx(0.74 - 0.08, abs=3e-3)
    lo, hi = by_tempo[200.0]["ci95_musicians"]
    assert lo <= by_tempo[200.0]["swing_ratio"] <= hi
    # Jamais d'extrapolation : rien sous 110 ni au-dessus de 290 BPM (tempos observés).
    for tempo in (60.0, 80.0, 100.0, 300.0, 320.0, 330.0):
        assert by_tempo[tempo]["swing_ratio"] is None and by_tempo[tempo]["status"] == "hors_plage"
    assert by_tempo[100.0]["clamp_to_bpm"] == 110.0 and by_tempo[300.0]["clamp_to_bpm"] == 290.0
    assert curve["bounds"]["tempo_min_bpm"] == pytest.approx(110.0) and curve["bounds"]["tempo_max_bpm"] == pytest.approx(290.0)
    assert curve["monotone"]["point_non_increasing"] and curve["monotone"]["share_resamples_non_increasing_musicians"] == 1.0
    assert curve["delta_120_to_240_bpm"]["value"] == pytest.approx(-0.096, abs=4e-3)
    assert curve["delta_120_to_240_bpm"]["excludes_zero_musicians"] and curve["exploitable"]
    # Aucune valeur de la table A6 hors de la plage.
    table = data["a6_table"]["curve"]["drums"]["points"]
    assert min(p["tempo"] for p in table) == 110.0 and max(p["tempo"] for p in table) == 290.0


def test_courbe_plateau_puis_decroissance_choisie_par_validation_croisee(tmp_path):
    data = measures(tmp_path, sweep(lambda t: 0.72 - 0.0009 * max(t - 160, 0), n=120))
    curve = data["curve"]["drums"]
    assert curve["chosen_model"] == "plateau_linear"
    assert curve["fit"]["params"]["hinge_bpm"] == pytest.approx(160.0, abs=10.0)
    assert curve["models"]["plateau_linear"]["cv_robust_std"] < curve["models"]["linear"]["cv_robust_std"]
    assert curve["fit"]["hinge"]["ci95_musicians"][0] <= 160.0 <= curve["fit"]["hinge"]["ci95_musicians"][1]


def test_courbe_constante_si_le_swing_ne_depend_pas_du_tempo(tmp_path):
    data = measures(tmp_path, sweep(lambda t: 0.65))
    curve = data["curve"]["drums"]
    assert curve["chosen_model"] == "constant" and not curve["exploitable"]
    assert all(p["swing_ratio"] == pytest.approx(0.65, abs=2e-3) for p in curve["points"] if p["swing_ratio"] is not None)


def test_courbe_indisponible_avec_peu_de_pistes(tmp_path):
    data = measures(tmp_path, sweep(lambda t: 0.7, n=10))
    assert data["curve"]["drums"]["available"] is False and "pistes mesurées" in data["curve"]["drums"]["reason"]
    assert data["a6_table"]["curve"]["drums"] is None


def test_courbe_de_la_basse_distincte_de_celle_de_la_batterie(tmp_path):
    tracks = sweep(lambda t: 0.72 - 0.0006 * (t - 100), bass_ratio=0.62, bass_lag=(0.0,) * 4)  # basse constante, batterie qui baisse
    data = measures(tmp_path, tracks)
    assert data["curve"]["drums"]["chosen_model"] != "constant"
    assert data["curve"]["bass"]["chosen_model"] == "constant" and not data["curve"]["bass"]["exploitable"]


# ---------------------------------------------------------------- fiabilité


def test_seuils_de_verdict():
    assert st.verdict(60, 8, 0.2, 0.01)["verdict"] == "assez"
    assert st.verdict(59, 8, 0.2, 0.01)["verdict"] == "juste"
    assert st.verdict(60, 7, 0.2, 0.01)["verdict"] == "juste"
    assert st.verdict(30, 5, 0.2)["verdict"] == "juste"
    assert st.verdict(29, 9, 0.1)["verdict"] == "trop peu"
    assert st.verdict(200, 4, 0.1)["verdict"] == "trop peu"
    assert st.verdict(0, 0, None)["verdict"] == "trop peu"
    one = st.verdict(100, 10, 0.3)
    assert one["verdict"] == "juste" and any("30%" in m for m in one["missed_for_assez"])
    wide = st.verdict(100, 10, 0.1, 0.03)
    assert wide["verdict"] == "juste" and any("IC" in m for m in wide["missed_for_assez"])
    assert st.verdict(100, 10, 0.1, 0.02)["verdict"] == "assez"


def test_un_seul_batteur_ne_donne_jamais_assez(tmp_path):
    tracks = {f"t{i}": {"tempo": 125.0 + i / 2, "ratio": 0.7, "drummer": "Seul"} for i in range(70)}
    data = measures(tmp_path, tracks)
    drums = data["classes"]["120-180"]["swing"]["drums"]
    assert drums["n_tracks_measured"] == 70 and drums["n_musicians_measured"] == 1
    assert drums["ci95_musicians"] is None  # pas de rééchantillonnage de musiciens possible
    assert data["reliability"]["swing"]["120-180"]["drums"]["verdict"] == "trop peu"
    assert data["reliability"]["swing"]["60-120"]["drums"]["verdict"] == "trop peu"  # classe vide


def test_dependance_chiffree_et_classe_la_plus_touchee(tmp_path):
    # Chaque batteur a son propre niveau de swing : les pistes d'un batteur ne sont pas indépendantes.
    tracks = {}
    for i in range(60):
        d = i % 6
        tracks[f"t{i}"] = {"tempo": 150.0 + (i % 10), "ratio": 0.60 + 0.03 * d, "drummer": f"D{d}", "bassist": f"B{i % 9}", "pianist": f"P{i % 9}"}
    data = measures(tmp_path, tracks)
    dep = data["limits"]["dependence"]
    worst = dep["most_affected_tempo_class"]
    assert worst["class"] == "120-180" and worst["instrument"] == "drums"
    assert worst["ci_width_ratio"] > 3.0 and worst["n_effective_tracks"] < 60 / 9
    rel = data["reliability"]["swing"]["120-180"]["drums"]
    assert rel["verdict"] == "juste" and "musiciens 6 < 8" in rel["missed_for_assez"]  # 6 batteurs : pas « assez »


# ---------------------------------------------------------------- micro-timing


def test_micro_timing_relatif_en_ms_en_pas_et_par_temps(tmp_path):
    tracks = {f"t{i}": {"tempo": 150.0 + i, "bass_lag": (0.01, 0.03, 0.01, 0.03), "piano_lag": 0.03,
                        "drummer": f"D{i % 4}", "bassist": f"B{i % 3}", "pianist": f"P{i % 3}"} for i in range(8)}
    data = measures(tmp_path, tracks)
    cls = data["micro_timing"]["classes"]["120-180"]
    bd = cls["relative"]["bass_minus_drums"]
    assert bd["all"]["per_track_trimmed_mean_ms"]["value"] == pytest.approx(20.0, abs=0.5)
    assert bd["beats_1_3"]["per_track_trimmed_mean_ms"]["value"] == pytest.approx(10.0, abs=0.5)
    assert bd["beats_2_4"]["per_track_trimmed_mean_ms"]["value"] == pytest.approx(30.0, abs=0.5)
    assert cls["beats_2_4_minus_1_3"]["bass_minus_drums"]["trimmed_mean_ms"]["value"] == pytest.approx(20.0, abs=0.5)
    pd = cls["relative"]["piano_minus_drums"]["all"]
    assert pd["per_track_trimmed_mean_ms"]["value"] == pytest.approx(30.0, abs=0.5)
    step_ms = 60000.0 / 153.5 / 4  # tempo médian des pistes de la classe
    assert pd["per_track_trimmed_mean_steps"]["value"] == pytest.approx(30.0 / step_ms, abs=0.02)
    assert cls["relative"]["bass_minus_piano"]["all"]["per_track_trimmed_mean_ms"]["value"] == pytest.approx(-10.0, abs=0.5)
    # Écart absolu de la batterie : nul (elle définit les temps de la piste synthétique).
    assert cls["absolute_vs_beat"]["drums"]["all"]["pooled_ms"]["p50"] == pytest.approx(0.0, abs=0.5)
    assert cls["absolute_vs_beat"]["piano"]["all"]["pooled_ms"]["p50"] == pytest.approx(30.0, abs=0.5)
    # Dispersion par piste : nulle (aucun bruit), 8 pistes avec assez de paires.
    assert cls["jitter_per_track"]["piano_minus_drums"]["n_tracks"] == 8
    assert cls["jitter_per_track"]["piano_minus_drums"]["std_ms"]["p50"] == pytest.approx(0.0, abs=0.5)
    assert data["classes"]["120-180"]["resolution"]["step_ms"] == pytest.approx(step_ms, rel=1e-3)


def test_resolution_des_csv_par_classe():
    class Fake:
        def __init__(self, tempo):
            self.track = type("T", (), {"tempo": tempo})()
    r = st.resolution_block([Fake(200.0)])
    assert r["step_ms"] == pytest.approx(75.0) and r["csv_resolution_steps"] == pytest.approx(10 / 75)
    assert r["swing_ratio_quantum_per_observation"] == pytest.approx(10 / 300)
    assert r["quantization_noise_sd_ms"]["difference_of_two_values"] == pytest.approx(10 / np.sqrt(6))
    slow, fast = st.resolution_block([Fake(100.0)]), st.resolution_block([Fake(300.0)])
    assert slow["csv_resolution_steps"] < r["csv_resolution_steps"] < fast["csv_resolution_steps"]
    assert st.resolution_block([]) == {}


def test_fiabilite_des_ecarts_relatifs_compte_les_pistes_a_assez_de_paires(tmp_path):
    tracks = {f"t{i}": {"tempo": 150.0, "drummer": f"D{i}", "bassist": f"B{i}", "pianist": f"P{i}"} for i in range(30)}
    tracks["court"] = {"tempo": 150.0, "n_bars": 1, "drummer": "Dc", "bassist": "Bc", "pianist": "Pc"}  # 5 paires < 30
    data = measures(tmp_path, tracks)
    rel = data["reliability"]["micro_timing"]["120-180"]["bass_minus_drums"]
    assert rel["n_tracks"] == 30 and rel["verdict"] == "juste" and rel["n_musicians"] == 30


# ---------------------------------------------------------------- sortie


def test_piano_midi_jamais_lu_sortie_deterministe_et_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "BOOTSTRAP_MEDIAN", FULL_RESAMPLES[0])
    monkeypatch.setattr(st, "BOOTSTRAP_CURVE", FULL_RESAMPLES[1])
    path = make_archive(tmp_path / "jtd.zip", sweep(lambda t: 0.74 - 0.0008 * (t - 100), n=40))

    class Recording(zipfile.ZipFile):
        reads: list[str] = []

        def read(self, name, pwd=None):
            Recording.reads.append(name if isinstance(name, str) else name.filename)
            return super().read(name, pwd)

    outputs = []
    for _ in range(2):
        with Recording(path) as z:
            outputs.append(corpus_cache.dumps_json(st.build_measures(z)))
    assert outputs[0] == outputs[1]
    assert Recording.reads and not any(n.endswith("piano_midi.mid") for n in Recording.reads)
    data = json.loads(outputs[0])
    for key in ("command", "provenance", "classes", "curve", "micro_timing", "limits", "reliability", "a6_table"):
        assert key in data
    prov = data["provenance"]
    assert prov["licence"] == "MIT" and prov["sha256"] == timing.SOURCE_SHA256 and prov["md5"] == timing.SOURCE_MD5
    assert "Cheston" in prov["attribution"] and "10.5334/tismir.186" in prov["attribution"]
    assert data["command"] == "python -m harmonium_lab.backing.swing_tempo --measures"
    assert prov["counts"]["n_tracks_retained"] == 40
    assert sum(prov["counts"]["tracks_per_class"].values()) == 40
    assert set(data["reliability"]["swing"]) == {"all", *st.CLASS_IDS}
    assert data["reliability"]["thresholds"]["assez"]["min_tracks"] == 60
    assert data["parameters"]["engine_default_swing_ratio"] == 0.71
    gap = data["classes"]["180-240"]["drums_vs_engine_default"]
    assert gap["gap"] == pytest.approx(data["classes"]["180-240"]["swing"]["drums"]["median"] - 0.71)


def test_cli_refuse_une_archive_alteree(tmp_path, monkeypatch, capsys):
    bad = tmp_path / "jtd.zip"
    bad.write_bytes(b"pas la bonne archive")
    monkeypatch.setattr(st, "ARCHIVE", bad)
    assert st.main(["--measures", "--out-dir", str(tmp_path / "out")]) == 1
    assert "SHA256" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()
    monkeypatch.setattr(st, "ARCHIVE", tmp_path / "absente.zip")
    assert st.main(["--out-dir", str(tmp_path / "out")]) == 1


def test_cli_mesures_puis_resume_et_deux_executions_identiques(tmp_path, monkeypatch, capsys):
    path = make_archive(tmp_path / "jtd.zip", sweep(lambda t: 0.74 - 0.0008 * (t - 100), n=40))
    monkeypatch.setattr(st.timing, "open_archive", lambda p: zipfile.ZipFile(path))
    texts = []
    for run in ("a", "b"):
        out = tmp_path / run
        assert st.main(["--measures", "--out-dir", str(out)]) == 0
        texts.append((out / st.OUTPUT_NAME).read_text(encoding="utf-8"))
    assert texts[0] == texts[1]
    capsys.readouterr()
    assert st.main(["--summary", "--out-dir", str(tmp_path / "a")]) == 0
    printed = capsys.readouterr().out
    assert "Swing par classe" in printed and "Courbe drums" in printed
    assert st.main(["--summary", "--out-dir", str(tmp_path / "absent")]) == 1
