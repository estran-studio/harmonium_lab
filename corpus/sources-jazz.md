# Recensement des sources du corpus jazz/blues — Harmonium Lab (L0, phase 018)

Ce document recense les sources candidates pour le profil jazz/blues distribué (tâche **E7** du
plan `harmonium/specs/018-grille-et-moteur-neutre/plan.md`, décision **F3**) : accompagnement
sous une grille fournie par l'utilisateur (comping **E5**, walking bass **E6**, batterie swing).
Recherche et documentation seulement : **le propriétaire choisit**. Aucun fichier sous droits
n'est versionné ; aucun code n'est ajouté.

Cadre :
- **Principe V (style en données)** : le profil s'appuie sur des mesures tirées d'un corpus réel ;
  le labo mesure la distance entre le généré et ce corpus.
- **Principe VII (respect des sources)** : provenance et licence de chaque source notées ; toute
  musique peut servir d'**analyse** ; seuls les dérivés (mesures, cellules, profils) entrent dans
  les dépôts, jamais les enregistrements ni les transcriptions sous droits ; un style se nomme
  par sa **source précise**.
- **Décision D1 (usage interne, corpus trad)** : bruts en cache local gitignoré
  (`corpus/*/*` sauf `manifest.jsonl` et `VERSION`), dérivés agrégés versionnés.
- **Contrainte propre à E7** : le moteur est sous **MIT OR Apache-2.0**
  (`harmonium/Cargo.toml`, `license = "MIT OR Apache-2.0"`) et training pourrait être vendu
  (`demandes-training.md`, §E). Un dérivé distribué dans un profil doit donc pouvoir être
  utilisé **commercialement** : toute source **NC** (non commerciale) ou **SA** (partage à
  l'identique) est exclue du profil distribué, quel que soit son intérêt pour l'analyse.

**Méthode de vérification.** Chaque licence ci-dessous a été lue par l'auteur de ce document
le **2026-10-30** (date de consultation unique, sauf mention) à l'URL indiquée. Les pages Zenodo
renvoyaient HTTP 403 depuis le réseau de consultation ; leurs licences ont été lues dans les
métadonnées officielles du DOI (API DataCite, `https://api.datacite.org/dois/<DOI>`), qui
reprennent la licence déclarée par le déposant. Deux fichiers ont été téléchargés
temporairement dans `/tmp` pour compter les volumes, puis supprimés : métadonnées de la
Groove MIDI Dataset (archive MIDI seule, 3,1 Mo, SHA256 conforme à la page officielle) et
`wjazzd.db` v2.1 (42 Mo) ; `treebank.json` de la JHT a été lu en mémoire pour un compte. Rien
n'est entré dans le dépôt.

**Codes d'usage permis** (colonne « Usage ») :
- **A — analyse seule** : cache local gitignoré ; dérivés agrégés versionnés **au labo**
  (comme D1) ; rien dans un profil distribué.
- **B — distribuable** : dérivés versionnables **et** distribuables dans un profil du moteur,
  avec les mentions exigées par la licence.
- **—** : inutilisable (accès restreint ou conditions incompatibles même avec l'analyse
  versionnée).

---

## 1. Tableau de synthèse des sources

| Source | URL | Format | Licence (vérification, 2026-10-30) | Contenu | Volume | Usage | Décision |
|---|---|---|---|---|---|---|---|
| **Weimar Jazz Database (WJazzD) v2.1** | `jazzomat.hfm-weimar.de` | SQLite (+ MIDI) | ODbL 1.0 (base) + DbCL 1.0 (contenus) — [page de téléchargement](https://jazzomat.hfm-weimar.de/download/download.html), table `db_info` du fichier, [ODbL](https://opendatacommons.org/licenses/odbl/1-0/), [DbCL](https://opendatacommons.org/licenses/dbcl/1-0/) | Solos transcrits (monodiques) ; **par temps** : accord, forme, **hauteur de basse**, chorus | 456 solos ; 132 329 temps, dont 122 540 avec basse (438 solos) ; 361 solos *swing* ; 97 sur forme *Blues* | **B** pour les statistiques par temps (accords, basse, tempo, forme) ; **A** pour les solos | **Retenue** (pilier E6/E7) |
| **Groove MIDI Dataset (GMD) v1.0.0** | `magenta.withgoogle.com/datasets/groove` | MIDI (+ WAV) | CC BY 4.0 — [page officielle](https://magenta.withgoogle.com/datasets/groove) | Batterie humaine (Roland TD-11), style annoté | 1 150 fichiers ; *jazz* 101 fichiers (70,6 min, dont 11 *jazz/swing*), *neworleans* 53 (32,9 min), *blues* 4 (*shuffle*, 4,8 min) | **B** | **Retenue** (batterie E7) |
| **Jazz Trio Database (JTD) v0.2** | `github.com/HuwCheston/Jazz-Trio-Database` | CSV, MIDI, JSON | Annotations : MIT — [README §License](https://github.com/HuwCheston/Jazz-Trio-Database) ; audio : « License Agreement », accès restreint — [DOI 10.5281/zenodo.13828030](https://api.datacite.org/dois/10.5281/zenodo.13828030) | Attaques piano/basse/batterie, temps et mesures (automatiques), MIDI piano transcrit automatiquement | ≈ 45 h (README) | **B** pour les mesures de *timing* ; **A** pour le MIDI piano | **Retenue** (timing E5/E6/E7) |
| **Grilles du domaine public et formes communes** | [Duke CSPD, Public Domain Day 2026](https://cspd.law.duke.edu/publicdomainday/2026/) ; [Compendium USCO §802.5(A)](https://www.copyright.gov/comp3/chap800/ch800-performing-arts.pdf) ; [CARL, durée au Canada](https://www.carl-abrc.ca/influencing-policy/copyright/faq-term-extension-for-authored-works) | TOML F1 à écrire | Domaine public (règles §2.4) ; progressions standard = « common property » (USCO) | Blues 12 mesures, *rhythm changes*, grilles d'œuvres publiées ≤ 1930 | À constituer (≈ 10–30 grilles) | **B** | **Retenue** (grilles de démo et de test) |
| **iRb — iRealPro Corpus of Jazz Standards** (Shanahan & Broze) | `github.com/shanahdt/irealb` | Humdrum `**jazz` | CC BY 4.0 — [DOI 10.5281/zenodo.3546040](https://api.datacite.org/dois/10.5281/zenodo.3546040) ; dépôt GitHub sans fichier de licence | Grilles de standards (issues du forum iReal Pro) | 1 186 morceaux | **A** | **Réserve** (la CC BY ne couvre que l'apport des auteurs) |
| **Jazz Harmony Treebank (JHT)** | `github.com/DCMLab/JazzHarmonyTreebank` | JSON | Données : CC BY-NC-SA 4.0 — [LICENSE.md](https://github.com/DCMLab/JazzHarmonyTreebank/blob/master/LICENSE.md) ; le DOI [10.5281/zenodo.4245406](https://api.datacite.org/dois/10.5281/zenodo.4245406) (CC BY 4.0) est l'**article**, pas les données | Grilles iReal + arbres d'analyse | 1 170 grilles, dont 150 avec arbres (`treebank.json`) | **A** | **Réserve** (NC-SA) |
| **JAAH — Jazz Audio-Aligned Harmony** | `github.com/MTG/JAAH` | JSON, LAB | CC BY-NC-SA 4.0 — [DOI 10.5281/zenodo.1290737](https://api.datacite.org/dois/10.5281/zenodo.1290737) ; dépôt GitHub sans licence | Accords, mètre, structure alignés sur enregistrements (Smithsonian) | 113 pistes | **A** | **Réserve** (NC-SA ; audio non fourni) |
| **PiJAMA** | `zenodo.org/records/8354955` | MIDI | CC BY-NC 4.0 — [DOI 10.5281/zenodo.8354955](https://api.datacite.org/dois/10.5281/zenodo.8354955) | Piano jazz solo transcrit automatiquement | 2 777 interprétations, > 200 h | **A** | **Réserve** (NC ; voicings pour E5 en analyse) |
| **Ancien corpus `references/jazz-*`** (Doug McKenzie, bushgrafts.com) | `bushgrafts.com/jazz/` | MIDI GM/XG | **Non précisée** — [site](https://www.bushgrafts.com/) : « freely available », aucune licence, ISO vendu | Arrangements piano solo/trio de standards sous droits | 53 + 38 + 21 MIDI jazz (§4) | **A** | **Réserve** (analyse E5 seulement) |
| **FiloSax** | `dave-foster.github.io/filosax` | WAV, JAMS, JSON, MIDI | Conditions propres : recherche non commerciale, non transférable, aucune diffusion sans permission écrite — [page §License](https://dave-foster.github.io/filosax/) ; [DOI 10.5281/zenodo.6335779](https://api.datacite.org/dois/10.5281/zenodo.6335779) « Restricted Access » ; le DOI 10.5281/zenodo.5625643 (CC BY 4.0) est l'**article** | Saxophone + accords/temps ; accompagnements Aebersold (vendus séparément) | 48 morceaux × 5 saxophonistes | **—** | **Rejetée** |
| **McGill Billboard 2.0** | `ddmal.ca/research/The_McGill_Billboard_Project_(Chord_Analysis_Dataset)` | Texte, LAB | CC0 — [page officielle](https://ddmal.ca/research/The_McGill_Billboard_Project_(Chord_Analysis_Dataset)/) | Accords pop (échantillon des palmarès *Billboard*) | 890 entrées, 740 chansons | B | **Rejetée** (hors style ; comparaison seulement) |
| **CoCoPops** | `github.com/Computational-Cognitive-Musicology-Lab/CoCoPops` | Humdrum | CC BY-NC 4.0 — [README §Licence](https://github.com/Computational-Cognitive-Musicology-Lab/CoCoPops) | Mélodies + accords pop/rock | 414 transcriptions | A | **Rejetée** (hors style, NC) |
| **ChoCo** (agrégat) | `github.com/smashub/choco` | JAMS, RDF | Double : CC BY 4.0 / CC BY-NC-SA 4.0 (JAAH…) — [README §License](https://github.com/smashub/choco/blob/main/README.md) | Agrège iReal Pro, Real Book, Wikifonia, Band-in-a-Box, WJazzD, JAAH… | 20 080 fichiers JAMS | **—** | **Rejetée** (CC BY revendiquée sur des contenus tiers) |
| **iReal Pro (forum, playlists)** | `forums.irealpro.com` | `irealb://` | Aucune licence aux tiers : les contributeurs gardent le droit d'auteur, licence à Technimo seulement — [conditions du forum](https://forums.irealpro.com/help/terms/) ; [conditions iReal Pro](https://store.irealpro.com/terms) (en vigueur le 2026-02-19) | Grilles de standards (communauté) | « thousands » | **—** | **Rejetée** (passer par iRb si besoin) |
| **Lakh MIDI Dataset** | `colinraffel.com/projects/lmd` | MIDI | CC BY 4.0 déclarée, mais fichiers « scraped from publicly-available sources », non transcrits par l'auteur — [page officielle](https://colinraffel.com/projects/lmd/) | MIDI tous genres, sans étiquette jazz | 176 581 fichiers | **—** | **Rejetée** (provenance inconnue, pertinence faible) |
| **MAESTRO v3.0.0** | `magenta.withgoogle.com/datasets/maestro` | MIDI, WAV | CC BY-NC-SA 4.0 — [page officielle](https://magenta.withgoogle.com/datasets/maestro) | Piano classique (concours) | 1 276 interprétations, 198,7 h | **—** | **Rejetée** (hors style) |

---

## 2. Sources retenues

### 2.1 Weimar Jazz Database (WJazzD)

- **URL** : `https://jazzomat.hfm-weimar.de/download/downloads/wjazzd.db` (v2.1, base 2.2,
  modifiée le 2018-02-08, 42 512 384 octets, SHA256
  `af6a0d9debf042c3581565bd75baad591d32e166cd2ec7298519883de614bf12` au 2026-10-30).
  Documentation : `dbformat/dbformat.html`, `dbformat/dbcontent.html`.
- **Licence** : la page de téléchargement déclare l'**ODbL 1.0** ; la table `db_info` du fichier
  ajoute : « Any rights in individual contents of the database are licensed under the Database
  Contents License (**DbCL 1.0**) ». L'ODbL autorise explicitement l'usage commercial (§3.1).
  - **Ce que la licence couvre réellement** : la base (schéma, sélection, droit *sui generis*)
    et les droits que l'équipe Jazzomat détient sur ses annotations. Elle **ne couvre pas** les
    œuvres sous-jacentes : les compositions (standards, dont 96 « Great American Songbook ») et
    les **improvisations** des solistes (Coltrane, Parker…), qui restent la propriété de leurs
    ayants droit. L'ODbL le dit elle-même (§2.4 : pas de licence sur les droits des contenus
    individuels) ; la DbCL ne peut céder que ce que le concédant détient.
  - **Conséquence** : les solos transcrits sont en **usage A** (analyse seule, jamais de
    phrase copiée dans une banque de cellules distribuée). Les **statistiques par temps**
    (distribution des degrés de basse selon la position dans la mesure, accords, tempos,
    formes) sont des faits agrégés : un profil qui les contient est un **Produced Work**
    (ODbL §1.0) et, s'il est distribué, doit porter la mention de l'ODbL §4.3, par exemple :
    « Contains information from the Weimar Jazz Database, which is made available here under
    the Open Database License (ODbL). » Redistribuer la base ou un extrait substantiel
    (Derivative Database) imposerait le partage sous ODbL (§4.2, §4.4) : **à éviter**.
- **Contenu utile** (comptes faits sur le fichier) :
  - table `beats` : 132 329 temps de 456 solos, avec `chord` (symboles jazz : `Bb7`, `C-7`,
    `Ebj7`…), `form` (A1, B…), `bass_pitch` (hauteur MIDI de la basse au temps) renseignée sur
    122 540 temps (438 solos), `signature`, `chorus_id`. Provenance de `bass_pitch`
    (transcription manuelle ou automatique) **non précisée** dans la documentation consultée.
  - `solo_info.rhythmfeel` : SWING 361, TWOBEAT 32, LATIN 27, FUNK 20, BALLAD 10 ;
    `solo_info.style` : TRADITIONAL 32, SWING 66, BEBOP 56, COOL 54, HARDBOP 76, POSTBOP 147,
    FUSION 20, FREE 5.
  - `composition_info.template` : *Blues* 65 compositions → **97 solos, dont 87 en swing** ;
    *I Got Rhythm* 10 compositions.
- **E5 (comping)** : peu direct (aucun voicing) ; donne le **rythme harmonique** réel (accords
  par temps, changements en cours de mesure) pour éprouver E1/E5 sous des grilles réalistes.
- **E6 (walking bass)** : source principale. Mesures directes des critères d'acceptation :
  part des noires sur la fondamentale au changement d'accord, nature de la note du 4ᵉ temps
  (approche chromatique par-dessus/par-dessous, quinte, note diatonique), intervalles
  successifs, registre, répétitions, par tempo et par forme (blues vs standard).
- **E7 (profil)** : distributions de tempo (`avgtempo`, `tempoclass`), formes (blues 12, AABA
  32), vocabulaire d'accords pour les tests ; corpus de référence symbolique de la distance labo.
- **Ingestion probable** : nouveau module générique `harmonium_lab` (lecteur SQLite →
  représentation « boucles transcrites » de `styledist.symbolic` : notes de basse à
  `pos_16th`, accord par temps) ; `corpus/wjazzd/manifest.jsonl` + `VERSION` versionnés, base
  en cache gitignoré (le motif `corpus/*/*` du `.gitignore` le couvre déjà). Écarts à combler :
  `styledist.symbolic` ne lit qu'un accord par mesure en majeur/mineur ; les accords de 7ᵉ et
  les changements au temps relèvent de E1/E3.

### 2.2 Groove MIDI Dataset (GMD)

- **URL** : `https://storage.googleapis.com/magentadata/datasets/groove/groove-v1.0.0-midionly.zip`
  (3,11 Mo, SHA256 `651cbc524ffb891be1a3e46d89dc82a1cecb09a57c748c7b45b844c4841dcc1e`, vérifié).
- **Licence** : **CC BY 4.0**, « made available by Google LLC ». Batteurs engagés pour
  l'occasion (« more than 80% of duration coming from hired professionals ») : pas d'œuvre
  tierce sous-jacente identifiée ; usage commercial permis ; obligation : attribution
  (Gillick et al., ICML 2019) et lien de licence.
- **Contenu** (comptes faits sur `info.csv`) : *jazz* 101 fichiers (50 *beats*, 51 *fills* ;
  styles secondaires : `jazz` 46, `jazz/funk` 24, `jazz/swing` 11, `jazz/fusion` 11,
  `jazz/march` 3…), *neworleans* 53, *blues* 4 (`blues/shuffle`) ; 4/4 sauf 2 fichiers en 3/4.
  Vélocités, micro-timing et position de la pédale de charleston (CC 4) conservés.
- **E7** : patterns de ride (« ring-ding-a-ding »), charleston aux temps 2 et 4, *comping*
  caisse claire/grosse caisse, *fills*, dynamique ; directement transposables dans un
  `feet.toml`/patterns de batterie multi-notes (déjà supportés, `demandes-training.md` §E7).
  Volume swing modeste (11 fichiers étiquetés `jazz/swing`, 46 `jazz` sans précision) : à
  compléter par le timing de JTD.
- **Ingestion probable** : `loader.py`/`pretty_midi` existants ; table de correspondance Roland →
  GM fournie par la page officielle (ride 51/53/59). Écart : `styledist.symbolic` ne classe
  que kick {35, 36}, snare {37–40} et charleston {42, 44, 46} ; **la ride n'est pas un rôle**
  aujourd'hui.

### 2.3 Jazz Trio Database (JTD)

- **URL** : annotations via `mirdata` (`mirdata.initialize('jtd')`) ; dépôt
  `https://github.com/HuwCheston/Jazz-Trio-Database`.
- **Licence** : README : « The dataset is made available under the **MIT License**. Please note
  that your use of the audio files linked to on YouTube is not covered by the terms of this
  license. » Audio sur Zenodo : accès sur demande, « valid research projects » seulement
  (README) — **non utilisé**.
  - **Portée** : la MIT couvre les annotations produites par les auteurs (attaques, temps). Le
    `piano_midi.mid` est la transcription automatique d'improvisations enregistrées sous droits :
    la MIT ne peut pas en céder les droits → **usage A** pour ce MIDI ; les mesures de timing
    agrégées sont **B** (avec la mention MIT dans le manifeste).
- **Contenu** (doc `database-structure`) : par piste, `*_onset.csv` (piano, basse, batterie),
  `beats.csv` (attaques rapportées au temps, mètre, premiers temps), `piano_midi.mid`,
  `metadata.json` (année, musiciens, notes de qualité de séparation et de détection).
- **E5** : placement rythmique du comping (attaques du piano par rapport au temps) ; voicings
  du MIDI piano en analyse seulement.
- **E6** : placement de la basse (avance/retard sur le temps selon le tempo).
- **E7** : rapport de swing, synchronisation basse/batterie : paramètres de `SetSwing` et du
  micro-timing ; mesure labo du « feel » du généré.
- **Ingestion probable** : `mirdata` (dépendance optionnelle comme `.[stems]`) ou CSV directs ;
  les notions de tatum/cohérence de `audioref.grid` s'appliquent telles quelles aux attaques.

### 2.4 Grilles du domaine public et formes communes

- **Règle aux États-Unis (vérifiée)** : le 2026-01-01, les œuvres de **1930** sont entrées dans
  le domaine public ; le terme court depuis la **publication** (partition) ou
  l'**enregistrement au registre**, la date la plus ancienne l'emportant ; la sortie d'un disque
  ne compte pas (exemple Duke : *Mood Indigo*, disque 1930, partition 1931 → domaine public en
  2027). Donc, en 2026 : **compositions publiées ou enregistrées au registre en 1930 ou avant**
  (et non « avant 1930 » comme l'indiquait le brief). Les **enregistrements sonores** suivent un
  terme distinct : ceux de **1925** et avant sont libres aux États-Unis en 2026 (Music
  Modernization Act). Source : [Duke CSPD, Public Domain Day 2026](https://cspd.law.duke.edu/publicdomainday/2026/),
  qui cite parmi les compositions libérées *I Got Rhythm* (« the source of the foundational
  jazz chord progression known as the “rhythm changes” »), *Body and Soul*,
  *Georgia on My Mind*, *Embraceable You*, *But Not for Me*, *On the Sunny Side of the Street*.
- **Règle au Canada (vérifiée)** : depuis le 2022-12-30, vie de l'auteur + 70 ans, **non
  rétroactif** ([CARL](https://www.carl-abrc.ca/influencing-policy/copyright/faq-term-extension-for-authored-works)).
  Conséquence [inférence tirée de cette règle] : libres au Canada les œuvres dont tous les
  auteurs sont morts en **1971 ou avant**. Les deux régimes divergent :
  - *I Got Rhythm*, *Lady Be Good* (musique George Gershwin, 1898–1937) : libres aux
    États-Unis et au Canada (paroles d'Ira Gershwin, mort en 1983 : sans effet sur une grille
    d'accords, mais la qualification d'œuvre de collaboration au Canada **n'est pas vérifiée**) ;
  - blues de W. C. Handy (1873–1958 ; *St. Louis Blues* 1914, *Memphis Blues* 1912), œuvres de
    Fats Waller (1904–1943) publiées ≤ 1930 : libres dans les deux pays ;
  - *Body and Soul* (Johnny Green, 1908–1989) et *Georgia on My Mind* (Hoagy Carmichael,
    1899–1981) : **libres aux États-Unis seulement** (Canada : jusqu'en 2059 et 2051).
  - Dates de décès lues sur Wikipédia (résumés REST, 2026-10-30).
- **Formes communes (vérifiée)** : le Compendium du US Copyright Office (§802.5(A), éd. du
  2021-01-28) range « Chord symbols based on standard chord progressions » parmi le matériau
  « common property » non protégeable. C'est une pratique d'enregistrement de l'Office, pas un
  jugement ; aucun équivalent canadien n'a été vérifié. Le blues 12 mesures et la progression
  *rhythm changes* écrits par le propriétaire (sans copier une partition récente) relèvent de
  ce matériau.
- **Méthodes de walking bass / comping du domaine public** : aucune méthode publiée en 1930 ou
  avant n'a été trouvée pendant cette recherche ; la walking bass swing se généralise plus
  tard [inférence, non vérifiée]. Les techniques (notes guides 3-7, voicings sans fondamentale,
  drop 2) sont des procédés de métier, non des œuvres : E5 peut les coder sans source.
- **E5/E6/E7** : grilles de **démonstration** et de **test** distribuables (blues en fa, ii-V
  dans une mesure, *rhythm changes* en si♭ : exactement les cas d'acceptation de E1/E6),
  grilles par défaut du profil quand l'utilisateur n'en fournit pas.
- **Ingestion probable** : saisie manuelle en TOML au format F1 (`{ semitones, quality, bass }`)
  à partir des partitions de 1930 numérisées (liens archive.org donnés par Duke), une ligne de
  manifeste par grille (œuvre, compositeur, année de publication, statut US/Canada, source de
  la vérification).

---

## 3. Sources en réserve ou rejetées

### 3.1 En réserve (analyse seule, jamais dans un profil distribué)

- **iRb (iRealPro Corpus of Jazz Standards)** — CC BY 4.0 sur Zenodo, déposée par Shanahan et
  Broze. Les grilles viennent du forum iReal Pro, dont les contributeurs **gardent leurs
  droits** (conditions du forum) ; les œuvres sont des standards sous droits. La CC BY ne
  couvre donc que la conversion et la curation des auteurs. Intérêt : 1 186 grilles pour
  éprouver le moteur sous des grilles variées au labo (rendu sous grille, distance aux
  statistiques WJazzD). Risque faible pour des progressions standard (§2.4), mais on ne
  redistribue pas de grille entière tirée de iRb.
- **Jazz Harmony Treebank** — données CC BY-NC-SA 4.0 (fichier `LICENSE.md` du dépôt). NC-SA
  incompatible avec un moteur MIT/Apache ; utile pour l'analyse fonctionnelle des grilles.
- **JAAH** — CC BY-NC-SA 4.0 ; 113 pistes de la *Smithsonian Collection of Classic Jazz* et de
  la *Smithsonian Anthology* annotées (accords, mètre, structure). Utile avec `audioref`
  (stems, transcription de basse) sur des enregistrements achetés, en analyse seule. Les
  enregistrements de 1925 et avant sont libres aux États-Unis (§2.4) ; leur statut au Canada
  n'est **pas vérifié** ; et leur style (deux temps, tuba, banjo) ne correspond pas à un
  accompagnement swing.
- **PiJAMA** — CC BY-NC 4.0 ; seul grand corpus symbolique de piano jazz (voicings main
  gauche, comping en solo). Mesures agrégées de voicings pour guider E5 au labo seulement.
- **Ancien corpus `references/jazz-*`** — voir §4.

### 3.2 Rejetées

- **FiloSax** — conditions d'usage restrictives (signataire nominatif, recherche non
  commerciale, aucune diffusion de données permettant la reproduction sans permission écrite) ;
  accompagnements Aebersold vendus séparément. Même les dérivés agrégés versionnés poseraient
  question (clause 3). À ne pas demander.
- **McGill Billboard** — seule source **CC0** du lot (vérifiée), mais pop : sert au
  plus de point de comparaison (contraste pop/jazz des grilles), pas de corpus jazz.
- **CoCoPops** — CC BY-NC 4.0, pop/rock ; hors style.
- **ChoCo** — revendique CC BY 4.0 sur des partitions dont elle ne détient pas les droits
  (iReal Pro, Real Book, Wikifonia, Band-in-a-Box) ; JAAH y est en CC BY-NC-SA. Licence des
  sous-corpus **non vérifiée** à leur source pour Real Book, Wikifonia et Band-in-a-Box. Passer
  par les sources primaires (WJazzD, JAAH, iRb).
- **iReal Pro (forum)** — aucune licence accordée aux tiers ; les grilles sont des contenus
  d'utilisateurs sur des œuvres sous droits. Pour l'analyse, iRb couvre le même usage avec
  une licence publiée.
- **Lakh MIDI** — CC BY 4.0 déclarée sur une collecte web de MIDI dont l'auteur dit lui-même
  n'avoir transcrit aucun ; aucune étiquette de genre jazz ; provenance individuelle
  inconnue.
- **MAESTRO** — CC BY-NC-SA 4.0, répertoire classique : pertinence nulle pour E5–E7.

### 3.3 Pistes non examinées jusqu'au bout

- **Dig That Lick (DTL1000)** : 1 736 solos extraits automatiquement de l'audio (page d'accueil
  du projet) ; aucune licence de données trouvée sur le site consulté → **non vérifiée**.
- **Jazz Corpus (Granroth-Wilding & Steedman, 76 grilles)** : cité par ChoCo ; licence
  **non vérifiée**.
- **Real Book annoté (Mauch et al. 2007)** : licence **non vérifiée** ; repose sur le *Real
  Book*, recueil sous droits.

---

## 4. L'ancien corpus `references/jazz-calm`, `jazz-upbeat`, `training-backing`

- **Ce que c'est** : trois catégories de l'ancien pipeline de qualité (moteur piloté par les
  émotions), créées par le commit `1dadd85` (2026-03-24, « expand reference corpus from 28 to
  180 MIDI files »). Seuls les `meta.json` sont versionnés ; les MIDI sont gitignorés
  (`references/*/*.mid`) et **absents** du worktree ; les `profile.json` aussi (gitignorés).
  Les `harmonium_params` (tension, densité, *smoothness*, valence) visaient l'ancien
  *mapper* émotionnel.
- **Provenance** (`scripts/download_corpus.sh`) :
  - `jazz-calm` (53) et `jazz-upbeat` (38) : MIDI de **Doug McKenzie** (pianiste),
    `https://www.bushgrafts.com/jazz/Midi%20site/` — ses arrangements et interprétations, en
    piano solo ou en trio, de standards presque tous **sous droits** (*Moon River*, *Lush
    Life*, *Autumn Leaves*…) ;
  - `training-backing` (29 entrées dans `meta.json`) : le script en télécharge 27 —
    21 MIDI McKenzie + 6 MIDI classiques de `midiworld.com` (Mozart, Beethoven, Bach) ;
    `skylark.mid` et `debussy_arabesque1.mid` sont listés sans être téléchargés dans ce
    dossier (ils le sont dans `jazz-calm` et `ambient`) ; licence de midiworld **non vérifiée**.
- **Licence** : **non précisée**. Le site (consulté le 2026-10-30) dit seulement que les
  fichiers sont « freely available on this website » et vend une image ISO de l'ensemble ;
  aucune licence ni autorisation de réutilisation. Double couche de droits : arrangement de
  McKenzie + composition sous-jacente.
- **Peut-il servir ?** Oui, **en analyse seule (usage A)** : c'est la seule source à portée de
  main qui contienne de vrais **voicings de comping** de pianiste (arrangements trio), utile
  pour mesurer ce que E5 doit produire (étendue, nombre de notes, part des voicings sans
  fondamentale, mouvement des voix). Non : comme base d'un profil distribué, comme référence de
  walking bass ou de batterie (arrangements piano, GM/XG non homogènes), ni via ses
  `harmonium_params` obsolètes. La catégorie `training-backing` mêle jazz et classique : sans
  objet pour E7.

---

## 5. Recommandation

### Combinaison 1 (recommandée) — distribuable, sans source NC

**WJazzD (statistiques par temps, sous-ensemble swing) + GMD (batterie jazz/swing) + JTD
(timing) + grilles du domaine public et formes communes.**

| Couche du profil | Source | Licence | Mention à porter |
|---|---|---|---|
| Walking bass (E6) : degrés par position, approches, registre | WJazzD `beats.bass_pitch` × `chord` (rhythmfeel SWING ; sous-ensemble *Blues* pour la variante blues) | ODbL 1.0 / DbCL 1.0 | ODbL §4.3 (Produced Work) |
| Rythme harmonique, tempos, formes (tests, labo) | WJazzD `beats`, `solo_info`, `composition_info` | ODbL 1.0 | ODbL §4.3 |
| Batterie swing (ride, charleston, comping, fills) | GMD `jazz/*`, `blues/shuffle` | CC BY 4.0 | Attribution Gillick et al. 2019 |
| Swing ratio, placement basse/batterie/piano | JTD `beats.csv`, `*_onset.csv` | MIT | Notice MIT |
| Grilles de démo et de test | Domaine public (US et Canada) + formes communes | — | Œuvre, compositeur, année |
| Voicings (E5) | Règles de métier codées ; validation au labo contre PiJAMA / McKenzie (usage A) | — | — |

**Risques.**
1. Le comping (E5) n'a **aucune source distribuable** de voicings : il repose sur des règles
   connues, validées au labo contre des sources en usage A et à l'écoute. C'est la couche la
   plus fragile.
2. `bass_pitch` de WJazzD : provenance (manuelle ou automatique) non précisée ; les erreurs
   d'octave éventuelles faussent les intervalles → contrôler sur un échantillon.
3. Biais de WJazzD : solos d'improvisateurs, POSTBOP 147/456 ; la basse est celle qui
   accompagne ces solos (étendue historique non mesurée ici) → filtrer par
   `rhythmfeel = SWING` et `style`.
4. GMD : peu de swing étiqueté (11 + 46 fichiers) ; batteries jouées sur kit électronique.
5. Interprétation de l'ODbL pour un profil TOML : traité ici comme Produced Work ; si un jour
   on versionne des tables substantielles extraites de la base, c'est une Derivative Database
   → partage sous ODbL obligatoire.
6. Domaine public : vérifier chaque grille dans **les deux** juridictions (le profil est
   distribué hors des États-Unis) ; s'en tenir aux formes communes en cas de doute.

### Combinaison 2 — labo enrichi (analyse seule), en plus de la 1

**+ iRb (grilles variées pour rendre le moteur sous 1 186 standards), PiJAMA et McKenzie
(voicings), JAAH (audio aligné, via `audioref`).** Aucune de ces sources n'entre dans un profil
distribué ; leurs dérivés agrégés restent au labo (D1). Risque : glissement d'une statistique
NC dans un profil ; parade : champ `licence` obligatoire dans chaque `manifest.jsonl` et refus
des sources NC/SA au moment de construire un profil distribué.

### Nom de profil proposé : `wjazzd_swing`

- Le principe VII exige un nom par **source précise** (tradition datée ou jeu et zone,
  ex. `nt_desert`), jamais une étiquette générique : `jazz`, `blues`, `jazz_blues`, `swing`
  seuls sont exclus.
- La couche qui définit l'identité mesurable du profil (basse, rythme harmonique, tempos) et
  le corpus contre lequel le labo calcule la distance sont le **sous-ensemble
  `rhythmfeel = SWING` de la Weimar Jazz Database** (361 solos). `wjazzd_swing` nomme ce
  corpus et ce sous-ensemble, comme `nt_desert` nomme un jeu et une zone. GMD et JTD sont des
  couches d'appoint listées dans le manifeste, pas l'identité du style.
- Variante si le propriétaire veut un profil blues strict : `wjazzd_swing_blues` (solos
  *swing* sur forme *Blues* : 87 solos).
- Écarté : un nom de tradition datée (ex. « swing états-unien 1935–1960 ») — l'étendue
  historique du sous-ensemble n'a pas été mesurée ici, et le nom promettrait une époque que le
  corpus ne garantit pas.

---

## 6. Questions ouvertes pour le propriétaire

1. Accepter les **mentions** exigées dans le profil distribué : ODbL §4.3 (WJazzD), CC BY
   (GMD), MIT (JTD) ?
2. Domaine public des grilles : exiger **États-Unis et Canada** (exclut *Body and Soul*,
   *Georgia on My Mind*), ou États-Unis seulement ?
3. Autoriser les sources **NC/SA** (PiJAMA, JHT, JAAH) pour l'analyse au labo, en sachant
   qu'elles ne peuvent jamais nourrir un profil distribué ?
4. Nom : `wjazzd_swing` (swing général) ou `wjazzd_swing_blues` (blues seulement) ?
5. Ancien corpus `jazz-*` : le garder en analyse seule pour E5 (voicings McKenzie) ou retirer
   ses `meta.json` et la section du script ?
