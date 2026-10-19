"""Dataset trad québécois (specs/001-trad-dataset) : corpus, normalisation, manifeste et statistiques (D5)."""

from .cells import bar_to_cell, degree_to_notation, pitch_to_degree
from .features import (
    FEATURE_SCALARS,
    beat_eighths,
    chord_degree_label,
    features,
    parse_chord_symbol,
)
from .form import analyze_form, describe_form, plan_to_dict
from .loaders import load_abc, load_engine_midi, name_chord
from .model import (
    Note,
    TradTune,
    eighths_per_bar,
    mode_intervals,
    normalize_mode,
)
from .profile import PROFILE_VERSION, build_profile, load_profile, save_profile

__all__ = [
    "Note",
    "TradTune",
    "analyze_form",
    "bar_to_cell",
    "beat_eighths",
    "build_profile",
    "chord_degree_label",
    "describe_form",
    "degree_to_notation",
    "eighths_per_bar",
    "FEATURE_SCALARS",
    "features",
    "load_abc",
    "load_engine_midi",
    "load_profile",
    "mode_intervals",
    "name_chord",
    "normalize_mode",
    "parse_chord_symbol",
    "pitch_to_degree",
    "plan_to_dict",
    "PROFILE_VERSION",
    "save_profile",
]
