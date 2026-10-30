# Références Depths — *The Binding of Isaac* (Ridiculon)

Analyse intégrale d’**Abyss / The Depths**, avec **When Blood Dries / Necropolis** et **Puslo Profundum / Dank Depths** comme contexte. Méthode : mesures du mix entier, hypothèses métriques comparées, énergie des stems, chroma par mesure, répétitions, transcription automatique et propositions de **données** pour `isaac_depths`. Aucun profil moteur n’est installé ici.

**Provenance et droits.** Ridiculon (Matthias Bossi, Jon Evans), Rebirth / Afterbirth ; compilation de fan MegaSamantha, « The Binding of Isaac: Repentance - Full OST (HQ) », 2021-04-21. [Source](https://www.youtube.com/watch?v=pSO4td4rdRI), extraits selon le manifeste : Abyss **983–1216 s**, When Blood Dries **4615–4862 s**, Puslo Profundum **7945–8216 s**. Tous les minutages ci-dessous sont **locaux à l’extrait**, pas à la compilation. Droits réservés : analyse et inspiration seulement.

Racine privée **absolue**, hors de ce worktree :
`/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac`.

- Mix : `tracks/06_abyss.flac`, `tracks/23_when_blood_dries.flac`, `tracks/40_puslo_profundum.flac`.
- Stems de la principale, déjà séparés une seule fois par `htdemucs` sur MPS : `stems/htdemucs/06_abyss/{bass,drums,other,vocals}.wav`.
- MIDI, WAV et JSON de transcription : `transcriptions/06_abyss_depths_*.{mid,wav,json}`.

**Seuls `README.md`, `measures.json`, `grids.json` sont livrés dans ce dossier.** Ni enregistrement, ni stem, ni transcription sous droits n’est versionné. Il n’y a pas eu d’audition humaine de contrôle pendant cette analyse : les descriptions de timbres sont des hypothèses, pas des identifications certaines.

## 1. Mesures entières et contexte des 25 zones

`measures.json` conserve les **25** pistes `type=zone`, leurs métadonnées et les statistiques `context`, avec nos trois grilles sous `tracks.<id>.grid`. Il réutilise sans recalcul la mesure fraîche commune, terminée avec succès en 254,73 s ; seules ces grilles y sont ajoutées.

| Mesure | Abyss | When Blood Dries | Puslo Profundum | 25 zones : moyenne ± écart-type |
|---|---:|---:|---:|---:|
| Durée (s) | 233 | 247 | 271 | — |
| Tempo brut `beat_track` (BPM) | 95,7 | 117,5 | 95,7 | 114,71 ± 29,93 |
| Tempo de grille (BPM noire) | **95** | **120** | **95** | — |
| Attaques (/s) | 2,07 | 1,74 | 2,36 | 1,862 ± 0,636 |
| Stabilité brute du tempo | 0,9452 | 0,9737 | 0,9665 | 0,9709 ± 0,0096 |
| Force tonale | 1,7956 | 1,9052 | 1,4268 | 1,6503 ± 0,3543 |
| Entropie chromatique (bits) | 3,4594 | 3,4693 | 3,5228 | 3,5098 ± 0,0391 |
| Centroïde spectral (Hz) | **1239,75** | **1449,97** | **1099,33** | 1988,83 ± 481,99 |
| Rolloff 85 % (Hz) | 2794,93 | 3111,06 | 2154,91 | 4336,82 ± 1030,77 |
| Platitude spectrale | 0,003524 | 0,004205 | 0,002968 | — |
| RMS moyen | **0,044279** | 0,068838 | 0,066548 | 0,0898 ± 0,0243 |
| Étendue RMS (dB) | 80,00 | 73,51 | 80,00 | 75,73 ± 8,53 |
| Énergie HPSS harmonique / percussive | 84,37 / 15,63 % | 87,40 / 12,60 % | 82,97 / 17,03 % | 85,15 / 14,85 % |

Les trois Depths sont nettement **sombres spectralement** : centroïdes de 1099 à 1450 Hz, contre 1989 Hz en moyenne. Abyss se trouve à −1,55 écart-type de centroïde et son RMS moyen est le **minimum des 25 zones**. Cela ne signifie pas une orchestration vide : son stem batterie est énergétiquement fort mais concentré dans le grave. Necropolis est plus tonale et moins percussive selon HPSS ; Dank Depths a davantage d’attaques, mais une tonalité globale moins concentrée.

**Précautions métriques.** La part percussive HPSS mesure la séparation d’énergie harmonique/percussive, **pas** la proportion réelle de batterie. Le nombre d’attaques ne mesure ni le nombre d’instruments ni la densité de notes. `dynamic_range_db` est `max(rms_db) - min(rms_db)` avec plancher numérique : les 80 dB d’Abyss/Dank Depths sont dominés par les amorces, fondus et quasi-silences de compilation, **pas une plage EBU/LUFS** ni un contraste musical de 80 dB.

## 2. Calage métrique, tonique et ambiguïtés

### 2.1 Tempo et division

| Paramètre | Abyss | When Blood Dries | Puslo Profundum |
|---|---|---|---|
| Pulsation retenue | 95 BPM, 0,631578947 s | 120 BPM, 0,5 s | 95 BPM, 0,631578947 s |
| Mètre de travail | 4/4 | 4/4 | 4/4 |
| Croche / double-croche | 0,315789 / 0,157895 s | 0,25 / 0,125 s | 0,315789 / 0,157895 s |
| Origine locale | 0,110375 s | 0,125100 s | 0,439843 s |
| Mesures complètes | 92 | 123 | 107 |
| Fin de ces mesures | 232,742 s | 246,125 s | 270,966 s |
| Résidu de régression brute | 51,41 ms | 7,23 ms | 26,28 ms |
| Cohérence `R_beat/2` | 0,1607 | 0,7097 | 0,1539 |
| Cohérence `R_beat/3` | 0,0928 | 0,0515 | 0,0210 |
| Cohérence `R_beat/4` | **0,5335** | **0,8456** | **0,8975** |
| Dérive phase double-croche, début→fin | +5,34 ms | −0,84 ms | −2,18 ms |

Régression sur toute la batterie séparée pour Abyss, sur tout le mix pour les deux variantes ; contrôle indépendant sur les premières et dernières **60 secondes**. Les périodes sont stables malgré des placements très syncopés : le résidu de 51 ms d’Abyss est celui du suivi de battements, **pas** une dérive de tempo de 51 ms à chaque mesure.

Les demi/doubles tempos ont été comparés explicitement : **47,5 / 95 / 190**, **60 / 120 / 240** et **47,5 / 95 / 190 BPM**. Pour Abyss à 190 BPM, la cohérence de croche est 0,5341, correspondant précisément à la double-croche à 95 ; cela ne démontre pas un tempo musical de 190. À 47,5 BPM la division binaire est peu concentrée (0,0871). Le ternaire perd nettement face à la double-croche ; aucune nécessité de 12/8. Pour Necropolis, l’autocorrélation à quatre noires atteint **0,5676**, contre 0,4067 à trois. Pour Abyss/Dank Depths les pics à deux et quatre temps sont proches (0,3034/0,3196 et 0,4471/0,4539) : **4/4 reste une hypothèse de regroupement**, pas un résultat incontestable d’autocorrélation.

**Confiance :** haute sur la période et la division binaire ; moyenne sur 4/4 ; **faible à moyenne sur le premier temps musical**. Pour Abyss l’origine est la phase de double-croche et une convention de numérotation reproductible ; des décalages d’un pas ou d’un temps restent possibles à l’audition. Le score d’appui grave a plusieurs maxima concurrents. Les fichiers n’occultent pas cette ambiguïté : `confidence.downbeat` et `scores.window_coherence` la conservent dans `grids.json`. Les tableaux structurels et les transcriptions utilisent cette convention, sans prétendre à une partition éditée.

### 2.2 Centre grave local contre gabarit global

- **Abyss :** le chroma global choisit **C# mineur harmonique**, score 0,8206, marge 0,0159 sur D majeur. Mais le suivi de basse entier donne **530 doubles-croches D** contre **329 C#**, puis C 95, D# 44, G 42. D et C# occupent ensemble **69,3 % des cellules effectivement voisées**, et la fin est dominée par D. Un centre grave **D avec voisin inférieur C#**, passages C naturel et D#, explique mieux le rôle de la basse que le seul nom du gabarit global. À tonique D imposée, le gabarit hésite D majeur 0,8048 / D mineur harmonique 0,7967 : **tierce majeure/mineure non décidée** par cette méthode. Proposition stylistique : D mineur harmonique chromatisé, **choix de composition**, non certitude de transcription.
- **When Blood Dries :** clé estimée D ; gabarits **C dorien et D phrygien exactement à égalité** (0,8356, marge 0). Les chromas D=0,9419 et D#=0,8402 rendent plausible un pôle D et une seconde mineure. Sans basse séparée ni audition, **D phrygien reste une hypothèse**, pas une tonique basse mesurée.
- **Puslo Profundum :** clé estimée C#, mais meilleur mode **C mineur harmonique**, score 0,8394, marge 0,0068 sur C# majeur. C#=0,7182, D=0,7034 et C=0,6459 sont proches : **centre ambigu C/C#/D**, ne pas généraliser le D d’Abyss à toute la famille.

Le corpus de contexte comporte 17 étiquettes mineur harmonique, 4 majeur, 2 dorien, 2 phrygien. Ces comptes sont des résultats de gabarits, non une expertise harmonique définitive.

## 3. Structure complète d’Abyss

Mesures **0-based**, intervalles `[début, fin)`. La nouveauté harmonique automatique ne segmente pas la piste : le chroma reste très homogène. Il faut croiser les énergies des stems, pas inventer des changements d’accords à partir de la seule auto-similarité.

Une **période longue de 44 mesures = 111,158 s** ressort nettement : corrélations de RMS par mesure au décalage 44 de **0,843 basse**, **0,732 other**, **0,749 vocals**. Le meilleur score chromatique corrigé du fond est aussi à 44, mais faible (**+0,016**, très inférieur au seuil indicatif 0,15). Des cosinus chromatiques voisins de 0,99 à d’autres décalages ne prouvent donc pas une copie littérale : une texture presque statique les produit déjà.

| Bloc analytique | Mesures | Temps source | Évidence et interprétation prudente |
|---|---:|---:|---|
| Amorçage | avant 0 | 0–0,110 s | Presque silencieux ; RMS bass 0,0000039, drums 0,0000766, other 0,0001009. Pas de levée mélodique affirmée. |
| A — installation | 0–8 | 0,110–20,321 s | Batterie grave immédiate ; basse et nappe s’épaississent à 4–8 (RMS basse 0,0168→0,0274 ; other 0,0088→0,0173). |
| B — mouvement chromatique | 8–16 | 20,321–40,531 s | Basse C#/D avec passages C/D# ; petit maximum `vocals` à 12–16 (0,00395), insuffisant pour conclure « chœur ». |
| C — plateau pulsé | 16–24 | 40,531–60,742 s | Batterie quasi constante (RMS 0,0377–0,0380), variations du grave et de la texture, pas de break complet. |
| D — relance de texture | 24–32 | 60,742–80,952 s | Batterie 0,0394–0,0404 ; other augmente 0,0083→0,0136. Boucle représentative extraite. |
| E — plateau médian | 32–44 | 80,952–111,268 s | Nappe plus présente à 32–36 (other 0,01624), puis retour au tapis pulsé ; aucune cadence tonale certaine. |
| Retour du cycle long | 44–88 | 111,268–222,426 s | Même trajectoire globale en 44 mesures : maximum de basse 48–56, épisodes de texture 56–64 et 76–84. Variations d’orchestration, **pas copie audio exacte déclarée**. |
| Dissipation | 88–92 | 222,426–232,742 s | Basse 0,00117, batterie 0,00308, other 0,00436 en moyenne : chute d’énergie et fin sur résidu tonal D. |
| Queue d’extrait | après 92 | 232,742–233,000 s | Basse/vocals nuls ; drums RMS 0,0000482, other 0,0000067 : résidu de séparation quasi silencieux, pas d’accord supplémentaire revendiqué. |

Longueurs utiles : **4 mesures** pour les variations de batterie/timbre ; **8 mesures** pour comparer les cellules ; **44 mesures** pour le cycle d’arrangement. Il serait trompeur d’annoncer une boucle harmonique certaine de 4 ou 8 mesures. La proposition moteur §7 remplace volontairement ces 44 mesures par une arche originale plus courte et explicite.

## 4. Instrumentation probable et choix de rendu

Signatures globales des quatre stems d’Abyss, calculées sur toute leur durée :

| Stem / rôle probable | RMS | Centroïde (Hz) | Platitude | Interprétation / GM **0-based** |
|---|---:|---:|---:|---|
| `bass` | 0,02113 | 413,53 | 0,00454 | Grave riche en harmoniques, basse électrique/synthétique sombre. **38 Synth Bass 1**, ou **33 Electric Bass (finger)** si l’attaque l’exige à l’écoute. Octave D1/D2 incertaine. |
| `drums` | **0,03537** | **456,11** | 0,00242 | Pulses très graves, toms / percussion traitée / grosse caisse probables ; **pas** une preuve de kit rock clair. Kit GM canal 10, **36 Bass Drum 1**, toms **41/43/45** comme candidats d’écoute. |
| `other` | 0,01345 | 2206,99 | 0,01866 | Lit médium sombre avec traînées et attaques diffuses : nappe/orgue/guitare traitée indécidables. **91 Pad 4 (choir)** ou **89 Pad 2 (warm)** ; **18 Rock Organ** seulement si confirmé. |
| `vocals` | 0,00178 | 3194,02 | 0,07003 | Stem faible et bruité ; fuite d’aigus ou texture plutôt qu’un chœur démontré. **52 Choir Aahs** pour matérialiser le suivi expérimental, non pour certifier un instrument original. |

Le RMS de `vocals` n’est que 8,4 % de celui de `bass` ; ses notes ne justifient ni solo aigu continu ni sifflement. Aucun GM30, Phazzy Organ, ni Sausage Bassener n’est proposé. **GM18** est Rock Organ (et non 19, qui est Church Organ) ; les numéros sont ici tous 0-based.

Presets Odin **constatés comme fichiers plats** dans `/Users/william.quintal/Project/bascanada/odin-presets` : `Bass Crusher [RM].odin`, `Bass Low [RM].odin`, `Growly FM Bass [XR].odin`, `Haunt [RM].odin`, `Moonshade.odin`, `Eerie Pad.odin`. Les noms TOML sont les mêmes **sans extension**, sans sous-dossier fictif. Pas de copie de preset dans le dépôt. Les niveaux et morphings §7 sont des réglages proposés **non auditionnés**, pas des compensations de volume mesurées.

## 5. Transcription entière, boucles et preuves d’exécution

L’appel CLI unique a analysé les **233 secondes** une fois pour basse, percussion, lead et accords ; six jeux MIDI+WAV+JSON ont été produits avec succès en **22,17 s**, puis deux fenêtres supplémentaires ont été découpées depuis le sidecar intégral par les API existantes, sans second pyin, et rendues en **2,84 s**. FluidSynth + GeneralUser GS a ramené chaque pic à **0,125**. Aucun test de qualité musicale n’est assimilé à ces rendus.

### Couverture de la totalité de l’extrait

L’export décale l’origine d’**une mesure en arrière**, à **−2,415940572 s** : la mesure d’export `b+1` correspond à la mesure analytique `b`. Le fichier `depths_full`, mesures d’export `0:94`, couvre **−2,416 à 235,058 s**, donc toute la source **0–233 s**, avec **2,416 s de cadrage avant** et **2,058 s après**. Ce ne sont pas des secondes d’audio originales supplémentaires. L’amorce 0–0,110 s est incluse, de même que le fondu et la queue 232,742–233 s.

Le calcul d’accords CLI s’arrête aux mesures complètes (dernière fin à 232,742 s). La queue réelle restante a été mesurée : basse/vocals nulles, other RMS 0,0000067 (≈ −103,5 dBFS), batterie 0,0000482 (≈ −86,3 dBFS). **Pas de contenu harmonique significatif laissé sans transcription** ; aucun accord artificiel n’est ajouté sur ce résidu. Le MIDI représente des événements détectés, pas une reconstruction des bruitages, réverbérations et filtres continus de l’enregistrement.

| Suffixe après `06_abyss_` (chaque fois `.mid`, `.wav`, `.json`) | Mesures analytiques | Temps source couvert | Contenu / confiance |
|---|---:|---:|---|
| `depths_full` | entière + cadrage | source **0–233 s** ; export −2,416–235,058 | Quatre rôles, 638 segments de basse et 588 attaques détectés sur l’analyse entière. |
| `depths_intro` | 0–8 | 0,110–20,321 | Installation du grave et du tapis ; basse moyenne, accords faibles. |
| `depths_cycle` | 8–16 | 20,321–40,531 | Voisinage C#/D et incursions D# ; grille détaillée §6. |
| `depths_bridge` | 24–32 | 60,742–80,952 | Relance de texture ; extrait API depuis full. « bridge » = nom de fichier, pas preuve d’un pont harmonique. |
| `depths_middle` | 32–40 | 80,952–101,163 | Nappe médiane et basse syncopée. |
| `depths_reprise44` | 44–52 | 111,268–131,479 | Premier retour du cycle long ; extrait API depuis full. |
| `depths_return` | 72–80 | 182,005–202,216 | Retour tardif de matériau, pas première reprise. |
| `depths_final` | 80–92 + queue | 202,216–233,000 ; export jusqu’à 235,058 | Descente d’énergie et fin ; notes isolées de pyin dans le fondu à traiter comme suspectes. |

**Confiance mesurée :** basse `voiced_ratio=0,6686`, lead `0,2804`, accords `mean_score=0,725`, racine la plus fréquente C# sur seulement `20,4 %` des mesures. Le détecteur de batterie retourne `mean_margin=0,611`, `low_margin_rate=0`, mais classe **les 588 attaques en kick** ! Cela révèle un biais des règles spectrales sur cette percussion grave ; une forte marge ne garantit pas la bonne identité instrumentale. Positions rythmiques exploitables, séparation kick/snare/hat **non résolue**. Le lead faible reste expérimental, et le lissage d’octaves peut transformer des harmoniques de basse en notes D2. Les statistiques de confiance CLI portent sur **toute la piste**, même lorsqu’elles sont recopiées dans un petit sidecar de boucle.

Le processus a émis un avertissement numérique Numba (`invalid value encountered in cast`), puis s’est terminé avec succès et a écrit/rendu les six jeux. Il n’est ni masqué ni présenté comme preuve d’échec musical ; les limites de pyin demeurent celles ci-dessus.

## 6. Grilles détaillées : basse, batterie, accords

Seize doubles-croches par mesure, positions `0..15`. Les sidecars d’export stockent des positions **absolues** ; retirer `16 × (barre analytique + 1)` pour lire la position locale. Degrés chromatiques depuis **D** : D=0, D#=1, E=2, F=3, F#=4, G=5, C=10, C#=11. Les silences sont l’absence de cellules voisées, pas des notes inventées.

### 6.1 Basse : relevé automatique exact, non nettoyé

Notation `position:note/durée_en_pas`. Les notes d’un seul pas et les sauts d’octave sont moins fiables que le pôle global D/C#.

```text
mes. 0 : 0:F1/1, 2:D1/1, 3:C#1/1, 4:D1/5,
         10:D1/1, 12:D1/1, 14:D1/1, 15:E1/1
mes. 8 : 0:C#1/1, 2:C#1/2, 5:C#1/2, 7:C1/1, 8:C#1/1,
         9:C1/2, 11:D1/1, 12:C1/1, 13:G#0/1
mes.10 : 0:C1/1, 1:D1/1, 2:C#1/2, 4:F#1/1, 5:E1/1,
         6:D#1/1, 7:D1/1, 8:D#1/4, 12:D1/2, 14:E1/1, 15:D1/1
mes.14 : 0:B1/1, 1:D2/1, 2:C2/1, 3:D2/1, 4:G1/1,
         5:C#2/2, 8:C#2/1, 10:D2/1, 11:C#2/2, 13:D2/3
```

Cellule robuste à retenir comme inspiration : **D tenu/réarticulé, voisin inférieur C#, parfois C ; D# comme frottement supérieur**, sans recopier chaque micro-segment du détecteur. La mesure 8 penche vers C#, les 9–11 et 14 vers D/D#, ce qui exclut de résumer toute la piste par une seule basse D immobile.

### 6.2 Batterie : vote réel sur mes. 8–15

Nombre de mesures (sur huit) ayant au moins une attaque à la position :

```text
pos.       0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
attaques   4  3  1  3  1  4  0  2  3  7  2  5  1  6  2  6
vote       x  .  .  .  .  x  .  .  .  X  .  x  .  X  .  X
```

`X` = au moins 6/8 ; `x` = 4 ou 5/8. Tous ces événements portent l’étiquette automatique `kick` ; **ne pas fabriquer des lignes snare/hat d’après ce résultat**. Les positions impaires 9/13/15 montrent le décalage des attaques par rapport à la convention d’origine ; c’est aussi une raison de conserver une confiance modérée sur le premier temps. En proposition §7, déplacer cette poussée vers 8/12/14 est une **réécriture assumée**, non un « correctif » silencieux du relevé.

### 6.3 Accords par mesure : hypothèses de triades

Le détecteur ne compare que 24 gabarits majeurs/mineurs et doit choisir même sur un bourdon bruité ; il n’identifie ni accords slash, ni dyades, ni absence de tierce. Les noms suivants sont des **étiquettes de réduction**, pas une grille harmonique certifiée :

```text
mes.  0– 7 : | C#m | Dm | Cm | Cm | F#  | F#m | F#m | F#m |
mes.  8–15 : | C#m | A  | Cm | G# | C#m | Cm  | Cm  | G   |
mes. 24–31 : | G#  | Dm | Cm | A  | C#m | C#m | G   | Bm  |
mes. 32–39 : | F#m | F#m| F#m| Bm | F#m | Bm  | Bm  | Cm  |
mes. 44–51 : | C#m | Dm | Cm | Cm | F#m | F#m | F#m | A   |
mes. 88–91 : | Dm  | Dm | Dm | Dm |
```

La divergence entre ces racines, le chroma et le D/C# du grave interdit d’affirmer une progression fonctionnelle aussi mobile. Pour le profil inspiré, préférer pédales, dyades et rares paliers d’accords écrits explicitement, plutôt que sanctuariser les erreurs d’une transcription automatique.

## 7. Proposition originale de données `isaac_depths`

Schéma lu dans le **README actuel des profils moteur**, ainsi que les vrais `isaac_burning/profile.toml`, `feet.toml` et `cells.toml`. **Ne pas employer les anciens exemples Basement** avec `chords` directement sous une partie. Ce qui suit est une proposition d’écriture originale en D mineur harmonique à 95, inspirée du grave, du demi-ton et des cycles de texture, **distincte de la transcription**. Fragments TOML cohérents destinés aux sections correspondantes d’un nouveau profil ; aucune modification du dépôt moteur.

Arche de 32 mesures `P P C R`, deux tours possibles : P=8 mesures de pédale, C=8 mesures d’accords lents, R=8 mesures de retour sombre sans mélodie. Chaque alternative harmonique ci-dessous totalise **exactement huit mesures**. Mélodie/chœur discret dans C seulement ; pas de sifflement, pas de solo permanent. Les banques mélodiques sont des inventions courtes, pas des cellules extraites de l’original.

### 7.1 Forme, harmonie et banques de basse

```toml
[meta]
id = "isaac_depths"
name = "Depths de The Binding of Isaac — proposition"
tradition = "Ridiculon, Rebirth/Afterbirth — inspiration, non reproduction"
tags = ["isaac", "depths", "grave", "pedale"]
corpus = "harmonium_lab references/isaac-depths ; corpus privé Isaac, droits réservés"

[meter]
time_signature = { numerator = 4, denominator = 4 }
steps_per_bar = 16
steps_per_unit = 2
steps_per_pulse = 4
pulses_per_bar = 4
default_swing_ratio = 0.5
default_bpm = 95.0
min_bpm = 85.0
max_bpm = 110.0

[form]
sequence = [0, 0, 1, 2]
resolve = "per_tune"
repeat_variation = 0.10
tour_variation = 0.15
variation_operations = ["varied_end", "repeated_notes"]
avoid_adjacent = false
[[form.parts]]
name = "P"
melody_center_offset = 0
phrase_ends = [4, 8]
tracks_off = ["Melody"]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]
[[form.parts]]
name = "C"
melody_center_offset = -3
phrase_ends = [4, 8]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]
[[form.parts]]
name = "R"
melody_center_offset = 0
phrase_ends = [4, 8]
tracks_off = ["Melody"]
roles = ["Open", "Free", "Free", "Free", "Open", "Free", "Free", "Free"]

[melody]
cell_units = 8
strong_units = [0, 2, 4, 6]
weak_units = [1, 3, 5, 7]
key_modes = [{ key = 2, mode = "harmonic_minor", weight = 1 }]
[melody.params]
weight_role_run = 1
weight_role_arp = 0
weight_role_turn = 0
melody_center_midi = 62
tonic_midi_min = 50
tonic_midi_max = 62
tessitura_min = 50
tessitura_max = 72
base_velocity = 48
[melody.cells]
cells = [
  { role = "open", notes = "5 - - - 3 - - -", weight = 2 },
  { role = "open", notes = "1 - - - - - 7 -", weight = 1 },
  { role = "run", notes = "3 - - - 2 - 1 -", weight = 2 },
  { role = "run", notes = "5 - - - 7 - 8 -", weight = 1 },
]

[harmony]
model = "loop"
steps_per_chord = 16
default_bars_per_chord = 1
[harmony.parts.P]
kind = "pedal"
degree = 1
[harmony.parts.C]
kind = "chord_loop"
loops = [
  { weight = 3, chords = [
    { degree = 1, quality = "Minor", bars = 4 },
    { semitones = 8, quality = "Major", bars = 2 },
    { degree = 5, quality = "Major", bars = 2 },
  ] },
  { weight = 1, chords = [
    { degree = 1, quality = "Minor", bars = 2 },
    { degree = 4, quality = "Minor", bars = 2 },
    { semitones = 8, quality = "Major", bars = 2 },
    { degree = 1, quality = "Minor", bars = 2 },
  ] },
]
[harmony.parts.R]
kind = "chord_loop"
loops = [
  { weight = 2, chords = [
    { degree = 1, quality = "Minor", bars = 6 },
    { semitones = 1, quality = "Major", bars = 1 },
    { degree = 1, quality = "Minor", bars = 1 },
  ] },
  { weight = 1, chords = [
    { degree = 1, quality = "Minor", bars = 4 },
    { degree = 5, quality = "Major", bars = 2 },
    { degree = 1, quality = "Minor", bars = 2 },
  ] },
]

[accompaniment]
strong_steps = [0, 8]
strong_weight = 2
weak_weight = 1
tie_priority = ["I", "V", "IV"]
[accompaniment.bass]
low = 26
high = 37
[[accompaniment.bass.motifs]]
part = "P"
bars = 2
weight = 3
reference = "tonic"
notes = [
  { step = 0, duration = 8, semitones = 0, octave = 1, velocity = 88 },
  { step = 8, duration = 4, semitones = -1, octave = 1, velocity = 72, legato = true },
  { step = 12, duration = 12, semitones = 0, octave = 1, velocity = 84, legato = true },
  { step = 24, duration = 4, semitones = -2, octave = 1, velocity = 70, legato = true },
  { step = 28, duration = 4, semitones = -1, octave = 1, velocity = 76, legato = true },
]
[[accompaniment.bass.motifs]]
part = "P"
bars = 2
weight = 1
reference = "tonic"
notes = [
  { step = 0, duration = 12, semitones = 0, octave = 1, velocity = 86 },
  { step = 12, duration = 4, semitones = 1, octave = 1, velocity = 72, legato = true },
  { step = 16, duration = 12, semitones = 0, octave = 1, velocity = 84, legato = true },
  { step = 28, duration = 4, semitones = -1, octave = 1, velocity = 74, legato = true },
]
[[accompaniment.bass.motifs]]
bars = 1
weight = 3
reference = "chord_root"
notes = [
  { step = 0, duration = 8, semitones = 0, octave = 1, velocity = 86 },
  { step = 8, duration = 6, semitones = 0, octave = 1, velocity = 78 },
]
[[accompaniment.bass.motifs]]
bars = 1
weight = 1
reference = "chord_root"
notes = [
  { step = 0, duration = 12, semitones = 0, octave = 1, velocity = 84 },
  { step = 12, duration = 2, semitones = 7, octave = 1, velocity = 70 },
  { step = 14, duration = 2, semitones = 0, octave = 1, velocity = 76 },
]
[accompaniment.chords]
center = 55
max_drift = 6
strings = 3
default_pattern = 0
patterns = [{ hits = [{ step = 0, stroke = "block", duration = 16, velocity = 48, tie = true }] }]

[instruments]
melody_program = 52
chords_program = 91
bass_program = 38
percussion_program = 0
percussion_bank = 128
```

Les motifs spécifiques P ont priorité ; C et R emploient les deux motifs génériques pondérés. `octave=1` est un **décalage relatif** depuis la fenêtre MIDI 26..37, pas « octave MIDI 1 » : le D de base devient D2, choix de rendu pour garder de la lisibilité et ne pas prendre l’octave pyin pour vérité. La proposition évite délibérément les micro-notes rapides et leurs erreurs de suivi.

### 7.2 Banque de percussion proposée (`feet.toml`)

Réécriture de pulses graves et relances de doubles-croches, **pas attribution certaine des 588 coups**. Densités 0/1/2 toutes couvertes, alternatives par graine aux densités 1 et 2 ; Toe joue ici un tom grave, pas une caisse claire supposée.

```toml
heel_note = 36
toe_note = 41
heel_velocity = 88
toe_velocity = 76
feet_gain = 1.0
velocity_humanize = 3
[[patterns]]
density = 0
weight = 1
hits = [{ step = 0, track = "Heel" }, { step = 8, track = "Toe" }]
[[patterns]]
density = 1
weight = 3
hits = [
  { step = 0, track = "Heel" },
  { step = 8, track = "Toe" },
  { step = 12, track = "Heel", delta_velocity = -12 },
  { step = 14, track = "Toe", delta_velocity = -8 },
]
[[patterns]]
density = 1
weight = 1
hits = [
  { step = 0, track = "Heel" },
  { step = 5, track = "Toe", delta_velocity = -14 },
  { step = 8, track = "Toe" },
  { step = 13, track = "Heel", delta_velocity = -12 },
]
[[patterns]]
density = 2
weight = 2
hits = [
  { step = 0, track = "Heel" },
  { step = 4, track = "Toe", note = 43, delta_velocity = -18 },
  { step = 8, track = "Toe" },
  { step = 11, track = "Heel", delta_velocity = -14 },
  { step = 12, track = "Toe", note = 45, delta_velocity = -12 },
  { step = 14, track = "Heel", delta_velocity = -10 },
]
[[patterns]]
density = 2
weight = 1
hits = [
  { step = 0, track = "Heel" },
  { step = 5, track = "Toe", note = 43, delta_velocity = -14 },
  { step = 8, track = "Toe" },
  { step = 9, track = "Heel", delta_velocity = -18 },
  { step = 13, track = "Toe", note = 45, delta_velocity = -12 },
  { step = 15, track = "Heel", delta_velocity = -10 },
]
```

### 7.3 Odin émotionnel (sections du `profile.toml` proposé)

```toml
[[odin.Bass.zones]]
when = { tension = [0.65, 1.0], arousal = [0.45, 1.0] }
preset = "Growly FM Bass [XR]"
level_db = -6.0
glide_ms = 45.0
morph = [
  { param = "fil1_freq", arousal = 1200.0, tension = 700.0 },
  { param = "fil1_res", tension = 0.12 },
]
[[odin.Bass.zones]]
when = { valence = [-1.0, -0.4], arousal = [0.0, 0.4] }
preset = "Bass Low [RM]"
level_db = -5.0
glide_ms = 70.0
morph = [{ param = "fil1_freq", arousal = 600.0 }]
[[odin.Bass.zones]]
preset = "Bass Crusher [RM]"
level_db = -2.0
glide_ms = 40.0
morph = [{ param = "fil1_freq", arousal = 1400.0, tension = 800.0 }]

[[odin.Chords.zones]]
when = { tension = [0.65, 1.0] }
preset = "Moonshade"
level_db = -7.0
morph = [
  { param = "fil1_freq", arousal = 1200.0, valence = 500.0 },
  { param = "env1_release", density = -0.4 },
]
[[odin.Chords.zones]]
when = { arousal = [0.0, 0.3], valence = [-1.0, -0.4] }
preset = "Eerie Pad"
level_db = -5.0
morph = [{ param = "fil1_freq", valence = 400.0, tension = 600.0 }]
[[odin.Chords.zones]]
preset = "Haunt [RM]"
level_db = -3.0
morph = [
  { param = "fil1_freq", arousal = 1000.0, valence = 500.0 },
  { param = "env1_release", density = -0.3 },
]
```

Zones ordonnées, conditions conjointes, **dernier défaut sans `when`** pour chaque piste ; hystérésis 0,03 et bascule aux frontières selon le moteur actuel. Le morphing couvre tension, arousal, valence et density sans prétendre modifier des types de filtre, routages ou états de preset. La batterie reste SoundFont ; pas de zones Odin sur Heel/Toe. SoundFont reste obligatoire et utilisable sans compilation Odin.

**Aléatoire maîtrisé :** deux boucles C et deux R, deux motifs P, deux motifs génériques, deux patterns aux densités 1/2 ; choix pondérés stables selon la graine, pas réécriture incessante à chaque mesure. Les harmonies d’une partie rejouée gardent leur alternative. Les fragments sont séparés par destination : `[files] feet="feet.toml"` relierait la banque externe lors d’une intégration, sans placer ses `[[patterns]]` à la racine du profil.

**Limites d’expression actuelles :** pas de changements harmoniques intra-mesure dans `chord_loop`, pas d’accord slash ni de tierce absente dans une triade ; la pédale est le bon outil pour l’ambiguïté. Les zones Odin changent timbre et paramètres, **pas** la progression, la tonique ni la probabilité des banques par émotion. Une copie exacte du cycle sonore de 44 mesures, des bruits continus, de la distorsion de studio ou des variations de timbre de l’original n’est donc pas revendiquée. La proposition n’exige aucun nouveau code moteur ; une restitution acoustique identique demanderait une autre tâche, pas un champ TOML inventé.

## 8. Reproduction exacte et périmètre

Depuis la racine de ce dépôt, utiliser l’environnement **du checkout principal**, pas une `.venv` locale :

```bash
export PYTHONPATH=src OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2
PY=/Users/william.quintal/Project/bascanada/harmonium_lab/.venv/bin/python
ROOT=/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac
SF=/Users/william.quintal/Project/bascanada/harmonium/assets/GeneralUser-GS.sf2

"$PY" -m harmonium_lab.cli audioref-measures \
  --manifest "$ROOT/manifest.jsonl" --corpus-root "$ROOT" \
  --filter 'id=06_abyss|23_when_blood_dries|40_puslo_profundum' \
  --context type=zone --grids references/isaac-depths/grids.json \
  --grid '{"estimate":false}' --output references/isaac-depths/measures.json

"$PY" -m harmonium_lab.cli audioref-loops \
  --track "$ROOT/tracks/06_abyss.flac" \
  --stems "$ROOT/stems/htdemucs/06_abyss" --track-id 06_abyss \
  --grid '{"beat_s":0.631578947368421,"tatums_per_beat":2,"beats_per_bar":4,"origin_s":-2.4159405718525966}' \
  --tonic D --parts bass drums lead chords \
  --bass-prog 38 --pad-prog 91 --lead-prog 52 \
  --loop depths_full:0:94 --loop depths_intro:1:9 \
  --loop depths_cycle:9:17 --loop depths_bridge:25:33 \
  --loop depths_middle:33:41 --loop depths_reprise44:45:53 \
  --loop depths_return:73:81 --loop depths_final:81:94 \
  --soundfont "$SF" --out "$ROOT/transcriptions"
```

La première commande est celle à utiliser pour **reproduire le livrable avec ses grilles** ; elle n’a pas été relancée ici sur 25 zones. L’exécution observée a utilisé `--filter type=zone --context type=zone --grid '{"estimate":false}'` vers `/tmp/harmonium-017/isaac-niveaux-measures.json`, puis recopié les trois grilles vérifiées ; mêmes mesures et même contexte. La seconde commande reproduit les huit fenêtres en un appel ; pendant cette analyse, les six fenêtres initiales ont été suivies des deux découpes API `depths_bridge` et `depths_reprise44` décrites §5.

Pour recréer les stems si nécessaire, avec l'environnement Demucs distinct
de celui du labo (les quatre WAV complets sont sinon réutilisés) :

```bash
PYTHONPATH=src /tmp/demucs-env/bin/python - <<'PY'
from pathlib import Path
from harmonium_lab.audioref.stems import separate
root = Path('/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac')
separate([('06_abyss', root / 'tracks/06_abyss.flac')],
         root / 'stems', model='htdemucs', device='mps', shifts=1)
PY
```

Calculs complémentaires réellement exécutés : `fit_beat`, `onset_times`, `coherence` pour périodes ×0,5/1/2 et divisions 2/3/4 ; `bar_period` ; `bar_chroma`, `self_similarity`, `analyze_structure(max_loop_bars=80)` ; RMS/centroïde/platitude des quatre stems. La corrélation de répétition est `corrcoef(rms[:-44], rms[44:])`, par stem. Les signatures et intervalles ci-dessus permettent de refaire ces calculs avec les modules `audioref/grid.py`, `structure.py`, `transcribe.py`, `render.py`. Les scripts de travail `/tmp/isaac-depths-{analysis,refine,detail,transcribe,extra}.py` ne font pas partie du livrable et ne sont pas nécessaires aux deux commandes ci-dessus.

**Périmètre de vérification :** aucune audition, comparaison aveugle ni installation de profil moteur ; les variantes restent analysées depuis le mix entier. Contrôles techniques d'intégration réussis : JSON/TOML, presets, lecture et couverture des 25 triplets privés. Tests du labo : **286 réussis, 31 ignorés, 8 avertissements** ; détails dans le [récapitulatif commun](../isaac-niveaux.md). Aucun fichier du moteur modifié.
