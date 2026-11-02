# `gmd-soul` — famille soul (Groove MIDI Dataset, phase 019, L2)

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
| soul | beat | 8 | 221 | 8.9 | 2 | 4-4 8 | straight 8 | juste |
| soul | fill | 23 | 28 | 1.1 | 1 | 4-4 23 | straight 23 | juste |
| soul/groove10 | beat | 4 | 64 | 2.5 | 4 | 4-4 4 | straight 4 | juste |
| soul/groove3 | beat | 4 | 64 | 3.0 | 4 | 4-4 4 | straight 4 | juste |
| soul/groove4 | beat | 4 | 64 | 3.2 | 4 | 4-4 4 | straight 4 | juste |
| soul/groove9 | beat | 4 | 64 | 2.4 | 4 | 4-4 4 | straight 4 | juste |
| soul/motown | beat | 4 | 136 | 4.4 | 1 | 4-4 4 | straight 4 | juste |
| soul/motown | fill | 12 | 23 | 0.7 | 1 | 4-4 12 | straight 11, swing 1 | juste |

Total : 63 fichiers, 664 mesures entières.

Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; **juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; **juste** ≥ 10 fichiers.

## Ce que disent les mesures

- **soul**, groupe `4-4:straight` (8 fichiers, 221 mesures, 105 BPM médian, fiabilité juste) : timekeeper `hat_closed` (77%), figure `sparse` (64%) ; kick le plus fréquent [0, 4, 8, 12] (25%) ; caisse claire [1, 4, 6, 9, 12, 14] (10%) ; 4 patterns proposés.
- **soul/groove10**, groupe `4-4:straight` (4 fichiers, 64 mesures, 102 BPM médian, fiabilité juste) : timekeeper `hat_closed` (100%), figure `eighths` (88%) ; kick le plus fréquent [0, 10, 15] (47%) ; caisse claire [4, 7, 9, 12] (19%) ; 3 patterns proposés.
- **soul/groove3**, groupe `4-4:straight` (4 fichiers, 64 mesures, 86 BPM médian, fiabilité juste) : timekeeper `hat_closed` (100%), figure `sixteenths` (97%) ; kick le plus fréquent [0, 3, 9, 10, 13, 15] (48%) ; caisse claire [4, 7, 12] (33%) ; 3 patterns proposés.
- **soul/groove4**, groupe `4-4:straight` (4 fichiers, 64 mesures, 80 BPM médian, fiabilité juste) : timekeeper `hat_closed` (100%), figure `sparse` (52%) ; kick le plus fréquent [0, 8] (98%) ; caisse claire [4, 12] (77%) ; 0 patterns proposés.
- **soul/groove9**, groupe `4-4:straight` (4 fichiers, 64 mesures, 105 BPM médian, fiabilité juste) : timekeeper `hat_closed` (75%), figure `eighths` (73%) ; kick le plus fréquent [0, 10, 15] (75%) ; caisse claire [4, 12] (75%) ; 3 patterns proposés.
- **soul/motown**, groupe `4-4:straight` (4 fichiers, 136 mesures, 126 BPM médian, fiabilité juste) : timekeeper `ride` (54%), figure `other` (39%) ; kick le plus fréquent [0, 6, 8] (12%) ; caisse claire [0, 4, 8, 12] (33%) ; 4 patterns proposés.

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
