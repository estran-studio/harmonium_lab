# `gmd-reggae` — famille reggae (Groove MIDI Dataset, phase 019, L2)

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
| reggae | beat | 3 | 253 | 8.5 | 2 | 4-4 3 | straight 2, ternary 1 | juste |
| reggae | fill | 16 | 16 | 0.7 | 1 | 4-4 16 | straight 16 | juste |
| reggae/slow | beat | 1 | 29 | 1.9 | 1 | 4-4 1 | straight 1 | trop peu |

Total : 20 fichiers, 298 mesures entières.

Fiabilité (seuils de `gmd_styles.RELIABILITY`) : `beat` **assez** ≥ 8 fichiers, ≥ 3 batteurs, ≥ 200 mesures ; **juste** ≥ 3 fichiers et ≥ 60 mesures ; sinon **trop peu**. `fill` **assez** ≥ 30 fichiers, ≥ 3 batteurs ; **juste** ≥ 10 fichiers.

## Ce que disent les mesures

- **reggae**, groupe `4-4:straight` (2 fichiers, 132 mesures, 102 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (66%), figure `sparse` (39%) ; kick le plus fréquent [0, 4, 8, 12] (72%) ; caisse claire [14] (2%) ; 0 patterns proposés.
- **reggae**, groupe `4-4:ternary` (1 fichiers, 121 mesures, 141 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (87%), figure `sparse` (47%) ; 0 patterns proposés.
- **reggae/slow**, groupe `4-4:straight` (1 fichiers, 29 mesures, 64 BPM médian, fiabilité trop peu) : timekeeper `hat_closed` (100%), figure `sixteenths` (72%) ; 0 patterns proposés.

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
