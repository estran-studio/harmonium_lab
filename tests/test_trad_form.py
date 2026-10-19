"""Tests DS-T3b : forme des airs depuis le texte ABC (reprises, voltas, levées).

Sans réseau : fixtures locales + MIDI généré. La couverture du vrai corpus
relève de `harmonium-lab trad-form-report`, pas des tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harmonium_lab.trad import features, load_abc, load_profile

FIXTURES = Path(__file__).parent / "fixtures" / "trad"


def form_of(name: str) -> dict:
    return features(load_abc(FIXTURES / name))["form"]


def feat_of(name: str) -> dict:
    return features(load_abc(FIXTURES / name))


class TestPickup:
    def test_pickup_aabb(self) -> None:
        form = form_of("reel_pickup.abc")
        assert form["scheme"] == "AABB"
        assert form["parts"] == [8, 8, 8, 8]
        assert form["is_aabb"] is True
        assert form["pickup"] == 2.0
        assert form["cause"] is None

    def test_pickup_bar_count(self) -> None:
        assert feat_of("reel_pickup.abc")["n_bars"] == 32


class TestVoltas:
    def test_volta_aabb(self) -> None:
        form = form_of("reel_volta.abc")
        assert form["scheme"] == "AABB"
        assert form["parts"] == [8, 8, 8, 8]
        assert form["is_aabb"] is True

    def test_endings_differ_between_passes(self) -> None:
        feat = feat_of("reel_volta.abc")
        cells = feat["cells"]["per_bar"]
        assert len(cells) == 32
        # Fins 1re/2e différentes, corps identiques entre les passes.
        assert cells[7] != cells[15]
        assert cells[0:7] == cells[8:15]


class TestDoubleColon:
    def test_double_colon_aabb(self) -> None:
        form = form_of("reel_double_colon.abc")
        assert form["scheme"] == "AABB"
        assert form["is_aabb"] is True
        assert feat_of("reel_double_colon.abc")["n_bars"] == 32


class TestSixteenBars:
    def test_sixteen_not_aabb(self) -> None:
        form = form_of("reel_16bars.abc")
        assert form["scheme"] == "AA"
        assert form["parts"] == [16, 16]
        assert form["is_aabb"] is False
        assert form["cause"] == "partie-unique"


class TestThreeParts:
    def test_three_parts(self) -> None:
        form = form_of("reel_3parts.abc")
        assert form["scheme"] == "AABBCC"
        assert form["parts"] == [8] * 6
        assert form["is_aabb"] is False
        assert form["cause"] == "trois-parties-et-plus"
        assert feat_of("reel_3parts.abc")["n_bars"] == 48


class TestFallback:
    def test_music21_fallback_marked(self, tmp_path: Path) -> None:
        # Sans K: : l'analyse ABC directe échoue, music21 prend le relais.
        abc = tmp_path / "sans_cle.abc"
        abc.write_text(
            "X:1\nT:Sans cle\nM:4/4\nL:1/8\n"
            "|:DFAF DFAF|GBAG GBAG|AFDF AFDF|EAEA A2AA:|"
            ":DFAF DFAF|GBAG GBAG|AFDF AFDF|EAEA A2AA:|\n"
        )
        tune = load_abc(abc)
        assert tune.form["source"] == "music21-fallback"
        assert tune.form["cause"].startswith("repli-music21:")
        assert features(tune)["n_bars"] > 0

    def test_no_crash_on_fixtures(self) -> None:
        for name in [
            "reel_dmajor.abc", "jig_gmajor.abc", "waltz_dmajor.abc",
            "crooked_reel.abc", "reel_pickup.abc", "reel_volta.abc",
            "reel_double_colon.abc", "reel_16bars.abc", "reel_3parts.abc",
        ]:
            feat = feat_of(name)
            assert feat["n_bars"] > 0
            assert feat["form"]["scheme"]


class TestFormReportCli:
    def test_report_runs(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        import shutil

        from harmonium_lab.cli import main

        tunes = tmp_path / "tunes" / "reel"
        tunes.mkdir(parents=True)
        for name in ("reel_dmajor.abc", "reel_16bars.abc"):
            shutil.copy(FIXTURES / name, tunes / name)
        manifest = tmp_path / "manifest.jsonl"
        manifest.write_text(
            '{"id": "reel_dmajor", "title": "Reel Majeur"}\n'
            '{"id": "reel_16bars", "title": "Reel Seize"}\n'
        )
        assert main(["trad-form-report", "--type", "reel", "--corpus", str(tmp_path)]) == 0
        out = capsys.readouterr().out
        assert "AABB" in out and "reel_dmajor" in out and "reel_16bars" in out

    def test_report_no_tunes(self, tmp_path: Path) -> None:
        from harmonium_lab.cli import main

        assert main(["trad-form-report", "--type", "reel", "--corpus", str(tmp_path)]) == 1
