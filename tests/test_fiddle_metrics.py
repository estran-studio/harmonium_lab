import numpy as np
import pytest

from harmonium_lab.trad.fiddle_compare import RATE
from harmonium_lab.trad.fiddle_metrics import level_and_brightness


def test_velocity_level_and_brightness_are_separate_quantities():
    time = np.arange(RATE)/RATE
    quiet = np.column_stack([.1*np.sin(2*np.pi*440*time)]*2)
    louder = level_and_brightness(quiet*2)
    baseline = level_and_brightness(quiet)
    assert louder['rms_dbfs']-baseline['rms_dbfs'] == pytest.approx(6.021,abs=.002)
    assert louder['centroid_hz'] == baseline['centroid_hz'] == 440
    bright = quiet + np.column_stack([.1*np.sin(2*np.pi*10000*time)]*2)
    assert level_and_brightness(bright)['energy_above_8khz_pct'] == pytest.approx(50,abs=.01)
    assert level_and_brightness(bright)['centroid_hz'] > 5000
    # La mesure ne doit pas annuler des canaux en opposition de phase.
    quiet[:,1] *= -1
    assert level_and_brightness(quiet) == baseline
