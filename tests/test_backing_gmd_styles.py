"""Tests de `harmonium_lab.backing.gmd_styles` : fixtures SYNTHÉTIQUES seulement (aucun brut GMD)."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import pretty_midi
import pytest

from harmonium_lab.backing import drums, gmd_styles as g
from harmonium_lab.backing.drums import Hit

RIDE, KICK, SNARE, PEDAL, HAT, BELL, XSTICK = 51, 36, 38, 44, 42, 53, 37


def midi_bytes(notes: list[tuple[float, int, int]], bpm: float = 120.0) -> bytes:
    """MIDI de batterie en mémoire : `(position en pulsations, hauteur, vélocité)`."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0, is_drum=True)
    spb = 60.0 / bpm
    for beat, pitch, vel in notes:
        inst.notes.append(pretty_midi.Note(velocity=vel, pitch=pitch, start=beat * spb, end=beat * spb + 0.05))
    pm.instruments.append(inst)
    buffer = io.BytesIO()
    pm.write(buffer)
    return buffer.getvalue()


def hits(notes: list[tuple[float, int, int]]) -> list[Hit]:
    return [Hit(b, p, v) for b, p, v in sorted(notes)]


def row(path="d1/a.mid", style="rock", kind="beat", sig="4-4", bpm=120, duration=60.0, drummer="d1") -> drums.FileRow:
    return drums.FileRow(path, drummer, f"{drummer}/s1", path[:-4], style, bpm, kind, sig, duration, "train")


def eighths(n_beats: int, offbeat: float, pitch: int = HAT, start: float = 0.0) -> list[tuple[float, int, int]]:
    notes = []
    for b in range(n_beats):
        notes.append((start + b, pitch, 80))
        notes.append((start + b + offbeat, pitch, 60))
    return notes


# ---------------------------------------------------------------- rôles et table de correspondance


def test_chaque_hauteur_roland_a_un_role_fin_coherent_avec_le_role_d_e7():
    assert set(g.PITCH_ROLE) == set(drums.ROLAND_TABLE)
    coarse = {"snare": {"snare", "sidestick"}, "tom": {"tom_high", "tom_mid", "tom_low"}, "ride": {"ride", "ride_bell"}}
    for pitch, role in g.PITCH_ROLE.items():
        e7 = drums.ROLAND_TABLE[pitch][1]
        assert role in coarse.get(e7, {e7}), (pitch, role, e7)
    assert g.PITCH_ROLE[37] == "sidestick" and g.PITCH_ROLE[53] == "ride_bell"
    assert g.PITCH_ROLE[48] == g.PITCH_ROLE[50] == "tom_high" and g.PITCH_ROLE[43] == g.PITCH_ROLE[58] == "tom_low"
    assert set(g.PITCH_ROLE.values()) == set(g.ROLES)


# ---------------------------------------------------------------- feel


def feel_of(notes, sig="4-4"):
    return g.classify_feel(hits(notes), sig)


@pytest.mark.parametrize("offbeat, expected", [(0.5, "straight"), (0.6, "swing"), (2 / 3, "ternary"), (0.72, "ternary")])
def test_feel_des_croches_du_charleston(offbeat, expected):
    info = feel_of(eighths(40, offbeat))
    assert info["feel"] == expected
    if expected != "straight":
        assert info["ratio"] == pytest.approx(offbeat, abs=0.01)


def test_doubles_croches_droites_ne_sont_pas_prises_pour_un_swing():
    """Charleston en doubles croches : les attaques à 0,75 ne doivent pas tirer r vers un swing."""
    notes = []
    for b in range(40):
        notes += [(b + k / 4, HAT, 70) for k in range(4)]
    info = feel_of(notes)
    assert info["feel"] == "straight" and info["evidence"] == "timekeeper:sixteenths"


def test_feel_sans_contretemps_et_metrique_composee():
    quarters = [(float(b), RIDE, 80) for b in range(40)] + [(float(b), KICK, 90) for b in range(40)]
    assert feel_of(quarters) == {"feel": "straight", "ratio": 0.5, "evidence": "none", "n_evidence": 0}
    # 6/8 : la croche tombe à 0,5 pulsation : jamais de feel ternaire.
    assert g.classify_feel(hits(eighths(40, 2 / 3)), "6-8")["feel"] == "straight"


def test_feel_juge_sur_les_autres_roles_si_le_timekeeper_manque_mais_pas_sur_la_grosse_caisse():
    ghost = [(b + 2 / 3, SNARE, 40) for b in range(30)] + [(float(b), SNARE, 80) for b in range(30)]
    assert feel_of(ghost)["feel"] == "ternary" and feel_of(ghost)["evidence"] == "other_roles:ratio"
    kick_only = [(b + 2 / 3, KICK, 90) for b in range(30)]
    assert feel_of(kick_only)["evidence"] == "none"


# ---------------------------------------------------------------- quantification


def test_quantification_sur_les_trois_grilles_et_ecart_signe():
    assert g.quantize(1 / 3, "ternary", 2 / 3)[:2] == (0, 1)
    assert g.quantize(2 / 3, "ternary", 2 / 3)[:2] == (0, 2)
    assert g.quantize(0.97, "ternary", 2 / 3)[:2] == (1, 0)  # juste avant le temps suivant
    beat, step, off = g.quantize(0.30, "ternary", 2 / 3)
    assert (beat, step) == (0, 1) and off == pytest.approx(0.30 - 1 / 3)  # en avance : négatif
    assert [g.quantize(x, "straight", 0.5)[1] for x in (0.0, 0.26, 0.49, 0.77)] == [0, 1, 2, 3]
    assert g.quantize(0.6, "swing", 0.6)[:2] == (0, 2)
    assert g.quantize(3.99, "straight", 0.5)[:2] == (4, 0)
    assert g.steps_per_beat("ternary") == 3 and g.steps_per_beat("swing") == 4


def test_mesures_en_trois_quatre_six_huit_et_ternaire():
    # 3/4 droit : 12 pas ; le pas de la troisième pulsation est 8.
    notes = [(b + k / 4, HAT, 70) for b in range(30) for k in (0, 2)] + [(float(b), KICK, 90) for b in range(0, 30, 3)]
    perf = g.read_performance(midi_bytes(notes))
    ms = g.measures_of(perf, row(sig="3-4"), "straight", 0.5)
    assert ms and all(m.steps_per_bar == 12 and m.bar_beats == 3.0 for m in ms)
    assert set(ms[1].role_steps("hat_closed")) == {0, 2, 4, 6, 8, 10}
    assert ms[1].role_steps("kick") == (0,)
    # 4/4 ternaire : 12 pas, croche swinguée au pas 2 de la pulsation (2/3).
    swung = eighths(40, 2 / 3)
    ms = g.measures_of(g.read_performance(midi_bytes(swung)), row(), "ternary", 2 / 3)
    assert ms[1].steps_per_bar == 12
    assert ms[1].role_steps("hat_closed") == (0, 2, 3, 5, 6, 8, 9, 11)
    # 6/8 : 3 pulsations par mesure, 12 pas droits.
    ms = g.measures_of(g.read_performance(midi_bytes(eighths(30, 0.5))), row(sig="6-8"), "straight", 0.5)
    assert ms and ms[0].steps_per_bar == 12


def test_premiere_mesure_incomplete_et_fin_de_fichier():
    """Entrée en cours de mesure : première mesure écartée ; dernière mesure incomplète écartée."""
    late = [(2.5 + b, KICK, 90) for b in range(10)]  # première attaque à 2,5 pulsations de la mesure 0
    ms = g.measures_of(g.read_performance(midi_bytes(late)), row(), "straight", 0.5)
    assert all(m.role_steps("kick") for m in ms)
    full = [(float(b), KICK, 90) for b in range(10)]
    ms = g.measures_of(g.read_performance(midi_bytes(full)), row(), "straight", 0.5)
    assert len(ms) == 2  # 10 pulsations : mesures 0 et 1 entières ; la troisième (2 temps) est tronquée


def test_micro_timing_en_pas_et_en_ms_et_fidelite_de_grille():
    # Charleston toujours 0,1 pulsation en retard sur le temps, à 120 BPM : 0,4 pas, 50 ms.
    notes = [(b + 0.1, HAT, 70) for b in range(60)] + [(b, KICK, 90) for b in range(60)]
    ms = g.measures_of(g.read_performance(midi_bytes(notes, 120)), row(bpm=120), "straight", 0.5)
    mt = g.micro_timing(ms)
    on = mt["hat_closed"]["on_beat"]
    assert on["steps"]["p50"] == pytest.approx(0.4, abs=0.02) and on["ms"]["p50"] == pytest.approx(50, abs=3)
    assert abs(mt["kick"]["on_beat"]["steps"]["p50"]) < 0.02
    fit = g.grid_fit(ms)
    assert fit["within_quarter_step"] < 0.6  # le charleston (0,4 pas) sort du quart de pas, la grosse caisse non


# ---------------------------------------------------------------- figures


def measure_with(role_steps: dict[str, list[int]], feel="straight") -> g.Measure:
    m = g.Measure("f", "rock", "beat", feel, 0.5, 120, 4.0)
    for role, steps in role_steps.items():
        m.steps[role] = {s: (80, 42, 0.0) for s in steps}
    return m


def test_figures_du_timekeeper():
    assert g.figure_of(measure_with({})) == "none"
    assert g.figure_of(measure_with({"ride": [0, 4, 8, 12]})) == "quarters"
    assert g.figure_of(measure_with({"hat_closed": [0, 2, 4, 6, 8, 10, 12, 14]})) == "eighths"
    assert g.figure_of(measure_with({"hat_closed": list(range(16))})) == "sixteenths"
    assert g.figure_of(measure_with({"ride": [0, 4, 6, 8, 12, 14]})) == "spang"
    # Ternaire : mêmes noms, sous-pas 0..2 par pulsation.
    assert g.figure_of(measure_with({"ride": [0, 3, 5, 6, 9, 11]}, "ternary")) == "spang"
    assert g.figure_of(measure_with({"hat_closed": [0, 2, 3, 5, 6, 8, 9, 11]}, "ternary")) == "eighths"
    assert g.figure_of(measure_with({"hat_closed": list(range(12))}, "ternary")) == "sixteenths"
    assert g.figure_of(measure_with({"hat_closed": [4, 12]})) == "sparse"
    # Le rôle le plus joué est le timekeeper : ride_bell seul compte.
    assert g.timekeeper_of(measure_with({"ride_bell": [0, 4], "hat_closed": [0]})) == "ride_bell"


# ---------------------------------------------------------------- fiabilité


@pytest.mark.parametrize("kind, files, drummers, measures, expected", [
    ("beat", 8, 3, 200, "assez"), ("beat", 8, 2, 400, "juste"), ("beat", 7, 3, 400, "juste"),
    ("beat", 3, 1, 60, "juste"), ("beat", 3, 1, 59, "trop peu"), ("beat", 2, 1, 900, "trop peu"),
    ("fill", 30, 3, 30, "assez"), ("fill", 10, 1, 10, "juste"), ("fill", 9, 3, 500, "trop peu"),
])
def test_seuils_de_fiabilite(kind, files, drummers, measures, expected):
    assert g.reliability(kind, files, drummers, measures) == expected


# ---------------------------------------------------------------- passe complète sur archive synthétique


def synthetic_archive() -> tuple[zipfile.ZipFile, list[drums.FileRow]]:
    """Archive GMD factice : rock droit (3 fichiers), shuffle ternaire (2), samba (2 fichiers dont 1 fill sans
    contretemps), un fichier 5/4 refusé."""
    files: dict[str, bytes] = {}
    rows: list[drums.FileRow] = []

    def add(path, style, kind, sig, notes, drummer="drummer1", bpm=120):
        files[f"groove/{path}"] = midi_bytes(notes, bpm)
        rows.append(row(path, style, kind, sig, bpm, 60.0, drummer))

    backbeat = lambda n: ([(float(b), KICK, 90) for b in range(0, n, 2)] + [(float(b), SNARE, 90) for b in range(1, n, 2)]
                          + eighths(n, 0.5))
    for i in range(3):
        add(f"d{i}/rock{i}.mid", "rock", "beat", "4-4", backbeat(80), drummer=f"drummer{i}")
    shuffle = lambda n: ([(float(b), KICK, 90) for b in range(0, n, 2)] + [(float(b), SNARE, 90) for b in range(1, n, 2)]
                         + eighths(n, 2 / 3, RIDE))
    for i in range(2):
        add(f"d{i}/shuffle{i}.mid", "rock/shuffle", "beat", "4-4", shuffle(80), drummer=f"drummer{i}")
    add("d1/samba0.mid", "latin/samba", "beat", "4-4", backbeat(80), drummer="drummer1")
    add("d1/samba1.mid", "latin/samba", "beat", "4-4", backbeat(80), drummer="drummer2")
    add("d1/samba_fill.mid", "latin/samba", "fill", "4-4", [(0.0, SNARE, 90), (0.5, 48, 80), (1.0, 45, 80), (2.0, 43, 80)])
    add("d1/odd.mid", "rock/prog", "beat", "5-4", backbeat(40))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return zipfile.ZipFile(io.BytesIO(buffer.getvalue())), rows


def test_passe_complete_feels_groupes_et_rejets():
    archive, rows = synthetic_archive()
    built = g.build_all(archive, rows)
    rock = built["blocks"]["rock"]["groups"]
    assert set(rock) == {"4-4:straight"} and rock["4-4:straight"]["beat"]["n_files"] == 3
    assert rock["4-4:straight"]["beat"]["steps_per_bar"] == 16
    shuffle = built["blocks"]["rock/shuffle"]["groups"]
    assert set(shuffle) == {"4-4:ternary"} and shuffle["4-4:ternary"]["beat"]["steps_per_bar"] == 12
    assert shuffle["4-4:ternary"]["beat"]["timekeeper"]["roles"]["ride"]["n"] > 0
    # Le fichier 5/4 est refusé avec sa raison, sans mesure.
    prog = built["blocks"]["rock/prog"]
    assert prog["n_rejected"] == 1 and "5-4" in prog["rejected"][0]["reason"] and prog["groups"] == {}
    # Le fill sans contretemps de timekeeper a une preuve dans les toms ; ses mesures existent.
    fill = built["blocks"]["latin/samba"]["groups"]["4-4:straight"]["fill"]
    assert fill["n_files"] == 1


def test_un_fill_sans_preuve_de_feel_herite_du_feel_des_beats_du_style():
    archive, rows = synthetic_archive()
    # Ajoute un fill de shuffle sans contretemps exploitable.
    fill_row = row("d1/shuffle_fill.mid", "rock/shuffle", "fill")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name in archive.namelist():
            z.writestr(name, archive.read(name))
        z.writestr("groove/d1/shuffle_fill.mid", midi_bytes([(0.0, SNARE, 90), (1.0, SNARE, 90), (2.0, KICK, 90)]))
    archive = zipfile.ZipFile(io.BytesIO(buffer.getvalue()))
    built = g.build_all(archive, rows + [fill_row])
    fill = next(r for r in built["results"] if r.row.path == "d1/shuffle_fill.mid")
    assert fill.feel == "ternary" and fill.evidence == "inherited_from_beats"
    assert all(m.feel == "ternary" for m in fill.measures)


def test_dossiers_famille_et_style_secondaire(tmp_path: Path):
    archive, rows = synthetic_archive()
    built = g.build_all(archive, rows)
    folders = g.write_all(built, tmp_path)
    # latin/samba et rock/shuffle sont nommés (ALWAYS_OWN) ; rock/prog (un fichier refusé) reste dans la famille.
    assert set(folders) == {"gmd-latin", "gmd-latin-samba", "gmd-rock", "gmd-rock-shuffle"}
    family = json.loads((tmp_path / "gmd-rock" / "measures-drums.json").read_text(encoding="utf-8"))
    assert set(family["styles"]) == {"rock", "rock/prog"}
    assert family["styles_with_own_folder"] == {"rock/shuffle": "gmd-rock-shuffle"}
    assert family["styles_with_own_folder_summary"]["rock/shuffle"]["groups"]["4-4:ternary"]["beat"]["n_files"] == 2
    # Licence et mention dans chaque JSON et chaque README.
    for folder in folders:
        data = json.loads((tmp_path / folder / "measures-drums.json").read_text(encoding="utf-8"))
        assert data["provenance"]["licence"] == "CC-BY-4.0" and data["provenance"]["sha256"] == drums.SOURCE_SHA256
        text = (tmp_path / folder / "README.md").read_text(encoding="utf-8")
        assert "CC-BY-4.0" in text and "Gillick" in text and drums.SOURCE_SHA256 in text
    inventory = json.loads((tmp_path / "gmd-inventory.json").read_text(encoding="utf-8"))
    assert inventory["provenance"]["counts"]["n_files_rejected"] == 1


def test_sorties_deterministes_et_sans_note_copiee(tmp_path: Path):
    archive, rows = synthetic_archive()
    a, b = tmp_path / "a", tmp_path / "b"
    g.write_all(g.build_all(archive, rows), a)
    g.write_all(g.build_all(archive, rows), b)
    for path in sorted(a.rglob("*")):
        if path.is_file():
            assert path.read_bytes() == (b / path.relative_to(a)).read_bytes(), path
    # Aucune liste de coups par fichier : pas de chemin de MIDI dans les agrégats.
    text = (a / "gmd-rock" / "measures-drums.json").read_text(encoding="utf-8")
    assert "rock0.mid" not in text and "d0/" not in text


def test_patterns_proposes_exigent_trois_fichiers_et_pas_de_fichier_dominant():
    archive, rows = synthetic_archive()
    built = g.build_all(archive, rows)
    rock = built["blocks"]["rock"]["groups"]["4-4:straight"]["proposed_patterns"]
    assert rock["patterns"], rock["skipped"]  # 3 fichiers, 78 mesures chacun : éligible
    densities = {p["density"] for p in rock["patterns"]}
    assert densities == {0, 1, 2}
    d0 = next(p for p in rock["patterns"] if p["density"] == 0)
    assert {h["role"] for h in d0["hits"]} == {"hat_closed"}
    d1 = next(p for p in rock["patterns"] if p["density"] == 1)
    assert [h["step"] for h in d1["hits"] if h["role"] == "snare"] == [4, 12]
    # Deux fichiers seulement (rock/shuffle) : aucun pattern, raison écrite.
    shuffle = built["blocks"]["rock/shuffle"]["groups"]["4-4:ternary"]["proposed_patterns"]
    assert shuffle["patterns"] == [] and shuffle["skipped"]


def test_manifeste_complet_marque_le_sous_ensemble_e7_et_la_famille():
    base = {"drummer": "d1", "session": "d1/s", "id": "d1/s/1", "bpm": "120", "beat_type": "beat",
            "duration": "10.5", "split": "train"}
    rows = [
        {**base, "style": "rock/halftime", "time_signature": "4-4", "midi_filename": "b.mid"},
        {**base, "style": "jazz", "time_signature": "3-4", "midi_filename": "a.mid"},
    ]
    manifest = drums.manifest_rows(drums.parse_rows(rows))
    assert [(m["path"], m["family"], m["group"]) for m in manifest] == [
        ("a.mid", "jazz", "core"), ("b.mid", "rock", None)]
    assert all(m["licence"] == "CC-BY-4.0" for m in manifest)
    # Le sous-ensemble E7 reste 4/4 seulement : le 3/4 jazz n'y entre pas.
    assert drums.select_rows(rows) == []
