"""SK4 : sources factices file:// uniquement, boucles et erreurs observables."""
import hashlib
import json

import numpy as np
import pytest
import soundfile as sf

from harmonium_lab.trad.fiddle_compare import discontinuities
from harmonium_lab.trad.fiddle_sf2 import RATE, Zone, assemble, build, looped, prepare


def tone(duration=3):
    t = np.arange(round(duration*RATE))/RATE
    return .2*np.sin(2*np.pi*196*t)


def test_loop_join_remains_smooth_across_many_repetitions():
    audio = tone()
    start, end = round(.503*RATE), round(1.8*RATE)
    prepared = looped(audio, start, end)
    held = np.concatenate([prepared[:end], *[prepared[start:end]]*4])
    assert discontinuities(held)['suspect_count'] == 0
    # Une soudure brute sur des phases distinctes est réellement détectée.
    broken = np.concatenate([audio[:end], audio[start:end]])
    assert discontinuities(broken)['suspect_count'] > 0


def test_prepare_removes_silence_and_slow_rise_without_initial_step():
    audio = tone()
    audio[:RATE//4] = 0
    audio[RATE//4:RATE//2] *= np.linspace(0,1,RATE//4)
    prepared, _ = prepare(audio)
    first = np.sqrt(np.mean(prepared[:round(.065*RATE)]**2))
    steady = np.sqrt(np.mean(prepared[RATE:2*RATE]**2))
    assert first/steady > .8
    assert prepared[0] == 0
    with pytest.raises(ValueError, match='silencieux'):
        prepare(np.zeros(RATE))
    with pytest.raises(ValueError, match='non fini'):
        prepare(np.full(RATE,np.nan))


def test_overlapping_velocity_or_key_zones_are_rejected():
    a = tone()
    z = Zone(a,55,55,88,0,80,1000,2000)
    other = Zone(a,69,55,88,80,127,1000,2000)
    with pytest.raises(ValueError, match='recouvrent'):
        assemble([z,other],'fixture')
    with pytest.raises(ValueError, match='boucle invalide'):
        assemble([Zone(a,55,55,88,0,127,2000,1000)],'fixture')


def test_build_downloads_pinned_fixture_and_rebuilds_offline(tmp_path):
    sources = []
    for layer in (1,2):
        path = tmp_path/f'layer{layer}.wav'
        sf.write(path,tone()*(.5 if layer == 1 else 1),RATE,subtype='PCM_16')
        sources.append({'articulation':'arco','root':55,'layer':layer,'file':path.name,
                        'url':path.as_uri(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (tmp_path/'sources.json').write_text(json.dumps({'samples':sources}))
    manifest = tmp_path/'manifest.jsonl'
    manifest.write_text(json.dumps({'id':'fixture','status':'accepted','build':'vsco-arco',
                                   'source_manifest':'sources.json','selected':{'bank':0,'program':40}})+'\n')
    raw = tmp_path/'cache'
    build(manifest,raw,inventory=True)
    font = raw/'fixture.sf2'
    expected = hashlib.sha256(font.read_bytes()).hexdigest()
    for source in sources:
        (tmp_path/source['file']).unlink()
    font.unlink()
    build(manifest,raw,offline=True)
    assert hashlib.sha256(font.read_bytes()).hexdigest() == expected
    (raw/'vsco'/sources[0]['file']).write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='empreinte différente'):
        build(manifest,raw,offline=True)
