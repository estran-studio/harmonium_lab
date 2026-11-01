"""Tests de la variété par graine : cas synthétiques (identiques → 0, toutes différentes → 1)."""

from __future__ import annotations

import json

import pytest

from harmonium_lab import seedvariety as sv

N_SEEDS = 16


def _bar(index: int, *, part: int = 0, chords=(), bass=(), drums=(), instance=(0, 1, 0)) -> sv.Bar:
    return sv.Bar(index, part, instance, {"chords": tuple(chords), "bass": tuple(bass), "drums": tuple(drums)})


def _runs(make) -> dict[int, list[sv.Bar]]:
    """16 graines × 8 mesures (deux parties de 4) ; `make(seed, bar)` donne les signatures de la mesure."""
    return {
        seed: [_bar(b, part=(b - 1) // 4, instance=(0, 1, (b - 1) // 4), **make(seed, b)) for b in range(1, 9)]
        for seed in range(1, N_SEEDS + 1)
    }


def test_identical_seeds_have_no_variety():
    runs = _runs(lambda s, b: {"chords": [(0, 0, "m", True, 0)], "bass": [(0, -12, 16)], "drums": [(3, 0, 36)]})
    r = sv.seed_variety(runs, ["A", "B"])
    for layer in sv.LAYERS:
        for unit in ("bars", "parts"):
            assert r["layers"][layer][unit]["share"] == 0.0
            assert r["layers"][layer][unit]["diversity"] == 0.0
            assert r["layers"][layer][unit]["distinct_mean"] == 1.0
    assert r["combined"]["any"]["bars"]["share"] == 0.0
    assert r["distinct_runs"] == {"chords": 1, "bass": 1, "drums": 1}


def test_all_different_seeds_are_maximal():
    runs = _runs(lambda s, b: {"chords": [(0, s, "", False, 0)], "bass": [(0, s, 16)], "drums": [(3, s, 36)]})
    r = sv.seed_variety(runs)
    for layer in sv.LAYERS:
        for unit in ("bars", "parts"):
            assert r["layers"][layer][unit]["share"] == 1.0
            assert r["layers"][layer][unit]["diversity"] == 1.0
            assert r["layers"][layer][unit]["distinct_mean"] == N_SEEDS
    assert r["combined"]["all"]["parts"]["share"] == 1.0
    assert r["distinct_runs"] == {"chords": N_SEEDS, "bass": N_SEEDS, "drums": N_SEEDS}


def test_layers_are_independent_and_two_alternatives_cap_diversity():
    # Batterie : deux alternatives réparties entre graines, dans la seconde partie seulement.
    def make(seed, bar):
        drums = [(3, seed % 2, 36)] if bar > 4 else [(3, 0, 36)]
        return {"chords": [(0, 0, "", False, 0)], "bass": [(0, 0, 16)], "drums": drums}

    r = sv.seed_variety(_runs(make), ["A", "B"])
    assert r["layers"]["chords"]["bars"]["share"] == 0.0
    assert r["layers"]["bass"]["parts"]["share"] == 0.0
    d = r["layers"]["drums"]
    assert d["bars"]["share"] == 0.5 and d["parts"]["share"] == 0.5
    assert d["bars"]["diversity"] == pytest.approx(0.5 * (1 / (N_SEEDS - 1)), abs=1e-4)   # 2 valeurs sur 16 graines
    assert d["by_part"]["A"]["occurrences"]["share"] == 0.0
    assert d["by_part"]["B"]["occurrences"]["share"] == 1.0
    assert r["combined"]["any"]["bars"]["share"] == 0.5
    assert r["combined"]["all"]["bars"]["share"] == 0.0


def test_silent_layer_is_reported_apart_from_stable_layer():
    # Basse jouée seulement dans la première partie : la seconde n'est pas « stable », elle est absente.
    def make(seed, bar):
        return {"chords": [], "bass": [(0, seed, 16)] if bar <= 4 else [], "drums": []}

    bass = sv.seed_variety(_runs(make))["layers"]["bass"]["bars"]
    assert bass["share"] == 0.5
    assert bass["share_active"] == 1.0
    assert bass["active_units"] == 4


def test_only_bars_present_in_every_seed_are_compared():
    runs = _runs(lambda s, b: {"bass": [(0, s, 16)]})
    runs[2] = runs[2][:6]
    assert sv.seed_variety(runs)["bars_compared"] == 6
    with pytest.raises(ValueError):
        sv.seed_variety({1: runs[1]})


def _entry(bar: int, key: int, root_pc: int, pitch: int, offset: int, tune: int = 0, changes: bool = True) -> dict:
    measure = {
        "position": {"key": key, "part": 0, "tune_index": tune, "tour": 1, "sequence_index": 0},
        "chord_root_pc": root_pc, "chord_quality": None, "chord_is_minor": True, "chord_bass_pc": root_pc,
        "notes": [
            {"track": 2, "start_step": 0, "pitch": pitch, "duration_steps": 16, "velocity": 90},
            {"track": 3, "start_step": 4, "pitch": 36, "duration_steps": 0, "velocity": 100 + offset,
             "performance": {"offset": offset}},
            {"track": 0, "start_step": 0, "pitch": 70 + offset, "duration_steps": 2, "velocity": 80},
        ],
    }
    if changes:
        measure["chord_changes"] = [{"start_step": 0, "context": {
            "root_pc": root_pc, "quality": None, "is_minor": True, "bass_pc": root_pc}}]
    return {"bar": bar, "measure": measure}


def test_signatures_are_relative_to_the_key_and_ignore_humanization():
    # Même motif joué en ré (2) et en sol (7), vélocités et décalages différents, mélodie différente.
    a = sv.bar_from_entry(_entry(1, key=2, root_pc=2, pitch=38, offset=-9))
    b = sv.bar_from_entry(_entry(1, key=7, root_pc=7, pitch=43, offset=5))
    assert a.sigs == b.sigs
    c = sv.bar_from_entry(_entry(1, key=2, root_pc=2, pitch=40, offset=-9))
    assert c.sigs["bass"] != a.sigs["bass"] and c.sigs["chords"] == a.sigs["chords"]


def test_closing_measure_without_chord_changes_and_first_tune_only(tmp_path):
    entries = [_entry(1, 2, 2, 38, 0), _entry(2, 2, 2, 38, 0, changes=False), _entry(3, 2, 2, 38, 0, tune=1),
               _entry(70, 2, 2, 38, 0)]
    path = tmp_path / "truth.json"
    path.write_text(json.dumps({"measures": entries}), encoding="utf-8")
    bars = sv.load_truth(path, max_bars=64)
    assert [b.index for b in bars] == [1, 2]            # air 2 et mesures au-delà de --bars écartés
    assert bars[1].sigs["chords"] == ((0, 0, "", True, 0),)   # accord de la mesure de clôture
