# Dataset trad québécois — écouter, comparer, s'inspirer

**Statut** : en cours | **Date** : 2026-10-19 | **Repo** : `harmonium_lab` (Python) | **Consommateur** : moteur `harmonium` (`harmonium_core::trad`)

## Pourquoi

Le moteur génère des reels (phase 1 du moteur). Le propriétaire n'est pas
expert : il ne peut pas dire *pourquoi* un air sonne « pas trad ». Le dataset
remplace l'expertise par trois outils :

1. **Écouter à armes égales** — chaque air réel est rendu avec la même
   SoundFont (GeneralUser GS), le même violon, la même basse/guitare et des
   pieds comparables au moteur ; un kit en aveugle mélange réels et générés.
   La question devient « est-ce que j'entends la différence ? ».
2. **Comparer** — les mêmes statistiques trad sont calculées sur le corpus
   et sur la sortie du moteur ; le rapport dit en clair où ça diverge.
3. **S'inspirer** — le vocabulaire du moteur (cellules d'une mesure,
   enchaînements d'accords, tempos) est extrait du corpus au lieu d'être
   inventé.

La direction musicale du jeu (`1867_lore`, `design/jeu.md` §10 bis,
`design/biomes/*.md`) fixe les styles : reel (salles, boss du Diable),
gigue (pas de gigue du gameplay), valse (veillées), quadrille / cotillon /
marche (bal de Québec).

## Décisions

### D1 — Droits : usage interne

Les sources sont téléchargées par script et **jamais redistribuées** : seuls
les manifestes (titre, source, URL, licence, empreinte) et les statistiques
dérivées sont versionnés. Le jeu n'embarque jamais un air du corpus tel quel ;
le moteur ne reçoit que des tables agrégées (cellules en degrés, fréquences).

### D2 — Sources v1

| Source | Contenu | Licence |
|---|---|---|
| John Chambers, `trillian.mit.edu/~jc/music/abc/Quebec/{reel,jig,waltz,march,...}` | ~387 reels, ~71 gigues, ~31 valses, ~6 marches en ABC, avec accords (`"G"`), `R:`, `O:`, `Z:` | non précisée — usage interne, attribution |
| The Session, `github.com/adactio/TheSession-data` | ABC typés (reel, jig, waltz, march, …) ; filtrage québécois par enregistrements d'artistes québécois et titres français | ODbL |

Quadrille / cotillon : peu de transcriptions dédiées ; v1 = airs marqués
comme tels dans les sources (titre, `R:`, notes) + marches. Lacune documentée,
pas inventée.

### D3 — Disposition

```text
corpus/trad/                      gitignoré, recréé par `make trad-corpus`
  raw/<source>/...                fichiers tels que téléchargés
  tunes/<type>/<id>.abc           un air par fichier, normalisé
corpus/trad/manifest.jsonl        VERSIONNÉ : une ligne par air
corpus/trad/VERSION               VERSIONNÉ : version du corpus (constitution II)
target/trad_render/<type>/<id>.{mid,musicxml,wav}   gitignoré
references/trad-<type>/profile.json                  versionné (statistiques)
```

Ligne de manifeste :
`{id, title, aliases, type, meter, key, mode, bars, source, url, license, sha256, included_because, incipit}`
où `type ∈ {reel, jig, waltz, march, quadrille, cotillon}`, `id` stable
(slug titre + empreinte courte), `incipit` = 2 premières mesures en hauteurs
(sert au dédoublonnage entre sources).

### D4 — Rendu à armes égales

ABC → MIDI par `abc2midi` (`brew install abcmidi`) avec reprises jouées
(AABB), programmes GM identiques au moteur (violon 40, guitare acier 24 pour
les accords de l'ABC, basse acoustique 32), un motif de pieds `%%MIDI drum`
équivalent à la table D9 du moteur (talon 36 / pointe 37), tempo par type
(reel 230 à la noire, gigue 115 à la noire pointée, valse 150, marche 110),
swing nul (le violon de l'ABC est noté droit). MIDI → WAV par `fluidsynth`
avec `GeneralUser-GS.sf2` (la même banque que le moteur, `make soundfont`
côté moteur). MusicXML par `music21` pour le crate Rust si besoin.

### D5 — Statistiques trad (mêmes fonctions pour corpus et moteur)

Sur la mélodie (canal 0 du moteur ; voix principale de l'ABC) :
- forme : segmentation en parties de 8 mesures, détection AABB, taux de
  mesures identiques (1-2 vs 5-6, reprises) ;
- cadences : degré de la dernière note forte des mesures 4 et 8 ;
- registre : ambitus et hauteur moyenne par partie (A vs B) ;
- intervalles : histogramme (unisson, seconde, tierce, quarte, quinte, >
  quinte), taux de mouvement conjoint ;
- rythme : histogramme des durées et des positions d'attaque dans la mesure ;
- tonalité et mode ; vocabulaire de cellules (une mesure en degrés, notation
  du moteur : `1 3 5 3 1 3 5 3`, `5,`, `-`).
Sur l'harmonie (accords de l'ABC ; pistes Chords/Bass du moteur) :
vocabulaire en degrés, enchaînements, rythme harmonique.

Profil par type = distribution (moyenne, écart-type, quantiles,
histogrammes) sur tout le corpus de ce type.

### D6 — Comparaison et écoute

- `harmonium-lab trad-compare --generated <dir de .mid> --type reel` :
  rapport JSON + Markdown en français, écarts triés par z-score, avec une
  phrase par écart (« les reels réels font 31 % de sauts ≥ quarte, le moteur
  12 % »), et les 3 airs réels les plus proches de chaque généré.
- `harmonium-lab blindtest --type reel --real 10 --generated 10` : WAV
  renommés au hasard dans `target/blindtest/<horodatage>/`, feuille de
  réponse vide, corrigé séparé, script de score.

### D7 — Inspiration vers le moteur

`harmonium-lab mine-cells --type reel -o reel_cells.toml` : cellules d'une
mesure extraites du corpus, en degrés relatifs à la tonique, au format exact
de `harmonium_core/src/trad/reel_cells.toml`, rôle déduit de la position
(mesure 1 `open`, 4 `cad_half`, 8 `cad_full`, autres `run`/`arp`/`turn` par
les intervalles), poids = fréquence. Plus : table d'enchaînements d'accords
et plages de tempo par type. Le moteur les adopte par PR, après écoute.

## Découpage

| Tâche | Contenu | Dépend de |
|---|---|---|
| DS-T1 | Téléchargement + normalisation + manifeste + dédoublonnage (D1-D3), `make trad-corpus` | — |
| DS-T2 | Rendu MIDI/WAV/MusicXML à armes égales (D4), `make trad-render` | T1 |
| DS-T3 | Extracteur de statistiques trad + profils par type (D5) ; mise à jour de `types.py` aux 5 pistes du moteur | T1 (format) — démarre sur fixtures |
| DS-T4 | `trad-compare` + `blindtest` (D6) | T2, T3 |
| DS-T5 | `mine-cells` + tables d'harmonie/tempo (D7) | T3 |

## Acceptation

1. `make trad-corpus` sur machine vierge : manifeste reproduit à
   l'identique (mêmes `sha256`), comptes par type affichés.
2. Un reel, une gigue, une valse rendus : WAV audibles avec violon, accords,
   basse et pieds ; AABB joué.
3. Profils `trad-reel`, `trad-jig`, `trad-waltz` construits ; sur le corpus
   reel, ≥ 80 % des airs détectés AABB à 8 mesures (sinon on documente
   pourquoi : airs « croches », parties de 16).
4. `trad-compare` sur les démos du moteur (`harmonium/demos/*.mid`) produit
   un rapport lisible par un non-musicien.
5. `blindtest` produit un kit jouable de 20 fichiers.
6. `mine-cells` produit un TOML que le parseur du moteur accepte
   (`CellBank` : vérifié en le chargeant via un test Rust ou une commande).
