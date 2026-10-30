# Isaac — Caves, Depths et Womb : comparaison labo

Analyses de **Ridiculon** (Matthias Bossi, Jon Evans), réalisées le 30 octobre
2026 sur les découpes du manifeste Isaac. Méthode des références
[Basement](isaac-basement/README.md) et [Nuclear Throne / Désert](nt-desert/README.md) :
mesures des mix entiers, calage rythmique, structure et instrumentation probable
par stems `htdemucs`, transcriptions automatiques et propositions de données.
**Aucune audition de contrôle n'est revendiquée.** Les noms de modes et de timbres
restent explicitement hypothétiques lorsque le signal ne les départage pas.

## Ce qui distingue les trois niveaux

Tempos à la noire ; regroupement de travail **4/4 binaire**, avec premier temps
moins certain que la période. Les centres locaux viennent de la basse séparée,
pas du seul meilleur gabarit de gamme sur le mix.

| Niveau / principale | Tempo de grille | Centre et mode : résultat, puis choix de profil | Caractère | Instruments probables / programmes GM 0-based | Distinction dans Isaac |
|---|---:|---|---|---|---|
| **[Caves](isaac-caves/README.md)** — 04 *Sodden Hollow* | **120 BPM** | Pôles **D# / A**, séparés d'un triton ; mode unique non résolu. **D# phrygien** proposé pour `isaac_caves`, choix d'écriture et non identification certaine. | Demi-temps percussif, alternance de pédales et descente chromatique ; sections où la basse disparaît mais le kit continue. | Basse très traitée **38**, kit **36/38/42**, nappe **89** ou **91**, couleur chorale discrète **52**. | Part percussive HPSS **maximale des 25 zones : 24,73 %** ; grande récurrence de **56 mesures**. Plus brillant que les deux autres familles ; ne pas réduire ce niveau à la pédale D de Basement. |
| **[Depths](isaac-depths/README.md)** — 06 *Abyss* | **95 BPM** | Grave **D / C#**, avec C et D# ; tierce et mode non décidés. **D mineur harmonique chromatisé** proposé pour `isaac_depths`. | Pulses et toms graves, nappe sombre, variations lentes de texture plutôt que progression fonctionnelle certaine. | Basse **38** ou **33**, grosses percussions **36**, toms **41/43/45**, nappe **91** ou **89** ; chœur **52** seulement comme couleur expérimentale. | RMS moyen **minimal des 25 zones : 0,044279** ; cycle d'arrangement de **44 mesures** corroboré par les énergies des stems. Batterie si grave que le classifieur étiquette tous les coups « kick » : ne pas inventer un backbeat certifié. |
| **[Womb](isaac-womb/README.md)** — 09 *Viscera* | **≈90 BPM** | Région **Bb–B** grave ; Bb comme centre probable, voisin supérieur possiblement glissé. **Bb phrygien / pédale chromatique** proposé pour `isaac_womb`, mode incertain. | Bourdon organique/modulé, texture formantique ponctuelle, kit renforcé dans la seconde moitié. | Basse **38** ou **34**, nappe **89** ou **91**, voix/texture **52** ou **53**, kit **36/38/42**. | Part percussive HPSS **minimale : 5,82 %**, malgré beaucoup d'attaques ; retour de matériau à **32 mesures**, avec événements formantiques répétés et entrée nette du kit vers **85,6 s**. Le F dominant du chroma ne suffit pas à nommer la tonique. |

La comparaison au [Basement](isaac-basement/README.md) est une différence de
vocabulaire mesuré : ses grilles tournent autour de 140–144 BPM et ses principales
pédales locales sont D ou F#. Ce n'est pas une échelle automatique de difficulté
ni une consigne d'accélérer les niveaux successifs.

## Variantes d'étage : commun et non commun

- **Caves :** *Capiticus Calvaria* (22, Catacombs) et *Kave Diluvii*
  (37, Flooded Caves) confirment la grille à **120 BPM**, mais ni la même
  percussion ni une tonique unique. Les gabarits globaux favorisent D mineur
  harmonique pour ces deux variantes, contre C# mineur harmonique sur le mix de
  *Sodden Hollow* ; leurs marges restent faibles. Le maximum d'énergie percussive
  de la principale ne se généralise donc pas aux trois pistes.
- **Depths :** *When Blood Dries* (23, Necropolis) est calé à **120 BPM**, pas
  95 ; *Puslo Profundum* (40, Dank Depths) partage les **95 BPM** d'*Abyss*.
  Leur point commun robuste est la brillance faible : centroïdes de famille
  **1099–1450 Hz**. D phrygien pour Necropolis et C mineur harmonique pour Dank
  Depths restent des hypothèses de mix, pas des basses locales isolées.
- **Womb :** *Caesarian* (55, Utero) et *Cicatrix* (35, Scarred Womb)
  confirment une grille lente proche de **90 BPM**. Les deux premières pistes
  ont une faible part percussive HPSS ; *Cicatrix* est plus percussif. Les
  gabarits D mineur harmonique et F mineur harmonique des variantes ne prouvent
  pas une transposition de la basse Bb de *Viscera*.

La famille Caves a des centroïdes **2024–2604 Hz**, Womb **1493–1784 Hz** :
aucun chevauchement avec Depths dans ces neuf mesures. Ces résultats décrivent
les mix de cette compilation, pas une égalisation cible universelle.

**Précautions communes.** Les statistiques de contexte portent sur les
**25 pistes `type=zone`**, y compris celles étudiées. HPSS sépare des énergies,
pas des instruments ; une attaque peut provenir d'une basse distordue.
`dynamic_range_db` est l'étendue min–max des RMS et dépend fortement des
silences/fondus de découpe : ses valeurs ne sont ni des LUFS ni la dynamique
musicale utile. Les gabarits de gamme, triades forcées, octaves PYIN et identités
de coups ne sont pas assimilés à une partition validée à l'oreille.

## Données proposées : schéma actuel, pas installation moteur

Chaque README contient une proposition **originale**, distincte des transcriptions :

- `harmony.parts.<partie>` avec `kind = "chord_loop"` et
  **`loops = [{ weight, chords }]`** ; chaque alternative a exactement la longueur
  de la partie. Les pédales emploient `degree = 1`, avec voisin chromatique
  facultatif. Les anciennes formes `chords` directement dans la partie ne sont
  pas reprises.
- Motifs de basse pondérés et banques de percussion couvrant les densités 0/1/2,
  avec alternatives par graine ; les choix ne sont pas des superpositions.
- **`[[odin.<Piste>.zones]]`**, conditions émotionnelles ordonnées et dernière
  zone sans `when`. Noms vérifiés contre les fichiers réels du dossier plat
  `~/Project/bascanada/odin-presets` : notamment Bass Crusher [RM], Bass Low [RM],
  Growly FM Bass [XR], Haunt [RM], Moonshade et Eerie Pad. Programmes SoundFont
  conservés pour le rendu sans Odin.

Aucune extension moteur n'est requise pour ces **propositions d'écriture**.
Les limites sont nommées dans les dossiers : accords entiers par mesure,
qualités Major/Minor ou pédales/dyades, pas de restitution exacte des glissements
microtonaux, des traitements de studio ni de l'automation originale des stems.
Ces fragments documentaires ne constituent pas trois profils installables et
n'ont pas été validés par le chargeur moteur. Aucun fichier du dépôt `harmonium`
n'a été modifié. Phazzy Organ, Sausage Bassener sur notes rapides, sifflement et
guitare saturée GM30 sont exclus des propositions.

## Couverture, droits et reproduction

Les principales sont analysées **sur leurs 254, 233 et 183 secondes**.
**25 triplets MIDI/WAV/JSON** ont été produits : huit pour Caves, huit pour
Depths, neuf pour Womb. Ils comprennent des réductions intégrales et des boucles
représentatives. Caves et Womb ont des compléments de levée/queue ; l'export
Depths utilise une origine reculée et du cadrage silencieux déclaré pour couvrir
0–233 s. Les fichiers WAV sont rendus par FluidSynth / GeneralUser GS et
normalisés au pic 0,125 ; la normalisation rend aussi les résidus artificiellement
audibles. Les temps source et confiances sont consignés dans chaque README et
sidecar privé.

Conformément au **principe VII**, mix, stems et transcriptions restent uniquement
dans le checkout principal gitignoré :

```text
/Users/william.quintal/Project/bascanada/harmonium_lab/corpus/isaac/
  manifest.jsonl
  tracks/
  stems/htdemucs/
  transcriptions/
```

Seuls ce récapitulatif et les **trois README, trois `measures.json`, trois
`grids.json`** sont versionnés. Chaque README donne les commandes
`audioref-measures --corpus-root ... --context type=zone` et `audioref-loops`,
avec grille, plages, banque et répertoire privé exacts. Les mesures de mix
proviennent d'un appel commun frais des 25 zones, puis des grilles spécifiques
sont ajoutées ; les diagnostics complémentaires éventuels sont distingués de
la sortie CLI de base.

Contrôle d'intégration effectué : lecture des JSON et du TOML documentaire,
longueurs des alternatives harmoniques, bornes des motifs, existence des presets,
identité des mesures avec l'appel frais, lecture des MIDI et des WAV de tous les
exports, couverture temporelle réunie des principales, échantillons finis et pics
WAV bornés à 0,126. Les limites musicales ne disparaissent pas parce que ces
contrôles techniques passent.

Commande de tests du labo depuis ce worktree, sans réinstaller ni modifier
l'environnement partagé :

```bash
PYTHONPATH=src make test \
  VENV=/Users/william.quintal/Project/bascanada/harmonium_lab/.venv
```

**Résultat observé : 286 tests réussis, 31 ignorés, 8 avertissements.**
Les avertissements concernent les signaux synthétiques courts/vide de librosa
et une conversion numérique Numba ; aucun échec. La lecture des 25 exports
privés a été vérifiée indépendamment de cette suite de tests.
