# `gmd-hiphop` — famille hiphop (Groove MIDI Dataset, phase 019, L2)

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
| hiphop | beat | 30 | 796 | 36.8 | 3 | 4-4 30 | straight 30 | assez |
| hiphop | fill | 61 | 83 | 4.0 | 1 | 4-4 61 | straight 50, swing 10, ternary 1 | juste |
| hiphop/groove6 | beat | 4 | 64 | 2.9 | 4 | 4-4 4 | straight 4 | juste |

Total : 95 fichiers, 943 mesures entières.

Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; **juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; **juste** ≥ 10 fichiers.

## Ce que disent les mesures

- **hiphop**, groupe `4-4:straight` (30 fichiers, 796 mesures, 92 BPM médian, fiabilité assez) : timekeeper `hat_closed` (79%), figure `other` (24%) ; kick le plus fréquent [0, 2, 3, 5, 6, 14] (9%) ; caisse claire [4, 12] (33%) ; 10 patterns proposés.
- **hiphop/groove6**, groupe `4-4:straight` (4 fichiers, 64 mesures, 87 BPM médian, fiabilité juste) : timekeeper `hat_closed` (100%), figure `sixteenths` (48%) ; kick le plus fréquent [0, 7, 9, 10, 13, 15] (38%) ; caisse claire [4, 12] (45%) ; 3 patterns proposés.

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
