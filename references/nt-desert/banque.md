# G6 — Banque SoundFont `nt_desert`

## Livrable et décision d'écoute

Banque construite dans le labo, sans modification du code ni du README du moteur :
`/Users/william.quintal/Project/bascanada/harmonium/assets/nt_desert.sf2`.
**3 351 554 octets**, 6 presets, 24 échantillons mono PCM16 à 44,1 kHz.

SHA256 de la SF2 :
`3ee78dc2ec83120d6fe2b217a7e99ecc5843e351dbe8b6f7464e266d69a5d397`.
Deux constructions depuis les WAV vérifiés donnent le même binaire.

Décision du propriétaire intégrée : la pédale grave de *Fläshyn* est une **scie
tenue**, pas une guitare GM 30. Les programmes **81 et 38** sont des scies à
saturation légère, bouclées avec sustain plein. **Aucun preset GM 30**.
La piste de basse des MIDI G0 reste en programme 38 ; une variante d'écoute du
mix avec cette piste en 81 est aussi disponible, sans changer les notes G0.

La tenue est démontrée par mesure, pas seulement par la présence de générateurs
SF2. La ressemblance globale avec la bande originale reste à juger à l'oreille :
les mesures montrent encore un déficit important de brillance dans *Fläshyn*.

## Sources et licences

- [Manifeste](../../samples/nt_desert/manifest.jsonl) : une ligne par échantillon,
  avec `source`, `author`, `license`, paramètres de synthèse, affectation MIDI,
  enveloppe, fenêtre de boucle et SHA256 **du WAV préparé**.
- [Métadonnées](../../samples/nt_desert/bank.json) : nom affiché et notice SF2.
- Auteur des échantillons : `harmonium_lab`. Tous sont créés dans le labo par
  synthèse procédurale numpy, sans téléchargement et **sans aucun prélèvement de
  l'OST, de stems, de GeneralUser, ni d'une autre banque**.
- Échantillons produits : **CC0-1.0**, utilisables et redistribuables commercialement
  ([texte de la dédicace](https://creativecommons.org/publicdomain/zero/1.0/)).
  Les dépendances de calcul gardent leurs licences propres ; ce ne sont pas des
  sources d'échantillons. La banque ne contient que le PCM calculé et les tables SF2.
- Référence d'analyse seulement : *Nuclear Throne OST*, Jukio Kallio / Vlambeer,
  2015 ; publication officielle du compositeur
  <https://www.youtube.com/watch?v=Jk5jogaEsz8>. Provenance et droits dans
  `corpus/nuclear_throne/manifest.jsonl` et le [rapport G0](README.md).
  Enregistrements, stems, transcriptions et rendus restent hors versionnement.
- GeneralUser GS, S. Christian Collins : témoin de comparaison uniquement,
  non incorporé dans la banque. Licence commerciale explicite et source dans
  `samples/fiddles/manifest.jsonl`. SHA256 du témoin :
  `9575028c7a1f589f5770fccc8cff2734566af40cd26ed836944e9a5152688cfe`.

## Affectations et choix de timbres

Tous les programmes ci-dessous sont **0-indexés**. Cette banque n'est pas une
banque GM complète : G7 doit sélectionner ces presets et ces touches de batterie.

| Banque / programme | Timbre | Construction / rôle |
|---|---|---|
| 0 / **81** | Sawtooth Hold | Scie principale à 90 %, quatre scies légèrement désaccordées à 2,5 % chacune ; saturation `tanh`, présence, boucle. Pédale grave ou lead ; samples E1, E2, C4, C5. |
| 0 / **38** | Saw Bass Hold | Même recette de scie, corps sinusoïdal à la fondamentale et saturation un peu plus forte ; pas d'enveloppe décroissante. Samples E1, E2, E3. |
| 0 / **78** | Whistle Lead | Sinus + harmoniques, souffle filtré, petit scoop et vibrato ; alternative de motif aigu, non employée dans les quatre MIDI de preuve. |
| 0 / **88** | Warm Pad | Ensemble de scies, octave/quinte, souffle discret et filtre chaud ; attaque 80 ms, release 600 ms. |
| 0 / **89** | Dark Warm Pad | Variante plus sombre du pad, filtre 2,3 kHz ; attaque 120 ms, release 800 ms. Pas un balayage de filtre. |
| **128 / 0** | Dry Rock Kit | Percussions procédurales one-shot : membranes à chute de hauteur, timbre de caisse claire bruité, réseaux métalliques inharmoniques pour les cymbales. Saturation des frappes ; aucune réverbération gravée dans les samples. |

Touches du kit : **36 kick, 37 side stick, 38 snare, 41 tom grave, 45 tom médium,
48 tom aigu, 42 charleston fermé, 44 au pied, 46 ouvert, 49 crash, 51 ride**.
Les trois charlestons partagent `exclusiveClass = 1` : une nouvelle frappe coupe
la précédente. Les autres touches de batterie ne sont pas définies.

Les zones de tessiture ne se chevauchent pas. Les presets mélodiques couvrent
0–127 par transposition, mais la qualité aux extrêmes n'est pas validée ; les
registres de travail sont ceux de G0 (basse 26–44, accords 48–64, motif 64–72).
Une transposition éloignée change la couleur et la vitesse du vibrato.

Proposition d'affectation pour G7 : basse 38, pédale/lead 81, accords 88 (89 pour
un tapis plus sombre), percussion banque 128 programme 0. Le jeu charge cette
SF2 comme **banque principale**, sans banque de pieds dédiée qui détournerait le
routage des percussions. Aucun changement moteur n'est livré ici.

## Construction reproductible

Depuis le labo, après `make setup` :

```sh
make bank-sf2 BANK=nt_desert
# Destination explicite, si nécessaire :
make bank-sf2 BANK=nt_desert BANK_SF2=/chemin/harmonium/assets/nt_desert.sf2
```

La cible générique exécute `harmonium_lab.bank.prepare`, puis
`harmonium_lab.bank.build`, comme le modèle préparation → SF2 de `trad-sf2`.
Le nom vient de `BANK`, du dossier et des métadonnées : aucun nom de jeu dans
`src/harmonium_lab/bank/` ni dans la cible. `BANK_DIR` permet un dossier explicite.
La synthèse ne demande aucun accès réseau.

`prepare` resynthétise chaque recette et vérifie SHA256 + boucle contre le
manifeste : un ancien cache ne peut pas masquer un changement de code ou de
paramètres. `build` vérifie aussi les WAV préparés avant assemblage. Une empreinte
différente provoque une erreur, pas une substitution silencieuse. Pour inventorier
**volontairement** une modification de recette :

```sh
.venv/bin/python3 -m harmonium_lab.bank.prepare --root samples/nt_desert --inventory
make bank-sf2 BANK=nt_desert
```

`prepared/` est gitignoré. La sortie par défaut est `../harmonium/assets/<nom>.sf2`
si le dépôt moteur est voisin ; dans un worktree du labo, le checkout principal
est résolu pour retrouver ce même dépôt. Sinon, repli explicite sur `target/`.
`assets/*.sf2` est déjà gitignoré dans le moteur ; aucune modification de son
`.gitignore` n'est nécessaire.

Environnement de preuve : macOS arm64, Python **3.14.7**, numpy **2.5.4**, soundfile
**0.14.0** / libsndfile **1.2.2**, librosa **1.0.0**, FluidSynth **2.5.3**.
Les empreintes PCM sont vérifiées dans cet environnement ; sur une autre pile
numérique, toute divergence sera signalée, non acceptée automatiquement.

## Preuve de tenue

Note G#1 (MIDI **32**) tenue pendant environ 6 s, vélocité 100, rendu FluidSynth
avec la banque. Mesure RMS en dBFS par fenêtres de **0,5 s** entre 0,25 et 5,75 s :
attaque écartée, **release et silence après NoteOff exclus**. Chaque WAV est
normalisé au pic 0,125 ; cela ne change pas les différences de RMS en dB.
Le critère exige moins de 3 dB ; on vérifie même l'excursion entre toutes les
fenêtres, plus stricte qu'une simple comparaison début/fin.

| Programme / note | Chute depuis la première fenêtre | Excursion max–min | Résultat |
|---|---:|---:|---|
| 38 / G#1 (32) | 0,00 dB | **0,01 dB** | Passe |
| 81 / G#1 (32) | 0,00 dB | **0,02 dB** | Passe |
| 81 / E4 (64) | 0,06 dB | **0,07 dB** | Passe |

Les valeurs de **chaque** fenêtre sont dans
[`banque-mesures.json`](banque-mesures.json), section `sustain`. Les WAV sont dans
`target/bank_compare/tenue_<programme>_<note>.wav`.
La première note de basse de `02_flashyn_full_loop_A.mid`, isolée sans modifier
sa hauteur, sa vélocité ni sa durée (**4,953 s**), donne également une excursion
**0,02 dB en 38 / 0,03 dB en 81** (`g0_isolated_pedal` dans le JSON).

L'essai initial a révélé un battement excessif dans l'aigu avec cinq oscillateurs
à poids égaux. Le centre dominant corrige cette cause, sans changer le seuil du
test. Les tests vérifient aussi que la note s'éteint après NoteOff : une tenue
infinie qui ignorerait les relâchements ne satisfait pas le contrat.

## Rendus G0 et mesures audio

Dossier d'écoute, hors dépôt :
`/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/nuclear_throne/transcriptions/`.

Pour chacun des quatre stems de fichier demandés, trois WAV sont côte à côte :
`<stem>_GeneralUser.wav`, `<stem>_nt_desert.wav`, `<stem>_original.wav`.
Les deux premiers viennent de FluidSynth, le dernier est la coupe de l'original ;
les trois sont normalisés au pic 0,125 pour l'écoute. Les anciens `<stem>.wav` de
G0 sont laissés intacts. Variante supplémentaire :
`02_flashyn_full_loop_A_pedal81_nt_desert.wav` (seul le programme de basse passe de
38 à 81). Ni les MIDI de départ ni les FLAC ne sont modifiés.

Reproduire les deux rendus et le rapport depuis ce worktree (`CORPUS` désigne le
corpus local du checkout principal ; chemins passés comme arguments, pas en code) :

```sh
CORPUS=/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/nuclear_throne
SF2=/Users/william.quintal/Project/bascanada/harmonium/assets/nt_desert.sf2
make bank-compare BANK_SF2="$SF2" COMPARE_ARGS="--tracks $CORPUS/tracks \
  --midis $CORPUS/transcriptions/02_flashyn_full_loop_A.mid \
  $CORPUS/transcriptions/02_flashyn_bass_riff_D.mid \
  $CORPUS/transcriptions/02_flashyn_drums_groove.mid \
  $CORPUS/transcriptions/19_a_way_pedal_A.mid \
  --sustain 38:32:6 --sustain 81:32:6 --sustain 81:64:6"
```

Le rapport brut est `target/bank_compare/report.json`. Le dérivé versionné
[`banque-mesures.json`](banque-mesures.json) garde les mesures, empreintes des MIDI,
empreintes des banques et méthode, sans transcription ni audio.

Méthode : `audioref.measures.measure_track` → `audio.py`, mono 22 050 Hz.
Chaque rendu est mesuré **sur la durée de la coupe source**, sans sa queue de
release. Centroïde et rolloff 85 % caractérisent la brillance. `CV RMS` = écart-type
/ moyenne des RMS par trame, indépendant du gain ; une valeur basse indique une
énergie plus stable. Les RMS ci-dessous sont ramenés au même pic 0,125 **dans la
fenêtre analysée**. Le JSON garde aussi RMS bruts, platitude et plage dynamique.

| Boucle / version | Centroïde (Hz) | Rolloff (Hz) | RMS moyen, pic égal | CV RMS | Plage dynamique (dB) |
|---|---:|---:|---:|---:|---:|
| Fläshyn mix A — original | 3309 | 6908 | 0,0385 | 0,145 | 6,97 |
| Fläshyn mix A — GeneralUser | 1466 | 3292 | 0,0244 | 0,351 | 13,65 |
| Fläshyn mix A — **nt_desert** | **1536** | **3147** | **0,0308** | **0,141** | **10,37** |
| Riff D — original (mix complet) | 3150 | 6774 | 0,0409 | 0,107 | 5,20 |
| Riff D — GeneralUser (basse seule) | 512 | 1085 | 0,0353 | 0,253 | 31,45 |
| Riff D — **nt_desert** (basse seule) | **521** | **1096** | **0,0519** | **0,280** | **61,06** |
| Groove — original (mix complet) | 3309 | 6908 | 0,0385 | 0,145 | 6,97 |
| Groove — GeneralUser (batterie seule) | 2887 | 5962 | 0,0239 | 0,888 | 57,14 |
| Groove — **nt_desert** (batterie seule) | **2638** | **4570** | **0,0302** | **0,842** | **63,74** |
| A Way pédale A — original | 1197 | 2281 | 0,0113 | 0,988 | 80,00 |
| A Way pédale A — GeneralUser | 483 | 734 | 0,0274 | 0,437 | 13,80 |
| A Way pédale A — **nt_desert** | **1052** | **2109** | **0,0384** | **0,153** | **13,89** |

## Interprétation, limites et quoi écouter

1. **Pédale qui ne disparaît plus.** Écouter `02_flashyn_full_loop_A`, surtout
   entre 0,5 et 4,9 s du WAV (original **2,267–9,124 s**). Comparer les versions
   38 et `pedal81` : présence continue et grain de scie, sans rajouter d'attaques
   ni de notes pour masquer la décroissance signalée par le propriétaire.
2. **Action encore trop sombre.** Le centroïde du mix reste autour de 1,54 kHz
   contre 3,31 kHz dans l'original. Le CV RMS du mix se rapproche, mais cela ne
   démontre pas un timbre identique. Le kit seul est même moins brillant que le
   témoin GeneralUser selon le rolloff : ne pas revendiquer une amélioration
   générale de brillance. Écouter le claquement de caisse claire, le kick et la
   place du charleston ; G0 contient seulement 30 frappes dans ce groove et ne
   restitue pas tout le charleston continu de l'enregistrement.
3. **Riff D** : original **15,981–22,838 s**. Juger l'articulation D/D#, la masse
   grave et les trous entre notes, pas la distance spectrale d'une basse seule à
   un mix complet. La grande plage dynamique du rendu vient des silences et des
   releases courtes entre les notes ; ce n'est pas une perte de sustain pendant
   la pédale. Le kit synthétisé n'est pas une batterie acoustique échantillonnée.
4. **A Way**, original **0–8 s** : la nappe gagne en brillance (1052/2109 Hz contre
   1197/2281 Hz dans l'original), mais reste trop constante. La coupe originale
   a une forte montée de niveau ; un pad à sustain plein ne reproduit ni cette
   automation ni le traitement d'espace. La plage de 80 dB est le plafond de
   l'analyse librosa, pas une mesure de dynamique utile de toute la composition.
5. **Limites de transcription.** Les MIDI G0 sont inchangés, avec vélocités et
   gate déjà fixés. Les parties isolées sont comparées au mix original, pas à des
   stems réputés purs. Harmonie, voicings, rythmes, mixage et mastering ne sont
   pas corrigés par cette tâche. Aucun score de ressemblance global ni validation
   d'écoute du propriétaire n'est revendiqué.

## Vérifications exécutées

- `make bank-sf2 BANK=nt_desert` : synthèse hors réseau, vérification des 24 SHA256,
  assemblage et dépôt dans les assets du moteur ; reconstruction identique.
- Rendu FluidSynth des quatre MIDI demandés avec les deux banques, et de la
  variante pédale 81 ; mesures sur les fenêtres source, ci-dessus.
- Les 11 touches définies du kit ont chacune été rendues isolément ; le rendu
  d'écoute de contrôle est `target/bank_smoke/kit.wav`.
- Tenues et NoteOff des programmes 38/81 dans le grave et l'aigu ; régression
  conservée pour le battement excessif de 81/E4.
- `make test` : **275 réussis, 31 ignorés**, 7 avertissements librosa/numba dans
  les tests audio existants. Les 9 nouveaux cas G6 passent, sans dépendance aux
  transcriptions ni aux FLAC locaux. Empreintes altérées, recettes modifiées,
  chevauchements de zones et boucles hors limites sont rejetés.

## Note à reporter dans `harmonium/assets/README.md` — non appliquée

> `nt_desert.sf2` : banque du désert construite par `harmonium_lab` avec
> `make bank-sf2 BANK=nt_desert`. Échantillons entièrement procéduraux CC0-1.0,
> provenance et SHA256 dans `samples/nt_desert/manifest.jsonl` du labo. Banque 0 :
> scies tenues 38/81, sifflement 78, nappes 88/89 ; banque 128 programme 0 : kit
> rock sec (36, 37, 38, 41, 42, 44, 45, 46, 48, 49, 51). Fichier gitignoré,
> banque principale du jeu, pas banque de pieds. Voir le compte rendu
> `references/nt-desert/banque.md` du labo pour les mesures et limites.
