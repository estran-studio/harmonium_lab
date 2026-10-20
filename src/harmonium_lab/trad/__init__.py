"""Dataset trad québécois (specs/001-trad-dataset) : corpus, normalisation, manifeste et statistiques (D5)."""

from .blindtest import (
    AudioPlayer,
    build_kit,
    find_audio_player,
    load_feuille,
    normalize_verdict,
    play_kit,
    print_score,
    score_feuille,
    update_feuille,
)
from .cells import bar_to_cell, degree_to_notation, pitch_to_degree
from .features import (
    FEATURE_SCALARS,
    beat_eighths,
    chord_degree_label,
    features,
    parse_chord_symbol,
)
from .compare import (
    EXPLANATIONS,
    compare_to_profile,
    deviations_for_file,
    explain,
    feature_vector,
    nearest_reals,
    reference_stats,
)
from .form import analyze_form, describe_form, plan_to_dict
from .loaders import load_abc, load_engine_midi, name_chord
from . import mine
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
    "AudioPlayer",
    "build_kit",
    "find_audio_player",
    "load_feuille",
    "normalize_verdict",
    "play_kit",
    "print_score",
    "score_feuille",
    "update_feuille",
    "compare_to_profile",
    "deviations_for_file",
    "analyze_form",
    "bar_to_cell",
    "beat_eighths",
    "build_profile",
    "chord_degree_label",
    "describe_form",
    "degree_to_notation",
    "eighths_per_bar",
    "FEATURE_SCALARS",
    "EXPLANATIONS",
    "explain",
    "feature_vector",
    "load_engine_midi",
    "nearest_reals",
    "mode_intervals",
    "mine",
    "name_chord",
    "normalize_mode",
    "reference_stats",
    "score_feuille",
    "pitch_to_degree",
    "plan_to_dict",
    "PROFILE_VERSION",
    "save_profile",
]
