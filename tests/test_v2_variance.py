"""V2 : grille utilisateur (`usergrid`), grappes de tempo et critères (`v2variance`) sur des cas construits à la main."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from harmonium_lab import usergrid as ug
from harmonium_lab import v2variance as v2

PROFILE = """\
[meta]
id = "essai"

[meter]
steps_per_bar = {spb}
default_bpm = 100.0

[melody]
cell_units = 1

# partie d'origine
[form]
sequence = [0, 1]
[[form.parts]]
name = "A"
[[form.parts]]
name = "B"

[harmony]
model = "{model}"
steps_per_chord = {spc}

[harmony.parts.A]
kind = "pedal"
degree = 1

[instruments]
chords_program = 0
{extra}"""


def write_profile(root: Path, spb=16, spc=4, model="loop", extra="") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "profile.toml").write_text(PROFILE.format(spb=spb, spc=spc, model=model, extra=extra), encoding="utf-8")
    (root / "cells.toml").write_text("# banque\n", encoding="utf-8")
    return root


def chords_of(profile: Path) -> list[dict]:
    data = tomllib.loads((profile / "profile.toml").read_text(encoding="utf-8"))
    return data["harmony"]["parts"]["Grille"]["loops"][0]["chords"]


@pytest.mark.parametrize("spb,spc,n,expected", [
    (16, 4, 1, [16]), (16, 4, 2, [8, 8]),
    (12, 4, 2, [4, 8]),       # la moitié (6) n'est pas un multiple de 4 : un créneau, puis le reste
    (12, 3, 2, [6, 6]),       # 6 = 2 créneaux de 3
    (16, 16, 2, None),        # un seul créneau par mesure : pas de deuxième accord
    (24, 24, 2, None),
])
def test_split_bar_respects_chord_slots(spb, spc, n, expected):
    assert ug.split_bar(spb, spc, n) == expected


@pytest.mark.parametrize("spb,spc", [(16, 4), (12, 4), (12, 3), (24, 8)])
def test_grid_durations_fill_each_bar_and_follow_slots(tmp_path, spb, spc):
    src = write_profile(tmp_path / "src", spb, spc)
    report = ug.make_profile(src, tmp_path / "dst", 8)
    steps = [c["steps"] for c in chords_of(tmp_path / "dst")]
    assert sum(steps) == 8 * spb                        # la partie entière, exactement (règle du chargeur)
    assert all(s % spc == 0 for s in steps)             # multiples de `steps_per_chord`
    assert report.merged_bars == 0


def test_one_slot_per_bar_merges_the_split_bar(tmp_path):
    src = write_profile(tmp_path / "src", 16, 16)
    report = ug.make_profile(src, tmp_path / "dst", 8)
    chords = chords_of(tmp_path / "dst")
    assert len(chords) == 8 and report.merged_bars == 1
    assert [c["quality"] for c in chords][6] == "7"      # ii7 V7 devient V7


def test_longer_grid_repeats_the_standard_grid(tmp_path):
    src = write_profile(tmp_path / "src")
    ug.make_profile(src, tmp_path / "dst", 24)
    data = tomllib.loads((tmp_path / "dst" / "profile.toml").read_text(encoding="utf-8"))
    assert len(data["form"]["parts"][0]["roles"]) == 24 and data["form"]["parts"][0]["phrase_ends"] == [24]
    assert sum(c["steps"] for c in chords_of(tmp_path / "dst")) == 24 * 16
    with pytest.raises(ValueError, match="multiple de 8"):
        ug.make_profile(src, tmp_path / "bad", 12)


def test_form_is_replaced_and_other_files_survive(tmp_path):
    src = write_profile(tmp_path / "src")
    ug.make_profile(src, tmp_path / "dst")
    data = tomllib.loads((tmp_path / "dst" / "profile.toml").read_text(encoding="utf-8"))
    assert [p["name"] for p in data["form"]["parts"]] == ["Grille"] and data["form"]["sequence"] == [0]
    assert list(data["harmony"]["parts"]) == ["Grille"]
    assert data["instruments"] == {"chords_program": 0} and data["melody"] == {"cell_units": 1}
    assert (tmp_path / "dst" / "cells.toml").is_file()


def test_fixed_tonality_is_added_or_kept(tmp_path):
    plain = ug.make_profile(write_profile(tmp_path / "a"), tmp_path / "a_out")
    assert not plain.tonality_from_profile
    data = tomllib.loads((tmp_path / "a_out" / "profile.toml").read_text(encoding="utf-8"))
    assert data["fixed_tonality"] == {"key": ug.FIXED_KEY, "mode": ug.FIXED_MODE}
    kept = ug.make_profile(write_profile(tmp_path / "b", extra='\n[fixed_tonality]\nkey = 2\nmode = "dorian"\n'), tmp_path / "b_out")
    assert kept.tonality_from_profile and kept.fixed_tonality == {"key": 2, "mode": "dorian"}
    data = tomllib.loads((tmp_path / "b_out" / "profile.toml").read_text(encoding="utf-8"))
    assert data["fixed_tonality"] == {"key": 2, "mode": "dorian"}


def test_only_loop_profiles_take_a_user_grid(tmp_path):
    src = write_profile(tmp_path / "src", model="melody_functional")
    assert not ug.is_loop(src)
    with pytest.raises(ValueError, match="pas `loop`"):
        ug.make_profile(src, tmp_path / "dst")


def test_tempo_clusters_use_the_first_tempo_of_each_cluster():
    # 100 ouvre la grappe 0 ; 107 y entre (≤ 8) ; 109 est à 9 du premier : grappe 1 ; 120 est à 11 de 109 : grappe 2
    assert v2.tempo_clusters([100, 107, 109, 120]) == [0, 0, 1, 2]
    assert v2.tempo_clusters([90, 90, 90]) == [0, 0, 0]


def _rows(n, **fields):
    base = {"tempo": 100.0, "key": 0, "mode": "ionian", "swing": 0.5, "melody": 0, "chords": 0, "bass": 32, "kit": (128, 0),
            "voicing": "a", "arc": "x", "session": {}}
    return [{**base, **{k: (v(i) if callable(v) else v) for k, v in fields.items()}} for i in range(n)]


def test_host_view_drops_tempo_and_tonality():
    rows = _rows(16, tempo=lambda i: 60.0 + 20 * i, key=lambda i: i % 12)
    summary = v2.habillage_summary(rows)
    assert summary["distinct"] == 16 and summary["tonalites"] == 12
    assert summary["distinct_hote_tempo_tonalite"] == 1       # rien d'autre ne change : l'hôte les impose
    rows = _rows(16, tempo=lambda i: 60.0 + 20 * i, chords=lambda i: i % 3)
    assert v2.habillage_summary(rows)["distinct_hote_tempo_tonalite"] == 3


def _measure(**over):
    layer = {"identical_pairs": 0.0, "active_share": 1.0, "adjacent": {"exact": 0.9, "graded": 0.5},
             "adjacent_steady": {"exact": 0.9, "graded": 0.5}}
    inter = {"distinct_runs": 16, "share_active": 1.0}
    var = {"intra": {k: layer for k in ("all", "chords", "comping_rhythm", "comping_voicing", "bass", "drums", "orchestration")},
           "inter": {k: inter for k in ("comping_rhythm", "bass", "drums", "orchestration")},
           "orchestration_programs": {"1": [0, 4, 26], "2": [32, 33], "9": [128000, 128040]},
           "numeric": {"all": {"density": {"trajectory": [10.0, 20.0, 30.0, 15.0]},
                               "velocity": {"trajectory": [70.0, 75.0, 82.0, 72.0]}}}}
    var["intra"]["chords"] = {**layer, "adjacent": {"exact": 0.0, "graded": 0.0}}
    m = {"seeds": 16, "habillage": v2.habillage_summary(_rows(16, tempo=lambda i: 60.0 + 20 * i, chords=lambda i: i % 3)),
         "variance": var}
    m.update(over)
    return m


def _by_id():
    return {c.ident: c for c in v2.build_criteria()}


def test_a_varied_measure_holds_every_criterion():
    verdicts = {i: c.check(_measure())[1] for i, c in _by_id().items()}
    assert verdicts == {i: True for i in verdicts}


def test_a_looping_layer_fails_and_a_muted_layer_is_not_applicable():
    m = _measure()
    m["variance"]["intra"]["drums"] = {**m["variance"]["intra"]["drums"], "identical_pairs": 1.0}
    assert _by_id()["2"].check(m)[1] is False                  # une couche qui rejoue le chorus précédent
    assert _by_id()["1"].check(m)[1] is True                   # l'accompagnement entier, lui, ne boucle pas
    m["variance"]["intra"]["all"] = {**m["variance"]["intra"]["all"], "identical_pairs": 0.1}
    assert _by_id()["1"].check(m)[1] is False
    muted = _measure()
    muted["variance"]["intra"]["drums"] = {"identical_pairs": None, "active_share": 0.0, "adjacent": {"exact": None, "graded": None},
                                           "adjacent_steady": {"exact": None, "graded": None}}
    assert _by_id()["7"].check(muted)[1] is None


def test_grid_view_counts_host_habillages_and_ignores_tempo():
    m = _measure(grid={"applicable": True, "bars": 8})
    ok = _by_id()
    assert ok["H2"].check(m)[1] is None                       # l'hôte impose le tempo
    assert ok["H1"].check(m)[1] is False                      # 3 habillages hors tempo et tonalité : sous le seuil de la grille


def test_arc_is_read_from_the_second_chorus_so_track_entries_do_not_count():
    # une piste qui entre au 2e chorus gonfle le 1er ; ensuite la courbe est plate : pas d'arc
    assert v2.steady_range([22.0, 34.0, 34.0, 33.0]) < 0.05
    assert v2.steady_range([31.0, 51.0, 54.0, 18.0]) > 0.25       # montée puis retombée
    assert v2.steady_range([10.0, 10.0]) == 0.0                   # deux chorus : toute la courbe
    assert v2.steady_range([None, None, None]) is None


def test_bass_threshold_depends_on_the_bass_class():
    m = _measure()
    m["variance"]["intra"]["bass"] = {**m["variance"]["intra"]["bass"], "adjacent": {"exact": 0.30, "graded": 0.2}}
    bass = _by_id()["6"]
    assert bass.check({**m, "bass_walking": False})[1] is True     # un riff qui varie de 30 % : au-dessus de 10 %
    assert bass.check({**m, "bass_walking": True})[1] is False     # une marche à 30 % : sous 80 %


def test_muted_comping_makes_the_inter_seed_criterion_not_applicable():
    m = _measure()
    for k in ("comping_rhythm", "drums"):
        m["variance"]["inter"][k] = {"distinct_runs": 1, "share_active": 0.0}
    assert _by_id()["H3"].check(m)[1] is None


def test_drum_distance_rows_read_each_script_output_shape():
    from harmonium_lab import v2distance as d
    per_metric = {"moyenne": {"profil": 0.1, "sans_arc": 0.2, "non_calibre": 0.9}}
    assert d.drums_row("gmd_blues_shuffle", per_metric) == {"profil": 0.1, "sans_arc": 0.2, "non_calibre": 0.9}
    assert d.drums_row("gmd_rock", {"gmd_rock": per_metric}) == {"profil": 0.1, "sans_arc": 0.2, "non_calibre": 0.9}
    witness = {"wjazzd_ballad": {"moyenne": {"profil": 0.5, "temoin": 0.3}}}
    assert d.drums_row("wjazzd_ballad", witness) == {"profil": 0.5, "temoin": 0.3}      # B2/B5 : témoin, pas copie sans arc
    samba = {k: {"moyenne": v} for k, v in (("profil", 0.35), ("sans_arc_ni_session", 0.37), ("non_calibre", 0.73))}
    assert d.drums_row("gmd_latin_brazilian_samba", samba) == {"profil": 0.35, "sans_arc": 0.37, "non_calibre": 0.73}
    both = {"afrocuban + rhumba": per_metric, "afrocuban": {"moyenne": {"profil": 9.9}}}
    assert d.drums_row("gmd_afrocuban", both)["profil"] == 0.1                           # les deux styles du GMD


def test_same_tick_program_changes_keep_file_order(tmp_path):
    """Le profil écrit sa basse (34), la session la sienne (33) au même tick : celle de la session sonne."""
    import mido
    from harmonium_lab import chorusvariety as cv
    track = mido.MidiTrack([mido.Message("program_change", channel=2, program=34, time=0),
                            mido.Message("program_change", channel=2, program=33, time=0),
                            mido.Message("program_change", channel=2, program=30, time=960)])
    mid = mido.MidiFile(ticks_per_beat=480)
    mid.tracks.append(track)
    path = tmp_path / "x.mid"
    mid.save(path)
    events = cv.midi_programs(path)
    assert events == [(0, 2, 34), (0, 2, 33), (960, 2, 30)]
    sigs = cv.orchestration_sigs({2: (0, 34)}, events, {1: 0, 2: 960})
    assert sigs[1] == ((2, 0, 33),) and sigs[2] == ((2, 0, 30),)
