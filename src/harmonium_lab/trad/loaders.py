"""Chargeurs ``TradTune`` : ABC du corpus et MIDI du moteur (D3/D5).

ABC : parsé par ``music21`` (``converter.parse`` sur ``*.abc``), reprises
développées par ``expandRepeats`` (AABB joué), voix principale = première
partie, accords = ``ChordSymbol`` (annotations ``"G"`` de l'ABC).

MIDI moteur : parsé par ``mido``. Canal 0 = mélodie, canal 1 = accords
(symboles reconstruits depuis les simultanéités), canal 2 = basse (doublure,
ignorée pour les symboles), canaux 3/4/9 = pieds (ignorés). L'export du
moteur ne ferme pas toujours ses notes (pas de ``note_off``) : les notes
restées ouvertes sont closes en legato (fin = attaque suivante du même
canal, sinon fin de piste). Signature rythmique et tonalité lues depuis
les méta-événements ; sans méta de tonalité, repli Krumhansl-Schmuckler
de ``music21`` sur la mélodie. Sans méta de signature, repli documenté
sur 4/4 (ou forçage explicite).
"""

from __future__ import annotations

from pathlib import Path

import mido

from .model import Note, TradTune, eighths_per_bar, normalize_mode

MELODY_CHANNEL = 0
CHORDS_CHANNEL = 1

_CHORD_THIRD_MAJOR = 4
_CHORD_THIRD_MINOR = 3
_CHORD_FIFTH = 7
_CHORD_TRITONE = 6


def load_abc(path: Path | str) -> TradTune:
    """Charge un air ABC en ``TradTune`` (reprises développées)."""
    import music21

    path = Path(path)
    score = music21.converter.parse(str(path))
    expanded = score.expandRepeats()
    parts = list(expanded.parts)
    if not parts:
        raise ValueError(f"{path}: aucune partie trouvée")
    part = parts[0]

    measures = list(part.getElementsByClass("Measure"))
    if not measures:
        raise ValueError(f"{path}: aucune mesure trouvée")

    first_ts = part.recurse().getElementsByClass("TimeSignature")
    if not len(first_ts):
        raise ValueError(f"{path}: signature rythmique absente")
    ts = first_ts[0]
    meter = f"{ts.numerator}/{ts.denominator}"
    eighths = eighths_per_bar(ts.numerator, ts.denominator)

    tonic_pc, key_name, mode = _key_from_stream(expanded)

    bars: list[list[Note]] = []
    chords: list[list[tuple[float, str]]] = []
    for measure in measures:
        bar: list[Note] = []
        for el in measure.recurse().notes:
            if el.isRest or isinstance(el, music21.harmony.Harmony):
                # ChordSymbol ("G" de l'ABC) : traité dans les accords ci-dessous.
                continue
            if el.isChord:
                # Doubles-cordes de violon : la plus aiguë porte la mélodie.
                pitches = sorted(p.midi for p in el.pitches)
                pitch = pitches[-1]
            else:
                pitch = el.pitch.midi
            onset = round(float(el.offset) * 2.0, 3)
            duration = round(float(el.quarterLength) * 2.0, 3)
            bar.append(Note(pitch=pitch, onset=onset, duration=duration))
        bar.sort(key=lambda n: (n.onset, n.pitch))
        bars.append(bar)

        bar_chords: list[tuple[float, str]] = []
        for el in measure.recurse().getElementsByClass("ChordSymbol"):
            bar_chords.append((round(float(el.offset) * 2.0, 3), str(el.figure)))
        bar_chords.sort()
        chords.append(bar_chords)

    return TradTune(
        tune_id=path.stem,
        key_tonic_pc=tonic_pc,
        key_name=key_name,
        mode=mode,
        meter=meter,
        eighths_per_bar=eighths,
        bars=bars,
        chords=chords,
        source="abc",
    )


def _key_from_stream(score) -> tuple[int, str, str]:
    """Tonique (pc), nom, mode : clé explicite > armure > Krumhansl."""
    from music21 import key as m21key

    flat = score.flatten()
    keys = list(flat.getElementsByClass(m21key.Key))
    if keys:
        k = keys[0]
        return k.tonic.pitchClass, k.tonic.name, normalize_mode(k.mode)
    sigs = list(flat.getElementsByClass(m21key.KeySignature))
    if sigs:
        k = sigs[0].asKey()
        return k.tonic.pitchClass, k.tonic.name, normalize_mode(k.mode)
    detected = score.analyze("key")
    return (
        detected.tonic.pitchClass,
        detected.tonic.name,
        normalize_mode(detected.mode),
    )


def load_engine_midi(
    path: Path | str,
    numerator: int | None = None,
    denominator: int | None = None,
) -> TradTune:
    """Charge un MIDI du moteur en ``TradTune`` (canal 0 = mélodie)."""
    path = Path(path)
    mid = mido.MidiFile(str(path))
    ticks_per_beat = mid.ticks_per_beat
    eighth_ticks = ticks_per_beat / 2.0

    meta_num, meta_den = None, None
    meta_key: str | None = None
    for track in mid.tracks:
        for msg in track:
            if msg.type == "time_signature" and meta_num is None:
                meta_num, meta_den = msg.numerator, msg.denominator
            elif msg.type == "key" and meta_key is None:
                meta_key = msg.key
    num = numerator or meta_num or 4
    den = denominator or meta_den or 4
    bar_ticks = ticks_per_beat * num * 4.0 / den

    # Attaques en FIFO par (canal, hauteur) ; notes closes (canal, hauteur, début, fin).
    pending: dict[tuple[int, int], list[int]] = {}
    closed: list[tuple[int, int, int, int]] = []
    starts_by_channel: dict[int, list[int]] = {}
    end_tick = 0
    for track in mid.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            end_tick = max(end_tick, tick)
            if msg.type == "note_on" and msg.velocity > 0:
                pending.setdefault((msg.channel, msg.note), []).append(tick)
                starts_by_channel.setdefault(msg.channel, []).append(tick)
            elif msg.type in ("note_off",) or (msg.type == "note_on" and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if pending.get(key):
                    closed.append((msg.channel, msg.note, pending[key].pop(0), tick))
    # Repli legato : l'export moteur laisse les notes ouvertes (mélodie,
    # accords) ; chaque note se termine à l'attaque suivante de son canal.
    for (ch, pitch), starts in pending.items():
        ordered = sorted(starts_by_channel.get(ch, []))
        for start in starts:
            following = [s for s in ordered if s > start]
            end = min(following) if following else max(end_tick, start)
            closed.append((ch, pitch, start, end))

    melody = sorted(n for n in closed if n[0] == MELODY_CHANNEL)
    chord_notes = sorted(n for n in closed if n[0] == CHORDS_CHANNEL)

    n_bars = (max([n[3] for n in closed] + [0]) + int(bar_ticks) - 1) // max(int(bar_ticks), 1)
    n_bars = max(n_bars, 1)
    bars: list[list[Note]] = [[] for _ in range(n_bars)]
    for _, pitch, start, end in melody:
        idx = min(int(start // bar_ticks), n_bars - 1)
        bars[idx].append(
            Note(
                pitch=pitch,
                onset=round((start % bar_ticks) / eighth_ticks, 3),
                duration=round(max(end - start, 0) / eighth_ticks, 3),
            )
        )
    for bar in bars:
        bar.sort(key=lambda n: (n.onset, n.pitch))

    # Accords : simultanéités du canal 1 groupées par (mesure, tick).
    onsets: dict[tuple[int, int], list[int]] = {}
    for _, pitch, start, _ in chord_notes:
        idx = min(int(start // bar_ticks), n_bars - 1)
        onsets.setdefault((idx, start), []).append(pitch)
    chords: list[list[tuple[float, str]]] = [[] for _ in range(n_bars)]
    for (idx, start), pitches in sorted(onsets.items()):
        chords[idx].append(
            (round((start % bar_ticks) / eighth_ticks, 3), name_chord(pitches))
        )

    if meta_key is not None:
        tonic_pc, key_name, mode = _parse_mido_key(meta_key)
    else:
        tonic_pc, key_name, mode = _krumhansl_melody_key(
            [n.pitch for bar in bars for n in bar]
        )

    return TradTune(
        tune_id=path.stem,
        key_tonic_pc=tonic_pc,
        key_name=key_name,
        mode=mode,
        meter=f"{num}/{den}",
        eighths_per_bar=eighths_per_bar(num, den),
        bars=bars,
        chords=chords,
        source="engine-midi",
    )


def name_chord(pitches: list[int]) -> str:
    """Nom d'accord (``"D"``, ``"Am"``) depuis une simultanéité du canal 1.

    Fondamentale = classe de hauteur expliquant tierce + quinte (tolère les
    renversements des voicings serrés) ; repli sur la note la plus grave.
    Orthographe en dièses, déterministe.
    """
    from .model import PC_NAMES

    pcs = sorted({p % 12 for p in pitches})
    if not pcs:
        return "?"
    lowest = min(pitches) % 12
    for cand in pcs:
        rel = sorted((p - cand) % 12 for p in pcs)
        if _CHORD_FIFTH in rel and (
            _CHORD_THIRD_MAJOR in rel or _CHORD_THIRD_MINOR in rel
        ):
            root = cand
            break
    else:
        root = lowest
    rel = sorted((p - root) % 12 for p in pcs)
    if _CHORD_THIRD_MAJOR in rel:
        suffix = ""
    elif _CHORD_THIRD_MINOR in rel:
        suffix = "dim" if _CHORD_TRITONE in rel else "m"
    else:
        suffix = ""
    return f"{PC_NAMES[root]}{suffix}"


def _parse_mido_key(name: str) -> tuple[int, str, str]:
    """Méta-tonalité mido (``"D"``, ``"Bm"``) -> (pc, nom, mode)."""
    from .model import PC_NAMES

    # mido : majeur "D", mineur "Bm" (suffixe "m").
    minor = name.endswith("m")
    root = name[:-1] if minor else name
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[root[0]]
    if len(root) > 1:
        base += 1 if root[1] == "#" else -1
    pc = base % 12
    return pc, PC_NAMES[pc], ("aeolian" if minor else "ionian")


def _krumhansl_melody_key(pitches: list[int]) -> tuple[int, str, str]:
    """Estimation Krumhansl (music21) sur la mélodie, repli déterministe."""
    if not pitches:
        return 0, "C", "ionian"
    from music21 import note as m21note
    from music21 import stream as m21stream

    stream = m21stream.Stream()
    for midi in pitches:
        stream.append(m21note.Note(midi))
    detected = stream.analyze("key")
    return (
        detected.tonic.pitchClass,
        detected.tonic.name,
        normalize_mode(detected.mode),
    )
