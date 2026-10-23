# DS-T9b — valeurs proposées pour les profils britanniques du moteur (non appliquées)

Dérivées des références régénérées (`references/structure/britannique_coloniale-{jig,hornpipe}.json`) et des secondes fins mesurées par `specs/011-phase3-phrase/measure_endings.py` du dépôt moteur (relancé sans modification, lab-root = ce worktree). La formule est celle des profils actuels : rejouée sur les **anciennes** références, elle reproduit à l'identique tous les champs `roles`, `second_ending` et `rhythm` des trois profils. Chaque bloc remplace le champ du même nom dans le `[[form.parts]]` indiqué ; rien d'autre ne change.

- `marche_britannique_coloniale` : **aucun changement** (aucun air de marche touché ; références et secondes fins identiques).
- Contrôle : copies des trois profils dans `/tmp`, blocs substitués, `harmonium-cli --export --profile <dossier> --bars 34 --seed 3` (binaire existant, dépôt moteur non modifié) : chargement et validation passent ; chaque `roles` somme à 10 000.

Formules : poids = `round(taux × 10 000)` à partir des effectifs `transformations` (CopyOf/SequenceOf/VariedEndOf) et `Free` = reste ; décalages = effectifs `sequence_shifts` ; cadences m.4/m.8 : `CadTonic` = repos tonique, `CadHalf` = finale longue − repos tonique, `CadOpen` = reste ; B:m.7 : `CopyOfPart` = `B:m7/A:m7` exact et les autres poids de la mesure sont multipliés par `1 − p` ; `second_ending` = effectifs `eight_{A,B}:second_written` ; `rhythm` = motifs de mesure pleine, entiers, à au moins deux durées distinctes de `real.rhythm.cells`, poids = effectifs.

### `gigue_britannique_coloniale` — partie A — `roles (positions modifiées : m.2, m.3, m.4, m.5, m.6, m.7, m.8)`

```toml
roles = [
  "Open",
  { choose = [{ role = { CopyOf = 1 }, weight = 322 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = 1, weight = 5 }, { degrees = -2, weight = 3 }, { degrees = 2, weight = 2 }, { degrees = -1, weight = 1 }, { degrees = -4, weight = 1 }, { degrees = 3, weight = 1 }] } }, weight = 418 }, { role = { VariedEndOf = 1 }, weight = 579 }, { role = "Free", weight = 8681 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 1125 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = -1, weight = 7 }, { degrees = -2, weight = 2 }, { degrees = 1, weight = 2 }, { degrees = 2, weight = 2 }, { degrees = -7, weight = 1 }, { degrees = 5, weight = 1 }] } }, weight = 482 }, { role = { VariedEndOf = 1 }, weight = 1029 }, { role = "Free", weight = 7364 }] },
  { choose = [{ role = "CadTonic", weight = 193 }, { role = "CadHalf", weight = 868 }, { role = "CadOpen", weight = 8939 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 7395 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = -1, weight = 2 }, { degrees = -2, weight = 1 }, { degrees = -3, weight = 1 }] } }, weight = 129 }, { role = { VariedEndOf = 1 }, weight = 386 }, { role = "Free", weight = 2090 }] },
  { choose = [{ role = { CopyOf = 2 }, weight = 5338 }, { role = { SequenceOf = { bar = 2, shift = [{ degrees = -1, weight = 2 }, { degrees = 1, weight = 1 }, { degrees = 2, weight = 1 }] } }, weight = 129 }, { role = { VariedEndOf = 2 }, weight = 1865 }, { role = "Free", weight = 2668 }] },
  { choose = [{ role = { CopyOf = 3 }, weight = 1576 }, { role = { SequenceOf = { bar = 3, shift = [{ degrees = 1, weight = 2 }, { degrees = -1, weight = 1 }, { degrees = -3, weight = 1 }, { degrees = -4, weight = 1 }] } }, weight = 161 }, { role = { VariedEndOf = 3 }, weight = 1576 }, { role = "Free", weight = 6687 }] },
  { choose = [{ role = "CadTonic", weight = 1286 }, { role = "CadHalf", weight = 643 }, { role = "CadOpen", weight = 8071 }] },
]
```

### `gigue_britannique_coloniale` — partie A — `second_ending`

```toml
second_ending = { choose = [{ role = "CadTonic", weight = 213 }, { role = "CadFifth", weight = 15 }, { role = "CadOther", weight = 32 }] }
```

### `gigue_britannique_coloniale` — partie A — `rhythm (m.4 et m.8, même distribution)`

```toml
rhythm = [
  { bar = 4, patterns = [
    { durations = [2, 1, 2, 1], weight = 1046 },
    { durations = [2, 1, 1, 1, 1], weight = 972 },
    { durations = [1, 1, 1, 2, 1], weight = 961 },
    { durations = [3, 2, 1], weight = 495 },
    { durations = [3, 1, 1, 1], weight = 275 },
    { durations = [1, 1, 1, 3], weight = 247 },
    { durations = [2, 1, 3], weight = 135 },
    { durations = [1, 2, 2, 1], weight = 11 },
    { durations = [4, 1, 1], weight = 10 },
    { durations = [1, 2, 3], weight = 4 },
    { durations = [1, 2, 1, 1, 1], weight = 3 },
    { durations = [1, 2, 1, 2], weight = 2 },
    { durations = [2, 1, 1, 2], weight = 2 },
    { durations = [1, 1, 1, 1, 2], weight = 1 },
    { durations = [5, 1], weight = 1 },
  ] },
  { bar = 8, patterns = [
    { durations = [2, 1, 2, 1], weight = 1046 },
    { durations = [2, 1, 1, 1, 1], weight = 972 },
    { durations = [1, 1, 1, 2, 1], weight = 961 },
    { durations = [3, 2, 1], weight = 495 },
    { durations = [3, 1, 1, 1], weight = 275 },
    { durations = [1, 1, 1, 3], weight = 247 },
    { durations = [2, 1, 3], weight = 135 },
    { durations = [1, 2, 2, 1], weight = 11 },
    { durations = [4, 1, 1], weight = 10 },
    { durations = [1, 2, 3], weight = 4 },
    { durations = [1, 2, 1, 1, 1], weight = 3 },
    { durations = [1, 2, 1, 2], weight = 2 },
    { durations = [2, 1, 1, 2], weight = 2 },
    { durations = [1, 1, 1, 1, 2], weight = 1 },
    { durations = [5, 1], weight = 1 },
  ] },
]
```

### `gigue_britannique_coloniale` — partie B — `roles (positions modifiées : m.2, m.3, m.4, m.5, m.6, m.7, m.8)`

```toml
roles = [
  "Open",
  { choose = [{ role = { CopyOf = 1 }, weight = 436 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = 1, weight = 11 }, { degrees = -1, weight = 7 }, { degrees = 2, weight = 2 }, { degrees = -2, weight = 1 }, { degrees = -4, weight = 1 }, { degrees = 3, weight = 1 }] } }, weight = 772 }, { role = { VariedEndOf = 1 }, weight = 839 }, { role = "Free", weight = 7953 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 1611 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = -1, weight = 7 }, { degrees = 1, weight = 7 }, { degrees = -3, weight = 6 }, { degrees = 2, weight = 5 }, { degrees = 3, weight = 2 }, { degrees = -2, weight = 1 }, { degrees = -7, weight = 1 }, { degrees = 4, weight = 1 }, { degrees = 5, weight = 1 }, { degrees = 7, weight = 1 }] } }, weight = 1074 }, { role = { VariedEndOf = 1 }, weight = 940 }, { role = "Free", weight = 6375 }] },
  { choose = [{ role = "CadTonic", weight = 168 }, { role = "CadHalf", weight = 2047 }, { role = "CadOpen", weight = 7785 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 4866 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = -4, weight = 3 }, { degrees = 3, weight = 3 }, { degrees = -2, weight = 1 }, { degrees = -6, weight = 1 }, { degrees = 1, weight = 1 }] } }, weight = 302 }, { role = { VariedEndOf = 1 }, weight = 201 }, { role = "Free", weight = 4631 }] },
  { choose = [{ role = { CopyOf = 2 }, weight = 3289 }, { role = { SequenceOf = { bar = 2, shift = [{ degrees = -1, weight = 1 }, { degrees = -4, weight = 1 }, { degrees = -5, weight = 1 }, { degrees = 1, weight = 1 }, { degrees = 3, weight = 1 }, { degrees = 4, weight = 1 }] } }, weight = 201 }, { role = { VariedEndOf = 2 }, weight = 1242 }, { role = "Free", weight = 5268 }] },
  { choose = [{ role = { CopyOf = 3 }, weight = 523 }, { role = { SequenceOf = { bar = 3, shift = [{ degrees = -3, weight = 1 }, { degrees = 1, weight = 1 }, { degrees = 2, weight = 1 }, { degrees = 4, weight = 1 }] } }, weight = 87 }, { role = { VariedEndOf = 3 }, weight = 523 }, { role = { CopyOfPart = { part = "A", bar = 7 } }, weight = 3503 }, { role = "Free", weight = 5364 }] },
  { choose = [{ role = "CadTonic", weight = 1779 }, { role = "CadHalf", weight = 604 }, { role = "CadOpen", weight = 7617 }] },
]
```

### `gigue_britannique_coloniale` — partie B — `second_ending`

```toml
second_ending = { choose = [{ role = "CadTonic", weight = 103 }, { role = "CadFifth", weight = 12 }, { role = "CadOther", weight = 21 }] }
```

### `gigue_britannique_coloniale` — partie B — `rhythm (m.4 et m.8, même distribution)`

```toml
rhythm = [
  { bar = 4, patterns = [
    { durations = [2, 1, 2, 1], weight = 1046 },
    { durations = [2, 1, 1, 1, 1], weight = 972 },
    { durations = [1, 1, 1, 2, 1], weight = 961 },
    { durations = [3, 2, 1], weight = 495 },
    { durations = [3, 1, 1, 1], weight = 275 },
    { durations = [1, 1, 1, 3], weight = 247 },
    { durations = [2, 1, 3], weight = 135 },
    { durations = [1, 2, 2, 1], weight = 11 },
    { durations = [4, 1, 1], weight = 10 },
    { durations = [1, 2, 3], weight = 4 },
    { durations = [1, 2, 1, 1, 1], weight = 3 },
    { durations = [1, 2, 1, 2], weight = 2 },
    { durations = [2, 1, 1, 2], weight = 2 },
    { durations = [1, 1, 1, 1, 2], weight = 1 },
    { durations = [5, 1], weight = 1 },
  ] },
  { bar = 8, patterns = [
    { durations = [2, 1, 2, 1], weight = 1046 },
    { durations = [2, 1, 1, 1, 1], weight = 972 },
    { durations = [1, 1, 1, 2, 1], weight = 961 },
    { durations = [3, 2, 1], weight = 495 },
    { durations = [3, 1, 1, 1], weight = 275 },
    { durations = [1, 1, 1, 3], weight = 247 },
    { durations = [2, 1, 3], weight = 135 },
    { durations = [1, 2, 2, 1], weight = 11 },
    { durations = [4, 1, 1], weight = 10 },
    { durations = [1, 2, 3], weight = 4 },
    { durations = [1, 2, 1, 1, 1], weight = 3 },
    { durations = [1, 2, 1, 2], weight = 2 },
    { durations = [2, 1, 1, 2], weight = 2 },
    { durations = [1, 1, 1, 1, 2], weight = 1 },
    { durations = [5, 1], weight = 1 },
  ] },
]
```

### `hornpipe_britannique_coloniale` — partie A — `roles (positions modifiées : m.2, m.3, m.4, m.5, m.6, m.7, m.8)`

```toml
roles = [
  "Open",
  { choose = [{ role = { SequenceOf = { bar = 1, shift = [{ degrees = 1, weight = 2 }, { degrees = -4, weight = 1 }, { degrees = 2, weight = 1 }] } }, weight = 667 }, { role = { VariedEndOf = 1 }, weight = 667 }, { role = "Free", weight = 8666 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 500 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = -1, weight = 4 }, { degrees = -3, weight = 1 }, { degrees = 2, weight = 1 }] } }, weight = 1000 }, { role = { VariedEndOf = 1 }, weight = 167 }, { role = "Free", weight = 8333 }] },
  { choose = [{ role = "CadHalf", weight = 1833 }, { role = "CadOpen", weight = 8167 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 8500 }, { role = { VariedEndOf = 1 }, weight = 333 }, { role = "Free", weight = 1167 }] },
  { choose = [{ role = { CopyOf = 2 }, weight = 7500 }, { role = { VariedEndOf = 2 }, weight = 833 }, { role = "Free", weight = 1667 }] },
  { choose = [{ role = { CopyOf = 3 }, weight = 2000 }, { role = { VariedEndOf = 3 }, weight = 2500 }, { role = "Free", weight = 5500 }] },
  { choose = [{ role = "CadTonic", weight = 667 }, { role = "CadHalf", weight = 2667 }, { role = "CadOpen", weight = 6666 }] },
]
```

### `hornpipe_britannique_coloniale` — partie A — `second_ending`

```toml
second_ending = { choose = [{ role = "CadTonic", weight = 46 }, { role = "CadFifth", weight = 3 }, { role = "CadOther", weight = 3 }] }
```

### `hornpipe_britannique_coloniale` — partie A — `rhythm (m.4 et m.8, même distribution)`

```toml
rhythm = [
  { bar = 4, patterns = [
    { durations = [1, 1, 1, 1, 2, 1, 1], weight = 103 },
    { durations = [2, 2, 2, 1, 1], weight = 83 },
    { durations = [1, 1, 1, 1, 2, 2], weight = 49 },
    { durations = [2, 1, 1, 1, 1, 1, 1], weight = 39 },
    { durations = [2, 1, 1, 2, 1, 1], weight = 39 },
    { durations = [2, 2, 1, 1, 1, 1], weight = 36 },
    { durations = [1, 1, 1, 1, 1, 1, 2], weight = 20 },
    { durations = [1, 1, 1, 1, 4], weight = 16 },
    { durations = [2, 2, 3, 1], weight = 12 },
    { durations = [4, 2, 1, 1], weight = 12 },
    { durations = [2, 1, 2, 1, 1, 1], weight = 10 },
    { durations = [1, 2, 1, 2, 2], weight = 7 },
    { durations = [1, 1, 1, 2, 1, 1, 1], weight = 6 },
    { durations = [2, 2, 4], weight = 6 },
    { durations = [3, 1, 1, 1, 1, 1], weight = 6 },
    { durations = [1, 1, 1, 1, 3, 1], weight = 5 },
    { durations = [2, 1, 1, 1, 1, 2], weight = 4 },
    { durations = [2, 2, 1, 1, 2], weight = 4 },
    { durations = [4, 2, 2], weight = 4 },
    { durations = [6, 1, 1], weight = 4 },
    { durations = [2, 1, 1, 2, 2], weight = 3 },
    { durations = [1, 1, 2, 1, 1, 1, 1], weight = 2 },
    { durations = [1, 1, 2, 2, 1, 1], weight = 2 },
    { durations = [3, 1, 2, 2], weight = 2 },
    { durations = [4, 1, 1, 1, 1], weight = 2 },
    { durations = [6, 2], weight = 2 },
    { durations = [1, 1, 2, 4], weight = 1 },
    { durations = [2, 1, 1, 3, 1], weight = 1 },
    { durations = [2, 1, 1, 4], weight = 1 },
    { durations = [3, 1, 3, 1], weight = 1 },
  ] },
  { bar = 8, patterns = [
    { durations = [1, 1, 1, 1, 2, 1, 1], weight = 103 },
    { durations = [2, 2, 2, 1, 1], weight = 83 },
    { durations = [1, 1, 1, 1, 2, 2], weight = 49 },
    { durations = [2, 1, 1, 1, 1, 1, 1], weight = 39 },
    { durations = [2, 1, 1, 2, 1, 1], weight = 39 },
    { durations = [2, 2, 1, 1, 1, 1], weight = 36 },
    { durations = [1, 1, 1, 1, 1, 1, 2], weight = 20 },
    { durations = [1, 1, 1, 1, 4], weight = 16 },
    { durations = [2, 2, 3, 1], weight = 12 },
    { durations = [4, 2, 1, 1], weight = 12 },
    { durations = [2, 1, 2, 1, 1, 1], weight = 10 },
    { durations = [1, 2, 1, 2, 2], weight = 7 },
    { durations = [1, 1, 1, 2, 1, 1, 1], weight = 6 },
    { durations = [2, 2, 4], weight = 6 },
    { durations = [3, 1, 1, 1, 1, 1], weight = 6 },
    { durations = [1, 1, 1, 1, 3, 1], weight = 5 },
    { durations = [2, 1, 1, 1, 1, 2], weight = 4 },
    { durations = [2, 2, 1, 1, 2], weight = 4 },
    { durations = [4, 2, 2], weight = 4 },
    { durations = [6, 1, 1], weight = 4 },
    { durations = [2, 1, 1, 2, 2], weight = 3 },
    { durations = [1, 1, 2, 1, 1, 1, 1], weight = 2 },
    { durations = [1, 1, 2, 2, 1, 1], weight = 2 },
    { durations = [3, 1, 2, 2], weight = 2 },
    { durations = [4, 1, 1, 1, 1], weight = 2 },
    { durations = [6, 2], weight = 2 },
    { durations = [1, 1, 2, 4], weight = 1 },
    { durations = [2, 1, 1, 3, 1], weight = 1 },
    { durations = [2, 1, 1, 4], weight = 1 },
    { durations = [3, 1, 3, 1], weight = 1 },
  ] },
]
```

### `hornpipe_britannique_coloniale` — partie B — `roles (positions modifiées : m.2, m.3, m.4, m.5, m.6, m.7, m.8)`

```toml
roles = [
  "Open",
  { choose = [{ role = { CopyOf = 1 }, weight = 820 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = 1, weight = 3 }] } }, weight = 492 }, { role = { VariedEndOf = 1 }, weight = 984 }, { role = "Free", weight = 7704 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 1639 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = -1, weight = 2 }, { degrees = -2, weight = 1 }, { degrees = -4, weight = 1 }, { degrees = 1, weight = 1 }] } }, weight = 820 }, { role = { VariedEndOf = 1 }, weight = 1311 }, { role = "Free", weight = 6230 }] },
  { choose = [{ role = "CadTonic", weight = 492 }, { role = "CadHalf", weight = 1803 }, { role = "CadOpen", weight = 7705 }] },
  { choose = [{ role = { CopyOf = 1 }, weight = 4262 }, { role = { SequenceOf = { bar = 1, shift = [{ degrees = -4, weight = 1 }] } }, weight = 164 }, { role = "Free", weight = 5574 }] },
  { choose = [{ role = { CopyOf = 2 }, weight = 2787 }, { role = { SequenceOf = { bar = 2, shift = [{ degrees = 1, weight = 1 }] } }, weight = 164 }, { role = { VariedEndOf = 2 }, weight = 1639 }, { role = "Free", weight = 5410 }] },
  { choose = [{ role = { CopyOf = 3 }, weight = 373 }, { role = { VariedEndOf = 3 }, weight = 560 }, { role = { CopyOfPart = { part = "A", bar = 7 } }, weight = 4310 }, { role = "Free", weight = 4757 }] },
  { choose = [{ role = "CadTonic", weight = 820 }, { role = "CadHalf", weight = 1475 }, { role = "CadOpen", weight = 7705 }] },
]
```

### `hornpipe_britannique_coloniale` — partie B — `second_ending`

```toml
second_ending = { choose = [{ role = "CadTonic", weight = 12 }, { role = "CadOther", weight = 1 }] }
```

### `hornpipe_britannique_coloniale` — partie B — `rhythm (m.4 et m.8, même distribution)`

```toml
rhythm = [
  { bar = 4, patterns = [
    { durations = [1, 1, 1, 1, 2, 1, 1], weight = 103 },
    { durations = [2, 2, 2, 1, 1], weight = 83 },
    { durations = [1, 1, 1, 1, 2, 2], weight = 49 },
    { durations = [2, 1, 1, 1, 1, 1, 1], weight = 39 },
    { durations = [2, 1, 1, 2, 1, 1], weight = 39 },
    { durations = [2, 2, 1, 1, 1, 1], weight = 36 },
    { durations = [1, 1, 1, 1, 1, 1, 2], weight = 20 },
    { durations = [1, 1, 1, 1, 4], weight = 16 },
    { durations = [2, 2, 3, 1], weight = 12 },
    { durations = [4, 2, 1, 1], weight = 12 },
    { durations = [2, 1, 2, 1, 1, 1], weight = 10 },
    { durations = [1, 2, 1, 2, 2], weight = 7 },
    { durations = [1, 1, 1, 2, 1, 1, 1], weight = 6 },
    { durations = [2, 2, 4], weight = 6 },
    { durations = [3, 1, 1, 1, 1, 1], weight = 6 },
    { durations = [1, 1, 1, 1, 3, 1], weight = 5 },
    { durations = [2, 1, 1, 1, 1, 2], weight = 4 },
    { durations = [2, 2, 1, 1, 2], weight = 4 },
    { durations = [4, 2, 2], weight = 4 },
    { durations = [6, 1, 1], weight = 4 },
    { durations = [2, 1, 1, 2, 2], weight = 3 },
    { durations = [1, 1, 2, 1, 1, 1, 1], weight = 2 },
    { durations = [1, 1, 2, 2, 1, 1], weight = 2 },
    { durations = [3, 1, 2, 2], weight = 2 },
    { durations = [4, 1, 1, 1, 1], weight = 2 },
    { durations = [6, 2], weight = 2 },
    { durations = [1, 1, 2, 4], weight = 1 },
    { durations = [2, 1, 1, 3, 1], weight = 1 },
    { durations = [2, 1, 1, 4], weight = 1 },
    { durations = [3, 1, 3, 1], weight = 1 },
  ] },
  { bar = 8, patterns = [
    { durations = [1, 1, 1, 1, 2, 1, 1], weight = 103 },
    { durations = [2, 2, 2, 1, 1], weight = 83 },
    { durations = [1, 1, 1, 1, 2, 2], weight = 49 },
    { durations = [2, 1, 1, 1, 1, 1, 1], weight = 39 },
    { durations = [2, 1, 1, 2, 1, 1], weight = 39 },
    { durations = [2, 2, 1, 1, 1, 1], weight = 36 },
    { durations = [1, 1, 1, 1, 1, 1, 2], weight = 20 },
    { durations = [1, 1, 1, 1, 4], weight = 16 },
    { durations = [2, 2, 3, 1], weight = 12 },
    { durations = [4, 2, 1, 1], weight = 12 },
    { durations = [2, 1, 2, 1, 1, 1], weight = 10 },
    { durations = [1, 2, 1, 2, 2], weight = 7 },
    { durations = [1, 1, 1, 2, 1, 1, 1], weight = 6 },
    { durations = [2, 2, 4], weight = 6 },
    { durations = [3, 1, 1, 1, 1, 1], weight = 6 },
    { durations = [1, 1, 1, 1, 3, 1], weight = 5 },
    { durations = [2, 1, 1, 1, 1, 2], weight = 4 },
    { durations = [2, 2, 1, 1, 2], weight = 4 },
    { durations = [4, 2, 2], weight = 4 },
    { durations = [6, 1, 1], weight = 4 },
    { durations = [2, 1, 1, 2, 2], weight = 3 },
    { durations = [1, 1, 2, 1, 1, 1, 1], weight = 2 },
    { durations = [1, 1, 2, 2, 1, 1], weight = 2 },
    { durations = [3, 1, 2, 2], weight = 2 },
    { durations = [4, 1, 1, 1, 1], weight = 2 },
    { durations = [6, 2], weight = 2 },
    { durations = [1, 1, 2, 4], weight = 1 },
    { durations = [2, 1, 1, 3, 1], weight = 1 },
    { durations = [2, 1, 1, 4], weight = 1 },
    { durations = [3, 1, 3, 1], weight = 1 },
  ] },
]
```
