"""Séparation de sources (demucs) : `<out>/<modèle>/<id>/<source>.wav`.

Dépendance optionnelle : `pip install -e ".[stems]"`. Les stems dérivent
d'enregistrements sous droits : le dossier de sortie doit être hors dépôt.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_MODEL = "htdemucs"


def default_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def stem_dir(out_root: Path, model: str, track_id: str) -> Path:
    return out_root / model / track_id


def separate(tracks: list[tuple[str, Path]], out_root: Path, model: str = DEFAULT_MODEL,
             device: str | None = None, shifts: int = 1, force: bool = False) -> list[Path]:
    """Sépare chaque `(id, chemin)` ; saute les pistes déjà séparées sauf `force`."""
    try:
        from demucs.api import Separator, save_audio
    except ImportError as exc:  # pragma: no cover - dépend de l'extra
        raise RuntimeError("demucs introuvable : installe l'extra `pip install -e \".[stems]\"`") from exc

    separator = None
    done: list[Path] = []
    for track_id, path in tracks:
        target = stem_dir(out_root, model, track_id)
        if not force and target.is_dir() and any(target.glob("*.wav")):
            done.append(target)
            continue
        if separator is None:
            separator = Separator(model=model, device=device or default_device(), shifts=shifts)
        _, stems = separator.separate_audio_file(path)
        target.mkdir(parents=True, exist_ok=True)
        for name, wav in stems.items():
            save_audio(wav.cpu(), target / f"{name}.wav", samplerate=separator.samplerate)
        done.append(target)
    return done
