# `gmd-latin` — famille latin (Groove MIDI Dataset, phase 019, L2)

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
| latin | beat | 8 | 572 | 22.0 | 1 | 4-4 8 | straight 6, ternary 2 | juste |
| latin/ando | beat | 1 | 111 | 2.7 | 1 | 3-4 1 | straight 1 | trop peu |
| latin/bomba | beat | 1 | 89 | 3.7 | 1 | 4-4 1 | straight 1 | trop peu |
| latin/bounce | beat | 2 | 132 | 5.0 | 1 | 4-4 2 | straight 2 | trop peu |
| latin/brazilian | beat | 4 | 106 | 3.8 | 2 | 4-4 4 | straight 3, ternary 1 | juste |
| latin/brazilian-baiao | beat | 3 | 200 | 7.9 | 2 | 4-4 3 | straight 3 | juste |
| latin/brazilian-baiao | fill | 29 | 29 | 1.1 | 1 | 4-4 29 | straight 29 | juste |
| latin/brazilian-bossa | beat | 2 | 631 | 19.9 | 1 | 4-4 2 | straight 2 | trop peu |
| latin/brazilian-frevo | beat | 1 | 79 | 2.4 | 1 | 4-4 1 | straight 1 | trop peu |
| latin/brazilian-ijexa | beat | 3 | 85 | 3.2 | 1 | 4-4 3 | straight 3 | juste |
| latin/brazilian-maracatu | beat | 2 | 182 | 7.6 | 1 | 4-4 2 | straight 1, ternary 1 | trop peu |
| latin/brazilian-samba | beat | 5 | 322 | 14.0 | 1 | 4-4 5 | straight 5 | juste |
| latin/brazilian-sambareggae | beat | 3 | 180 | 7.6 | 1 | 4-4 3 | straight 3 | juste |
| latin/brazilian-songo | beat | 5 | 446 | 15.4 | 2 | 4-4 5 | straight 5 | juste |
| latin/chacarera | beat | 3 | 241 | 6.4 | 1 | 3-4 1, 4-4 2 | straight 1, ternary 2 | juste |
| latin/dominican-merengue | beat | 1 | 166 | 5.1 | 1 | 4-4 1 | straight 1 | trop peu |
| latin/merengue | beat | 1 | 12 | 0.3 | 1 | 4-4 1 | straight 1 | trop peu |
| latin/reggaeton | beat | 1 | 32 | 1.5 | 1 | 4-4 1 | straight 1 | trop peu |
| latin/samba | beat | 2 | 136 | 4.7 | 1 | 4-4 2 | straight 2 | trop peu |
| latin/samba | fill | 17 | 13 | 0.5 | 1 | 4-4 17 | straight 16, swing 1 | juste |
| latin/venezuelan-joropo | beat | 1 | 41 | 2.1 | 1 | 4-4 1 | swing 1 | trop peu |
| latin/venezuelan-merengue | beat | 1 | 0 | 2.8 | 0 | 5-8 1 | — | trop peu |
| latin/venezuelan-sangueo | beat | 1 | 34 | 1.3 | 1 | 4-4 1 | straight 1 | trop peu |

Total : 97 fichiers, 3839 mesures entières ; 1 fichier(s) non mesuré(s) (métrique à un seul fichier : 5/4, 5/8).

Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; **juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; **juste** ≥ 10 fichiers.

## Ce que disent les mesures

- **latin**, groupe `4-4:straight` (6 fichiers, 431 mesures, 95 BPM médian, fiabilité juste) : timekeeper `hat_closed` (57%), figure `other` (37%) ; kick le plus fréquent [0, 3, 9, 11, 12] (24%) ; caisse claire [6, 14] (14%) ; 0 patterns proposés.
- **latin**, groupe `4-4:ternary` (2 fichiers, 141 mesures, 118 BPM médian, fiabilité trop peu) : timekeeper `ride` (89%), figure `sparse` (86%) ; kick le plus fréquent [0] (82%) ; caisse claire [3] (6%) ; 0 patterns proposés.
- **latin/ando**, groupe `3-4:straight` (1 fichiers, 111 mesures, 125 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (47%), figure `sparse` (34%) ; 0 patterns proposés.
- **latin/bomba**, groupe `4-4:straight` (1 fichiers, 89 mesures, 96 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (39%), figure `sparse` (65%) ; 0 patterns proposés.
- **latin/bounce**, groupe `4-4:straight` (2 fichiers, 132 mesures, 106 BPM médian, fiabilité trop peu) : timekeeper `none` (77%), figure `none` (77%) ; kick le plus fréquent [0, 4, 8, 12] (33%) ; caisse claire [3, 6, 7, 11, 14, 15] (17%) ; 0 patterns proposés.
- **latin/brazilian**, groupe `4-4:straight` (3 fichiers, 97 mesures, 101 BPM médian, fiabilité juste) : timekeeper `ride` (42%), figure `sparse` (35%) ; kick le plus fréquent [4, 6, 12] (30%) ; caisse claire [1, 3, 5, 8, 9, 11, 12, 13, 15] (6%) ; 0 patterns proposés.
- **latin/brazilian**, groupe `4-4:ternary` (1 fichiers, 9 mesures, 92 BPM médian, fiabilité trop peu) : timekeeper `none` (100%), figure `none` (100%) ; 0 patterns proposés.
- **latin/brazilian-frevo**, groupe `4-4:straight` (1 fichiers, 79 mesures, 133 BPM médian, fiabilité trop peu) : timekeeper `none` (97%), figure `none` (97%) ; 0 patterns proposés.
- **latin/brazilian-ijexa**, groupe `4-4:straight` (3 fichiers, 85 mesures, 108 BPM médian, fiabilité juste) : timekeeper `hat_closed` (52%), figure `quarters_plus` (44%) ; kick le plus fréquent [4, 6, 12, 14] (35%) ; 0 patterns proposés.
- **latin/brazilian-maracatu**, groupe `4-4:straight` (1 fichiers, 82 mesures, 96 BPM médian, fiabilité trop peu) : timekeeper `none` (100%), figure `none` (100%) ; 0 patterns proposés.
- **latin/brazilian-maracatu**, groupe `4-4:ternary` (1 fichiers, 100 mesures, 96 BPM médian, fiabilité trop peu) : timekeeper `none` (98%), figure `none` (98%) ; 0 patterns proposés.
- **latin/dominican-merengue**, groupe `4-4:straight` (1 fichiers, 166 mesures, 130 BPM médian, fiabilité trop peu) : timekeeper `ride` (48%), figure `sparse` (69%) ; 0 patterns proposés.
- **latin/merengue**, groupe `4-4:straight` (1 fichiers, 12 mesures, 158 BPM médian, fiabilité trop peu) : timekeeper `none` (100%), figure `none` (100%) ; 0 patterns proposés.
- **latin/reggaeton**, groupe `4-4:straight` (1 fichiers, 32 mesures, 90 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (62%), figure `quarters_plus` (47%) ; 0 patterns proposés.
- **latin/venezuelan-joropo**, groupe `4-4:swing` (1 fichiers, 41 mesures, 80 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (100%), figure `sixteenths` (61%) ; 0 patterns proposés.
- **latin/venezuelan-sangueo**, groupe `4-4:straight` (1 fichiers, 34 mesures, 101 BPM médian, fiabilité trop peu) : timekeeper `ride` (74%), figure `sparse` (41%) ; 0 patterns proposés.

Styles secondaires détaillés dans leur propre dossier : `gmd-latin-brazilian-baiao`, `gmd-latin-brazilian-bossa`, `gmd-latin-brazilian-samba`, `gmd-latin-brazilian-sambareggae`, `gmd-latin-brazilian-songo`, `gmd-latin-chacarera`, `gmd-latin-samba`.

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
