# `gmd-rock` — famille rock (Groove MIDI Dataset, phase 019, L2)

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
| rock | beat | 193 | 5367 | 204.6 | 9 | 3-4 1, 4-4 187, 6-8 5 | straight 167, swing 7, ternary 19 | assez |
| rock | fill | 88 | 134 | 5.3 | 4 | 4-4 88 | straight 84, swing 1, ternary 3 | assez |
| rock/folk | beat | 1 | 100 | 4.5 | 1 | 4-4 1 | straight 1 | trop peu |
| rock/groove8 | beat | 4 | 60 | 3.9 | 4 | 4-4 4 | straight 4 | juste |
| rock/halftime | beat | 1 | 125 | 3.6 | 1 | 4-4 1 | straight 1 | trop peu |
| rock/halftime | fill | 36 | 41 | 1.2 | 1 | 4-4 36 | straight 36 | juste |
| rock/indie | beat | 4 | 174 | 8.1 | 2 | 4-4 4 | straight 4 | juste |
| rock/indie | fill | 6 | 5 | 0.3 | 1 | 4-4 6 | straight 6 | trop peu |
| rock/prog | beat | 3 | 226 | 8.8 | 1 | 4-4 2, 5-4 1 | straight 1, ternary 1 | trop peu |
| rock/rockabilly | beat | 1 | 260 | 5.2 | 1 | 4-4 1 | ternary 1 | trop peu |
| rock/shuffle | beat | 4 | 296 | 11.1 | 3 | 4-4 4 | straight 1, swing 1, ternary 2 | juste |

Total : 341 fichiers, 6788 mesures entières ; 1 fichier(s) non mesuré(s) (métrique à un seul fichier : 5/4, 5/8).

Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; **juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; **juste** ≥ 10 fichiers.

## Ce que disent les mesures

- **rock**, groupe `3-4:straight` (1 fichiers, 108 mesures, 102 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (56%), figure `quarters_plus` (45%) ; 0 patterns proposés.
- **rock**, groupe `4-4:straight` (154 fichiers, 4440 mesures, 105 BPM médian, fiabilité assez) : timekeeper `ride` (35%), figure `sparse` (38%) ; kick le plus fréquent [4] (9%) ; caisse claire [4, 12] (30%) ; 22 patterns proposés.
- **rock**, groupe `4-4:swing` (7 fichiers, 105 mesures, 130 BPM médian, fiabilité juste) : timekeeper `ride` (53%), figure `sparse` (74%) ; kick le plus fréquent [0] (6%) ; caisse claire [1, 4, 6, 8, 11, 13, 15] (3%) ; 0 patterns proposés.
- **rock**, groupe `4-4:ternary` (19 fichiers, 610 mesures, 96 BPM médian, fiabilité assez) : timekeeper `hat_closed` (50%), figure `sparse` (44%) ; kick le plus fréquent [0, 3, 6, 9] (12%) ; caisse claire [3, 9] (39%) ; 6 patterns proposés.
- **rock**, groupe `6-8:straight` (5 fichiers, 104 mesures, 70 BPM médian, fiabilité juste) : timekeeper `ride` (63%), figure `other` (38%) ; kick le plus fréquent [0, 3, 5, 6, 9, 11] (14%) ; caisse claire [1, 4, 7, 10] (14%) ; 0 patterns proposés.
- **rock/folk**, groupe `4-4:straight` (1 fichiers, 100 mesures, 90 BPM médian, fiabilité trop peu) : timekeeper `none` (56%), figure `none` (56%) ; 0 patterns proposés.
- **rock/groove8**, groupe `4-4:straight` (4 fichiers, 60 mesures, 65 BPM médian, fiabilité juste) : timekeeper `hat_closed` (100%), figure `other` (52%) ; kick le plus fréquent [0, 7, 8] (60%) ; caisse claire [4, 12] (45%) ; 3 patterns proposés.
- **rock/halftime**, groupe `4-4:straight` (1 fichiers, 125 mesures, 140 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (35%), figure `eighths` (23%) ; 1 patterns proposés.
- **rock/prog**, groupe `4-4:straight` (1 fichiers, 152 mesures, 125 BPM médian, fiabilité trop peu) : timekeeper `none` (72%), figure `none` (72%) ; 0 patterns proposés.
- **rock/prog**, groupe `4-4:ternary` (1 fichiers, 74 mesures, 190 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (46%), figure `other` (49%) ; 0 patterns proposés.
- **rock/rockabilly**, groupe `4-4:ternary` (1 fichiers, 260 mesures, 200 BPM médian, fiabilité trop peu) : timekeeper `none` (76%), figure `none` (76%) ; 0 patterns proposés.

Styles secondaires détaillés dans leur propre dossier : `gmd-rock-indie`, `gmd-rock-shuffle`.

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
