"""Acquisition privée : aucun accès réseau ; le manifeste est factice."""
import hashlib
import struct
import zipfile

import pytest

from harmonium_lab.trad.fiddle_samples import acquire, presets


def sf2_bytes():
    names = [(b"Solo Violin", 2, 0), (b"Piano", 0, 0), (b"EOP", 0, 0)]
    phdr = b"".join(struct.pack("<20sHHHIII", n, p, b, 0, 0, 0, 0) for n, p, b in names)
    pdta = b"pdta" + b"phdr" + struct.pack("<I", len(phdr)) + phdr
    data = b"sfbkLIST" + struct.pack("<I", len(pdta)) + pdta
    return b"RIFF" + struct.pack("<I", len(data)) + data


def test_inventory_reads_actual_bank_program_and_ignores_sentinel(tmp_path):
    path = tmp_path / "fixture.sf2"
    path.write_bytes(sf2_bytes())
    assert presets(path) == [{"name": "Solo Violin", "bank": 0, "program": 2},
                             {"name": "Piano", "bank": 0, "program": 0}]
    path.write_bytes(sf2_bytes()[:-50])
    with pytest.raises((ValueError, struct.error)):
        presets(path)


def test_download_zip_cache_hash_and_rejection(tmp_path):
    source = tmp_path / "source.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("folder/violin.sf2", sf2_bytes())
    rows = [{"id": "fixture", "status": "accepted", "url": source.as_uri(),
             "member": "folder/violin.sf2", "selected": {"bank": 0, "program": 2}},
            {"id": "forbidden", "status": "rejected", "url": "https://invalid.test"}]
    raw = tmp_path / "cache"
    acquire(rows, raw, inventory=True)
    assert rows[0]["sha256"] == hashlib.sha256(sf2_bytes()).hexdigest()
    assert rows[0]["violin_presets"] == [{"name": "Solo Violin", "bank": 0, "program": 2}]
    source.unlink()
    acquire(rows, raw, offline=True)
    (raw / "fixture.sf2").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="empreinte"):
        acquire(rows, raw, offline=True)
    assert not (raw / "forbidden.sf2").exists()


def test_missing_cache_and_missing_preset_fail(tmp_path):
    row = {"id": "fixture", "status": "accepted", "url": "file:///unavailable",
           "selected": {"bank": 0, "program": 40}}
    with pytest.raises(RuntimeError, match="hors ligne"):
        acquire([row], tmp_path, offline=True)
    (tmp_path / "fixture.sf2").write_bytes(sf2_bytes())
    with pytest.raises(ValueError, match="preset"):
        acquire([row], tmp_path, inventory=True)
