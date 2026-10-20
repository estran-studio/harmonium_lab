import mido
import numpy as np

from harmonium_lab.trad.fiddle_compare import comparison_stem, discontinuities, select_tunes


def absolute(mid):
    tick = 0
    events = []
    for message in mido.merge_tracks(mid.tracks):
        tick += message.time
        events.append((tick, message))
    return events


def test_solo_then_backing_cuts_notes_at_bar_sixteen():
    source = mido.MidiFile(ticks_per_beat=120)
    melody = mido.MidiTrack([mido.Message("program_change", channel=0, program=40),
                            mido.Message("note_on", channel=0, note=69, velocity=55),
                            mido.Message("note_off", channel=0, note=69, time=120),
                            mido.Message("note_on", channel=0, note=76, velocity=110, time=7500),
                            mido.Message("note_off", channel=0, note=76, time=120)])
    backing = mido.MidiTrack([mido.Message("program_change", channel=1, program=32),
                             mido.Message("note_on", channel=1, note=45, velocity=80),
                             mido.Message("note_off", channel=1, note=45, time=3840),
                             mido.Message("note_on", channel=1, note=50, velocity=80),
                             mido.Message("note_off", channel=1, note=50, time=4000)])
    feet = mido.MidiTrack([mido.Message("note_on", channel=9, note=36, velocity=90)])
    source.tracks.extend([melody, backing, feet])
    solo = absolute(comparison_stem(source, melody=True, program=2))
    assert [(t, m.velocity) for t, m in solo if m.type == "note_on"] == [(0, 96), (7620, 96)]
    assert [(t, m.note) for t, m in solo if m.type == "note_off"] == [(120, 69), (7680, 76)]
    assert [m.program for _, m in solo if m.type == "program_change"] == [2]
    accompaniment = absolute(comparison_stem(source, melody=False))
    assert [(t, m.note) for t, m in accompaniment if m.type == "note_on"] == [(3840, 50)]
    assert [(t, m.note) for t, m in accompaniment if m.type == "note_off"] == [(7680, 50)]
    assert all(m.channel == 1 for _, m in accompaniment if hasattr(m, "channel"))
    assert solo[-1][0] == accompaniment[-1][0] == 7680


def test_click_detector_distinguishes_smooth_wave_and_stereo_jump():
    rate = 44100
    smooth = .2 * np.sin(np.arange(rate) * 2 * np.pi * 440 / rate)
    assert discontinuities(smooth)["suspect_count"] == 0
    stereo = np.stack([smooth.copy(), -smooth.copy()], axis=1)
    stereo[rate//2:, 0] += .5
    stereo[rate//2:, 1] -= .5
    detected = discontinuities(stereo)
    assert detected["suspect_count"] == 1
    assert abs(detected["times_s"][0] - .5) < .001


def test_tune_selection_uses_three_named_reels_and_ignores_missing_cache(tmp_path):
    rows = []
    for ident, title in [("other", "Autre reel"), ("anne", "Saint Anne's Reel"),
                         ("bea", "Reel Béatrice"), ("joy", "Joys of Quebec")]:
        rows.append({"id": ident, "title": title, "type": "reel", "source": "chambers"})
        path = tmp_path / "tunes/reel" / (ident + ".abc")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture")
    assert [r["id"] for r in select_tunes(list(reversed(rows)), tmp_path)] == ["anne", "bea", "joy"]
