# wjazzd-twobeat : accompagnements `rhythmfeel = TWOBEAT` de la Weimar Jazz Database (phase 019, L2)

Mesures de la **marche de basse** et de son **rythme au temps** sur un sous-ensemble non swing de WJazzD, pour une bibliothèque de styles. Comptes, parts et centiles uniquement : aucune phrase de solo, aucune suite de notes n'est conservée (principe VII).

## Provenance et licence

- Source : Weimar Jazz Database (WJazzD), WJazzD 2.1 (base 2.2, publiée le 2018-02-08), SHA256 `af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12` (vérifié avant toute lecture).
- Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus).
- Mention requise (ODbL §4.3) : « Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0). »
- Sous-ensemble : solo_info.rhythmfeel = 'TWOBEAT' (valeur exacte) ; mesures 4/4 de chorus (bar >= 1) à quatre temps, basse complète et accord connu (NC et symboles non analysés écartés).
- Les mesures dérivées sont des faits agrégés ; la base elle-même reste dans `corpus/wjazzd/raw/` (cache gitignoré). Manifeste des solos : `corpus/wjazzd/manifest.jsonl` (champ `l2_subset`).

## Reproduction

```bash
python -m harmonium_lab.backing.wjazzd_subsets --subset TWOBEAT
```

Écrit `references/wjazzd-twobeat/measures-bass.json` et ce `README.md` ; deux exécutions donnent des fichiers identiques (clés triées, arrondis fixes, bootstrap à graine fixe `wjazzd-subsets-v1`, 2000 rééchantillons).

## Effectifs

- **32 solos** `TWOBEAT` (valeur exacte) ; 30 ont au moins une mesure valide. Hors sous-ensemble : 6 solos à `rhythmfeel` composé (`A:LATIN/B:SWING` 1, `FUNK/SWING` 1, `LATIN/FUNK` 3, `LATIN/SWING` 1).
- **846 mesures** (chorus, toutes signatures) dont **752 valides** (3008 temps) ; **20,1 min** de mesures valides (21,9 min de mesures 4/4). Méthode : minutes = mesures × 4 temps / avgtempo du solo (BPM, la noire est le temps), sommées sur les solos. Contrôle sur tous les temps de chorus, toutes signatures : 21,6 min à `avgtempo` contre 21,4 min (étendue des `onset`).
- **46 chorus** vus en 4/4 (35 sans le dernier chorus de chaque solo, qui peut être tronqué) ; longueurs des chorus conservés (mesures×effectif) : 8×2, 12×4, 13×2, 14×1, 16×6, 17×4, 18×3, 19×2, 24×2, 31×2, 32×3, 34×3, 35×1.
- Tempos (`avgtempo`) : min 70,6, p25 142,6, médiane 183,8, p75 207,4, max 273,6 BPM.
- Enregistrements : 1925–1941 (32 dates lues, 0 inconnues) ; par décennie : 1920s ×24, 1930s ×2, 1940s ×6.
- Signatures des solos : 4/4 ×32. Mesures non 4/4 (écartées par le lecteur E7) : 0 mesures dans 0 solo(s) ; solos sans aucune mesure 4/4 : 0.

### Mesures écartées (toutes signatures)

| motif | mesures | part |
|---|---|---|
| signature ≠ 4/4 | 0 | 0 % |
| incomplète | 19 | 2 % |
| basse manquante | 70 | 8 % |
| accord absent / NC / non analysé | 5 | 1 % |
| valides | 752 | 89 % |

Accords (temps 4/4 d'un chorus) : 3338 avec symbole, 0 sans symbole, 27 `NC`, 0 non analysés. 2 solo(s) n'ont aucune mesure valide.

## Principales mesures (tous solos du sous-ensemble, IC à 95 % par bootstrap par solo)

| indicateur | estimation [IC 95 %] | n événements | n solos | IC absent car |
|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 25 % [18–33 %] | 709 | 30 |  |
| approche 4ᵉ temps (changement à la barre) : aucune | 68 % [62–75 %] | 477 | 30 |  |
| approche 4ᵉ temps (changement à la barre) : chromatique | 18 % [13–23 %] | 477 | 30 |  |
| approche 4ᵉ temps (changement à la barre) : diatonique | 14 % [9–20 %] | 477 | 30 |  |
| approche (tous contextes) : aucune | 69 % [65–75 %] | 863 | 30 |  |
| approche (tous contextes) : chromatique | 17 % [14–21 %] | 863 | 30 |  |
| approche (tous contextes) : diatonique | 13 % [9–19 %] | 863 | 30 |  |
| note de passage : note d'accord | 41 % [33–48 %] | 1156 | 30 |  |
| note de passage : degré de gamme | 20 % [15–25 %] | 1156 | 30 |  |
| note de passage : chromatique | 39 % [33–46 %] | 1156 | 30 |  |
| intervalles : répétitions (Δ = 0) | 37 % [32–43 %] | 2977 | 30 |  |
| mesures `quarters` (aucune répétition) | 29 % [23–37 %] | 752 | 30 |  |
| mesures `halves` (t1=t2, t3=t4) | 10 % [6–14 %] | 752 | 30 |  |
| mesures à un seul accord | 76 % [66–86 %] | 752 | 30 |  |
| intervalle médian (demi-tons, valeur absolue) | 2,0 [1,0–2,0] | 2977 | 30 |  |
| intervalle p90 (demi-tons, valeur absolue) | 10,0 [7,0–12,0] | 2977 | 30 |  |

Le 1ᵉʳ temps de mesure sans changement et le détail des approches (haut/bas, distance) sont dans le JSON (`groups.all.arrival`, `.approach`, `.passage`, `.intervals`).

## Rythme de la basse (au temps)

Sur 752 mesures valides. `bar_pattern` : égalités de hauteur entre temps consécutifs de la mesure. **Une hauteur répétée est soit une noire rejouée, soit une note tenue : indiscernable.**

| motif | mesures | part |
|---|---|---|
| quarters | 220 | 29 % |
| quarters_half | 79 | 11 % |
| quarter_half_quarter | 61 | 8 % |
| quarter_dotted_half | 59 | 8 % |
| half_quarters | 108 | 14 % |
| halves | 75 | 10 % |
| dotted_half_quarter | 66 | 9 % |
| whole | 84 | 11 % |

Longueur des suites de temps à hauteur identique (en temps, barres de mesure franchies) : 1 temps : 69 % (1323), 2 temps : 19 % (353), 3 temps : 6 % (114), 4+ temps : 6 % (114) ; moyenne 1,58 temps ; 56 % des temps sont dans une suite de 2 temps ou plus.
Attache sur la barre de mesure (dernier temps = 1ᵉʳ temps de la mesure suivante) : 28 % (204/721). Répétitions par position : 1-2 44 %, 2-3 36 %, 3-4 39 %.
Hauteurs distinctes par mesure (1/2/3/4) : 11 % / 38 % / 37 % / 14 %.

**Les croches ne sont pas observables** (une note de basse par noire) : aucun motif de croches n'est déduit, et la longueur « 1 temps » ne dit pas si la note est brève ou répétée.

## Classes de tempo et fiabilité

Seuils (solos avec mesures valides ET mesures valides) : **assez** ≥ 20 solos et ≥ 1500 mesures ; **juste** ≥ 8 solos et ≥ 500 mesures ; sinon **trop peu**. Justification : le solo est l'unité de rééchantillonnage ; avec un écart-type d'environ 0,2 entre solos sur une part (ordre de grandeur relevé en E7), la demi-largeur de l'IC vaut ≈ 0,09 pour 20 solos, ≈ 0,14 pour 8, ≈ 0,20 pour 4.

| groupe (BPM) | solos | solos avec mesures | mesures valides | minutes | chorus | fiabilité | largeur médiane IC (parts) |
|---|---|---|---|---|---|---|---|
| tous | 32 | 30 | 752 | 20,1 | 46 | **juste** | 0,11 |
| < 120 | 3 | 3 | 121 | 5,7 | 9 | **trop peu** | 0,32 |
| 120–180 | 11 | 11 | 235 | 6,7 | 16 | **trop peu** | 0,13 |
| 180–240 | 16 | 15 | 364 | 7,3 | 18 | **trop peu** | 0,15 |
| ≥ 240 | 2 | 1 | 32 | 0,5 | 3 | **trop peu** | — |

| indicateur | tous | < 120 | 120–180 | 180–240 | ≥ 240 |
|---|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 25 % [18–33 %] | 35 % [21–67 %] | 20 % [12–34 %] | 25 % [13–36 %] | 53 % [pas d'IC] |
| approche 4ᵉ temps (changement à la barre) : chromatique | 18 % [13–23 %] | 11 % [3–20 %] | 15 % [10–20 %] | 21 % [12–30 %] | 27 % [pas d'IC] |
| intervalles : répétitions (Δ = 0) | 37 % [32–43 %] | 34 % [2–54 %] | 32 % [25–39 %] | 43 % [36–51 %] | 23 % [pas d'IC] |
| intervalle médian (demi-tons, valeur absolue) | 2,0 [1,0–2,0] | 2,0 [0,0–4,0] | 3,0 [1,0–5,0] | 1,0 [0,0–1,0] | 4,0 [pas d'IC] |
| mesures `quarters` (aucune répétition) | 29 % [23–37 %] | 34 % [10–92 %] | 33 % [21–47 %] | 24 % [17–31 %] | 41 % [pas d'IC] |
| mesures `halves` (t1=t2, t3=t4) | 10 % [6–14 %] | 20 % [0–26 %] | 4 % [2–7 %] | 11 % [6–17 %] | 6 % [pas d'IC] |
| mesures à un seul accord | 76 % [66–86 %] | 74 % [67–88 %] | 62 % [44–84 %] | 84 % [73–94 %] | 100 % [pas d'IC] |

Chaque cellule : estimation [IC 95 %] ; effectifs par groupe dans le JSON (`groups.<groupe>.indicators`, `n_events`, `n_solos`).

**Verdict du sous-ensemble : juste** (30 solos avec mesures valides, 752 mesures valides).

## Limites

- Les croches ne sont PAS observables : `bass_pitch` n'a qu'une valeur par temps (une noire) ; aucune durée, aucune attaque, aucun silence de basse n'est dans la base. Le rythme de la basse se limite aux répétitions de hauteur d'un temps au suivant, aux suites de temps à hauteur identique et à l'attache sur la barre de mesure.
- Une hauteur répétée peut être une noire rejouée ou une note tenue (blanche, ronde) : la donnée ne les distingue pas. `halves` = deux blanches OU deux paires de noires répétées.
- Peu de solos par sous-ensemble (10 à 32) et par classe de tempo : les intervalles de confiance (bootstrap par solo, méthode des percentiles) sont larges et, avec moins de quelques solos, trop optimistes ; ils ne disent rien du biais de sélection de la base (choix des solos, solistes, morceaux).
- La basse annotée est peu cohérente avec la grille d'accords (voir E7, `bass_measures` : la basse de l'accord n'est jouée qu'à 41 % des changements d'accord en swing) : les parts d'arrivée sont celles de l'annotation, pas celles d'une marche idéale.
- Mesures hors 4/4, sans basse complète ou sans accord utilisable écartées (voir `discarded`) ; les intervalles et les approches ne franchissent jamais une mesure écartée. Les suites de temps à hauteur identique sont tronquées aux bords des suites de mesures valides.
- Aucune phrase de solo, aucune suite de notes n'est conservée : uniquement des comptes, parts et centiles.
- Non représentatif d'un « 2 temps » moderne : les 32 solos sont tous de style `TRADITIONAL`, de 8 solistes (trompette/cornet, trombone, clarinette, saxophone soprano : Armstrong, Beiderbecke, Bechet, Dodds, Ory, Higginbotham, Allen, Shavers) ; 24 enregistrés en 1925–1928, 2 en 1938, 6 en 1941. `record_info.releasedate` (2007 pour 18 solos) date les publications, pas les enregistrements : on lit `track_info.recordingdate`.
- La basse d'enregistrements acoustiques/anciens (tuba, contrebasse, sax basse) est difficile à transcrire : la basse annotée suit peu la grille (arrivée sur la basse de l'accord au changement 25 %, IC 18–33 %, contre 41 % en swing ; passages chromatiques 39 % contre 27 %). Cela peut venir de l'annotation autant que du style : la donnée ne permet pas de trancher.
- Le « balancement à deux temps » ne se lit pas clairement au temps : seulement 10 % de mesures `halves` (t1=t2, t3=t4) et 11 % de `whole`, alors que 29 % de mesures sont sans aucune répétition. Une basse à deux temps jouée en noires piquées ou en blanches n'est pas distinguable ici.
- Tempos de 70,6 à 273,6 BPM (médiane 183,85) ; les classes `< 120` (3 solos) et `≥ 240` (2 solos, 1 avec mesures) sont inutilisables, `120–180` (11 solos) et `180–240` (16 solos, 15 avec mesures) sont « trop peu ».

## Exploitable pour le moteur / non exploitable

- Seul sous-ensemble à 30 solos avec mesures : les parts globales (approche, répétitions 37 %, mesures à un accord 76 %) ont des IC raisonnables ; ils décrivent le jazz traditionnel années 1920–40, pas un style à imiter tel quel.
- Utile comme contraste (basse plus statique : notes répétées plus fréquentes, 37 % contre 20 % en swing) avec le swing, à condition de garder à l'esprit l'incertitude d'annotation.
- NON exploitable : un réglage par tempo ; tout ce qui relève du caractère à deux temps (accent sur 1 et 3, notes piquées, ghost notes).
- Exploitables : parts et centiles de la marche de basse au temps (arrivées, approches du 4ᵉ temps, notes de passage, intervalles, registre), rythme harmonique (accords par mesure), motifs de répétition de hauteur par mesure, tempos et formes, avec leurs IC par solo.
- Non exploitables : tout ce qui est plus fin que la noire (croches, anticipations, durées réelles des notes), les silences de basse, la dynamique et les timbres, les phrases ou suites de notes (non conservées).
- Un indicateur dont l'IC est absent ou très large (voir le tableau) ne sert pas de cible chiffrée.
