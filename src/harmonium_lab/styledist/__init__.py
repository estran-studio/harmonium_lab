"""Distance d'un profil de jeu à son corpus de référence (phase 014, M1).

Trois étages, sans nom de jeu en dur :

- `engine`   : rend N graines × M mesures d'un profil via le CLI du moteur ;
- `audio`    : distance audio (spectre, rythme, tonalité, dynamique, bandes)
  aux pistes de référence, normalisée par la dispersion d'un corpus de contexte ;
- `symbolic` : distance symbolique (basse, batterie, accords, boucles) aux
  transcriptions de boucles du corpus.

Les enregistrements, stems, transcriptions MIDI et rendus restent hors dépôt
(principe VII) ; seule la sortie JSON `distance-<profil>.json` est versionnée.
"""
