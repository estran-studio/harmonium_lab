# Recensement des sources du corpus trad — Harmonium Lab (DS-T6)

Ce document recense les sources candidates pour l'extension multi-styles du corpus musical de référence d'Harmonium, couvrant les traditions **québécoise**, **acadienne** et **britannique coloniale** (vers 1760–1840).

Conformément aux principes de la constitution Harmonium :
- **Principe V (Style en données)** : chaque tradition et type d'air s'appuie sur des données réelles distribuées par profil statistique.
- **Principe VII (Respect des traditions)** : la provenance et les droits sont rigoureusement documentés ; **aucune musique autochtone n'est collectée dans cette tâche** (la consultation préalable des nations est obligatoire avant toute collecte).
- **Décision D1 (Usage interne)** : les fichiers musicaux bruts sont téléchargés en cache local gitignoré et **ne sont jamais redistribués** ; seuls les manifestes (`manifest.jsonl`), fichiers de version (`VERSION`), statistiques agrégées (`profile.json`) et ce document de recensement sont versionnés.

---

## 1. Tableau de synthèse des sources

| Source | URL principale | Format | Licence / Conditions | Nb d'airs retenus | Tradition | Époque | Décision |
|---|---|---|---|---:|---|---|---|
| **The Session (Québec)** | `github.com/adactio/TheSession-data` | JSON (ABC) | ODbL | 412 | Québécoise | XIXᵉ–XXᵉ s. | **Retenue** |
| **John Chambers (Québec)** | `trillian.mit.edu/~jc/music/abc/Quebec/` | ABC | Non précisée (usage interne, attribution JC) | 352 | Québécoise | XIXᵉ–XXᵉ s. | **Retenue** |
| **The Session (Acadie)** | `github.com/adactio/TheSession-data` | JSON (ABC) | ODbL | 268 | Acadienne | XIXᵉ–XXᵉ s. | **Retenue** |
| **John Chambers (Canada / Acadie)** | `trillian.mit.edu/~jc/music/abc/Canada/reel/` | ABC | Non précisée (usage interne, attribution JC) | 2 | Acadienne | XXᵉ s. | **Retenue** |
| **Nottingham Music Database** | `github.com/jukedeck/nottingham-dataset` | ABC | Domaine public (NMD) / GPL-3.0 (jukedeck) | 980 | Britannique coloniale | c. 1651–1840 | **Retenue** |
| **John Chambers (AmRev & Garnison)** | `trillian.mit.edu/~jc/music/abc/AmRev/` | ABC | Non précisée (domaine public / usage interne) | 21 | Britannique coloniale | c. 1760–1820 | **Retenue** |
| **Thomas Cahusac (1809)** | `trillian.mit.edu/~jc/music/abc/Vintage/` | ABC | Domaine public (Londres, 1809) | 24 | Britannique coloniale | 1809 | **Retenue** |
| **Village Music Project (VMP)** | `village-music-project.org.uk` | ABC | CC-BY-NC-SA | 0 | Britannique | XVIIIᵉ–XIXᵉ s. | **Rejetée** |
| **Giles Gibbs / Buttrey Fife MS** | Connecticut Historical Society / MCH | PDF | Domaine public | 0 | Britannique coloniale | 1777–1800 | **Rejetée** |
| **The Session (Irlandais non filtré)** | `thesession.org` | JSON / ABC | ODbL | 0 | Irlandaise contemporaine | XXᵉ s. | **Rejetée** |
| **Cajun non étiqueté acadien** | Divers recueils cajuns | ABC / MP3 | Variée | 0 | Louisianaise / Cajun | XXᵉ s. | **Rejetée** |
| **Musiques autochtones** | Diverses archives | Divers | Propriété des nations | 0 | Autochtone | Immemorial | **Exclue** |

---

## 2. Sources retenues

### 2.1 Tradition québécoise

#### 1. The Session — Filtrage québécois
- **URL** : `https://github.com/adactio/TheSession-data` (`tunes.json`, `recordings.json`, `aliases.json`)
- **Format** : JSON normalisé avec notation ABC embarquée.
- **Licence** : Open Database License (ODbL).
- **Volume** : 412 airs retenus (après fusion et dédoublonnage avec John Chambers).
- **Critères d'inclusion** :
  1. Enregistré par au moins un artiste québécois documenté dans `quebec_artists.json` (ex. La Bottine Souriante, Jean Carignan, Le Vent du Nord, Genticorum, De Temps Antan, etc.).
  2. OU titre français avéré avec mots-outils ou vocabulaire trad (ex. *Gigue du Pendu*, *Valse Triste*).
  3. OU alias français explicite dans la base.
- **Pertinence** : Pilier fondamental du jeu musical québécois (reels, gigues, valses, marches).

#### 2. John Chambers — Collection Québec
- **URL** : `http://trillian.mit.edu/~jc/music/abc/Quebec/` (sous-dossiers `reel/`, `jig/`, `waltz/`, `march/`, `montrealsession/`, `misc/`, racine)
- **Format** : Fichiers `.abc` individuels avec symboles d'accords guitare/piano.
- **Licence** : Non précisée formellement ; usage interne de recherche avec attribution systématique à John Chambers.
- **Volume** : 352 airs retenus.
- **Pertinence** : Transcriptions de référence avec grilles d'accords explicites, indispensables pour l'accompagnement trad et la génération de cellules harmoniques.

---

### 2.2 Tradition acadienne

#### 3. The Session — Filtrage acadien
- **URL** : `https://github.com/adactio/TheSession-data`
- **Format** : JSON avec notation ABC.
- **Licence** : ODbL.
- **Volume** : 268 airs retenus (168 reels, 55 gigues, 29 hornpipes, 11 marches, 5 valses).
- **Critères d'inclusion** :
  1. Enregistrement par un artiste ou violoneux acadien documenté (`acadian_artists.json`) :
     - **Barachois** (Albert Arsenault, Louise Arsenault, Chuck Arsenault, Hélène Bergeron — Île-du-Prince-Édouard) ;
     - **Vishtèn** (Pastelle LeBlanc, Emmanuelle LeBlanc, Pascal Miousse — Î.-P.-É. / Îles-de-la-Madeleine) ;
     - **Joe Cormier / Joseph Cormier** (Chéticamp, Cap-Breton — violoneux acadien émérite, National Heritage Fellow) ;
     - **The Robichaud Brothers** (Gerry et Armand Robichaud — Saint-Paul, Nouveau-Brunswick) ;
     - **Samantha Robichaud** (Nouveau-Brunswick) ;
     - **Eddy Arsenault** (Baie-Egmont, Î.-P.-É. — grand violoneux acadien) ;
     - **Donny LeBlanc** (Margaree / Chéticamp, Cap-Breton) ;
     - **Suroît** (Îles-de-la-Madeleine) ;
     - **Marc Boudreau** (Cap-Breton) ;
     - **Mario Landry** (Nouveau-Brunswick).
  2. Titre ou alias portant explicitement la racine acadienne (*Acadian*, *Acadie*, *Acadien*, *Acadienne*, *Turlutte Acadienne*, etc.).
- **Pertinence** : Représentation authentique du violon et de la danse acadienne maritime (Nouveau-Brunswick, Baie Sainte-Marie, Chéticamp, Île-du-Prince-Édouard, Îles-de-la-Madeleine).

#### 4. John Chambers — Collection Canada (Avila LeBlanc)
- **URL** : `http://trillian.mit.edu/~jc/music/abc/Canada/reel/`
- **Format** : ABC.
- **Licence** : Non précisée (usage interne, attribution John Chambers).
- **Volume** : 2 airs retenus (*Avila LeBlanc #1*, *Avila LeBlanc #2*).
- **Pertinence** : Airs d'Avila LeBlanc, violoneux acadien majeur de Bouctouche (Nouveau-Brunswick).

---

### 2.3 Tradition britannique coloniale (vers 1760–1840)

#### 5. Nottingham Music Database (NMD)
- **URL** : `https://raw.githubusercontent.com/jukedeck/nottingham-dataset/master/ABC_original/`
- **Format** : ABC.
- **Licence** : Domaine public (compilation originelle par Phil Rowe) / GPL-3.0 (nettoyage jukedeck).
- **Volume** : 980 airs retenus (479 reels / contredanses, 344 gigues, 75 hornpipes, 58 valses, 4 quadrilles).
- **Composantes historiques retenues** :
  - **Ashover Manuscript** (`ashover.abc`, Derbyshire, c. 1764) : recueil manuscrit de David Wall, contemporain direct de la Proclamation royale de 1763 et de la Conquête britannique au Canada. Contient contredanses, gigues et hornpipes authentiques du XVIIIᵉ siècle.
  - **The English Dancing Master** (`playford.abc`, John & Henry Playford, 1651–1728) : contredanses anglaises classiques dansées dans les salons et assemblées de Québec, Trois-Rivières et Montréal.
  - **Hornpipes traditionnels** (`hpps.abc`) : hornpipes britanniques des XVIIIᵉ et XIXᵉ siècles (*Harvest Home*, *Fisher's Hornpipe*, *Sailor's Hornpipe*, *Portsmouth*, *Navvie on the Line*).
  - **Recueils de contredanses, gigues et valses** (`jigs.abc`, `reelsa-c.abc` à `reelsu-z.abc`, `waltzes.abc`).
- **Pertinence** : Base statistique colossale et stylistiquement homogène pour le profilage des danses coloniales anglaises.

#### 6. John Chambers — Collection AmRev et marches de garnison
- **URL** : `http://trillian.mit.edu/~jc/music/abc/AmRev/` et `http://trillian.mit.edu/~jc/music/abc/England/march/`
- **Format** : ABC.
- **Licence** : Non précisée (domaine public / usage interne, attribution John Chambers).
- **Volume** : 21 airs retenus (13 marches AmRev, 12 marches régimentaires, 6 reels, 9 gigues ; 8 doublons fusionnés).
- **Contenu** : Marches de fifre et tambour et contredanses de la guerre de Sept Ans, de la guerre d'Indépendance américaine et de la guerre de 1812 :
  - *The World Turned Upside Down* (marche de garnison britannique jouée à Yorktown en 1781) ;
  - *The British Grenadiers* (marche régimentaire historique) ;
  - *Duke of York's March*, *Hampshire March*, *Holborn March* ;
  - *The White Cockade*, *The Girl I Left Behind Me*, *Rakes of Mallow*, *Road to Boston*.
- **Pertinence** : Clé de voûte de l'ambiance sonore militaire coloniale de 1837 (fifre et tambour, casernes britanniques).

#### 7. Thomas Cahusac — 24 Country Dances for the Year 1809
- **URL** : `http://trillian.mit.edu/~jc/music/abc/Vintage/24CountryDances_1809_Cahusac.abc`
- **Format** : ABC.
- **Licence** : Domaine public (Londres, Thomas Cahusac, 1809).
- **Volume** : 24 airs retenus (12 gigues en 6/8, 8 contredanses en 2/4 ou 4/4, 2 hornpipes, 2 valses).
- **Pertinence** : Publication musicale londonienne de 1809 exportée dans les colonies nord-américaines pour les maîtres de danse et assemblées coloniales.

---

## 3. Sources rejetées ou exclues

### 8. The Village Music Project (VMP)
- **URL** : `https://www.village-music-project.org.uk/`
- **Format** : ABC hétérogène réparti sur des pages web statiques / billets de blog.
- **Licence** : CC-BY-NC-SA.
- **Époque** : 1750–1860 (manuscrits de ménétriers anglais : James Biggins 1779, John Johnson 1748, Dixon 1811).
- **Décision** : **Rejetée**.
- **Justification** : L'accès direct aux fichiers ABC bruts par index HTTP est bloqué (erreur 404 sur les répertoires `/abc/`), obligeant à un grattage (scraping) fragile page par page. En outre, la syntaxe ABC varie considérablement d'un bénévole à l'autre (absence fréquente de barres de reprise standardisées, syntaxe non conforme à music21/abc2midi), ce qui provoquerait un taux de rejet anormalement élevé sans valeur ajoutée par rapport à la Nottingham Database.

### 9. Giles Gibbs Jr. His Book for the Fife (1777) et John Buttrey MS (c. 1780–1800)
- **URL** : Archives de la Connecticut Historical Society et Musée canadien de l'histoire.
- **Format** : Fac-similés manuscrits numérisés (PDF/JPEG).
- **Licence** : Domaine public.
- **Époque** : 1777–1800.
- **Décision** : **Rejetée**.
- **Justification** : Ces recueils majeurs de fifre (dont John Buttrey, fifre britannique stationné au Canada) ne disposent pas d'une transcription intégrale, machine-readable et libre en ABC. Une transcription manuelle note à note sortirait du cadre d'ingestion automatisée de cette tâche.

### 10. The Session — Répertoire irlandais / moderne non filtré
- **URL** : `https://thesession.org/`
- **Format** : JSON.
- **Licence** : ODbL.
- **Époque** : Majoritairement XXᵉ–XXIᵉ siècles (compositions modernes, revival folk).
- **Décision** : **Rejetée**.
- **Justification** : Le répertoire global de The Session est dominé par la musique irlandaise moderne post-1970. Sans filtrage strict par tradition et par artiste, l'incorporer introduirait des tournures modales et harmoniques contemporaines incompatibles avec la réalité musicale de la garnison et des colons britanniques du Bas-Canada vers 1760–1840.

### 11. Répertoire cajun non étiqueté acadien
- **URL** : Collections Cajun ABC (John Chambers `Cajun/`, The Session).
- **Format** : ABC.
- **Licence** : Variée.
- **Époque** : XXᵉ siècle.
- **Décision** : **Rejetée**.
- **Justification** : Conformément à la directive stricte : « *airs de violon acadiens et cajuns seulement si étiquetés acadiens* ». La tradition cajune de Louisiane a connu une histoire distincte après 1755, incorporant des éléments de blues, créoles et country. Seuls les airs portant explicitement la mémoire acadienne ou issus de répertoires maritimes sont conservés pour préserver l'identité du style acadien d'Harmonium.

### 12. Musiques et chants des nations autochtones
- **URL** : N/A.
- **Format** : N/A.
- **Licence** : Propriété culturelle collective des nations autochtones.
- **Décision** : **Exclue** (Principe VII de la Constitution).
- **Justification** : Le principe VII de la constitution Harmonium stipule formellement : *« Pour les musiques autochtones : pas de chants sacrés ou cérémoniels, pas de corpus sans droits clairs, et une validation par des musiciens ou conseillers des nations concernées avant qu'un style entre dans le jeu »*. La directive de la tâche DS-T6 réitère explicitement : *« Pas de musiques autochtones dans cette tâche »*. Aucun air autochtone ne sera collecté ni profilé sans un processus préalable de consultation et de collaboration avec les nations concernées.

---

## 4. Statistiques des corpus retenus

| Tradition | Racine corpus | Airs totaux | Types éligibles au profil (≥ 15 airs) |
|---|---|---:|---|
| **Québécoise** | `corpus/trad/` | 764 | `reel` (576), `jig` (90), `waltz` (69), `march` (18), `quadrille` (16) |
| **Acadienne** | `corpus/acadienne/` | 270 | `reel` (169), `jig` (55), `hornpipe` (29) |
| **Britannique coloniale** | `corpus/britannique_coloniale/` | 1 025 | `reel` (493), `jig` (365), `hornpipe` (78), `waltz` (60), `march` (25) |

Ce recensement garantit la traçabilité complète de chaque air ingéré, l'intégrité déterministe des manifestes et le respect absolu des traditions musicales du jeu *1837*.
