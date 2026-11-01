"""Tests de `harmonium_lab.backing.engine_values` : mesures agrégées synthétiques → valeurs de profil."""

from __future__ import annotations

import tomllib

from harmonium_lab.backing import engine_values


def hit(role: str, step: int, note: int, rel: float, velocity: float) -> dict:
    return {"role": role, "step": step, "note": note, "rel_velocity": rel, "velocity": velocity}


def drums_doc() -> dict:
    """Un groove de ride (poids 40), un autre plus fort (poids 10) et une relance sans ride."""
    quiet = [hit("ride", 0, 51, 0.8, 56.0), hit("ride", 4, 51, 1.2, 84.0), hit("hat_pedal", 4, 44, 1.0, 60.0)]
    loud = [hit("ride", 0, 51, 1.0, 140.0 / 2), hit("ride", 4, 51, 1.4, 98.0)]
    fill = [hit("snare", 0, 38, 1.5, 90.0), hit("kick", 2, 36, 1.0, 70.0), hit("tom", 6, 43, 1.0, 64.0)]
    return {"proposed_patterns": {"patterns": [
        {"density": 1, "weight": 40, "hits": quiet},
        {"density": 1, "weight": 10, "hits": loud},
        {"density": 2, "weight": 5, "hits": fill},
    ]}}


def test_la_voix_porte_la_velocite_mediane_du_role_et_la_note_la_plus_frequente():
    doc = drums_doc()
    voices = engine_values.voices_from(doc["proposed_patterns"]["patterns"])
    assert voices["ride"] == {"note": 51, "velocity": 70}
    assert voices["hat_pedal"]["note"] == 44
    # 90 / 1,5 = 60, au gain de calage du rôle (kit de rendu)
    assert voices["snare"]["velocity"] == round(60 * engine_values.ROLE_GAIN["snare"])


def test_le_niveau_du_groupe_est_ramene_a_celui_de_la_voix_en_gardant_la_forme_des_accents():
    text = engine_values.percussion_toml(drums_doc())
    table = tomllib.loads(text)
    voices = {v["name"]: v for v in table["voices"]}
    patterns = [p for p in table["patterns"] if p["density"] == 1]
    assert [p["weight"] for p in patterns] == [40, 10]

    def levels(pattern: dict) -> list[int]:
        return [voices["ride"]["velocity"] + h.get("delta_velocity", 0) for h in pattern["hits"]
                if h["voice"] == "ride"]

    quiet, loud = (levels(p) for p in patterns)
    # Même forme d'accent (temps 2 plus fort que le temps 1 dans un rapport 1,5 puis 1,4), même niveau
    # moyen : le groupe joué plus fort dans l'enregistrement n'est pas plus fort dans le profil.
    assert quiet[1] > quiet[0] and loud[1] > loud[0]
    assert abs(sum(quiet) / len(quiet) - sum(loud) / len(loud)) <= 1


def test_la_relance_sans_ride_devient_la_cadence_de_densite_2_pas_un_pattern_ordinaire():
    table = tomllib.loads(engine_values.percussion_toml(drums_doc()))
    assert {p["density"] for p in table["patterns"]} == {1}
    (cadence,) = table["cadence_patterns"]
    assert cadence["density"] == 2
    assert {h["voice"] for h in cadence["hits"]} == {"snare", "kick", "tom"}


def test_les_voix_grave_et_aigue_sont_routees_sur_les_pistes_du_moteur():
    table = tomllib.loads(engine_values.percussion_toml(drums_doc()))
    tracks = {v["name"]: v["track"] for v in table["voices"]}
    assert tracks["kick"] == "PercussionLow"
    assert tracks["ride"] == tracks["snare"] == "PercussionHigh"


def test_la_sortie_est_deterministe_et_porte_l_en_tete():
    a = engine_values.percussion_toml(drums_doc(), "# en-tête\n")
    assert a == engine_values.percussion_toml(drums_doc(), "# en-tête\n")
    assert a.startswith("# en-tête\n")


def bass_doc() -> dict:
    return {"groups": {"all": {
        "approach": {"all": {"weights": {"shares": {"none": 0.592, "chromatic": 0.214, "diatonic": 0.194}}}},
        "passage_engine": {"shares": {"chord_tone": 0.478, "chromatic": 0.293, "scale_step": 0.229}},
    }}}


def test_les_poids_de_basse_sont_des_entiers_de_somme_cent_et_les_passages_chromatiques_vont_aux_pas_de_gamme():
    weights = engine_values.bass_weights(bass_doc())
    approach, passing = weights["approach"], weights["passing"]
    assert sum(approach.values()) == 100 and sum(passing.values()) == 100
    # 59 + 21 + 19 = 99 : l'arrondi est rendu au poids le plus fort (`none`).
    assert approach == {"none_weight": 60, "chromatic_weight": 21, "diatonic_weight": 19}
    assert passing == {"chord_tone_weight": 48, "scale_step_weight": 52}
