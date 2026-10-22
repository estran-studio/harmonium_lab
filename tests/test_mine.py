"""Tests DS-T5 : extraction D7 sur mini-corpus locaux (aucun réseau)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harmonium_lab.trad import mine as M

REEL_AABB = """X:1
T:Mini reel
R:reel
M:4/4
L:1/8
K:D
|: "D"DFAF DFAF | "G"GBAG GBAG | "D"AFDF AFDF | "A"E2EA A2AA | "D"DFAF DFAF | "G"GBAG GBAG | "Em"EFGE EFGE | "D"DFAd DEDD :|
|: "D"d2fd Adfd | "G"g2bg Agbg | "D"afdf afdf | "A"a2ea Aeaa | "D"d2fd Adfd | "G"g2bg Agbg | "Bm"BABc dcBA | "D"f2af ded2 :|
"""

REEL_CROCHE = """X:2
T:Mini croche
R:reel
M:4/4
L:1/8
K:D
|: "D"DFAF DFAF | "G"GBAG GBAG | "D"DFAF DFAFD | "A"EAAc BAAc :|
|: "D"d2fd Adfd | "G"g2bg Agbg | "D"afdf afdf | "A"a2ea Aeaa :|
"""


def engine_bank_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent.parent / "harmonium" / "profiles" / "reel_quebecois" / "cells.toml",
        Path("/Users/william.quintal/Project/bascanada/harmonium/profiles/reel_quebecois/cells.toml"),
        here.parent.parent.parent / "harmonium" / "harmonium_core" / "src" / "trad" / "reel_cells.toml",
        Path("/Users/william.quintal/Project/bascanada/harmonium/harmonium_core/src/trad/reel_cells.toml"),
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    pytest.skip("banque moteur introuvable (lecture seule harmonium)")


@pytest.fixture
def mini_corpus(tmp_path: Path) -> Path:
    tunes = tmp_path / "tunes" / "reel"
    tunes.mkdir(parents=True)
    (tunes / "aabb.abc").write_text(REEL_AABB)
    (tunes / "croche.abc").write_text(REEL_CROCHE)
    (tmp_path / "VERSION").write_text("test+2\n")
    return tmp_path


class TestValidateCell:
    def test_valid(self) -> None:
        assert M.validate_cell("1 3 5 3 1 3 5 3") is None
        assert M.validate_cell("3 2 1 7, 1 - - -") is None

    def test_rejects(self) -> None:
        assert M.validate_cell("1 3 5") == "mauvais-nombre"
        assert M.validate_cell("- 3 5 3 1 3 5 3") == "commence-par-tenue"
        assert M.validate_cell("0 1 2 3 4 5 6 7") == "degré-hors-plage"
        assert M.validate_cell("1 2 3 4 5 6 7 15") == "degré-hors-plage"
        assert M.validate_cell("1, 1 1 1 1 1 1 8") == "ambitus-dépassé"
        # Deux sauts > quinte (1->8, 8->1) : rejeté.
        assert M.validate_cell("1 8 1 8 1 2 3 4") == "trop-de-grands-sauts"
        # Un seul grand saut : accepté.
        assert M.validate_cell("1 8 7 6 5 4 3 2") is None

    def test_engine_bank_valid(self) -> None:
        for role, notes in M.load_engine_bank(engine_bank_path()):
            assert role in M.ROLES
            assert M.validate_cell(notes) is None, notes


class TestClassifyCell:
    def test_run(self) -> None:
        assert M.classify_cell([62, 64, 66, 67, 69, 71, 73, 74], 2, "ionian") == "run"

    def test_arp(self) -> None:
        assert M.classify_cell([62, 66, 69, 66, 62, 66, 69, 66], 2, "ionian") == "arp"

    def test_turn(self) -> None:
        assert M.classify_cell([69, 71, 69, 67, 66, 67, 66, 64], 2, "ionian") == "turn"


class TestMineCells:
    def test_roles_positionnels(self, mini_corpus: Path) -> None:
        cells, stats = M.mine_cells(mini_corpus, "reel", top_per_role=10)
        by_role = {c["role"]: c["notes"] for c in cells}
        assert stats["airs_lus"] == 2
        assert stats["airs_erreur"] == 0
        # Mesure 1 -> open, avec la cellule exacte du fixture.
        opens = [c for c in cells if c["role"] == "open"]
        assert any(c["notes"] == "1 3 5 3 1 3 5 3" for c in opens)
        assert any(c["role"] == "cad_half" for c in cells)
        assert any(c["role"] == "cad_full" for c in cells)

    def test_croche_hors_positionnel(self, mini_corpus: Path) -> None:
        _, stats = M.mine_cells(mini_corpus, "reel", top_per_role=10)
        assert stats["airs_croche_positionnel_ignore"] == 1

    def test_top_par_role(self, mini_corpus: Path) -> None:
        cells, _ = M.mine_cells(mini_corpus, "reel", top_per_role=1)
        assert len(cells) <= len(M.ROLES)
        for role in M.ROLES:
            assert len([c for c in cells if c["role"] == role]) <= 1

    def test_render_bank(self, mini_corpus: Path) -> None:
        cells, _ = M.mine_cells(mini_corpus, "reel", top_per_role=10)
        text = M.render_bank(cells, "reel", "test+2", 2, "2026-10-20")
        assert text.startswith("# Cellules minées")
        assert "test+2 (2 airs)" in text
        assert text.rstrip().endswith("]")
        for c in cells:
            assert M.validate_cell(c["notes"]) is None
            assert f'{{ role = "{c["role"]}", notes = "{c["notes"]}" }}' in text


class TestMineHarmony:
    def test_harmony(self, mini_corpus: Path) -> None:
        h = M.mine_harmony(mini_corpus, "reel")
        assert h["airs"] == 2
        assert h["top_accords"][0]["degre"] == "I"
        assert "V" in h["mesure_4"]
        assert "I" in h["mesure_8"]
        assert any("->" in b for b in h["bigrammes"])
        assert "ionian" in h["par_mode"]


class TestMineTempo:
    def test_q_manquant_signale(self, tmp_path: Path) -> None:
        tunes = tmp_path / "tunes" / "reel"
        tunes.mkdir(parents=True)
        (tunes / "a.abc").write_text(REEL_AABB)
        (tmp_path / "VERSION").write_text("test+1\n")
        t = M.mine_tempo(tmp_path, "reel")
        assert t["types"]["reel"]["airs"] == 1
        assert t["types"]["reel"]["tempo_q"] is None
        assert "reel" in t["q_manquant"]

    def test_q_lu(self, tmp_path: Path) -> None:
        tunes = tmp_path / "tunes" / "jig"
        tunes.mkdir(parents=True)
        (tunes / "a.abc").write_text("X:1\nT:J\nR:jig\nM:6/8\nL:1/8\nQ:1/4=120\nK:G\n|:GAG BAG|ABA AGA|\n")
        t = M.mine_tempo(tmp_path, "jig")
        q = t["types"]["jig"]["tempo_q"]
        assert q is not None and q["min"] == 120
        assert t["types"]["jig"]["signatures"] == {"6/8": 1}


class TestMineCli:
    def test_mine_cells_cli(self, mini_corpus: Path, tmp_path: Path) -> None:
        from harmonium_lab.cli import main

        out = tmp_path / "reel_cells.toml"
        assert main(["mine-cells", "--type", "reel", "--corpus", str(mini_corpus),
                     "-o", str(out), "--top", "2"]) == 0
        assert out.exists()
        weights = tmp_path / "reel_cells.weights.json"
        assert weights.exists()
        assert json.loads(weights.read_text())[0]["count"] >= 1

    def test_mine_harmony_cli(self, mini_corpus: Path, tmp_path: Path) -> None:
        from harmonium_lab.cli import main

        out = tmp_path / "h.json"
        assert main(["mine-harmony", "--type", "reel", "--corpus", str(mini_corpus),
                     "-o", str(out)]) == 0
        assert json.loads(out.read_text())["airs"] == 2

    def test_mine_tempo_cli(self, mini_corpus: Path, capsys: pytest.CaptureFixture) -> None:
        from harmonium_lab.cli import main

        assert main(["mine-tempo", "--type", "reel", "--corpus", str(mini_corpus)]) == 0
        assert "MANQUANT" in capsys.readouterr().out
