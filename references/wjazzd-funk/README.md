# wjazzd-funk : accompagnements `rhythmfeel = FUNK` de la Weimar Jazz Database (phase 019, L2)

Mesures de la **marche de basse** et de son **rythme au temps** sur un sous-ensemble non swing de WJazzD, pour une bibliothèque de styles. Comptes, parts et centiles uniquement : aucune phrase de solo, aucune suite de notes n'est conservée (principe VII).

## Provenance et licence

- Source : Weimar Jazz Database (WJazzD), WJazzD 2.1 (base 2.2, publiée le 2018-02-08), SHA256 `af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12` (vérifié avant toute lecture).
- Licence : ODbL-1.0 (base) + DbCL-1.0 (contenus).
- Mention requise (ODbL §4.3) : « Contains information from the Weimar Jazz Database (Jazzomat Research Project, HfM Weimar), which is made available here under the Open Database License (ODbL); individual contents under the Database Contents License (DbCL 1.0). »
- Sous-ensemble : solo_info.rhythmfeel = 'FUNK' (valeur exacte) ; mesures 4/4 de chorus (bar >= 1) à quatre temps, basse complète et accord connu (NC et symboles non analysés écartés).
- Les mesures dérivées sont des faits agrégés ; la base elle-même reste dans `corpus/wjazzd/raw/` (cache gitignoré). Manifeste des solos : `corpus/wjazzd/manifest.jsonl` (champ `l2_subset`).

## Reproduction

```bash
python -m harmonium_lab.backing.wjazzd_subsets --subset FUNK
```

Écrit `references/wjazzd-funk/measures-bass.json` et ce `README.md` ; deux exécutions donnent des fichiers identiques (clés triées, arrondis fixes, bootstrap à graine fixe `wjazzd-subsets-v1`, 2000 rééchantillons).

## Effectifs

- **20 solos** `FUNK` (valeur exacte) ; 16 ont au moins une mesure valide. Hors sous-ensemble : 6 solos à `rhythmfeel` composé (`A:LATIN/B:SWING` 1, `FUNK/SWING` 1, `LATIN/FUNK` 3, `LATIN/SWING` 1).
- **1222 mesures** (chorus, toutes signatures) dont **928 valides** (3712 temps) ; **31,3 min** de mesures valides (36,9 min de mesures 4/4). Méthode : minutes = mesures × 4 temps / avgtempo du solo (BPM, la noire est le temps), sommées sur les solos. Contrôle sur tous les temps de chorus, toutes signatures : 41,0 min à `avgtempo` contre 40,9 min (étendue des `onset`).
- **32 chorus** vus en 4/4 (24 sans le dernier chorus de chaque solo, qui peut être tronqué) ; longueurs des chorus conservés (mesures×effectif) : 12×5, 16×7, 26×1, 37×1, 49×1, 50×2, 61×1, 67×1, 73×1, 87×1, 107×1, 118×1, 141×1.
- Tempos (`avgtempo`) : min 84,0, p25 105,8, médiane 117,8, p75 144,9, max 159,4 BPM.
- Enregistrements : 1969–2009 (20 dates lues, 0 inconnues) ; par décennie : 1960s ×4, 1970s ×2, 1990s ×10, 2000s ×4.
- Signatures des solos : 4/4 ×18, 9/4 ×2. Mesures non 4/4 (écartées par le lecteur E7) : 141 mesures dans 3 solo(s) (3/4 : 123 mesures / 1 solo(s), 9/4 : 18 mesures / 2 solo(s)) ; solos sans aucune mesure 4/4 : 3.

### Mesures écartées (toutes signatures)

| motif | mesures | part |
|---|---|---|
| signature ≠ 4/4 | 141 | 12 % |
| incomplète | 12 | 1 % |
| basse manquante | 140 | 11 % |
| accord absent / NC / non analysé | 1 | 0 % |
| valides | 928 | 76 % |

Accords (temps 4/4 d'un chorus) : 4301 avec symbole, 0 sans symbole, 8 `NC`, 0 non analysés. 4 solo(s) n'ont aucune mesure valide.

## Principales mesures (tous solos du sous-ensemble, IC à 95 % par bootstrap par solo)

| indicateur | estimation [IC 95 %] | n événements | n solos | IC absent car |
|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 45 % [34–63 %] | 672 | 12 |  |
| approche 4ᵉ temps (changement à la barre) : aucune | 68 % [62–73 %] | 494 | 12 |  |
| approche 4ᵉ temps (changement à la barre) : chromatique | 22 % [17–28 %] | 494 | 12 |  |
| approche 4ᵉ temps (changement à la barre) : diatonique | 10 % [6–16 %] | 494 | 12 |  |
| approche (tous contextes) : aucune | 72 % [65–77 %] | 1077 | 16 |  |
| approche (tous contextes) : chromatique | 14 % [11–19 %] | 1077 | 16 |  |
| approche (tous contextes) : diatonique | 14 % [8–20 %] | 1077 | 16 |  |
| note de passage : note d'accord | 40 % [29–54 %] | 1518 | 14 |  |
| note de passage : degré de gamme | 23 % [15–30 %] | 1518 | 14 |  |
| note de passage : chromatique | 36 % [26–47 %] | 1518 | 14 |  |
| intervalles : répétitions (Δ = 0) | 28 % [24–34 %] | 3696 | 16 |  |
| mesures `quarters` (aucune répétition) | 38 % [29–46 %] | 928 | 16 |  |
| mesures `halves` (t1=t2, t3=t4) | 7 % [4–11 %] | 928 | 16 |  |
| mesures à un seul accord | 82 % [61–97 %] | 928 | 16 |  |
| intervalle médian (demi-tons, valeur absolue) | 2,0 [2,0–3,0] | 3696 | 16 |  |
| intervalle p90 (demi-tons, valeur absolue) | 10,0 [8,0–11,0] | 3696 | 16 |  |

Le 1ᵉʳ temps de mesure sans changement et le détail des approches (haut/bas, distance) sont dans le JSON (`groups.all.arrival`, `.approach`, `.passage`, `.intervals`).

## Rythme de la basse (au temps)

Sur 928 mesures valides. `bar_pattern` : égalités de hauteur entre temps consécutifs de la mesure. **Une hauteur répétée est soit une noire rejouée, soit une note tenue : indiscernable.**

| motif | mesures | part |
|---|---|---|
| quarters | 357 | 38 % |
| quarters_half | 111 | 12 % |
| quarter_half_quarter | 117 | 13 % |
| quarter_dotted_half | 44 | 5 % |
| half_quarters | 123 | 13 % |
| halves | 63 | 7 % |
| dotted_half_quarter | 56 | 6 % |
| whole | 57 | 6 % |

Longueur des suites de temps à hauteur identique (en temps, barres de mesure franchies) : 1 temps : 73 % (1952), 2 temps : 19 % (510), 3 temps : 5 % (127), 4+ temps : 3 % (74) ; moyenne 1,39 temps ; 47 % des temps sont dans une suite de 2 temps ou plus.
Attache sur la barre de mesure (dernier temps = 1ᵉʳ temps de la mesure suivante) : 22 % (201/912). Répétitions par position : 1-2 32 %, 2-3 30 %, 3-4 30 %.
Hauteurs distinctes par mesure (1/2/3/4) : 6 % / 28 % / 44 % / 22 %.

**Les croches ne sont pas observables** (une note de basse par noire) : aucun motif de croches n'est déduit, et la longueur « 1 temps » ne dit pas si la note est brève ou répétée.

## Classes de tempo et fiabilité

Seuils (solos avec mesures valides ET mesures valides) : **assez** ≥ 20 solos et ≥ 1500 mesures ; **juste** ≥ 8 solos et ≥ 500 mesures ; sinon **trop peu**. Justification : le solo est l'unité de rééchantillonnage ; avec un écart-type d'environ 0,2 entre solos sur une part (ordre de grandeur relevé en E7), la demi-largeur de l'IC vaut ≈ 0,09 pour 20 solos, ≈ 0,14 pour 8, ≈ 0,20 pour 4.

| groupe (BPM) | solos | solos avec mesures | mesures valides | minutes | chorus | fiabilité | largeur médiane IC (parts) |
|---|---|---|---|---|---|---|---|
| tous | 20 | 16 | 928 | 31,3 | 32 | **juste** | 0,12 |
| < 120 | 12 | 10 | 623 | 22,9 | 21 | **juste** | 0,15 |
| 120–180 | 8 | 6 | 305 | 8,4 | 11 | **trop peu** | 0,19 |
| 180–240 | 0 | 0 | 0 | 0,0 | 0 | **trop peu** | — |
| ≥ 240 | 0 | 0 | 0 | 0,0 | 0 | **trop peu** | — |

| indicateur | tous | < 120 | 120–180 | 180–240 | ≥ 240 |
|---|---|---|---|---|---|
| arrivée sur la basse de l'accord au changement | 45 % [34–63 %] | 41 % [29–65 %] | 53 % [35–81 %] | n/a | n/a |
| approche 4ᵉ temps (changement à la barre) : chromatique | 22 % [17–28 %] | 20 % [15–25 %] | 25 % [16–37 %] | n/a | n/a |
| intervalles : répétitions (Δ = 0) | 28 % [24–34 %] | 26 % [22–33 %] | 33 % [27–41 %] | n/a | n/a |
| intervalle médian (demi-tons, valeur absolue) | 2,0 [2,0–3,0] | 3,0 [2,0–4,0] | 2,0 [1,0–2,0] | n/a | n/a |
| mesures `quarters` (aucune répétition) | 38 % [29–46 %] | 44 % [34–51 %] | 28 % [13–39 %] | n/a | n/a |
| mesures `halves` (t1=t2, t3=t4) | 7 % [4–11 %] | 4 % [2–8 %] | 12 % [6–17 %] | n/a | n/a |
| mesures à un seul accord | 82 % [61–97 %] | 75 % [43–98 %] | 96 % [91–100 %] | n/a | n/a |

Chaque cellule : estimation [IC 95 %] ; effectifs par groupe dans le JSON (`groups.<groupe>.indicators`, `n_events`, `n_solos`).

**Verdict du sous-ensemble : juste** (16 solos avec mesures valides, 928 mesures valides).

## Limites

- Les croches ne sont PAS observables : `bass_pitch` n'a qu'une valeur par temps (une noire) ; aucune durée, aucune attaque, aucun silence de basse n'est dans la base. Le rythme de la basse se limite aux répétitions de hauteur d'un temps au suivant, aux suites de temps à hauteur identique et à l'attache sur la barre de mesure.
- Une hauteur répétée peut être une noire rejouée ou une note tenue (blanche, ronde) : la donnée ne les distingue pas. `halves` = deux blanches OU deux paires de noires répétées.
- Peu de solos par sous-ensemble (10 à 32) et par classe de tempo : les intervalles de confiance (bootstrap par solo, méthode des percentiles) sont larges et, avec moins de quelques solos, trop optimistes ; ils ne disent rien du biais de sélection de la base (choix des solos, solistes, morceaux).
- La basse annotée est peu cohérente avec la grille d'accords (voir E7, `bass_measures` : la basse de l'accord n'est jouée qu'à 41 % des changements d'accord en swing) : les parts d'arrivée sont celles de l'annotation, pas celles d'une marche idéale.
- Mesures hors 4/4, sans basse complète ou sans accord utilisable écartées (voir `discarded`) ; les intervalles et les approches ne franchissent jamais une mesure écartée. Les suites de temps à hauteur identique sont tronquées aux bords des suites de mesures valides.
- Aucune phrase de solo, aucune suite de notes n'est conservée : uniquement des comptes, parts et centiles.
- 8 solos sur 20 sont de forme `open` (improvisation sur vamp à 1–3 symboles d'accord pour tout le solo) : ils font 55 % des mesures valides. Leur accord est propagé, donc leurs mesures sont valides, mais ils gonflent la part de mesures à un seul accord (82 %) et ne donnent presque aucun changement d'accord : les parts « au changement » reposent sur 12 solos seulement.
- 4 solos n'ont aucune mesure valide : 3 n'ont aucune mesure en 4/4 (deux en 9/4, un en 3/4 : 141 mesures non 4/4, 11,5 % du sous-ensemble) et `Pop Tune #1` (melid 82) n'a aucune basse annotée : ses 140 mesures sont toutes les mesures « sans basse » du sous-ensemble (11,5 %).
- Tempos de 84 à 159 BPM (médiane 117,8) : aucune mesure à 180 BPM ou plus, les deux classes hautes sont vides ; `< 120` (12 solos, 10 avec mesures) est « juste », `120–180` (8 solos dont 6 avec mesures) « trop peu ».
- Style `FUSION` pour les 20 solos, 1969–2009, de souffleurs (sax ténor 10, sax alto 5, trompette 5) sur des morceaux fusion/funk ; les syncopes d'une basse funk sont des croches ou doubles-croches : non observables ici.

## Exploitable pour le moteur / non exploitable

- Distribution globale des notes, intervalles (médiane 2, p90 10), registre et approches d'une basse jazz-fusion : indications avec IC larges (arrivée sur la basse au changement 45 %, IC 34–63 %).
- Les 12 solos à forme écrite et les 8 solos sur vamp peuvent être séparés au besoin à partir de `composition_form` du manifeste.
- NON exploitable : tout le caractère funk (syncopes en croches/doubles-croches, notes fantômes, répétitions rythmiques précises) ; un réglage par tempo.
- Exploitables : parts et centiles de la marche de basse au temps (arrivées, approches du 4ᵉ temps, notes de passage, intervalles, registre), rythme harmonique (accords par mesure), motifs de répétition de hauteur par mesure, tempos et formes, avec leurs IC par solo.
- Non exploitables : tout ce qui est plus fin que la noire (croches, anticipations, durées réelles des notes), les silences de basse, la dynamique et les timbres, les phrases ou suites de notes (non conservées).
- Un indicateur dont l'IC est absent ou très large (voir le tableau) ne sert pas de cible chiffrée.
