"""Téléchargement idempotent et poli (cache local, délai, User-Agent identifié)."""

from __future__ import annotations

import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "harmonium-lab/0.1 (corpus trad quebecois; usage interne; github.com/estran-studio)"
TIMEOUT_S = 60
RETRIES = 3

# Python ≥ 3.13 active VERIFY_X509_STRICT : certains serveurs (ex. thesession.org,
# raw.githubusercontent.com selon la chaîne locale) échouent alors que la chaîne
# reste valide. On garde la vérification de chaîne et de nom d'hôte.
_SSL = ssl.create_default_context()
_SSL.verify_flags &= ~ssl.VERIFY_X509_STRICT


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
        data = self._download(url)
        tmp = dest.with_name(dest.name + ".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return dest

    def _download(self, url: str) -> bytes:
        last_err: Exception | None = None
        for attempt in range(1, RETRIES + 1):
            wait = self.delay_s - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.network_requests += 1
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT_S, context=_SSL) as resp:
                    data = resp.read()
                if not data:
                    raise OSError("réponse vide")
                return data
            except (urllib.error.URLError, OSError) as exc:
                last_err = exc
                if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500 and exc.code != 429:
                    break
                print(f"  ! {url} (essai {attempt}/{RETRIES}) : {exc}", file=sys.stderr)
                time.sleep(2.0 * attempt)
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
