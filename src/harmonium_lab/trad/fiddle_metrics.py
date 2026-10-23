"""Mesures SK4 complémentaires ; SK3 et ses fenêtres restent inchangés."""
from __future__ import annotations

from pathlib import Path

import mido
import numpy as np

from .fiddle_compare import RATE, TEMPO, VELOCITY, rms, synthesize


def envelope(audio: np.ndarray) -> np.ndarray:
    return np.sqrt(np.convolve(np.mean(audio**2, axis=1), np.ones(441)/441, mode='same'))


def level_and_brightness(audio: np.ndarray) -> dict:
    # Moyenne de puissance des canaux : aucune annulation stéréo.
    power = np.mean(np.abs(np.fft.rfft(audio, axis=0))**2, axis=1)
    frequencies = np.fft.rfftfreq(len(audio), 1/RATE)
    total = max(float(power.sum()), 1e-20)
    return {'rms_dbfs':round(20*np.log10(max(rms(audio), 1e-10)), 3),
            'centroid_hz':round(float(np.sum(power*frequencies)/total), 2),
            'energy_above_8khz_pct':round(float(power[frequencies > 8000].sum()/total*100), 5)}


def probe_sk4(font: Path, preset: dict, work: Path, held_wav: Path) -> dict:
    # Import ici pour ne pas former un deuxième synthétiseur ou un cycle d'import.
    import soundfile as sf
    held, _ = sf.read(held_wav, always_2d=True)
    notes = (55,62,69,76)
    references = {}
    for index, note in enumerate(notes):
        onset = .5+index*3.5
        references[note] = float(envelope(held[round(onset*RATE):round((onset+.4)*RATE)]).max())
    midi = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack([
        mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(TEMPO)),
        mido.Message('control_change', control=0, value=preset['bank']//128),
        mido.Message('control_change', control=32, value=preset['bank']%128),
        mido.Message('program_change', program=preset['program']),
    ])
    midi.tracks.append(track)
    tick_seconds = mido.bpm2tempo(TEMPO)/1e6/480
    cursor = 480
    last = 0
    repeated, velocities = [], []
    for note in notes:
        for repeat in range(8):
            track.append(mido.Message('note_on', note=note, velocity=VELOCITY, time=cursor-last))
            track.append(mido.Message('note_off', note=note, time=216))
            repeated.append((note, repeat, cursor*tick_seconds))
            last = cursor+216
            cursor += 240
        cursor += 960
        for velocity in (60,110):
            track.append(mido.Message('note_on', note=note, velocity=velocity, time=cursor-last))
            track.append(mido.Message('note_off', note=note, time=1920))
            velocities.append((note, velocity, cursor*tick_seconds))
            last = cursor+1920
            cursor = last+960
    mid = work.with_suffix('.mid')
    midi.save(mid)
    audio = synthesize(mid, font, work.with_suffix('.wav'))
    repeated_rows = []
    for note in notes:
        levels = []
        for pitch, repeat, onset in repeated:
            if pitch != note:
                continue
            segment = audio[round((onset+.055)*RATE):round((onset+.065)*RATE)]
            level = rms(segment)
            levels.append({'repeat':repeat+1, 'level65_dbfs':round(20*np.log10(max(level,1e-10)),3),
                           'held400_peak_pct':round(level/max(references[note],1e-10)*100,2)})
        repeated_rows.append({'note':note, 'attacks':levels,
                              'mean_held400_peak_pct':round(float(np.mean([x['held400_peak_pct'] for x in levels])),2)})
    velocity_rows = []
    for note in notes:
        readings = {}
        for pitch, velocity, onset in velocities:
            if pitch != note:
                continue
            readings[velocity] = {
                'first130ms':level_and_brightness(audio[round(onset*RATE):round((onset+.13)*RATE)]),
                'sustain':level_and_brightness(audio[round((onset+.25)*RATE):round((onset+.9)*RATE)]),
            }
        differences = {}
        for window in ('first130ms','sustain'):
            differences[window] = {metric:round(readings[110][window][metric]-readings[60][window][metric], 5)
                                   for metric in readings[60][window]}
        velocity_rows.append({'note':note, 'velocity60':readings[60], 'velocity110':readings[110], 'delta110_minus60':differences})
    return {'tempo_quarter':TEMPO, 'eighth_ms':240*tick_seconds*1000, 'gate_pct':90,
            'level_window_ms':[55,65], 'reference':'pic RMS glissant 10 ms de la tenue 96, première fenêtre 400 ms',
            'repeated_eighths':repeated_rows, 'velocity_response':velocity_rows}
