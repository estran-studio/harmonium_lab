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

import json
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
    """Charge un air ABC en ``TradTune`` (forme depuis le texte, repli music21 marqué)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        return _load_abc_direct(path, text)
    except Exception as first_err:
        try:
            tune = _load_abc_music21(path)
        except Exception as second_err:
            raise second_err from first_err
        tune.form = {
            "scheme": "?",
            "parts": [],
            "is_aabb": False,
            "pickup": 0.0,
            "cause": f"repli-music21:{first_err}",
            "source": "music21-fallback",
        }
        return tune


def _load_abc_direct(path: Path, text: str) -> TradTune:
    """Chargeur principal : tokenisation ABC, forme développée, hauteurs MIDI."""
    from .form import analyze_form, plan_to_dict

    plan = analyze_form(text)
    bars: list[list[Note]] = []
    chords: list[list[tuple[float, str]]] = []
    for notes, bar_chords, _, _ in plan.bars:
        bar = [
            Note(pitch=p, onset=round(float(o), 3), duration=round(float(d), 3))
            for o, d, p in notes
            if p is not None
        ]
        bar.sort(key=lambda n: (n.onset, n.pitch))
        bars.append(bar)
        chords.append(sorted((round(float(o), 3), s) for o, s in bar_chords))
    if not any(bars):
        raise ValueError(f"{path}: aucune note trouvée")
    return TradTune(
        tune_id=path.stem,
        key_tonic_pc=plan.key_tonic_pc,
        key_name=plan.key_name,
        mode=plan.mode,
        meter=plan.meter,
        eighths_per_bar=plan.eighths_per_bar,
        bars=bars,
        chords=chords,
        source="abc",
        form=plan_to_dict(plan),
    )


def _load_abc_music21(path: Path) -> TradTune:
    """Repli : parse music21 + expandRepeats (levées et fins parfois perdues)."""
    import music21

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


def _chord_duration_eighths(num: int, den: int, tune_type: str | None = None) -> float:
    """Durée d'un accord en croches selon le style ou la métrique."""
    if (tune_type in ("jig", "gigue", "waltz", "valse")) or (num == 6 and den == 8) or (num == 3 and den == 4):
        return float(eighths_per_bar(num, den))
    if (num == 2 and den == 2) or (num == 4 and den == 4) or eighths_per_bar(num, den) >= 8:
        return 4.0
    return float(eighths_per_bar(num, den))


def _load_truth_chords(
    truth_path: Path | str,
    n_bars: int,
    eighths_per_b: int,
) -> list[list[tuple[float, str]]] | None:
    """Lit les accords depuis le fichier de vérité JSON (--record-truth)."""
    p = Path(truth_path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    snapshots = data.get("reports", []) if isinstance(data, dict) else data
    if not isinstance(snapshots, list) or not snapshots:
        return None

    sorted_snaps = sorted(
        snapshots,
        key=lambda s: (s.get("bar", 0), s.get("step", s.get("beat", 0)), s.get("timestamp_ms", 0)),
    )
    chords: list[list[tuple[float, str]]] = [[] for _ in range(n_bars)]
    prev_chord: str | None = None

    for snap in sorted_snaps:
        bar = snap.get("bar")
        if bar is None:
            continue
        bar_idx = int(bar) - 1
        if not (0 <= bar_idx < n_bars):
            continue
        chord = snap.get("chord")
        if not chord or chord == "?":
            continue
        if chord != prev_chord:
            step = snap.get("step", 0)
            beat = snap.get("beat", 1)
            onset = 0.0
            if eighths_per_b >= 8 and (step >= 8 or beat >= 3):
                onset = 4.0
            chords[bar_idx].append((onset, chord))
            prev_chord = chord

    return chords


def _infer_midi_chords(
    chord_notes: list[tuple[int, int, int, int]],
    n_bars: int,
    bar_ticks: float,
    eighth_ticks: float,
    num: int,
    den: int,
    tune_type: str | None = None,
) -> list[list[tuple[float, str]]]:
    """Infère les accords par classes de hauteur sur la durée d'accord du style."""
    chords: list[list[tuple[float, str]]] = [[] for _ in range(n_bars)]
    if not chord_notes:
        return chords

    bar_eighths = eighths_per_bar(num, den)
    dur = _chord_duration_eighths(num, den, tune_type)
    n_slots = max(1, int(round(bar_eighths / dur)))
    slot_eighths = bar_eighths / n_slots

    prev_chord: str | None = None

    for bar_idx in range(n_bars):
        for slot_idx in range(n_slots):
            slot_start_tick = bar_idx * bar_ticks + (slot_idx * slot_eighths) * eighth_ticks
            slot_end_tick = bar_idx * bar_ticks + ((slot_idx + 1) * slot_eighths) * eighth_ticks

            slot_pitches = [
                pitch
                for _, pitch, start, _ in chord_notes
                if slot_start_tick <= start < slot_end_tick
            ]
            if not slot_pitches:
                continue

            chord = name_chord(slot_pitches)
            if chord and chord != "?" and chord != prev_chord:
                onset = round(slot_idx * slot_eighths, 3)
                chords[bar_idx].append((onset, chord))
                prev_chord = chord

    return chords


def load_engine_midi(
    path: Path | str,
    numerator: int | None = None,
    denominator: int | None = None,
    truth_path: Path | str | None = None,
    tune_type: str | None = None,
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

    # Accords : vérité (--record-truth) en priorité, sinon inférence par classes de hauteur.
    target_truth = truth_path
    if target_truth is None:
        cand = path.with_suffix(".json")
        if cand.exists():
            target_truth = cand

    eighths = eighths_per_bar(num, den)
    chords = None
    if target_truth is not None:
        chords = _load_truth_chords(target_truth, n_bars, eighths)

    if chords is None:
        chords = _infer_midi_chords(
            chord_notes, n_bars, bar_ticks, eighth_ticks, num, den, tune_type
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
        eighths_per_bar=eighths,
        bars=bars,
        chords=chords,
        source="engine-midi",
    )


def name_chord(pitches: list[int]) -> str:
    """Nom d'accord (``"D"``, ``"Am"``) depuis les classes de hauteur du canal 1.

    Fondamentale = classe de hauteur expliquant tierce + quinte (tolère les
    renversements des voicings serrés) ; repli sur tierce seule (accords sans quinte) ;
    repli sur la note la plus grave. Orthographe en dièses, déterministe.
    """
    from .model import PC_NAMES

    pcs = sorted({p % 12 for p in pitches})
    if not pcs:
        return "?"
    lowest = min(pitches) % 12
    root = None
    for cand in pcs:
        rel = sorted((p - cand) % 12 for p in pcs)
        if _CHORD_FIFTH in rel and (
            _CHORD_THIRD_MAJOR in rel or _CHORD_THIRD_MINOR in rel
        ):
            root = cand
            break
    if root is None:
        for cand in pcs:
            rel = sorted((p - cand) % 12 for p in pcs)
            if _CHORD_THIRD_MAJOR in rel or _CHORD_THIRD_MINOR in rel:
                root = cand
                break
    if root is None:
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
