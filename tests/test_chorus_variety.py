"""Variance par chorus : cas synthétiques (chorus identiques → 0, tous différents → 1, orchestration détectée)."""

from __future__ import annotations

import json

import pytest

from harmonium_lab import chorusvariety as cv

N_SEEDS = 4
N_CHORUS = 5
PLACES = 4


def _runs(make, seeds=N_SEEDS, choruses=N_CHORUS) -> dict[int, list[cv.CBar]]:
    """`make(seed, chorus, place)` → signatures ou (signatures, métriques) d'une mesure."""
    runs = {}
    for s in range(seeds):
        bars = []
        for c in range(1, choruses + 1):
            for p in range(PLACES):
                made = make(s, c, p)
                sigs, metrics = made if isinstance(made, tuple) and len(made) == 2 and isinstance(made[1], dict) else (made, None)
                bars.append(cv.make_bar((c - 1) * PLACES + p + 1, c, p, sigs, part=0, metrics=metrics))
        runs[s] = bars
    return runs


def _loop(seed, chorus, place):
    return {"chords": [(0, place, "7", False, place)], "comping_rhythm": [0, 8], "comping_voicing": [(place, 4, 7)],
            "bass": [(0, 36 + place, 4)], "drums": [(4, 0, 51)], "orchestration": [(1, 0, 0), (2, 0, 32)]}


def test_identical_choruses_and_seeds_are_zero():
    r = cv.chorus_variance(_runs(_loop))
    for layer in cv.CORE:
        intra, inter = r["intra"][layer], r["inter"][layer]
        assert intra["adjacent"]["exact"] == 0.0 and intra["adjacent"]["graded"] == 0.0
        assert intra["identical_pairs"] == 1.0 and intra["distinct_choruses_mean"] == 1.0
        assert inter["share_active"] == 0.0 and inter["graded"] == 0.0
    assert r["intra"][cv.ALL]["adjacent"]["exact"] == 0.0


def test_all_different_choruses_and_seeds_are_one():
    def make(seed, chorus, place):
        tag = seed * 100 + chorus * 10 + place
        return {"chords": [(0, tag, "", False, 0)], "comping_rhythm": [tag], "comping_voicing": [(tag,)],
                "bass": [(0, tag, 4)], "drums": [(4, 0, tag)]}
    r = cv.chorus_variance(_runs(make))
    for layer in (*cv.CORE, cv.ALL):
        intra, inter = r["intra"][layer], r["inter"][layer]
        assert intra["adjacent"]["exact"] == 1.0 and intra["adjacent"]["graded"] == 1.0
        assert intra["any_pair"]["exact"] == 1.0 and intra["identical_pairs"] == 0.0
        assert intra["distinct_choruses_mean"] == N_CHORUS
        assert inter["share_active"] == 1.0 and inter["graded"] == 1.0 and inter["diversity"] == 1.0


def test_graded_distance_is_jaccard_and_exact_ignores_partial_overlap():
    # Chorus pair différant par une note sur trois : exact = 1 mesure sur 1, graduée = 1 − 2/4.
    def make(seed, chorus, place):
        return {"bass": [(0, 36, 4), (4, 38, 4), (8, 40 if chorus % 2 else 41, 4)]}
    r = cv.chorus_variance(_runs(make, choruses=2))
    adj = r["intra"]["bass"]["adjacent"]
    assert adj["exact"] == 1.0 and adj["graded"] == pytest.approx(0.5)


def test_orchestration_change_between_choruses_is_detected():
    def make(seed, chorus, place):
        sigs = _loop(seed, chorus, place)
        sigs["orchestration"] = [(1, 0, 0 if chorus < 3 else 4), (2, 0, 32)]   # le comping change au chorus 3
        return sigs
    r = cv.chorus_variance(_runs(make))
    orch = r["intra"]["orchestration"]
    assert orch["distinct_choruses_mean"] == 2.0
    assert orch["adjacent"]["exact"] == pytest.approx(1 / (N_CHORUS - 1))   # 1 paire voisine sur 4 change, toutes places
    assert orch["adjacent"]["graded"] == pytest.approx(1 / (N_CHORUS - 1) * 0.5)   # 1 piste sur 2
    assert r["orchestration_programs"]["1"] == [0, 4]
    # Les autres couches ne bougent pas : l'orchestration seule fait varier la mesure.
    assert r["intra"]["bass"]["adjacent"]["exact"] == 0.0


def test_fixed_orchestration_is_zero_between_choruses_and_seeds():
    r = cv.chorus_variance(_runs(_loop))
    assert r["intra"]["orchestration"]["identical_pairs"] == 1.0
    assert r["inter"]["orchestration"]["share_active"] == 0.0


def test_silent_layer_is_not_counted_and_entering_layer_is_a_change():
    def make(seed, chorus, place):
        return {"bass": [(0, 36, 4)] if chorus >= 2 else []}   # la basse entre au chorus 2
    r = cv.chorus_variance(_runs(make))
    bass = r["intra"]["bass"]
    assert bass["adjacent"]["exact"] == pytest.approx(1 / (N_CHORUS - 1))
    assert bass["adjacent_steady"]["exact"] == 0.0          # passé l'entrée : stable
    assert r["intra"]["drums"]["adjacent"]["exact"] is None  # couche muette : ni stable ni variable
    assert r["intra"]["drums"]["active_share"] == 0.0


def test_intra_variance_does_not_depend_on_seed_variance():
    # Les graines diffèrent entre elles mais chaque graine rejoue le même chorus : boucle par graine.
    r = cv.chorus_variance(_runs(lambda s, c, p: {"bass": [(0, 30 + s, 4)]}))
    assert r["intra"]["bass"]["adjacent"]["exact"] == 0.0
    assert r["inter"]["bass"]["share_active"] == 1.0


def test_numeric_layers_track_density_and_velocity_per_chorus():
    def make(seed, chorus, place):
        return {"bass": [(0, 36, 4)]}, {"n_all": 4.0 * chorus, "vel_all": 4.0 * chorus * (60 + 10 * chorus),
                                        "n_bass": 1.0, "vel_bass": 80.0, "intensity": 0.5}
    r = cv.chorus_variance(_runs(make))
    dens = r["numeric"]["all"]["density"]
    assert dens["trajectory"] == [4.0 * c for c in range(1, N_CHORUS + 1)]
    assert dens["intra"]["adjacent_change"] > 0 and dens["inter"]["cv"] == 0.0
    assert r["numeric"]["bass"]["velocity"]["intra"]["cv"] == 0.0
    assert r["numeric"]["engine"]["intensity"]["intra"]["adjacent_change"] == 0.0


def _entry(bar: int, tour: int, cycle: int, *, section="Tour", pitch=38, comp=(57, 60), changes=True, key=5) -> dict:
    measure = {
        "position": {"key": key, "part": 0, "tune_index": 0, "tour": tour, "sequence_index": 0,
                     "bar_in_cycle": cycle, "section": section},
        "notes": [{"track": 2, "start_step": 0, "pitch": pitch, "duration_steps": 4, "velocity": 80}]
                 + [{"track": 1, "start_step": 0, "pitch": p, "duration_steps": 4, "velocity": 60} for p in comp]
                 + [{"track": 4, "start_step": 0, "pitch": 51, "duration_steps": 1, "velocity": 70},
                    {"track": 3, "start_step": 8, "pitch": 36, "duration_steps": 1, "velocity": 90}],
        "chord_changes": ([{"start_step": 0, "context": {"root_pc": 5, "quality": "7", "is_minor": False, "bass_pc": 5}}]
                          if changes else None),
        "chord_root_pc": 5, "chord_quality": "7", "chord_is_minor": False, "chord_bass_pc": 5,
    }
    return {"bar": bar, "intensity": 0.5, "measure": measure}


def test_truth_reading_drops_intro_closing_and_later_tunes_and_aligns_by_place(tmp_path):
    entries = [_entry(1, 0, 0, section="Intro"), _entry(2, 1, 0), _entry(3, 1, 1, pitch=40),
               _entry(4, 2, 0), _entry(5, 2, 1, pitch=41), _entry(6, 3, 0), _entry(7, 3, 1, changes=False)]
    later = _entry(8, 1, 0)
    later["measure"]["position"]["tune_index"] = 1
    path = tmp_path / "truth.json"
    path.write_text(json.dumps({"measures": [*entries, later]}), encoding="utf-8")
    bars = cv.load_truth(path)
    assert [(b.chorus, b.pos) for b in bars] == [(1, 0), (1, 1), (2, 0), (2, 1), (3, 0)]   # clôture (bar 7) écartée
    t = cv.chorus_table(bars)
    assert t[1][0].sigs["bass"] == t[2][0].sigs["bass"] and t[1][1].sigs["bass"] != t[2][1].sigs["bass"]
    # Vélocités ignorées, rôle GM de la batterie, voicing relatif à la tonique (fa = 5).
    assert t[1][0].sigs["drums_ride"] == ((4, 0, 51),) and t[1][0].sigs["drums_kick"] == ((3, 8, 36),)
    assert t[1][0].sigs["comping_voicing"] == ((52, 55),) and t[1][0].sigs["comping_rhythm"] == (0,)
    assert t[1][0].metrics["n_comping"] == 2 and t[1][0].metrics["vel_bass"] == 80


def test_chorus_is_taken_from_chorus_field_then_tour_then_form_length(tmp_path):
    a, b = _entry(1, 1, 0), _entry(2, 2, 0)
    b["measure"]["position"]["chorus"] = 7
    assert cv.bar_from_entry(a).chorus == 1 and cv.bar_from_entry(b).chorus == 7
    bare = [_entry(i + 1, 0, i % 2) for i in range(6)]
    for e in bare:
        del e["measure"]["position"]["tour"]
        del e["measure"]["position"]["section"]
    path = tmp_path / "truth.json"
    path.write_text(json.dumps({"measures": bare}), encoding="utf-8")
    assert [(b.chorus, b.pos) for b in cv.load_truth(path)] == [(1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)]


def test_orchestration_reads_program_changes_by_bar():
    base = {1: (0, 0), 2: (0, 32), 9: (128, 32)}
    events = [(0, 1, 0), (3840, 1, 4)]                       # le comping change à la mesure 3 (1920 ticks par mesure)
    sigs = cv.orchestration_sigs(base, events, {1: 0, 2: 1920, 3: 3840, 4: 5760})
    assert sigs[1] == sigs[2] and sigs[3] == sigs[4] and sigs[2] != sigs[3]
    assert dict((c, p) for c, _, p in sigs[3]) == {1: 4, 2: 32, 9: 32}


def test_last_chorus_without_its_closing_place_is_still_a_loop():
    runs = _runs(_loop)
    runs = {s: [b for b in bars if not (b.chorus == N_CHORUS and b.pos == PLACES - 1)] for s, bars in runs.items()}
    r = cv.chorus_variance(runs)
    for layer in cv.CORE:
        assert r["intra"][layer]["identical_pairs"] == 1.0 and r["intra"][layer]["distinct_choruses_mean"] == 1.0


def test_seeds_sharing_one_stream_are_counted_as_one_sequence():
    # 4 graines, mais seulement deux flux de basse (parité de la graine) : chaque chorus varie, la graine à peine.
    r = cv.chorus_variance(_runs(lambda s, c, p: {"bass": [(0, 30 + (s % 2) * 10 + c, 4)]}))
    bass = r["inter"]["bass"]
    assert bass["distinct_runs"] == 2 and bass["share_active"] == 1.0
    assert r["intra"]["bass"]["adjacent"]["exact"] == 1.0
    assert r["inter"]["chords"]["distinct_runs"] == 1
    assert cv.chorus_variance(_runs(lambda s, c, p: {"bass": [(0, s, 4)]}))["inter"]["bass"]["distinct_runs"] == N_SEEDS
