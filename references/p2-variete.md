# P2 — alternatives extraites des transcriptions, et variété par graine

Phase 018, tâches **P2** (alternatives extraites du labo) et **métrique de variété** (plan 018,
« P1 / P2 — Preuve demandée »). Branche `wquintal/p2-variete-labo`, labo seulement : le dépôt moteur
n'est pas modifié. Mesures faites avec le moteur `harmonium` à `150b04f` (`main`, `TUNING_VERSION` 23, E1 et E3 fusionnés),
instantané `git archive` compilé dans `/tmp/p2/` pour ne pas dépendre de l'arbre de travail d'un autre agent.

Principe VII : audio, stems et transcriptions restent hors dépôt (`~/Project/bascanada/harmonium_lab/corpus/*/`).
Sont versionnés ici : le code, les propositions TOML (accords, motifs de basse, patterns : dérivés agrégés avec
provenance), et les mesures agrégées de ce compte rendu (`references/p2-variete/*.json`).

## Résumé

| Question | Réponse |
|---|---|
| Que mesure-t-on de la variété ? | Part des mesures et des parties dont accords, basse et batterie changent entre les graines 1–16, et nombre de signatures distinctes (`harmonium-lab seed-variety`). |
| Que vaut V1 ? | Les parties qui changent sur les **trois** couches : `nt_desert` 0 %, `isaac_basement` 67 %, `isaac_cellar` 62 %, `isaac_burning` 38 %, `isaac_downpour` 100 %. `nt_desert` n'a **aucune** variété d'accords ni de batterie. |
| Que sort de P2 ? | 4 boucles d'accords, 6 motifs de basse et 11 patterns de batterie proposés ; 2 boucles (pédales), 1 motif de basse et 2 patterns sont déjà au profil. Les transcriptions portent peu de matière (2 à 4 pistes par profil, 1 à 9 groupes par couche) : 26 groupes de basse sont écartés faute de soutien. **6 des 11 patterns n'ont pas de grosse caisse sur le premier temps** (dont un sans aucune grosse caisse, 7 caisses claires) : le classement kick / snare du transcripteur est peu fiable sur ces stems et les patterns en héritent. |
| La variété monte-t-elle ? | Peu en part de parties (déjà saturée à 100 % sur plusieurs couches), nettement en signatures distinctes par partie, et de 0 à 71 % des parties pour la batterie de `nt_desert`. |
| La distance au corpus tient-elle ? | Par couche : oui pour les accords et la basse partout (±1), oui pour la batterie de `isaac_burning`, `isaac_downpour` (symbolique) et `nt_desert` ; non pour la batterie de `isaac_basement` (Périculum −17,9). L'indicateur `boucles` (répétition à la longueur de boucle) baisse de 3 à 5 points dès qu'un pattern de batterie est ajouté. |
| Recommandation | Intégrer en partie : `isaac_burning` (accords + basse ; batterie à l'écoute), `isaac_downpour` (accords + basse ; batterie à l'écoute), `isaac_basement` (accords + basse, **sans** batterie), `nt_desert` (batterie, à l'écoute). Abandonner `isaac_cellar` (un pattern artefact). Écoute du propriétaire dans le studio encore à faire. |

## 1. Métrique de variété par graine

`src/harmonium_lab/seedvariety.py`, commande `harmonium-lab seed-variety` (cible `make seed-variety`).

- **Source.** `harmonium-cli --export --record-truth` : `measures[i]` donne, par mesure, les changements d'accord
  (`chord_changes`), les notes par piste (`track` 0 Melody, 1 Chords, 2 Bass, 3 PercussionLow, 4 PercussionHigh) et
  la position (air, tour, rang dans la séquence, partie, tonique). Le MIDI exporté ne sépare pas les deux
  batteries (canal 9 GM) ; la vérité terrain contient les mêmes attaques (recoupé : seed 1, 16 mesures de
  `isaac_basement`, 8 / 26 / 105 attaques de mélodie / basse / batterie dans la vérité terrain et dans le MIDI), d'où son emploi unique.
- **Signatures.** Accords : (pas, fondamentale, qualité, basse), relatifs à la tonique. Basse : (pas, hauteur relative à
  la tonique, durée). Batterie : (piste, pas, note). Vélocités et décalages d'interprétation sont ignorés (l'humanisation
  dérive de la graine même avec un motif identique).
- **Unités.** La mesure (même numéro dans les 16 graines) et la partie (occurrence de la forme : air, tour, rang ; sa signature
  est la suite des signatures de ses mesures). Premier air du set seulement : après la fin d'un air plus court que `--bars`
  (Downpour, 48 mesures), les mesures vides ne comptent pas.
- **Indicateurs** par couche : `share` (part des unités dont la signature change d'une graine à l'autre), `share_active`
  (même part sur les unités où la couche joue), `diversity` = (distinctes − 1) / (N − 1) (0 si les 16 graines sont
  identiques, 1 si toutes diffèrent ; plafonne à 1/15 avec deux alternatives), `distinct_mean` (signatures distinctes en
  moyenne), puis « au moins une couche » et « les trois couches ».
- **Tests** (`tests/test_seed_variety.py`) : 16 graines identiques → 0 ; toutes différentes → 1 ; couches indépendantes ;
  couche absente séparée de couche stable ; signatures relatives à la tonique et insensibles à l'humanisation ;
  mesure de clôture sans `chord_changes` et premier air seulement.

## 2. Mesure de référence V1

16 graines × 64 mesures, profils écrits à `150b04f`. `distinct/partie` = signatures distinctes par partie sur les 16 graines.

| Profil | Couche | Mesures qui varient | Parties qui varient | Distinctes / partie |
|---|---|---:|---:|---:|
| `nt_desert` | accords | 0 % | 0 % | 1,00 |
| | basse | 25 % | 29 % | 3,29 |
| | batterie | 0 % | 0 % | 1,00 |
| | une couche au moins / les trois | 25 / 0 % | 29 / 0 % | |
| `isaac_basement` | accords | 38 % | 75 % | 1,75 |
| | basse | 41 % | 100 % | 4,92 |
| | batterie | 70 % | 92 % | 1,92 |
| | une couche au moins / les trois | 97 / 0 % | 100 / 67 % | |
| `isaac_cellar` | accords | 19 % | 62 % | 1,62 |
| | basse | 100 % | 100 % | 8,50 |
| | batterie | 88 % | 100 % | 2,00 |
| | une couche au moins / les trois | 100 / 17 % | 100 / 62 % | |
| `isaac_burning` | accords | 23 % | 38 % | 1,38 |
| | basse | 100 % | 100 % | 11,62 |
| | batterie | 88 % | 100 % | 2,00 |
| | une couche au moins / les trois | 100 / 22 % | 100 / 38 % | |
| `isaac_downpour` | accords | 48 % | 100 % | 2,00 |
| | basse | 73 % | 100 % | 15,33 |
| | batterie | 88 % | 100 % | 2,00 |
| | une couche au moins / les trois | 98 / 42 % | 100 / 100 % | |

Lecture : à deux alternatives par couche (V1), la batterie plafonne à 2 signatures par partie ; les accords des
profils Isaac changent surtout dans les parties qui ont deux boucles (A2, D, Pont, C) ; `nt_desert` a un seul
candidat d'accords et de batterie partout (variété nulle) et une basse qui ne change que sur A2 (deux motifs de poids 3 et 1).
La part de parties qui varient sature vite (grande partie ⇒ une mesure suffit) : les signatures distinctes et la part
de mesures sont plus sensibles.

Données : `references/p2-variete/seed-variety-V1.json` (par partie nommée et par occurrence de partie en plus des totaux).

## 3. Extraction P2

`src/harmonium_lab/p2/` (`engine_profile.py`, `extract.py`, `emit.py`, `enrich.py`) ; commandes `harmonium-lab p2-extract`
(`make p2-extract`) et `harmonium-lab p2-enrich` (`make p2-enrich`).

### Méthode (comme le minage des cellules trad : observer, regrouper, pondérer par effectif)

1. **Observations par mesure**, dédupliquées par piste (la première boucle qui couvre une mesure l'emporte) : triade maj/min
   du transcripteur (qualité lissée sur une suite de mesures de même fondamentale : la qualité d'une pédale oscille
   entre maj et min), notes de basse, coups de batterie (kick, snare, hat) avec leur marge de classification.
2. **Fenêtres.** Accords : longueur d'une partie `chord_loop` du profil. Basse : `bars` d'un motif écrit. Alignées sur
   le début de chaque plage de mesures observées. Batterie : une mesure.
3. **Affectation à une partie** par similarité de la suite des fondamentales avec les références de la partie (ses boucles,
   sa pédale à qualité libre, ses motifs de basse à référence tonique), seuil 0,75 ; une mesure n'alimente qu'une partie
   (recouvrements résolus par similarité décroissante). Sinon : « non assignée ». Batterie : densité 0/1/2 dont les patterns écrits
   ont le nombre de coups moyen le plus proche (le schéma n'a pas de partie pour la batterie).
4. **Regroupement** par partie (batterie : global), clustering agglomératif à lien moyen, seuils : accords 0,85
   (4 mesures : identiques), basse et batterie 0,5 (Jaccard des attaques). Poids = effectif du groupe ; représentant = médoïde
   (une observation réelle). Soutien minimal : accords 1, basse 2, batterie 2 (groupes plus petits écartés, comptés dans `[stats]`).
5. **Traduction au schéma moteur actuel (E1/F1)** : accords en suites de `{ semitones, quality, bass?, steps }` (`bass` si une
   même classe tient la basse ≥ 70 % de la mesure sans être la fondamentale) ; motif de basse `{ part, bars, weight,
   reference, notes[{ step, duration, semitones, octave?, velocity, legato? }] }` relatif à la référence majoritaire de la
   partie (`tonic` ou `chord_root`), notes ≥ 2 pas (G7h), registre recalé sur celui des motifs écrits ; patterns par
   consensus (coup retenu s'il tombe dans au moins la moitié des mesures du groupe), `delta_velocity` à règle fixe
   (0 sur la pulsation, −16 ailleurs, −40 charleston : la transcription ne porte pas de vélocité).
6. **Statut** de chaque groupe : `nouveau` (ajouté au TOML), `présent` (équivalent à une alternative écrite : accords égaux,
   Jaccard ≥ 0,8 pour basse et batterie), `écart` (partie pédale, inexprimable), `non-assigné`.

### Sorties

`references/isaac-basement/proposals/isaac_basement.toml`, `references/isaac-cellar/proposals/isaac_cellar.toml`,
`references/isaac-burning/proposals/isaac_burning.toml`, `references/isaac-downpour/proposals/isaac_downpour.toml`,
`references/nt-desert/proposals/nt_desert.toml`. Un fichier = les **ajouts** dans le schéma moteur + `[[provenance]]`
(piste, mesures, minutage `m:ss` dans la piste, confiance, soutien, statut), `[[gaps]]` et `[stats]`.
`p2-enrich` écarte ces trois métadonnées, fusionne les ajouts au profil et **rééquilibre** les poids (par partie ou par densité,
le poids total des ajouts est ramené au poids total des alternatives écrites ; `--raw-weights` garde les effectifs).

| Profil | Pistes transcrites | Boucles nouv. / présentes / non assign. | Motifs de basse nouv. / présents / non assign. / écartés | Patterns nouv. / présents / écartés |
|---|---|---:|---:|---:|
| `isaac_basement` | 02, 21 | 2 / 1 / 3 | 1 / 0 / 9 / 6 | 4 / 1 / 1 |
| `isaac_cellar` | 21 | 0 / 1 / 1 | 0 / 0 / 5 / 3 | 1 / 1 / 0 |
| `isaac_burning` | 36 | 1 / 0 / 0 (+1 écart) | 3 / 0 / 3 / 6 | 2 / 0 / 0 |
| `isaac_downpour` | 47 | 1 / 0 / 2 | 2 / 1 / 2 / 8 | 2 / 0 / 5 |
| `nt_desert` | 02, 19 | 0 / 0 / 3 | 0 / 0 / 0 / 3 | 2 / 0 / 1 |

Les cinq profils enrichis passent le chargeur du moteur (`harmonium-cli --export` code 0, graines 2 et 3).

### Manques moteur (alternatives qui ne s'expriment pas)

1. **Parties `pedal` sans alternatives.** Seul `kind = "chord_loop"` porte `loops`. Une fenêtre d'accords proche d'une
   pédale mais différente (`isaac_burning` partie R, mesures 56–63 de *Fundamentum*, 1:37) n'a aucune place.
   Contournement possible côté données : une boucle à un seul accord
   sur toute la partie, qui perd le sens `pedal` (voisine, relance). Non fait.
2. **Aucune portée par partie ou par tour pour la batterie.** Les patterns se rangent par densité ; le tirage est stable par
   partie et densité, mais la banque est commune. Les transcriptions donnent des grooves de sections différentes
   (pédale d'intro, descente) qui ne peuvent pas être liés à leur section. Cause probable du résultat négatif de la
   batterie de `isaac_basement` (patterns de *Diptera Sonata* tirés aussi pendant ce que *Périculum* joue).
3. **Remplissages non pondérés.** `cadence_patterns` est unique par densité (V1) : aucune alternative de fill, et le
   transcripteur ne distingue que kick / snare / hat (pas de toms ni de crash).
4. **Forme fixe par graine.** Les fenêtres « non assignées » (par exemple *Fläshyn* B : 11 11 5m 0 4 4 8 5m face à
   l'alternance G/G# écrite) signalent des sections que le profil écrit autrement ; la séquence et la longueur des parties
   ne varient pas avec la graine, une section transcrite ne peut donc pas s'ajouter comme alternative de forme.

Limites de la donnée, pas du schéma : le transcripteur ne produit que des triades maj/min (aucune septième), classe mal
kick et snare (patterns sans grosse caisse au premier temps : `isaac_basement` ×2, `isaac_cellar` — sept caisses claires, aucune grosse caisse —,
`isaac_burning` densité 0, `isaac_downpour` densité 2, `nt_desert` densité 0, soit 6 sur 11), et la basse porte
quelques sauts d'octave ; la transcription a 2 à 16 mesures par boucle et peu de répétitions (groupes de 1 à 6).
Corriger le classement à la source (`audioref.transcribe.drum_hits`) vaudrait mieux qu'un filtre « il faut une grosse caisse » dans l'extraction, qui serait un a priori de style.

## 4. Preuve

### 4.1 Variété par graine : V1 → P2

Profils enrichis dans `/tmp/p2/p2profiles/<profil>_p2` ; 16 graines × 64 mesures. Données : `references/p2-variete/seed-variety-P2.json`.

| Profil | Couche | Mesures qui varient | Parties qui varient | Distinctes / partie |
|---|---|---:|---:|---:|
| `nt_desert` | accords | 0 → 0 % | 0 → 0 % | 1,00 → 1,00 |
| | basse | 25 → 25 % | 29 → 29 % | 3,29 → 3,57 |
| | batterie | 0 → **55 %** | 0 → **71 %** | 1,00 → 1,71 |
| `isaac_basement` | accords | 38 → 44 % | 75 → 75 % | 1,75 → 2,08 |
| | basse | 41 → **59 %** | 100 → 100 % | 4,92 → 6,25 |
| | batterie | 70 → 70 % | 92 → 92 % | 1,92 → **4,67** |
| `isaac_cellar` | accords | 19 → 19 % | 62 → 62 % | 1,62 → 1,62 |
| | basse | 100 → 100 % | 100 → 100 % | 8,50 → 8,50 |
| | batterie | 88 → 88 % | 100 → 100 % | 2,00 → 3,00 |
| `isaac_burning` | accords | 23 → 23 % | 38 → 38 % | 1,38 → 1,62 |
| | basse | 100 → 100 % | 100 → 100 % | 11,62 → 14,62 |
| | batterie | 88 → 88 % | 100 → 100 % | 2,00 → 3,00 |
| `isaac_downpour` | accords | 48 → 52 % | 100 → 100 % | 2,00 → 2,33 |
| | basse | 73 → 79 % | 100 → 100 % | 15,33 → 15,00 |
| | batterie | 88 → 88 % | 100 → 100 % | 2,00 → 3,00 |

Les trois couches ensemble, parties qui varient : `nt_desert` 0 → 0 %, `isaac_basement` 67 → 67 %, `isaac_cellar` 62 → 62 %,
`isaac_burning` 38 → 38 %, `isaac_downpour` 100 → 100 %. Parce que les propositions sont peu nombreuses et que
la part de parties est saturée, **le critère du plan (part de parties dont les trois couches changent) ne bouge pas** ;
le gain est dans la profondeur (signatures distinctes par partie : batterie 2 → 3 sur `isaac_cellar`, `isaac_burning` et `isaac_downpour`, 1,92 → 4,67 sur `isaac_basement`)
et, pour `nt_desert`, dans l'apparition de variété de batterie.

### 4.2 Distance au corpus (`make style-distance`), V1 → P2

Mêmes paramètres que les mesures M1 : graines 1–10, 48 mesures, contexte `type=zone`, banque GeneralUser (`isaac_*`,
`nt_desert` aussi avec `nt_desert.sf2`), mêmes pistes de référence que `distance-<profil>.json`. Le profil écrit est **re-mesuré**
ici au même moteur (`150b04f`) : ses scores diffèrent un peu des `distance-*.json` publiés (moteurs plus anciens ; par exemple
`isaac_cellar` audio 54,5 et symbolique 66,3 sont retrouvés à l'identique). Score 0–100, moyenne des pistes de référence.

| Profil | Mesure | V1 | P2 | Δ |
|---|---|---:|---:|---:|
| `isaac_basement` | audio | 40,4 | 40,1 | −0,3 |
| | symbolique | 65,9 | 64,5 | −1,4 |
| | · basse / batterie / accords / boucles | 69,2 / 70,3 / 71,1 / 53,2 | 69,0 / 68,2 / 71,2 / 49,9 | −0,2 / **−2,2** / +0,1 / −3,3 |
| `isaac_cellar` | audio | 54,5 | 57,0 | **+2,5** |
| | symbolique | 66,3 | 65,2 | −1,1 |
| | · basse / batterie / accords / boucles | 78,2 / 83,5 / 67,8 / 35,9 | 78,2 / 84,1 / 67,8 / 30,6 | 0 / +0,6 / 0 / −5,3 |
| `isaac_burning` | audio | 39,6 | 38,5 | −1,1 |
| | symbolique | 60,6 | 61,7 | +1,1 |
| | · basse / batterie / accords / boucles | 59,1 / 76,7 / 61,2 / 45,3 | 64,5 / 79,9 / 61,4 / 41,1 | **+5,4** / +3,2 / +0,2 / −4,2 |
| `isaac_downpour` | audio | 61,4 | 59,3 | −2,1 |
| | symbolique | 58,8 | 61,8 | +3,0 |
| | · basse / batterie / accords / boucles | 77,7 / 44,6 / 86,7 / 26,2 | 79,2 / 58,1 / 86,5 / 23,4 | +1,5 / **+13,5** / −0,2 / −2,8 |
| `nt_desert` | audio `nt_desert.sf2` / GeneralUser | 57,5 / 58,0 | 57,2 / 57,7 | −0,3 / −0,2 |
| | symbolique | 48,4 | 47,6 | −0,8 |
| | · basse / batterie / accords / boucles | 43,1 / 30,4 / 77,0 / 43,0 | 43,2 / 31,2 / 77,0 / 38,8 | +0,1 / +0,8 / 0 / −4,2 |

Bruit d'échantillonnage : doubler les graines (10 → 20) sur `isaac_cellar` et `isaac_downpour`, profil écrit et profil
enrichi, déplace les scores de 0,0 à 0,6 point. Tolérance retenue pour « pas pire » : **1 point**. Détails par groupe et par piste :
`references/p2-variete/distance.json`.

Lectures :

- Les groupes symboliques isolent les couches. **Accords** : ±0,2 partout (une seule boucle ajoutée par profil).
  **Basse** : +5,4 sur `isaac_burning`, +1,5 sur `isaac_downpour`, neutre ailleurs. **Batterie** : +13,5 sur `isaac_downpour`, +3,2 sur
  `isaac_burning`, +0,6 / +0,8 sur `isaac_cellar` / `nt_desert`, −2,2 sur `isaac_basement` (+13,5 contre *Diptera Sonata*, −17,9 contre *Périculum*).
- **Biais d'optimisme.** Les propositions viennent des mêmes transcriptions que la référence symbolique : une hausse symbolique
  (batterie de `isaac_downpour`, basse de `isaac_burning`) est en partie circulaire. Les baisses, elles, ne le sont pas.
- **`boucles` baisse partout où des patterns de batterie sont ajoutés** (−2,8 à −5,3), et seulement là : sur `isaac_basement` sans les patterns
  (voir 4.3) l'indicateur est neutre. Cet indicateur mesure la répétition à la longueur de boucle de la référence ; ajouter des alternatives de batterie en
  réduit la valeur par construction. À ne pas lire comme une dégradation musicale.
- Audio : seul `isaac_downpour` sort de la tolérance (−2,1 : taux d'attaques 59,7 → 44,3 contre *River of Despair* — les patterns extraits sont plus denses que le « clairsemé » écrit)
  et `isaac_burning` est à sa limite (−1,1 : dynamique −1,9, percussif −2,9). `isaac_cellar` gagne 2,5 (brillance 19,4 → 31,4) avec un pattern de sept caisses claires et aucune grosse caisse : le gain vient d'un son plus brillant, pas d'un rythme plus fidèle, et ne compte pas comme preuve.

### 4.3 Ablation : `isaac_basement` sans les patterns de batterie

Même proposition amputée de ses 4 patterns (`/tmp/p2/p2profiles/isaac_basement_p2nd`) :

| Mesure | V1 | P2 complet | P2 sans batterie |
|---|---:|---:|---:|
| symbolique *Diptera Sonata* / *Périculum* | 64,6 / 67,3 | 67,2 / 61,9 | 64,8 / 67,2 |
| audio *Diptera Sonata* / *Périculum* | 42,2 / 38,6 | 41,7 / 38,5 | 41,7 / 38,4 |
| batterie symbolique (*D.S.* / *P.*) | 56,8 / 83,9 | 70,3 / 66,0 | 56,8 / 83,9 |
| accords et basse : mesures qui varient | 38 % / 41 % | 44 % / 59 % | 44 % / 59 % |

Sans la batterie, la distance revient à V1 (symbolique 66,0 contre 65,9, `boucles` neutre) pendant que la variété d'accords (38 → 44 % des mesures)
et de basse (41 → 59 %) est conservée.

### 4.4 Rendus d'écoute

Rendus 64 mesures dans `/tmp/p2/listen/`, banque `GeneralUser-GS.sf2` (`nt_desert` : `nt_desert.sf2`), tous sous 0 dBFS (crête −1,5 à −12,4 dB).
Pour chaque profil : le profil écrit (`_v1_`) et le profil enrichi (`_p2_`), **même graine**. Les minutages sont ceux du rendu P2 :
mesures dont la signature de la couche n'apparaît dans aucune des 16 graines V1 à la même mesure, c'est-à-dire là où une alternative extraite
est jouée (`/tmp/p2/novel.json`).

Commande type (profil écrit : `--profile /tmp/p2/engine/profiles/<profil>`) :

```sh
/tmp/p2/target/release/harmonium-cli --export --bars 64 --profile /tmp/p2/p2profiles/<profil>_p2 --seed <g> \
  --soundfont ~/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2 \
  --percussion-soundfont ~/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2 \
  --record-wav /tmp/p2/listen/<profil>_p2_s<g>.wav
afplay /tmp/p2/listen/<profil>_p2_s<g>.wav        # puis le même fichier _v1_
```

| Profil, graine | Couche | À écouter (m:ss), alternative extraite jouée |
|---|---|---|
| `nt_desert`, 1 | batterie | 0:13–0:25, 0:54–1:06, 1:08–1:20 |
| `isaac_basement`, 10 | accords | 0:13–0:18, 0:27–0:32, 1:22–1:27 |
| | basse | 0:00–0:10, 0:54–1:05, 1:08–1:18 |
| | batterie (à comparer, jugée mauvaise) | 0:00–0:12, 0:54–1:06 |
| `isaac_cellar`, 1 | batterie | 0:00–0:12, 0:13–0:25, 0:27–0:39 |
| `isaac_burning`, 16 | accords | 0:15–0:18, 1:24–1:27 |
| | basse | 0:00–0:03, 0:20–0:25, 1:29–1:34 |
| | batterie | 0:00–0:12, 0:13–0:25, 0:27–0:39 |
| `isaac_downpour`, 1 | accords | 0:53–0:56, 1:06–1:13 |
| | basse | 0:03–0:26, 1:06–1:10 |
| | batterie (taux d'attaques à juger) | 0:00–0:11, 0:13–0:25, 0:26–0:38 |

Aucune écoute humaine revendiquée : l'écoute du propriétaire dans le studio (« New seed ») reste la validation exigée par le plan.

## 5. Recommandations, profil par profil

Règle : une couche est intégrée si sa variété monte (signatures distinctes par partie) et si ni sa distance symbolique de couche ni la distance audio
globale ne perdent plus de 1 point. Toute intégration reste soumise à l'écoute du propriétaire.

| Profil | Accords | Basse | Batterie | Décision |
|---|---|---|---|---|
| `isaac_basement` | 2 boucles A2 (poids 1) : variété 1,75 → 2,08, distance +0,1 | 1 motif A1 : variété 4,92 → 6,25, −0,2 | 4 patterns : **abandonner** (*Périculum* −17,9 ; 2 sans grosse caisse au premier temps ; manque 2 ci-dessus) | **Intégrer accords + basse, abandonner la batterie.** Ablation 4.3. |
| `isaac_cellar` | rien de nouveau (pédale A déjà là) | 3 groupes écartés (soutien 1) | 1 pattern : sept caisses claires, **aucune grosse caisse** (artefact) ; audio +2,5 par brillance seulement, `boucles` −5,3 | **Abandonner.** Rien d'exploitable. |
| `isaac_burning` | 1 boucle C : +0,2 ; 1 écart (pédale R, manque 1) | 3 motifs : variété 11,6 → 14,6, **+5,4** | 2 patterns : +3,2 ; la densité 1 (kick 0, 2, 6) est plausible, la densité 0 (`0S 4H 8S 12H`) n'a pas de grosse caisse | **Intégrer accords + basse ; batterie : garder la densité 1, écouter la densité 0.** Audio −1,1 à la limite (percussif −2,9). |
| `isaac_downpour` | 1 boucle C : −0,2 | 2 motifs : +1,5 | 2 patterns : **+13,5** symbolique mais audio −2,1 (attaques 59,7 → 44,3 : plus denses que l'écrit) ; la densité 1 (`0K 4H 8S 12H`) est plausible, la densité 2 (`0H 2S 4K 8S 10K 14S`) non | **Intégrer accords + basse ; batterie à trancher à l'écoute** (sinon abandonner : le gain symbolique est en partie circulaire). |
| `nt_desert` | rien (3 fenêtres non assignées) | rien (3 groupes écartés) | 2 patterns : variété 0 → 71 % des parties, +0,8, audio −0,2 / −0,3 ; la densité 1 (`0K 2S 8K 10S 14S 20K 22S`) est le groove écrit sans charleston, la densité 0 (`0S 2S 10S 14S 20K`) est suspecte | **Intégrer la batterie après écoute** (garder la densité 1). Seule source de variété de batterie pour ce profil ; coût de distance faible. |

Règle simple si l'orchestrateur n'en veut qu'une : intégrer accords + basse de `isaac_basement`, `isaac_burning` et `isaac_downpour` ; ne pas intégrer de batterie
extraite avant écoute (`isaac_burning` densité 1, `isaac_downpour` densité 1 et `nt_desert` densité 1 sont les seuls patterns plausibles) ; abandonner la batterie de
`isaac_basement` et tout `isaac_cellar`.

Pour aller plus loin que P2, deux goulots : la donnée (peu de répétitions dans 2 à 4 pistes) et le classement kick / snare du transcripteur
(`audioref.transcribe.drum_hits`), puis les manques moteur 1, 2 et 4 de la section 3.
Une batterie liée à la partie (manque 2) aurait gardé l'apport de *Diptera Sonata* sans le coût sur *Périculum*.

## 6. Reproduction

Variables : `ENGINE=~/Project/bascanada/harmonium` (ici : instantané `git archive HEAD` dans `/tmp/p2/engine`, compilé avec `CARGO_TARGET_DIR=/tmp/p2/target` ;
`ENGINE_BIN=/tmp/p2/target/release/harmonium-cli`) ; `ASSETS=~/Project/bascanada/harmonium/assets` ; `CORPUS=~/Project/bascanada/harmonium_lab/corpus`.

```sh
make setup
# 1. variété V1 (profils écrits)
make seed-variety ENGINE_DIR=$ENGINE ENGINE_BIN=$ENGINE_BIN LABEL=V1 VARIETY_DIR=/tmp/p2/variety
# 2. propositions → references/<profil>/proposals/
make p2-extract ENGINE_DIR=$ENGINE CORPUS_ROOT=$CORPUS
# 3. copies enrichies hors dépôt
for p in isaac_basement isaac_cellar isaac_burning isaac_downpour nt_desert; do
  make p2-enrich ENGINE_DIR=$ENGINE PROFILE=$p PROPOSAL=references/$(echo $p | tr _ -)/proposals/$p.toml OUT=/tmp/p2/p2profiles/${p}_p2
done
# 4. variété P2
make seed-variety ENGINE_DIR=$ENGINE ENGINE_BIN=$ENGINE_BIN LABEL=P2 VARIETY_DIR=/tmp/p2/variety \
  VARIETY_PROFILES="$(for p in nt_desert isaac_basement isaac_cellar isaac_burning isaac_downpour; do printf '/tmp/p2/p2profiles/%s_p2 ' $p; done)"
# 5. distance : écrit (PROFILE=id) puis enrichi (PROFILE=dossier), DIST_OUT hors dépôt, banques et pistes comme M1
make style-distance ENGINE_DIR=$ENGINE PROFILE=isaac_cellar REF=isaac-basement TRACKS=21_periculum STYLE_CORPUS=$CORPUS/isaac \
  CONTEXT="type=zone" BANKS="generaluser=$ASSETS/GeneralUser-GS.sf2" STYLE_DIST_DIR=/tmp/p2/style DIST_OUT=/tmp/p2/dist/v1_isaac_cellar.json
make style-distance ENGINE_DIR=$ENGINE PROFILE=/tmp/p2/p2profiles/isaac_cellar_p2 REF=isaac-basement TRACKS=21_periculum STYLE_CORPUS=$CORPUS/isaac \
  CONTEXT="type=zone" BANKS="generaluser=$ASSETS/GeneralUser-GS.sf2" STYLE_DIST_DIR=/tmp/p2/style DIST_OUT=/tmp/p2/dist/p2_isaac_cellar.json
make test
```

Pistes par profil (`TRACKS`, `REF`) : `isaac_basement` 02_diptera_sonata,21_periculum ; `isaac_cellar` 21_periculum ; `isaac_burning` 36_fundamentum ;
`isaac_downpour` 47_river_of_despair (`REF=isaac-basement` pour les quatre) ; `nt_desert` 02_flashyn,19_a_way (`REF=nt-desert`,
`STYLE_CORPUS=$CORPUS/nuclear_throne`, `BANKS="nt_desert=$ASSETS/nt_desert.sf2 generaluser=$ASSETS/GeneralUser-GS.sf2"`).
Le premier `style-distance` d'un corpus calcule les mesures audio du contexte (≈ 7 à 15 min, ensuite en cache dans `STYLE_DIST_DIR/cache`).
`style-distance` accepte désormais `DIST_OUT=` (fichier de sortie hors `references/`, pour ne pas écraser les `distance-<profil>.json` publiés).

Tests : `make test` (305 réussis dont 18 nouveaux, 31 ignorés ; `tests/test_seed_variety.py` et `tests/test_p2_extract.py`, fixture de transcriptions générée dans le test).

## 7. Limites

- Matière réduite : 4 pistes Isaac et 2 pistes NT transcrites, 2 à 16 mesures par boucle ; peu de groupes dépassent 3 observations. Les propositions sont donc des **alternatives de transcription**, pas des statistiques de corpus.
- Bruit de transcription (triades seules, kick/snare confondus, sauts d'octave de basse) : confiance par alternative en provenance ; elle ne corrige rien.
- Poids de la proposition = effectifs ; la preuve emploie les poids **rééquilibrés** (alternatives extraites = poids total des écrites). Un autre équilibre donne d'autres variétés.
- Distance symbolique circulaire (même source que la référence) ; distance audio non circulaire. Bruit des graines ≤ 0,6 point mesuré sur deux profils seulement.
- Variété mesurée sur le premier air, 64 mesures ; mémoire de set et airs suivants non couverts.
- Pas d'écoute humaine ; pas de Odin ni de mix : seuls les rendus GeneralUser / `nt_desert.sf2` sont faits.
