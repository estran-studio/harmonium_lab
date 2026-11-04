"""Tests de la mélodie swing (WJazzD, E12) : mesures, banque synthétisée, refus de copie, comparaison.

Tout est synthétique : les mesures sont écrites à la main, la vérité terrain est un mini JSON au format
`--record-truth`. Aucune note de solo réel n'entre dans `tests/`. Les contrôles sur la vraie base
(facultatifs) sont marqués `skipif`.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from harmonium_lab.backing import melody_cells as mc
from harmonium_lab.backing import melody_compare as cmp
from harmonium_lab.backing import melody_measures as mm
from harmonium_lab.backing import wjazzd
from harmonium_lab.backing.chords import parse_wjazzd

C7 = parse_wjazzd("C7")
CJ7 = parse_wjazzd("Cj7")


def bar(index: int, notes: list[tuple[int, int, int]], chord=C7) -> mm.MBar:
    """Mesure de `(créneau, hauteur, durée)` sur un seul accord."""
    return mm.MBar(index, tuple(mm.MNote(*n) for n in notes), (chord,) * 4)


def cell(role: str, notation: str) -> mc.Cell:
    return mc.Cell(role, tuple(mc.HOLD if t == "-" else int(t) for t in notation.split()))


# ── Primitives de mesure ─────────────────────────────────────────────────

@pytest.mark.parametrize("semitones, steps", [(0, 0), (1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (7, 4), (9, 5),
                                              (11, 6), (12, 7), (14, 8), (-3, -2), (-12, -7)])
def test_steps_of_compte_les_pas_de_la_gamme_majeure(semitones, steps):
    assert mm.steps_of(semitones) == steps


def test_relation_nomme_la_note_d_accord_la_gamme_et_le_chromatisme():
    assert [mm.relation(C7, p) for p in (60, 64, 67, 70, 69, 62, 61)] == \
        ["root", "third", "fifth", "seventh", "scale", "scale", "chromatic"]
    assert mm.relation(parse_wjazzd("C6"), 69) == "tone"  # le 6 écrit est une note de l'accord


def test_attaques_creneaux_et_parts_d_accord_sur_les_temps():
    # Mesure 1 : quatre attaques sur les temps, trois dans C7 ; mesure 2 : une croche hors accord (D, scale).
    bars = [bar(1, [(0, 60, 2), (2, 64, 2), (4, 62, 2), (6, 67, 2)]), bar(2, [(0, 60, 1), (1, 62, 7)])]
    doc = mm.measure([bars])
    assert doc["total"]["attacks_per_bar"]["counts"]["4"] == 1 and doc["total"]["attacks_per_bar"]["counts"]["2"] == 1
    assert doc["slot_attack_share"]["0"] == 1.0 and doc["slot_attack_share"]["1"] == 0.5
    assert doc["targets"]["beats"]["counts"]["scale"] == 1  # le ré du temps 3 de la mesure 1
    # Temps 1 et 3 : do, ré (mesure 1), do (mesure 2) ; le ré de la mesure 2 est sur une croche.
    assert doc["strong_chord_share"] == pytest.approx(2 / 3, abs=1e-3)
    assert doc["offbeat_chord_share"] == 0.0  # le ré de la croche


def test_anticipation_comptee_et_liee_quand_la_mesure_suivante_ne_rejoue_pas_le_temps_un():
    bars = [bar(1, [(0, 60, 2), (7, 64, 1)]), bar(2, [(2, 62, 6)]), bar(3, [(0, 60, 2), (7, 64, 1)]),
            bar(4, [(0, 67, 8)])]
    doc = mm.measure([bars])["anticipation"]
    assert doc["bars_with_attack_7"] == 2 and doc["tied"] == 1 and doc["bars_without_downbeat"] == 1


def test_une_phrase_se_ferme_sur_un_silence_d_une_noire():
    # Deux attaques, un silence de quatre croches, une troisième : deux phrases.
    runs = list(mm.phrase_runs([[bar(1, [(0, 60, 1), (1, 62, 1), (6, 64, 1)])][0]]))
    assert [len(r) for r in runs] == [2, 1]


# ── Vérité terrain du moteur ─────────────────────────────────────────────

def truth_file(tmp_path: Path, notes: list[dict]) -> Path:
    measure = {"position": {"tune_index": 0, "key": 5},
               "chord_changes": [{"start_step": 0, "context": {"root_pc": 0, "bass_pc": 0, "quality": "7", "is_minor": False}}],
               "notes": notes}
    path = tmp_path / "truth.json"
    path.write_text(json.dumps({"measures": [{"bar": 1, "measure": measure}]}), encoding="utf-8")
    return path


def test_verite_terrain_ne_lit_que_la_melodie_et_compte_les_pas_impairs(tmp_path):
    notes = [{"track": 0, "start_step": 0, "pitch": 60, "duration_steps": 4},
             {"track": 0, "start_step": 5, "pitch": 62, "duration_steps": 1},  # seizième : écarté
             {"track": 0, "start_step": 8, "pitch": 64, "duration_steps": 8},
             {"track": 2, "start_step": 0, "pitch": 36, "duration_steps": 4}]  # basse
    solos, stats = mm.truth_solos([truth_file(tmp_path, notes)])
    assert [(n.slot, n.pitch, n.dur) for n in solos[0][0].notes] == [(0, 60, 2), (4, 64, 4)]
    assert stats["dropped"] == 1 and solos[0][0].chords[0].symbol.endswith("7")


# ── Cellules : niveaux, invariants, rapprochement ────────────────────────

def test_niveau_le_plus_bas_respecte():
    assert mc.level_of(mc.stats_of(cell("open", "5 - 3 - 1 - - -"))) == 1
    assert mc.level_of(mc.stats_of(cell("run", "5 - 8 - 8 - - -"))) == 2  # saut de 5 demi-tons : trop pour le niveau 1
    assert mc.level_of(mc.stats_of(cell("run", "1 2 3 4 5 6 7 8"))) == 3  # huit attaques, une octave d'ambitus
    assert mc.level_of(mc.stats_of(cell("run", "1 2 3 4 5 6 7 1"))) == 4  # saut de 11 demi-tons
    assert mc.level_of(mc.stats_of(cell("arp", "1 8 1 8 1 8 1 8"))) == 4  # saut d'octave > 7


def test_invariants_d5_du_moteur():
    assert mc.valid_cell(cell("run", "1 2 3 4 5 6 7 8"))
    assert not mc.valid_cell(cell("run", "- 2 3 4 5 6 7 8"))  # commence par une tenue
    assert not mc.valid_cell(cell("run", "1 2 3 4 5 6 7 9"))  # ambitus de huit pas
    assert not mc.valid_cell(cell("run", "1 7 1 7 1 2 3 4"))  # trois sauts > quinte


def test_le_rapprochement_effondre_une_ligne_conjointe_pas_un_arpege():
    arp, step = cell("arp", "1 3 5 3 1 3 5 3"), cell("run", "1 2 1 2 1 2 1 2")
    c7 = (0, 4, 7, 10)
    assert mc.realize(arp, 0, c7) == [0, 4, 7, 4, 0, 4, 7, 4]  # do mi sol : rien ne bouge
    assert mc.realize(step, 0, c7) == [0] * 8  # ré (2 demi-tons de do comme de mi) → do : premier minimum, la fondamentale
    assert mc.realized_repeat_share(step) > 3 * mc.realized_repeat_share(arp)


def test_toml_aller_retour_et_notation_du_moteur():
    bank = [(cell("open", "5 - 3 - 1 - - -"), 7), (cell("cad_full", "3 - 2 - 1 - - -"), 3)]
    text = mc.to_toml(bank, seed=12)
    assert {(c.role, c.notation, w) for c, w in mc.parse_toml_cells(text)} == \
        {("open", "5 - 3 - 1 - - -", 7), ("cad_full", "3 - 2 - 1 - - -", 3)}
    assert "ODbL 1.0 §4.3" in text and "# niveau 1" in text


# ── Refus de copie ───────────────────────────────────────────────────────

def solo_with_run() -> list[mm.MBar]:
    """Une gamme de huit croches conjointes (do à do) : tous les pas valent +1 pas diatonique."""
    return [bar(1, [(s, p, 1) for s, p in enumerate((60, 62, 64, 65, 67, 69, 71, 72))])]


def test_une_cellule_qui_recopie_une_suite_du_solo_est_refusee():
    guard = mc.CopyGuard([solo_with_run()])
    assert guard.matches(cell("run", "1 2 3 4 5 6 7 8")) == [f"{mc.N_RHYTHM} notes, pas et durées",
                                                              f"{mc.N_CONTOUR} notes, pas"]
    # Sept notes aux mêmes pas, une tenue au milieu : aucune fenêtre de six notes n'a les durées du solo,
    # seul le critère de contour (sept notes, sans durées) refuse.
    assert guard.matches(cell("run", "1 2 3 4 - 5 6 7")) == [f"{mc.N_CONTOUR} notes, pas"]
    # Un pas différent dans chaque fenêtre de N notes : jamais refusée.
    assert guard.matches(cell("run", "1 3 2 4 3 5 4 6")) == []


def test_une_suite_plus_courte_que_n_n_est_pas_une_copie():
    guard = mc.CopyGuard([solo_with_run()])
    assert guard.matches(cell("run", "1 2 3 4 5 - - -")) == []  # cinq notes, N = 6 et 7


def test_l_index_ne_franchit_pas_un_silence():
    # Cinq attaques, silence d'une noire, trois attaques : aucune fenêtre de six notes.
    solo = [bar(1, [(0, 60, 1), (1, 62, 1), (2, 64, 1), (3, 65, 1), (4, 67, 1), (7, 69, 1)]),
            bar(2, [(2, 60, 1), (3, 62, 1)])]
    index = mm.NGramIndex([solo], mc.N_RHYTHM)
    assert not index.keys


# ── Comparaison et conformité ────────────────────────────────────────────

def test_distance_nulle_d_un_ensemble_a_lui_meme():
    bars = [bar(i, [(0, 60, 1), (1, 62, 1), (2, 64, 2), (4, 67, 4)]) for i in range(1, 5)]
    doc = mm.measure([bars])
    doc["provenance"] = {}
    result = cmp.compare(doc, doc)
    assert result["distance"] == 0.0 and not result["missing"]


def test_conformite_aux_bornes_du_niveau_et_saut_d_une_mesure_a_l_autre():
    ok = bar(1, [(0, 60, 2), (2, 62, 2), (4, 64, 4)])  # 3 attaques, saut 2, ambitus 4
    jump = bar(2, [(0, 72, 4), (4, 74, 4)])  # saut de 8 demi-tons depuis le mi de la mesure 1
    closing = bar(3, [(0, 40, 8)])  # la mesure de clôture n'est pas filtrée : écartée
    out = cmp.compliance([[ok, jump, closing]], 1)
    assert out["bars"] == 2 and out["bars_out_of_bounds"] == 1 and out["violations"]["leap"] == 1
    assert out["worst"]["leap"] == 8


# ── Banque versionnée ────────────────────────────────────────────────────

BANK = mc.CELLS_OUTPUT
MEASURES = mm.OUTPUT
REAL = pytest.mark.skipif(not wjazzd.RAW_DB.is_file(), reason="brut WJazzD absent (cache gitignoré)")
ARTEFACTS = pytest.mark.skipif(not (BANK.is_file() and MEASURES.is_file()), reason="banque non générée")


@ARTEFACTS
def test_la_banque_versionnee_respecte_les_invariants_et_reste_filtrable():
    bank = mc.parse_toml_cells(BANK.read_text(encoding="utf-8"))
    assert {c.role for c, _ in bank} == set(mc.ROLE_COUNTS)
    assert all(mc.valid_cell(c) and w >= 1 for c, w in bank)
    levels = mc.level_table(bank)
    for role in mc.ROLE_COUNTS:  # E10 : de quoi tirer sans réécriture aux niveaux 1 à 3 pour chaque rôle
        assert all(levels[role][str(t)] >= 3 for t in (1, 2, 3)), (role, levels[role])
    cap = mc.Model(json.loads(MEASURES.read_text(encoding="utf-8"))).repeat_cap
    assert all(mc.realized_repeat_share(c) <= cap + 1e-9 for c, _ in bank)
    assert all(c.attacks[-1][1] % 7 == 1 for c, _ in bank if c.role == "cad_full")
    assert all(c.attacks[-1][1] % 7 in (2, 5, 0) for c, _ in bank if c.role == "cad_half")


@ARTEFACTS
def test_la_synthese_est_deterministe_a_graine_egale():
    model = mc.Model(json.loads(MEASURES.read_text(encoding="utf-8")))

    def draw(seed: int) -> list[str]:
        rng = random.Random(seed)
        return [c.notation for c in (mc.synthesize(model, "run", rng) for _ in range(400)) if c]

    assert draw(3) == draw(3) and draw(3) != draw(4)


@REAL
@ARTEFACTS
def test_aucune_cellule_de_la_banque_n_est_une_suite_de_n_notes_d_un_solo():
    solos, _ = mm.corpus_solos()
    guard = mc.CopyGuard(solos)
    bank = mc.parse_toml_cells(BANK.read_text(encoding="utf-8"))
    assert [c.notation for c, _ in bank if guard.matches(c)] == []
