# `gmd-jazz` — famille jazz (Groove MIDI Dataset, phase 019, L2)

Mesures agrégées de la batterie d'un style du Groove MIDI Dataset v1.0.0 (Gillick et al., ICML 2019), ramenées à la
grille du feel : probabilités par pas, vélocités, micro-timing par rôle, patterns par rôle, patterns proposés,
fills et leur position. **Aucune mesure d'un enregistrement n'est copiée** : agrégats seulement (principe VII).

## Licence et mention requise

- Source : Groove MIDI Dataset v1.0.0 (groove-v1.0.0-midionly.zip), <https://magenta.withgoogle.com/datasets/groove>.
- Licence : **CC-BY-4.0** (<https://creativecommons.org/licenses/by/4.0/>).
- SHA256 de l'archive, vérifié avant toute lecture : `651cbc524ffb891be1a3e46d89dc82a1cecb09a57c748c7b45b844c4841dcc1e` (identique à `corpus/sources-jazz.md`).
- Mention à reprendre : « Gillick, Roberts, Engel, Eck, Bamman, Learning to Groove with Inverse Sequence Transformations, ICML 2019 ; Groove MIDI Dataset v1.0.0, Google LLC, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) ».

## Reproduire

```sh
make backing-gmd        # télécharge et vérifie l'archive, écrit corpus/gmd/manifest.jsonl, references/gmd-*
```

Fichiers : `measures-drums.json` (ce dossier). Brut : `corpus/gmd/raw/` (cache gitignoré).

## Effectifs

| Style | Type | Fichiers | Mesures | Minutes | Batteurs | Métriques | Feel (fichiers) | Fiabilité |
|---|---|---|---|---|---|---|---|---|
| jazz | beat | 24 | 748 | 23.1 | 4 | 3-4 2, 4-4 22 | straight 13, swing 3, ternary 8 | assez |
| jazz | fill | 22 | 22 | 0.6 | 1 | 4-4 22 | straight 21, ternary 1 | juste |
| jazz/fast | beat | 1 | 126 | 1.8 | 1 | 4-4 1 | straight 1 | trop peu |
| jazz/funk | beat | 2 | 107 | 3.8 | 1 | 4-4 2 | straight 1, ternary 1 | trop peu |
| jazz/funk | fill | 22 | 28 | 0.9 | 1 | 4-4 22 | straight 21, ternary 1 | juste |
| jazz/fusion | beat | 4 | 62 | 2.7 | 1 | 4-4 4 | straight 4 | juste |
| jazz/fusion | fill | 7 | 12 | 0.5 | 1 | 4-4 7 | straight 6, ternary 1 | trop peu |
| jazz/klezmer | beat | 1 | 23 | 0.6 | 1 | 4-4 1 | straight 1 | trop peu |
| jazz/linear | beat | 2 | 334 | 8.6 | 1 | 4-4 2 | swing 1, ternary 1 | trop peu |
| jazz/march | beat | 3 | 236 | 7.8 | 1 | 4-4 3 | straight 3 | juste |
| jazz/mediumfast | beat | 2 | 115 | 2.6 | 1 | 4-4 2 | swing 1, ternary 1 | trop peu |
| jazz/swing | beat | 11 | 698 | 17.6 | 2 | 4-4 11 | straight 3, swing 6, ternary 2 | juste |

Total : 101 fichiers, 2511 mesures entières.

Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; **juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; **juste** ≥ 10 fichiers.

## Ce que disent les mesures

- **jazz**, groupe `3-4:swing` (1 fichiers, 131 mesures, 200 BPM médian, fiabilité trop peu) : timekeeper `ride` (93%), figure `quarters_plus` (56%) ; 0 patterns proposés.
- **jazz**, groupe `3-4:ternary` (1 fichiers, 86 mesures, 120 BPM médian, fiabilité trop peu) : timekeeper `ride` (99%), figure `quarters_plus` (73%) ; 0 patterns proposés.
- **jazz**, groupe `4-4:straight` (12 fichiers, 228 mesures, 120 BPM médian, fiabilité assez) : timekeeper `ride` (75%), figure `quarters_plus` (39%) ; kick le plus fréquent [0] (14%) ; caisse claire [7, 15] (3%) ; 4 patterns proposés.
- **jazz**, groupe `4-4:swing` (2 fichiers, 35 mesures, 120 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (54%), figure `other` (46%) ; 0 patterns proposés.
- **jazz**, groupe `4-4:ternary` (7 fichiers, 268 mesures, 120 BPM médian, fiabilité juste) : timekeeper `ride` (72%), figure `spang` (40%) ; kick le plus fréquent [0, 3, 6, 9] (15%) ; caisse claire [2, 5] (4%) ; 3 patterns proposés.
- **jazz/fast**, groupe `4-4:straight` (1 fichiers, 126 mesures, 290 BPM médian, fiabilité trop peu) : timekeeper `ride` (95%), figure `spang` (34%) ; 0 patterns proposés.
- **jazz/funk**, groupe `4-4:straight` (1 fichiers, 36 mesures, 116 BPM médian, fiabilité trop peu) : timekeeper `ride` (94%), figure `quarters_plus` (56%) ; 1 patterns proposés.
- **jazz/funk**, groupe `4-4:ternary` (1 fichiers, 71 mesures, 116 BPM médian, fiabilité trop peu) : timekeeper `ride` (79%), figure `sixteenths` (41%) ; 0 patterns proposés.
- **jazz/fusion**, groupe `4-4:straight` (4 fichiers, 62 mesures, 96 BPM médian, fiabilité juste) : timekeeper `hat_closed` (61%), figure `sparse` (48%) ; kick le plus fréquent [0, 6] (29%) ; caisse claire [12, 13] (24%) ; 0 patterns proposés.
- **jazz/klezmer**, groupe `4-4:straight` (1 fichiers, 23 mesures, 152 BPM médian, fiabilité trop peu) : timekeeper `none` (30%), figure `sparse` (70%) ; 0 patterns proposés.
- **jazz/mediumfast**, groupe `4-4:swing` (1 fichiers, 110 mesures, 180 BPM médian, fiabilité trop peu) : timekeeper `ride` (99%), figure `sparse` (38%) ; 0 patterns proposés.
- **jazz/mediumfast**, groupe `4-4:ternary` (1 fichiers, 5 mesures, 180 BPM médian, fiabilité trop peu) : timekeeper `ride` (100%), figure `spang` (60%) ; 0 patterns proposés.

Styles secondaires détaillés dans leur propre dossier : `gmd-jazz-linear`, `gmd-jazz-march`, `gmd-jazz-swing`.

## Grille et rôles

- `straight` : 16 pas en 4/4 (4 par pulsation, doubles croches) ; 12 en 3/4 et en 6/8.
- `swing` : même grille, pas 2 de chaque pulsation retardé au rapport r du fichier (0,56 ≤ r < 0,62).
- `ternary` : triolets : 3 pas par pulsation, 12 pas en 4/4, 9 en 3/4 (shuffle, 12/8, swing appuyé r ≥ 0,62).
- Rôles : kick, snare, sidestick (cross-stick), hat_closed, hat_pedal, hat_open, ride, ride_bell, crash, tom_high, tom_mid, tom_low ; table Roland → GM dans le JSON (`role_table`).
- Le GMD ne contient aucune percussion latine : les styles latins sont joués au kit (cross-stick, cloche de ride, toms).

## Limites

- Jeu sur kit électronique Roland TD-11 avec métronome : les vélocités et le micro-timing sont ceux de ce kit.
- Dix batteurs au total ; un style à un ou deux fichiers décrit un batteur, pas un style (fiabilité `trop peu`).
- Un fichier a un seul feel, décidé sur ses contretemps ; un fichier à feel mixte est classé sur sa majorité.
- Le feel ternaire quantifie sur des triolets : une double croche y est ramenée au pas le plus proche ; la fidélité est dans `grid_fit.within_quarter_step`.
- Les fills sont des fichiers isolés d'une à quatre mesures : `fill_position` donne leur début et leur fin dans la mesure.

Jamais de fichier MIDI du GMD dans le dépôt (`corpus/gmd/raw/` gitignoré).
