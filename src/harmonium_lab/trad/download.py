"""Téléchargement idempotent et poli (cache local, délai, User-Agent identifié).

Les transferts passent par `curl`, qui respecte `ALL_PROXY` / `https_proxy` / `http_proxy`, y compris
un proxy SOCKS (`socks5h://…`, alias `proxyon`) que `urllib` ne sait pas utiliser. Le fichier est
écrit directement sur disque (`.part` puis renommage) : pas de grosse banque en mémoire.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

USER_AGENT = "harmonium-lab/0.1 (corpus trad quebecois; usage interne; github.com/estran-studio)"
CONNECT_TIMEOUT_S = 30
# Abandon si le débit reste sous 1 Ko/s pendant 60 s (pas de durée totale : banques de 400 Mo).
STALL_BYTES_PER_S, STALL_S = 1000, 60
RETRIES = 3
# Erreur HTTP client (curl --fail ; code de sortie 22, ou 56 derrière un proxy) : inutile de réessayer,
# sauf 429. Les 5xx et coupures sont réessayés.
_CLIENT_ERROR = re.compile(r"returned error: 4(?!29)\d\d\b")


class Fetcher:
    """Récupère des URL vers `dest`, saute les fichiers déjà en cache, espace les requêtes réseau."""

    def __init__(self, delay_s: float = 0.3, offline: bool = False) -> None:
        self.delay_s = delay_s
        self.offline = offline
        self.network_requests = 0
        self.cache_hits = 0
        self._last = 0.0

    def get(self, url: str, dest: Path) -> Path:
        if dest.exists() and dest.stat().st_size > 0:
            self.cache_hits += 1
            return dest
        if self.offline:
            raise RuntimeError(f"hors ligne : {dest} absent du cache (source {url})")
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        self._download(url, tmp)
        tmp.replace(dest)
        return dest

    def _download(self, url: str, tmp: Path) -> None:
        curl = shutil.which("curl")
        if curl is None:
            raise RuntimeError("curl introuvable : nécessaire aux téléchargements")
        last_err = ""
        for attempt in range(1, RETRIES + 1):
            wait = self.delay_s - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.network_requests += 1
            cmd = [curl, "--silent", "--show-error", "--fail", "--location",
                   "--user-agent", USER_AGENT, "--connect-timeout", str(CONNECT_TIMEOUT_S),
                   "--speed-limit", str(STALL_BYTES_PER_S), "--speed-time", str(STALL_S),
                   "--retry", "2", "--continue-at", "-", "--output", str(tmp), url]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
                return
            last_err = proc.stderr.strip() or ("réponse vide" if proc.returncode == 0 else f"code {proc.returncode}")
            if _CLIENT_ERROR.search(last_err):
                break
            print(f"  ! {url} (essai {attempt}/{RETRIES}) : {last_err}", file=sys.stderr)
            time.sleep(2.0 * attempt)
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"échec du téléchargement de {url} : {last_err}")


_HREF = re.compile(r'href="([^"]+)"')


def list_abc_files(index_html: str) -> list[str]:
    """Noms de fichiers `.abc` listés dans un index Apache (liens relatifs simples uniquement)."""
    names: set[str] = set()
    for href in _HREF.findall(index_html):
        href = urllib.parse.unquote(href)
        if "/" in href or href.startswith(("?", "#")) or href in {"..", "."}:
            continue
        if href.lower().endswith(".abc"):
            names.add(href)
    return sorted(names)
