# `gmd-funk` — famille funk (Groove MIDI Dataset, phase 019, L2)

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
| funk | beat | 36 | 1904 | 80.2 | 4 | 4-4 36 | straight 34, ternary 2 | assez |
| funk | fill | 41 | 52 | 1.9 | 2 | 4-4 41 | straight 40, swing 1 | juste |
| funk/fast | beat | 1 | 70 | 2.3 | 1 | 4-4 1 | straight 1 | trop peu |
| funk/fast | fill | 18 | 18 | 0.5 | 1 | 4-4 18 | straight 18 | juste |
| funk/groove1 | beat | 4 | 64 | 1.9 | 4 | 4-4 4 | straight 4 | juste |
| funk/groove2 | beat | 4 | 63 | 2.4 | 4 | 4-4 4 | straight 4 | juste |
| funk/groove5 | beat | 4 | 64 | 3.0 | 4 | 4-4 4 | straight 4 | juste |
| funk/latin | beat | 2 | 132 | 5.3 | 1 | 4-4 2 | straight 2 | trop peu |
| funk/purdieshuffle | beat | 1 | 104 | 3.2 | 1 | 4-4 1 | ternary 1 | trop peu |
| funk/purdieshuffle | fill | 29 | 35 | 1.0 | 1 | 4-4 29 | straight 3, ternary 26 | juste |
| funk/rock | beat | 1 | 44 | 2.0 | 1 | 4-4 1 | straight 1 | trop peu |
| funk/rock | fill | 19 | 19 | 0.8 | 1 | 4-4 19 | straight 19 | juste |

Total : 160 fichiers, 2569 mesures entières.

Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; **juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; **juste** ≥ 10 fichiers.

## Ce que disent les mesures

- **funk**, groupe `4-4:straight` (34 fichiers, 1842 mesures, 96 BPM médian, fiabilité assez) : timekeeper `hat_closed` (74%), figure `other` (27%) ; kick le plus fréquent [0, 2, 10] (6%) ; caisse claire [4, 12] (15%) ; 19 patterns proposés.
- **funk**, groupe `4-4:ternary` (2 fichiers, 62 mesures, 102 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (82%), figure `sparse` (32%) ; caisse claire [1, 3, 4, 5, 7, 9, 10, 11] (42%) ; 0 patterns proposés.
- **funk/fast**, groupe `4-4:straight` (1 fichiers, 70 mesures, 125 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (77%), figure `sparse` (70%) ; 0 patterns proposés.
- **funk/groove1**, groupe `4-4:straight` (4 fichiers, 64 mesures, 138 BPM médian, fiabilité juste) : timekeeper `ride` (75%), figure `eighths` (77%) ; kick le plus fréquent [0, 2, 10, 11] (50%) ; caisse claire [4, 7, 9, 12, 15] (19%) ; 3 patterns proposés.
- **funk/groove2**, groupe `4-4:straight` (4 fichiers, 63 mesures, 105 BPM médian, fiabilité juste) : timekeeper `hat_closed` (100%), figure `quarters_plus` (56%) ; kick le plus fréquent [0, 3, 7, 9, 10] (70%) ; caisse claire [4, 12] (51%) ; 3 patterns proposés.
- **funk/groove5**, groupe `4-4:straight` (4 fichiers, 64 mesures, 84 BPM médian, fiabilité juste) : timekeeper `hat_closed` (91%), figure `sixteenths` (67%) ; kick le plus fréquent [0, 3, 10, 13] (27%) ; caisse claire [4, 7, 12] (22%) ; 3 patterns proposés.
- **funk/latin**, groupe `4-4:straight` (2 fichiers, 132 mesures, 100 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (65%), figure `other` (43%) ; kick le plus fréquent [0, 5, 7] (14%) ; caisse claire [4, 12] (24%) ; 0 patterns proposés.
- **funk/rock**, groupe `4-4:straight` (1 fichiers, 44 mesures, 92 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (36%), figure `eighths` (36%) ; 0 patterns proposés.

Styles secondaires détaillés dans leur propre dossier : `gmd-funk-purdieshuffle`.

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
