"""SK4 : banques privées VSCO à deux couches et copie FluidR3 à attaque courte."""
from __future__ import annotations

import argparse
import json
import math
import struct
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from harmonium_lab.feet.sf2 import _chunk, _cstr, _range, _string_chunk
from .download import Fetcher
from .fiddle_samples import acquire, digest

RATE = 44100
ATTACK_TC = round(1200 * math.log2(.002))
RELEASE_TC = round(1200 * math.log2(.035))


@dataclass
class Zone:
    audio: np.ndarray
    root: int
    lo: int
    hi: int
    vel_lo: int
    vel_hi: int
    loop_start: int
    loop_end: int


def chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    result = []
    position = 0
    while position + 8 <= len(data):
        tag, length = struct.unpack_from('<4sI', data, position)
        end = position + 8 + length
        if end > len(data):
            raise ValueError('chunk RIFF tronqué')
        result.append((tag, data[position + 8:end]))
        position = end + length % 2
    if position != len(data):
        raise ValueError('fin RIFF non alignée')
    return result


def assemble(zones: list[Zone], name: str) -> bytes:
    """Un preset 0/40, zones G3–E6, boucles jusqu'au note-off (sampleModes=3)."""
    if not zones:
        raise ValueError('banque vide')
    sample_data = bytearray()
    shdr = bytearray()
    igen = bytearray()
    ibag = bytearray()
    count = 0
    for index, zone in enumerate(zones):
        if not (0 <= zone.lo <= zone.root <= zone.hi <= 127 and
                0 <= zone.vel_lo <= zone.vel_hi <= 127 and
                0 < zone.loop_start < zone.loop_end < len(zone.audio)):
            raise ValueError('zone ou boucle invalide')
        for previous in zones[:index]:
            if max(zone.lo, previous.lo) <= min(zone.hi, previous.hi) and max(zone.vel_lo, previous.vel_lo) <= min(zone.vel_hi, previous.vel_hi):
                raise ValueError('zones qui se recouvrent')
        start = len(sample_data) // 2
        pcm = np.rint(np.clip(zone.audio, -1, 1) * 32767).astype('<i2')
        sample_data.extend(pcm.tobytes())
        end = len(sample_data) // 2
        sample_data.extend(bytes(46 * 2))
        shdr.extend(struct.pack('<20sIIIIIBbHH', _cstr(f'Violin {index}'.encode()), start, end,
                                start + zone.loop_start, start + zone.loop_end, RATE, zone.root, 0, 0, 1))
        generators = [(43, _range(zone.lo, zone.hi)), (44, _range(zone.vel_lo, zone.vel_hi)),
                      (34, ATTACK_TC), (38, RELEASE_TC), (54, 3), (58, zone.root), (53, index)]
        ibag.extend(struct.pack('<HH', count, 0))
        igen.extend(b''.join(struct.pack('<Hh', *g) for g in generators))
        count += len(generators)
    ibag.extend(struct.pack('<HH', count, 0))
    igen.extend(bytes(4))
    shdr.extend(bytes(46))
    tables = {
        b'phdr': struct.pack('<20sHHHIII', _cstr(name.encode()), 40, 0, 0, 0, 0, 0) + struct.pack('<20sHHHIII', _cstr(b'EOP'), 0, 0, 1, 0, 0, 0),
        b'pbag': struct.pack('<HHHH', 0, 0, 1, 0), b'pmod': bytes(10),
        b'pgen': struct.pack('<HhHh', 41, 0, 0, 0),
        b'inst': struct.pack('<20sH20sH', _cstr(b'Violin'), 0, _cstr(b'EOI'), len(zones)),
        b'ibag': bytes(ibag), b'imod': bytes(10), b'igen': bytes(igen), b'shdr': bytes(shdr),
    }
    info = _chunk(b'ifil', struct.pack('<HH', 2, 1)) + _string_chunk(b'isng', 'EMU8000')
    info += _string_chunk(b'INAM', name) + _string_chunk(b'ICOP', 'VSCO 2 CE CC0; Versilian Studios / Sam Gossner')
    body = _chunk(b'LIST', b'INFO' + info) + _chunk(b'LIST', b'sdta' + _chunk(b'smpl', bytes(sample_data)))
    body += _chunk(b'LIST', b'pdta' + b''.join(_chunk(tag, data) for tag, data in tables.items()))
    return b'RIFF' + struct.pack('<I', len(body) + 4) + b'sfbk' + body


def prepare(audio: np.ndarray) -> tuple[np.ndarray, int]:
    """Coupe silence et montée lente à 90 % du pic initial ; fondu 2 ms."""
    if not np.isfinite(audio).all() or len(audio) < RATE // 2:
        raise ValueError('échantillon trop court ou non fini')
    # La convolution FFT peut rendre une énergie de silence légèrement négative.
    energy = signal.convolve(audio ** 2, np.ones(441) / 441, mode='same')
    envelope = np.sqrt(np.maximum(energy, 0))
    peak = float(envelope.max())
    if peak < 1e-8:
        raise ValueError('échantillon silencieux')
    onset = int(np.flatnonzero(envelope >= peak * .02)[0])
    initial = envelope[onset:onset + round(.4 * RATE)]
    advance = max(0, int(np.flatnonzero(initial >= initial.max() * .9)[0]) - round(.005 * RATE))
    cut = onset + advance
    result = audio[cut:].copy()
    fade = min(round(.002 * RATE), len(result))
    result[:fade] *= np.linspace(0, 1, fade)
    return result, cut


def looped(audio: np.ndarray, start: int, end: int) -> np.ndarray:
    """Fondu linéaire de 50 ms vers les 50 ms PRÉCÉDANT le début de boucle."""
    crossfade = round(.05 * RATE)
    if not crossfade < start < end - crossfade < len(audio) - crossfade:
        raise ValueError('boucle trop courte')
    result = audio.copy()
    weight = np.linspace(0, 1, crossfade)
    result[end-crossfade:end] = (1-weight) * audio[end-crossfade:end] + weight * audio[start-crossfade:start]
    result[-crossfade:] *= np.linspace(1, 0, crossfade)
    return result


def load_sample(path: Path, root: int, target_root: int) -> np.ndarray:
    audio, rate = sf.read(path, always_2d=True)
    mono = audio.mean(axis=1)
    ratio = Fraction(RATE / rate * 2 ** ((root-target_root) / 12)).limit_denominator(10000)
    return signal.resample_poly(mono, ratio.numerator, ratio.denominator)


def build_vsco(sources: list[dict], raw: Path, *, hybrid: bool) -> tuple[bytes, list[dict]]:
    arco = [r for r in sources if r['articulation'] == 'arco']
    primary = [r for r in sources if r['articulation'] == ('spic' if hybrid else 'arco')]
    roots = sorted({r['root'] for r in primary})
    zones, report = [], []
    for index, note in enumerate(roots):
        lo = 55 if index == 0 else (roots[index-1] + note) // 2 + 1
        hi = 88 if index == len(roots)-1 else (note + roots[index+1]) // 2
        for layer in (1, 2):
            sustain = min((r for r in arco if r['layer'] == layer), key=lambda r: abs(r['root']-note))
            audio, cut = prepare(load_sample(raw / 'vsco' / sustain['file'], sustain['root'], note))
            # Le spiccato enregistré donne le transient fort ; la tenue arco évite
            # de boucler une queue percussive presque silencieuse.
            if hybrid and layer == 2:
                transient = next(r for r in primary if r['root'] == note and r['layer'] == layer)
                attack = load_sample(raw / 'vsco' / transient['file'], note, note)
                # Conserver le vrai coup d'archet, couper uniquement le silence.
                energy = signal.convolve(attack**2, np.ones(441)/441, mode='same')
                env = np.sqrt(np.maximum(energy, 0))
                trim = int(np.flatnonzero(env >= env.max()*.02)[0])
                attack = attack[trim:]
                attack[:88] *= np.linspace(0, 1, 88)
                join, width = round(.12*RATE), round(.05*RATE)
                sustain_level = np.sqrt(np.mean(audio[:round(.3*RATE)]**2))
                attack_level = np.sqrt(np.mean(attack[join-width:join]**2))
                audio *= attack_level / max(sustain_level, 1e-10)
                weight = np.linspace(0, 1, width)
                audio = np.concatenate([attack[:join-width], (1-weight)*attack[join-width:join] + weight*audio[:width], audio[width:]])
            start, end = round(.5*RATE), round(1.8*RATE)
            audio = audio[:round(2.1*RATE)]
            audio = looped(audio, start, end)
            zones.append(Zone(audio, note, lo, hi, 0 if layer == 1 else 81, 80 if layer == 1 else 127, start, end))
            report.append({'root':note, 'keys':[lo,hi], 'layer':layer, 'sustain_source':sustain['file'], 'trim_samples':cut,
                           'loop_start':start, 'loop_end':end, 'hybrid_spiccato':hybrid and layer == 2})
    return assemble(zones, 'VSCO hybrid' if hybrid else 'VSCO short arco'), report


def shorten_fluid(data: bytes) -> tuple[bytes, list[dict]]:
    """Copie intégrale : seuls les instruments du preset 0/40 sont modifiés.

    Modulateurs, échantillons, boucles et instruments non sélectionnés conservés.
    Le début est avancé de 120 ms au plus, jamais au-delà du début de boucle.
    """
    if data[:4] != b'RIFF' or data[8:12] != b'sfbk':
        raise ValueError('SF2 invalide')
    outer = chunks(data[12:])
    pdta_index = next(i for i, (tag, body) in enumerate(outer) if tag == b'LIST' and body[:4] == b'pdta')
    ordered = chunks(outer[pdta_index][1][4:])
    tables = dict(ordered)
    headers = list(struct.iter_unpack('<20sHHHIII', tables[b'phdr']))
    pbag = list(struct.iter_unpack('<HH', tables[b'pbag']))
    pgen = list(struct.iter_unpack('<Hh', tables[b'pgen']))
    chosen = next(i for i, h in enumerate(headers[:-1]) if h[1:3] == (40, 0))
    instruments = {value for bag in range(headers[chosen][3], headers[chosen+1][3])
                   for oper, value in pgen[pbag[bag][0]:pbag[bag+1][0]] if oper == 41}
    inst = list(struct.iter_unpack('<20sH', tables[b'inst']))
    ibag = list(struct.iter_unpack('<HH', tables[b'ibag']))
    igen = list(struct.iter_unpack('<Hh', tables[b'igen']))
    samples = list(struct.iter_unpack('<20sIIIIIBbHH', tables[b'shdr']))
    selected_bags = {bag for instrument in instruments for bag in range(inst[instrument][1], inst[instrument+1][1])}
    new_bags, new_gens, report = [], [], []
    for bag in range(len(ibag)-1):
        new_bags.append((len(new_gens), ibag[bag][1]))
        gens = igen[ibag[bag][0]:ibag[bag+1][0]]
        if bag in selected_bags:
            values = dict(gens)
            # Une zone globale peut porter une enveloppe héritée.
            values[34] = ATTACK_TC
            if 53 in values:
                sample = samples[values[53]]
                room = sample[3] - sample[1] - 64
                advance = max(0, min(round(sample[5]*.12), room))
                values[0] = min(32767, values.get(0, 0) + advance)
                report.append({'sample_id':values[53], 'advance_samples':advance})
            # keyRange / velRange en tête, sampleID en dernier (§8.1.2).
            gens = [(op, values.pop(op)) for op in (43,44) if op in values] + [(op,val) for op,val in values.items() if op != 53] + ([(53,values[53])] if 53 in values else [])
        new_gens.extend(gens)
    new_bags.append((len(new_gens), ibag[-1][1]))
    new_gens.append((0,0))
    tables[b'ibag'] = b''.join(struct.pack('<HH', *b) for b in new_bags)
    tables[b'igen'] = b''.join(struct.pack('<Hh', *g) for g in new_gens)
    outer[pdta_index] = (b'LIST', b'pdta' + b''.join(_chunk(tag, tables[tag]) for tag, _ in ordered))
    body = b''.join(_chunk(tag, value) for tag, value in outer)
    return b'RIFF' + struct.pack('<I', len(body)+4) + b'sfbk' + body, report


def build(manifest: Path, raw: Path, *, offline: bool = False, inventory: bool = False) -> None:
    rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
    acquire(rows, raw, offline=offline, inventory=inventory)
    fetcher = Fetcher(offline=offline)
    reports = {}
    for row in rows:
        if row['status'] != 'accepted' or not row.get('build'):
            continue
        if row['build'] == 'fluid-short':
            data, report = shorten_fluid((raw / 'fluidr3.sf2').read_bytes())
        else:
            sources = json.loads((manifest.parent / row['source_manifest']).read_text())['samples']
            for source in sources:
                path = raw / 'vsco' / source['file']
                fetcher.get(source['url'], path)
                if digest(path) != source['sha256']:
                    raise ValueError(f'empreinte différente : {path}')
            data, report = build_vsco(sources, raw, hybrid=row['build'] == 'vsco-hybrid')
        dest = raw / (row['id'] + '.sf2')
        dest.write_bytes(data)
        actual = digest(dest)
        if not inventory and actual != row.get('sha256'):
            raise ValueError(f'empreinte dérivée différente : {dest} (inventaire explicite requis)')
        if inventory:
            row.update(sha256=actual, size_bytes=len(data))
        reports[row['id']] = {'sha256':actual, 'size_bytes':len(data), 'zones':report}
        print(f"Construit : {dest} ({len(data)} octets)", flush=True)
    (raw / 'build.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
    if inventory:
        manifest.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('samples/fiddles/manifest.jsonl'))
    parser.add_argument('--raw', type=Path, default=Path('samples/fiddles/raw'))
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--inventory', action='store_true')
    args = parser.parse_args()
    build(args.manifest, args.raw, offline=args.offline, inventory=args.inventory)


if __name__ == '__main__':
    main()
