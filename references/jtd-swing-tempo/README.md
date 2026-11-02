# `jtd-swing-tempo` — swing et micro-timing selon le tempo (phase 019, L2 → A6)

Mesures agrégées du **rapport de swing** de la batterie, de la basse et du piano, et de leur **placement
relatif**, en fonction du tempo : classes de tempo, **courbe continue `swing_ratio(tempo)`** et table à
reprendre par la tâche A6 du moteur (« swing selon le tempo »). Prolonge E7 (`references/wjazzd-swing/`,
`measures-timing.json`, tranches de 25 BPM) sans le modifier. **Aucune phrase de solo, aucune suite de notes** :
seulement des comptes, des médianes, des centiles et des intervalles de confiance (principe VII).

## Provenance, licence, mention requise

| | |
|---|---|
| Source | Jazz Trio Database (JTD) v0.2, `jazz-trio-database-v02.zip` (release GitHub `v02-zenodo`, 2024-05-21) |
| Empreintes vérifiées avant toute lecture | SHA256 `42c3df0700e0cd6e73231b9ed111283600750305e2e9cf451f80664d1ec90025`, MD5 `43f543fb286c6222ae1f52bcf7561f37` (`timing.open_archive` refuse l'archive sinon) |
| Licence | MIT (annotations) — <https://github.com/HuwCheston/Jazz-Trio-Database> |
| Lu | `metadata.json`, `beats.csv`, `bass/drums/piano_onsets.csv` directement dans le ZIP ; **jamais** `piano_midi.mid` ni l'audio |

> Jazz Trio Database v0.2, MIT License : H. Cheston, J. L. Schlichting, I. Cross, P. M. C. Harrison,
> « Jazz Trio Database: Automated Annotation of Jazz Piano Trio Recordings Processed Using Audio Source
> Separation », *Transactions of the International Society for Music Information Retrieval* (TISMIR), 2024,
> DOI [10.5334/tismir.186](https://doi.org/10.5334/tismir.186).

Chaque piste est un **enregistrement sous droits** : seules ses annotations temporelles sont lues, le brut reste
en cache gitignoré (`corpus/jtd/raw/`).

## Reproduction

```sh
.venv/bin/python -m harmonium_lab.backing.swing_tempo --measures        # → references/jtd-swing-tempo/measures-swing-tempo.json
.venv/bin/python -m harmonium_lab.backing.swing_tempo --summary         # résumé lisible du JSON
.venv/bin/python -m harmonium_lab.backing.swing_tempo --measures --out-dir /chemin/autre   # sortie ailleurs
.venv/bin/python -m pytest tests/test_backing_swing_tempo.py tests/test_backing_timing.py
```

Prérequis : l'archive en cache (`make backing-fetch`). Deux exécutions donnent un fichier **identique octet pour octet**
(clés triées, arrondis à 4 décimales, aucun horodatage, graine de bootstrap fixe `20260211`, ≥ 1000 rééchantillons :
2000 pour les médianes de classe, 1000 pour la courbe et le micro-timing ; ≈ 25 s). `references/wjazzd-swing/`
n'est pas modifié (E7 régénéré : identique).

Le JSON : `command`, `provenance` (SHA256, MD5, licence, attribution, comptes), `parameters`, `classes`, `curve`,
`micro_timing`, `limits`, `reliability`, `a6_table` (la table prête à reprendre).

## Effectifs

Filtre = celui d'E7 (`timing.keep_track` : 4 temps par mesure, 60–330 BPM ; ≥ 60 % des temps avec basse **et** batterie
appariées) **sans** les tranches de 100 à 330 BPM, qui auraient écarté les pistes lentes :

| Étape | Pistes |
|---|---|
| Archive | 1 294 |
| 4 temps par mesure | 1 204 |
| Tempo de 60 à 330 BPM | 1 204 |
| Basse et batterie appariées ≥ 60 % (écartées : 228) | **976** (392 327 temps) |

**Fait important : l'archive entière ne contient aucun tempo hors de 102,06–299,31 BPM.** Rien entre 60 et 100 BPM, rien
au-dessus de 300 BPM : la classe « < 120 » est en réalité **100–120 BPM** (médiane 115 BPM) et « ≥ 240 » est
**240–300 BPM**. La plage 60–330 BPM du filtre est conservée par prudence mais n'a pas d'effet. Aucune valeur n'est
donnée hors de la plage observée.

### Classes de tempo

| Classe | Plage observée (médiane) | Pistes | Mesurées batterie / basse / piano | Batteurs / bassistes / pianistes distincts (pistes mesurées) |
|---|---|---|---|---|
| < 120 BPM | 102–120 (115) | 55 | 55 / 50 / 55 | 31 / 25 / 20 |
| 120–180 | 120–180 (149) | 370 | 369 / 313 / 370 | 75 / 65 / 32 |
| 180–240 | 180–240 (205) | 379 | 379 / 312 / 379 | 73 / 59 / 30 |
| ≥ 240 | 240–299 (263) | 172 | 171 / 124 / 172 | 57 / 48 / 27 |
| toutes | 102–299 (188) | 976 | 974 / 799 / 976 | 99 / 84 / 34 |

Les quatre classes demandées gardent **≥ 30 pistes mesurées chacune** (la plus petite : 55). Un découpage plus fin sous
120 BPM serait impossible : 60–110 BPM ne compte que 13 pistes (13 batteurs différents). Les bornes 120 / 180 / 240 sont donc conservées telles quelles.

Une piste est « mesurée » pour un instrument si elle a **au moins 20 attaques de contretemps**
(`MIN_SWING_OBSERVATIONS`) ; la basse, qui marche en noires, l'est moins souvent (799 pistes sur 976).

## Swing par classe et par instrument

Rapport de swing = fraction de l'intervalle entre deux temps où tombe la croche de contretemps, attaques entre 0,45 et
0,85 de l'intervalle (`timing.swing_observations`) : 0,5 = croches droites, 0,667 = triolet (long/court = 2:1),
long/court = r / (1 − r). Statistique : **médiane par piste**, puis médiane (valeur centrale), centiles et moyenne **sur les
pistes**. IC95 % = centiles 2,5 / 97,5 de la médiane sur 2 000 rééchantillons de **musiciens entiers** (« mus. » : un
batteur pèse sur plusieurs pistes) et, pour comparaison, de pistes (« pistes »). Dispersion entre pistes : écart
interquartile / écart-type / écart-type robuste (1,4826 × MAD).

### Batterie (valeur à reprendre pour A6)

| Classe | Pistes mesurées | Batteurs | Attaques | **Médiane** | IC95 % mus. | IC95 % pistes | p10 / p25 / p75 / p90 | Moyenne | Long/court | IQR / σ / MAD robuste | Largeur IC mus. ÷ pistes | Fiabilité |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| < 120 | 55 | 31 | 8 583 | **0,720** | 0,712 – 0,732 | 0,712 – 0,727 | 0,695 / 0,705 / 0,738 / 0,750 | 0,722 | 2,57 | 0,034 / 0,024 / 0,024 | 1,30 | juste |
| 120–180 | 369 | 75 | 71 753 | **0,708** | 0,703 – 0,714 | 0,706 – 0,714 | 0,667 / 0,691 / 0,726 / 0,738 | 0,702 | 2,43 | 0,035 / 0,042 / 0,026 | 1,38 | assez |
| 180–240 | 379 | 73 | 103 343 | **0,656** | 0,655 – 0,667 | 0,655 – 0,667 | 0,615 / 0,640 / 0,679 / 0,700 | 0,659 | 1,91 | 0,039 / 0,034 / 0,033 | 1,00 | assez |
| ≥ 240 | 171 | 57 | 48 323 | **0,591** | 0,583 – 0,609 | 0,583 – 0,600 | 0,550 / 0,571 / 0,619 / 0,652 | 0,597 | 1,44 | 0,048 / 0,037 / 0,036 | 1,52 | assez |
| toutes (mélange de tempos) | 974 | 99 | 232 002 | 0,677 | 0,667 – 0,686 | 0,676 – 0,679 | 0,587 / 0,633 / 0,709 / 0,729 | 0,668 | 2,10 | 0,075 / 0,054 / 0,051 | 6,58 | assez |

### Basse (indicatif : peu de contretemps par piste)

| Classe | Pistes mesurées | Bassistes | Attaques | Médiane | IC95 % mus. | IC95 % pistes | p10 / p25 / p75 / p90 | Moyenne | Long/court | IQR / σ / MAD robuste | Largeur IC mus. ÷ pistes | Fiabilité |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| < 120 | 50 | 25 | 3 869 | 0,713 | 0,699 – 0,727 | 0,701 – 0,723 | 0,679 / 0,693 / 0,729 / 0,750 | 0,713 | 2,48 | 0,036 / 0,026 / 0,026 | 1,26 | juste |
| 120–180 | 313 | 65 | 29 174 | 0,708 | 0,701 – 0,721 | 0,705 – 0,714 | 0,667 / 0,688 / 0,727 / 0,746 | 0,702 | 2,43 | 0,040 / 0,049 / 0,028 | 2,04 | assez |
| 180–240 | 312 | 59 | 28 275 | 0,679 | 0,673 – 0,688 | 0,677 – 0,680 | 0,630 / 0,655 / 0,705 / 0,720 | 0,677 | 2,11 | 0,050 / 0,040 / 0,037 | 5,77 | assez |
| ≥ 240 | 124 | 48 | 9 214 | 0,654 | 0,650 – 0,680 | 0,651 – 0,670 | 0,609 / 0,630 / 0,696 / 0,747 | 0,668 | 1,89 | 0,066 / 0,053 / 0,044 | 1,62 | assez |
| toutes | 799 | 84 | 70 532 | 0,692 | 0,688 – 0,700 | 0,690 – 0,697 | 0,630 / 0,667 / 0,719 / 0,738 | 0,688 | 2,25 | 0,052 / 0,047 / 0,038 | 1,78 | assez |

### Piano (comping et solo mêlés : indicatif)

| Classe | Pistes mesurées | Pianistes | Attaques | Médiane | IC95 % mus. | IC95 % pistes | p10 / p25 / p75 / p90 | Moyenne | Long/court | IQR / σ / MAD robuste | Largeur IC mus. ÷ pistes | Fiabilité |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| < 120 | 55 | 20 | 12 777 | 0,695 | 0,686 – 0,701 | 0,686 – 0,700 | 0,667 / 0,678 / 0,709 / 0,724 | 0,694 | 2,28 | 0,031 / 0,022 / 0,023 | 1,06 | juste |
| 120–180 | 370 | 32 | 99 778 | 0,698 | 0,691 – 0,706 | 0,694 – 0,700 | 0,657 / 0,676 / 0,718 / 0,735 | 0,696 | 2,31 | 0,042 / 0,033 / 0,031 | 2,77 | assez |
| 180–240 | 379 | 30 | 129 041 | 0,667 | 0,654 – 0,679 | 0,656 – 0,667 | 0,612 / 0,633 / 0,690 / 0,719 | 0,663 | 2,00 | 0,056 / 0,040 / 0,042 | 2,37 | assez |
| ≥ 240 | 172 | 27 | 60 708 | 0,619 | 0,604 – 0,636 | 0,609 – 0,625 | 0,571 / 0,598 / 0,639 / 0,667 | 0,619 | 1,62 | 0,041 / 0,033 / 0,030 | 1,96 | assez |
| toutes | 976 | 34 | 302 304 | 0,676 | 0,667 – 0,685 | 0,667 – 0,678 | 0,607 / 0,636 / 0,702 / 0,725 | 0,669 | 2,09 | 0,066 / 0,045 / 0,048 | 1,58 | assez |

### Dépendance entre pistes d'un même musicien (chiffrée)

Les IC « par piste » sont trop étroits : les pistes d'un même musicien se ressemblent. La largeur de l'IC par musicien
sur celle de l'IC par piste vaut **1,0 à 1,5** pour la batterie des quatre classes (batteurs nombreux et bien répartis : le
plus présent porte 8 à 15 % des pistes), mais **de 1,3 à 5,77 pour la basse, avec 5,77 à 180–240 BPM** (classe la plus touchée :
312 pistes mesurées équivalent à ≈ 9 pistes indépendantes pour la largeur de l'IC ; médiane posée sur un pic de valeurs
presque identiques, ce qui rend l'IC par piste artificiellement étroit) et 1,1 à 2,8 pour le piano (20 à 32
pianistes). Mélanger les tempos gonfle le rapport (6,58 pour la batterie « toutes classes » : l'écart entre
musiciens se confond avec l'effet du tempo). **Les IC à reprendre sont ceux « par musicien ».**

### Écart au `default_swing_ratio` du profil E7 (0,71)

| Classe | Médiane batterie | Écart à 0,71 | 0,71 dans l'IC95 % mus. ? |
|---|---|---|---|
| < 120 | 0,720 | +0,010 | non (IC 0,712 – 0,732) |
| 120–180 | 0,708 | −0,002 | oui |
| 180–240 | 0,656 | **−0,054** | non |
| ≥ 240 | 0,591 | **−0,119** | non |

0,71 convient jusqu'à ≈ 180 BPM ; au-delà, un swing de 0,71 est **trop ternaire** pour ce que font les batteurs (à 240–300
BPM ils jouent des croches presque égales : long/court 1,4:1 contre 2,45:1 à 0,71).

## Courbe continue `swing_ratio(tempo)`

Régression **robuste** (M-estimateur de Huber, échelle fixée par la MAD) des médianes de swing **par piste** sur le tempo ;
quatre formes comparées par **validation croisée par blocs de musiciens** (10 blocs : un musicien n'est jamais à la fois dans
l'ajustement et dans le test) ; IC95 % de la courbe par bootstrap de 1 000 rééchantillons de pistes puis de musiciens
(la charnière est cherchée à chaque rééchantillon : l'IC l'inclut).

| Modèle | Écart robuste hors échantillon (batterie) | Gain sur la constante |
|---|---|---|
| constante | 0,0562 | 0 % |
| linéaire en tempo | 0,0286 | 49,1 % |
| linéaire en ln(tempo) | 0,0309 | 45,0 % |
| **plateau puis décroissance linéaire** | **0,0268** | **52,2 %** |

Le plateau est 6 % meilleur que le linéaire en validation croisée ; ce n'est pas une preuve de forme (les trois modèles
non constants sont proches), mais il reproduit le bas de plage où le linéaire dépassait la médiane de la classe < 120 de 0,017.

**Modèle retenu pour la batterie** : `swing = 0,7213 + (−0,0976 / 100) × max(tempo − 140, 0)`, charnière à **140 BPM**
(IC95 % mus. 130–150), pente **−0,0976 par 100 BPM** au-delà (IC95 % mus. −0,108 – −0,090), écart 120 → 240 BPM
**−0,098** (IC −0,107 – −0,090). Spearman tempo / swing : −0,81. Monotone **non croissante** : oui sur les points ; vrai
dans 100 % des rééchantillons (pistes et musiciens).

**Écart résiduel** (dispersion entre pistes à tempo égal) : écart-type robuste **0,027** (p10 / p90 des résidus
−0,037 / +0,033) ; par classe 0,024 (< 120), 0,024 (120–180), 0,026 (180–240), 0,032 (≥ 240). Une piste isolée s'écarte de la courbe d'environ ± 0,03 : la courbe est une **tendance centrale**, pas une
prédiction par piste.

### Points de la courbe de la batterie (à reprendre)

IC95 % par musicien ; « voisines » = pistes mesurées à ± 15 BPM (toutes « ok » : ≥ 20). **Plage de validité :
102,06 – 299,31 BPM.** Hors de cette plage, **aucune valeur** (`status: hors_plage`, `clamp_to_bpm` = borne la plus proche) :
60–100 et 300–330 BPM ne sont pas dans les données.

| Tempo (BPM) | Swing (r) | IC95 % mus. | Long/court | Pistes voisines |
|---|---|---|---|---|
| 110 | 0,721 | 0,715 – 0,729 | 2,59 | 88 |
| 120 | 0,721 | 0,715 – 0,729 | 2,59 | 139 |
| 130 | 0,721 | 0,715 – 0,729 | 2,59 | 188 |
| 140 | 0,721 | 0,715 – 0,725 | 2,59 | 195 |
| 150 | 0,712 | 0,706 – 0,719 | 2,47 | 190 |
| 160 | 0,702 | 0,697 – 0,709 | 2,35 | 182 |
| 170 | 0,692 | 0,687 – 0,699 | 2,25 | 181 |
| 180 | 0,682 | 0,677 – 0,688 | 2,15 | 204 |
| 190 | 0,673 | 0,667 – 0,678 | 2,05 | 220 |
| 200 | 0,663 | 0,657 – 0,669 | 1,97 | 208 |
| 210 | 0,653 | 0,647 – 0,659 | 1,88 | 197 |
| 220 | 0,643 | 0,637 – 0,650 | 1,80 | 169 |
| 230 | 0,633 | 0,627 – 0,640 | 1,73 | 153 |
| 240 | 0,624 | 0,616 – 0,631 | 1,66 | 123 |
| 250 | 0,614 | 0,606 – 0,622 | 1,59 | 114 |
| 260 | 0,604 | 0,595 – 0,613 | 1,53 | 93 |
| 270 | 0,595 | 0,585 – 0,603 | 1,47 | 87 |
| 280 | 0,585 | 0,574 – 0,594 | 1,41 | 69 |
| 290 | 0,575 | 0,564 – 0,585 | 1,35 | 56 |

(Au tempo observé maximal 299,3 BPM : 0,566 [0,554 – 0,576] ; au minimal 102,1 BPM : 0,721 [0,715 – 0,729].)

### Contrôle par un lissage par tranches de 20 BPM

Médiane des pistes de chaque tranche (IC95 % par musicien) contre la courbe à leur tempo médian :

| Tranche (BPM) | Pistes | Médiane (IC95 %) | Courbe | Courbe dans l'IC ? |
|---|---|---|---|---|
| 100–120 | 55 | 0,720 (0,712 – 0,732) | 0,721 | oui |
| 120–140 | 121 | 0,721 (0,717 – 0,727) | 0,721 | oui |
| 140–160 | 133 | 0,711 (0,703 – 0,718) | 0,713 | oui |
| 160–180 | 115 | 0,690 (0,676 – 0,697) | 0,691 | oui |
| 180–200 | 154 | 0,677 (0,667 – 0,688) | 0,672 | oui |
| 200–220 | 126 | 0,655 (0,655 – 0,667) | 0,653 | non (de justesse : médiane au bord de l'IC) |
| 220–240 | 99 | 0,640 (0,627 – 0,646) | 0,635 | oui |
| 240–260 | 77 | 0,600 (0,587 – 0,620) | 0,615 | oui |
| 260–280 | 52 | 0,591 (0,574 – 0,609) | 0,594 | oui |
| 280–300 | 42 | 0,571 (0,571 – 0,591) | 0,576 | oui |

Écart maximal médiane − courbe : 0,015 (à 240–260 BPM). Les médianes de tranche sont **monotones à 0,001 près** (une
seule remontée, de 0,0009, de 100–120 à 120–140 : le plateau).

### Basse et piano : courbes exploitables mais faibles

Même méthode (modèle choisi par validation croisée : plateau puis décroissance pour les deux). Exploitables au sens écrit
dans le JSON (IC95 % de l'écart 120 → 240 BPM hors de 0 et gain de validation croisée ≥ 5 % sur la constante) :

| Instrument | Charnière (IC mus.) | Plateau | Pente par 100 BPM au-delà | Écart 120 → 240 (IC mus.) | Gain de validation croisée | Résidu robuste |
|---|---|---|---|---|---|---|
| Basse | 130 (110–140) | 0,715 | −0,044 | −0,048 (−0,057 – −0,038) | 9,7 % | 0,034 |
| Piano | 150 (140–180) | 0,702 | −0,073 | −0,066 (−0,074 – −0,053) | 28,9 % | 0,033 |

| Tempo (BPM) | Basse : r (IC95 % mus.) | Piano : r (IC95 % mus.) |
|---|---|---|
| 110 | 0,715 (0,707 – 0,723) | 0,702 (0,695 – 0,709) |
| 130 | 0,715 (0,707 – 0,722) | 0,702 (0,695 – 0,709) |
| 150 | 0,706 (0,700 – 0,715) | 0,702 (0,691 – 0,708) |
| 170 | 0,697 (0,692 – 0,705) | 0,688 (0,678 – 0,703) |
| 190 | 0,688 (0,684 – 0,695) | 0,673 (0,664 – 0,693) |
| 210 | 0,680 (0,675 – 0,686) | 0,658 (0,649 – 0,675) |
| 230 | 0,671 (0,665 – 0,678) | 0,644 (0,633 – 0,657) |
| 250 | 0,662 (0,654 – 0,670) | 0,629 (0,618 – 0,641) |
| 270 | 0,653 (0,644 – 0,663) | 0,615 (0,602 – 0,627) |
| 290 | 0,644 (0,633 – 0,656) | 0,600 (0,585 – 0,614) |

La basse décroît deux fois moins vite que la batterie (−0,048 contre −0,098 sur 120 → 240 BPM) avec un résidu plus
large (0,034, 0,051 par classe ≥ 240 BPM) : elle ne se règle pas avec la même précision. La batterie reste la
référence pour le swing du moteur ; basse et piano sont donnés pour information.

## Micro-timing par rapport au temps

Écart = attaque de *a* − attaque de *b* au **même temps** (appariement de `beats.csv`) ; négatif = *a* en avance. En pas du
profil (¼ de temps, au tempo de chaque piste) et en **ms**. Pour chaque piste : moyenne tronquée à 10 % de ses écarts ;
puis moyenne tronquée à 10 % entre pistes (valeur + IC95 % par musicien de référence : la batterie pour un écart à la
batterie). La **médiane est inutilisable seule** : les CSV sont à 10 ms, elle tombe sur la grille (0, ±10, ±20 ms) ; elle
figure dans le JSON (`pooled_*`, `per_track_median_*`) avec p10 / p25 / p50 / p75 / p90 et moyenne tronquée poolée.

| Classe | Écart | Paires | Moyenne tronq. (ms) [IC95 % mus.] | En pas [IC95 % mus.] | Poolé p10 / p50 / p90 (ms) | Temps 1-3 / 2-4 (ms) | 2-4 − 1-3 (ms) [IC] | Dispersion par piste : σ médian (pistes) |
|---|---|---|---|---|---|---|---|---|
| < 120 | basse − batterie | 11 598 | +2,1 [−0,7 ; +5,6] | +0,016 [−0,005 ; +0,041] | −30 / 0 / +30 | +0,9 / +3,2 | +1,9 [+0,2 ; +3,9] | 21,1 ms / 0,16 pas (55) |
| < 120 | piano − batterie | 10 062 | +16,7 [+11,6 ; +21,0] | +0,127 [+0,090 ; +0,159] | −30 / +10 / +60 | +16,9 / +16,6 | −0,9 [−2,9 ; +0,6] | 35,7 ms / 0,26 pas (55) |
| < 120 | basse − piano | 9 585 | −14,7 [−19,8 ; −9,1] | −0,112 [−0,154 ; −0,069] | −60 / −10 / +30 | −16,0 / −13,4 | +2,5 [−0,3 ; +5,3] | 36,0 ms / 0,26 pas (55) |
| 120–180 | basse − batterie | 97 521 | +2,6 [+0,3 ; +4,8] | +0,027 [+0,004 ; +0,048] | −20 / 0 / +30 | +1,6 / +3,5 | +1,9 [+1,0 ; +2,9] | 18,6 ms / 0,19 pas (370) |
| 120–180 | piano − batterie | 79 131 | +20,8 [+18,9 ; +23,0] | +0,207 [+0,186 ; +0,232] | −20 / +20 / +60 | +20,2 / +21,2 | +1,3 [+0,2 ; +2,4] | 30,6 ms / 0,31 pas (370) |
| 120–180 | basse − piano | 76 277 | −18,8 [−21,8 ; −15,4] | −0,186 [−0,214 ; −0,153] | −60 / −20 / +20 | −19,3 / −18,3 | +0,8 [−0,4 ; +1,9] | 31,7 ms / 0,31 pas (370) |
| 180–240 | basse − batterie | 135 352 | +3,3 [+1,1 ; +5,8] | +0,045 [+0,014 ; +0,080] | −20 / 0 / +30 | +2,1 / +4,4 | +2,3 [+1,3 ; +3,7] | 16,4 ms / 0,23 pas (379) |
| 180–240 | piano − batterie | 107 420 | +19,4 [+16,6 ; +22,3] | +0,266 [+0,229 ; +0,311] | −10 / +20 / +60 | +18,3 / +20,6 | +2,0 [+0,7 ; +3,4] | 24,3 ms / 0,34 pas (379) |
| 180–240 | basse − piano | 105 035 | −16,6 [−19,8 ; −12,8] | −0,226 [−0,269 ; −0,177] | −50 / −20 / +20 | −16,6 / −16,6 | +0,2 [−0,9 ; +1,2] | 24,5 ms / 0,34 pas (379) |
| ≥ 240 | basse − batterie | 75 255 | +4,3 [+2,0 ; +6,6] | +0,076 [+0,034 ; +0,113] | −20 / +10 / +30 | +3,4 / +4,9 | +1,6 [+0,1 ; +3,2] | 16,2 ms / 0,28 pas (172) |
| ≥ 240 | piano − batterie | 59 823 | +11,5 [+8,7 ; +13,8] | +0,204 [+0,157 ; +0,241] | −20 / +10 / +40 | +9,7 / +13,0 | +3,1 [+1,5 ; +4,7] | 20,8 ms / 0,37 pas (172) |
| ≥ 240 | basse − piano | 59 902 | −6,6 [−9,3 ; −3,7] | −0,117 [−0,166 ; −0,067] | −40 / −10 / +20 | −6,0 / −7,6 | −1,5 [−2,1 ; −0,9] | 20,7 ms / 0,37 pas (172) |
| toutes | basse − batterie | 319 726 | +3,2 [+1,2 ; +5,1] | +0,040 [+0,017 ; +0,065] | −20 / 0 / +30 | +2,0 / +4,1 | +2,0 [+1,1 ; +2,9] | 17,2 ms / 0,22 pas (976) |
| toutes | piano − batterie | 256 436 | +18,3 [+16,7 ; +20,2] | +0,223 [+0,201 ; +0,246] | −20 / +20 / +50 | +17,3 / +19,2 | +1,8 [+0,9 ; +2,8] | 25,7 ms / 0,33 pas (976) |
| toutes | basse − piano | 250 799 | −15,4 [−18,4 ; −12,7] | −0,183 [−0,215 ; −0,148] | −50 / −10 / +20 | −15,6 / −15,3 | +0,1 [−0,6 ; +0,8] | 26,1 ms / 0,33 pas (976) |

Lecture :

- **Piano − batterie** : le piano est **en retard d'environ 17–21 ms** à 100–240 BPM (0,13 → 0,27 pas) et de ≈ 11 ms à
  240–300 BPM (0,20 pas). Le retard est à peu près **constant en ms** (donc croissant en pas avec le tempo) jusqu'à
  240 BPM : c'est la bonne unité pour le régler.
- **Basse − batterie** : +2 à +4 ms (0,02 – 0,08 pas), **bien en dessous de la résolution des CSV** : à reprendre comme
  « basse sur la batterie » (décalage nul) ; ne pas régler de décalage fin.
- **Basse − piano** : −7 à −19 ms, déduit des deux précédents (basse devant le piano).
- **Temps 1-3 contre 2-4** : 2-4 est plus tardif de +0,2 à +3 ms : négligeable (≤ 3 ms) ; aucune asymétrie utilisable.
- **Dispersion** (σ par piste, médiane sur les pistes) : 16–21 ms pour la basse, 21–36 ms pour le piano, soit 0,16 –
  0,37 pas, supérieure au `jitter` ≤ 0,1 pas du moteur : l'amplitude réelle est plus large que ce que le moteur
  produit aujourd'hui.
- **Écarts absolus à la détection de temps** (JSON `micro_timing.classes.<classe>.absolute_vs_beat`) : basse ≈ +1 à +4 ms,
  batterie ≈ −1 ms, piano ≈ +10 à +18 ms, **donnés à titre d'information** : ils dépendent de la détection automatique des temps
  et ne sont pas à reprendre.

### Résolution de 10 ms par classe de tempo

Les CSV sont arrondis au centième de seconde. Ce que cela représente :

| Classe (tempo médian) | Pas du profil | 10 ms en pas | Quantum de swing par attaque | Bruit d'arrondi σ d'un écart, en pas |
|---|---|---|---|---|
| < 120 (115 BPM) | 130,2 ms | 0,077 | 0,019 | 0,031 |
| 120–180 (149) | 101,0 ms | 0,099 | 0,025 | 0,040 |
| 180–240 (205) | 73,3 ms | 0,136 | 0,034 | 0,056 |
| ≥ 240 (263) | 57,0 ms | 0,175 | 0,044 | 0,072 |

(0,13 pas à 200 BPM ; 0,18 pas à 263 BPM ; 0,26 pas à 400 BPM, hors plage observée.) Une attaque isolée donne un rapport de swing
quantifié par 10 ms ÷ durée d'un temps (0,033 à 200 BPM) ; les médianes sur des centaines d'attaques puis sur des dizaines de
pistes la dépassent, la dispersion d'une piste isolée et ses plus petits décalages non. Le bruit d'arrondi σ d'une différence
de deux instants est 10 ms ÷ √6 = 4,1 ms.

## Fiabilité

Seuils écrits (JSON `reliability.thresholds`), appliqués à chaque classe × instrument (pistes **mesurées**,
musiciens distincts **de l'instrument**) :

| Verdict | Critère |
|---|---|
| **assez** | ≥ 60 pistes mesurées, ≥ 8 musiciens distincts, aucun musicien > 25 % des pistes et, pour le swing, demi-largeur de l'IC95 % par musicien ≤ 0,02 (≈ l'écart entre classes voisines) |
| **juste** | ≥ 30 pistes mesurées et ≥ 5 musiciens distincts (sans satisfaire « assez ») |
| **trop peu** | en dessous : ne pas reprendre la valeur sans autre source |

Justification : à l'échelle des données, la classe la plus petite (55 pistes, 31 batteurs) a une demi-largeur d'IC par musicien
de 0,010 en swing (seuil 0,02, soit l'écart entre classes voisines) ; 30 pistes est le plancher d'E7 (`MIN_TRACKS_PER_BIN`),
5 musiciens évitent qu'un seul ou deux musiciens fassent la classe ; la part du plus gros musicien borne la dépendance.

| Classe | Batterie | Basse | Piano | Micro-timing (3 écarts relatifs) |
|---|---|---|---|---|
| < 120 BPM | **juste** (55 pistes, 31 batteurs) | **juste** (50, 25) | **juste** (55, 20) | **juste** (55 pistes) |
| 120–180 | **assez** (369, 75) | **assez** (313, 65) | **assez** (370, 32) | **assez** (370) |
| 180–240 | **assez** (379, 73) | **assez** (312, 59) | **assez** (379, 30) | **assez** (379) |
| ≥ 240 | **assez** (171, 57) | **assez** (124, 48) | **assez** (172, 27) | **assez** (172) |

« assez » porte sur les **effectifs** : l'arrondi de 10 ms et la détection automatique limitent d'autant la précision
des écarts fins (voir ci-dessous).

## Limites

- **Détection automatique** : temps et attaques sont détectés par des algorithmes sur des pistes séparées par séparation de
  sources (Cheston et al., TISMIR 2024), pas relevés à la main. Le swing de la batterie est dominé par le ride ; ghost
  notes et caisse claire peuvent y entrer. Les écarts **absolus** au temps dépendent de la détection : seuls les écarts
  **relatifs** entre instruments sont à reprendre.
- **Résolution** : 10 ms (tableau ci-dessus) ; les écarts basse − batterie (2–4 ms) sont sous cette résolution.
- **Musiciens répétés** : un même batteur, bassiste ou pianiste signe plusieurs pistes (976 pistes, 99 batteurs, 84 bassistes, 34 pianistes).
  Les IC par musicien sont les seuls honnêtes ; les IC par piste les sous-estiment (jusqu'à × 5,8).
- **Plage de tempo** : 102–299 BPM seulement. Aucune piste < 100 ni > 300 BPM : ballades lentes et tempos
  extrêmes ne sont pas couverts. Pas d'extrapolation.
- **Swing du piano** : soliste et comping mêlés (attaques de `piano_onsets.csv` entre 0,45 et 0,85 du temps) ; swing de la
  basse : peu de contretemps par piste (3 869 à 29 174 attaques par classe), pistes mesurées moins nombreuses (799 / 976).
- **Un seul rapport par piste** : la médiane sur la piste efface la variation intra-morceau (tempo non constant, sections
  plus ou moins swinguées) ; le tempo est celui de `metadata.json` (extrait de quelques minutes).
- **Corpus** : trios piano enregistrés (surtout 1950–2010), pas une mesure du « swing » en général ni d'autres styles
  (latin, funk, ballade) ; la valeur à reprendre vaut pour le swing de trio piano, pas pour toute la bibliothèque.
- **Forme de la courbe** : les trois modèles non constants ont des écarts de validation croisée proches (0,0268 – 0,0309) :
  la charnière à 140 BPM est une description commode, pas un seuil net (IC 130–150).

## Usage prévu par A6 (« swing selon le tempo »)

1. **Courbe de la batterie** : reprendre les points de la table ci-dessus (ou la formule du JSON, `a6_table.curve.drums`) ;
   `swing_ratio = 0,7213` jusqu'à 140 BPM puis `0,7213 − 0,000976 × (tempo − 140)`, **borné au tempo observé
   (102–299 BPM)** : au-delà, borner le tempo (`clamp_to_bpm`) plutôt qu'extrapoler.
2. **Valeurs par classe** (si A6 préfère des paliers) : 0,72 (< 120), 0,71 (120–180), 0,66 (180–240), 0,59 (≥ 240)
   (`a6_table.classes`, avec IC et verdicts). Le défaut 0,71 du profil `wjazzd_swing` ne vaut que jusqu'à ≈ 180 BPM.
3. **Micro-timing** : décaler le piano de ≈ +17 à +21 ms (≈ 11 ms à ≥ 240 BPM) par rapport à la batterie, la basse sur la batterie
   (+3 ms : à ne pas régler) ; convertir en pas au tempo courant (pas = 15 000 ÷ BPM ms).
4. **Basse et piano** : courbes secondaires (`a6_table.curve.bass`, `.piano`), plus faibles et plus larges : à n'utiliser
   que si le moteur règle un swing par piste.
5. **Ce que la donnée ne permet pas** : swing sous 100 ou au-dessus de 300 BPM, swing d'autres styles, variation
   intra-morceau, décalages sous 10 ms.
