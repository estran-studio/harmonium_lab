"""Accompagnement mesuré sur des corpus réels : basse, batterie et micro-timing (phase 018, E7).

Un module par rôle, chacun exécutable par `python -m harmonium_lab.backing.<module>` :

- `chords`, `wjazzd`, `bass_measures`, `bass_compare` : la basse (marche) lue sur la base
  Weimar (`corpus/wjazzd/`), mesurée en comptes et parts, puis comparée au généré du moteur ;
- les modules de batterie et de timing (autres sources, mêmes conventions).

Conventions communes : les bruts restent en cache gitignoré (`corpus/<source>/raw/`) et sont
vérifiés par SHA256 avant toute lecture ; seuls les manifestes (sans note), les `VERSION` et
les dérivés agrégés sous `references/wjazzd-swing/` sont versionnés ; les JSON sont
déterministes (clés triées, arrondis fixes, aucun horodatage).
"""
