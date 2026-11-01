VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
LAB := $(VENV)/bin/harmonium-lab
REFS_DIR := references
GENERATED_DIR := ../harmonium/harmonium_core/target/generated_music
REPORTS_DIR := target/quality_reports
TRAD_DIR := corpus/trad

.PHONY: setup corpus profiles trad-corpus trad-render trad-profiles trad-ornaments check-cells profile-draft test lab-export suite gate clean help trad-sf2 feet-preview fiddle-samples fiddle-sf2 fiddle-compare engine-tunes engine-reels
.PHONY: style-distance seed-variety p2-extract p2-enrich
.PHONY: backing-fetch backing-measures backing-values backing-validate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ════════════════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════════════════

setup: $(VENV)/bin/activate ## Create venv and install harmonium_lab
$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

# ════════════════════════════════════════════════════════════════════
# REFERENCE CORPUS
# ════════════════════════════════════════════════════════════════════

corpus: ## Download reference MIDI corpus (28 files, 5 categories)
	bash scripts/download_corpus.sh

profiles: setup ## Build reference profiles from corpus MIDI files
	@for cat in ambient jazz-calm jazz-upbeat training-backing classical-simple; do \
		echo "Building profile: $$cat..."; \
		$(LAB) profile \
			--input "$(REFS_DIR)/$$cat" \
			--category "$$cat" \
			--output "$(REFS_DIR)/$$cat/profile.json"; \
	done
	@echo "All profiles built."

CORPUS_ROOT ?= corpus
trad-ornaments: setup ## Mesurer les ornements écrits ABC par tradition, position et source (DS-T10)
	$(LAB) trad-ornaments --corpus-root $(CORPUS_ROOT)

trad-profiles: setup ## Build trad type profiles from corpus/* (DS-T3/D5/DS-T6)
	@if [ -d corpus/trad/tunes ]; then \
		for type in reel jig waltz march quadrille cotillon; do \
			if [ -d "corpus/trad/tunes/$$type" ]; then \
				echo "Building trad profile (quebecois): $$type..."; \
				$(LAB) trad-profile \
					--type "$$type" \
					--corpus "corpus/trad" \
					--output "$(REFS_DIR)/trad-$$type/profile.json"; \
			fi; \
		done; \
	fi
	@if [ -d corpus/acadienne/tunes ]; then \
		for type in reel jig hornpipe march waltz; do \
			if [ -d "corpus/acadienne/tunes/$$type" ]; then \
				count=$$(ls corpus/acadienne/tunes/$$type/*.abc 2>/dev/null | wc -l | tr -d ' '); \
				if [ "$$count" -ge 15 ]; then \
					echo "Building trad profile (acadienne): $$type ($$count tunes)..."; \
					$(LAB) trad-profile \
						--type "$$type" \
						--corpus "corpus/acadienne" \
						--output "$(REFS_DIR)/trad-acadienne-$$type/profile.json"; \
				fi; \
			fi; \
		done; \
	fi
	@if [ -d corpus/britannique_coloniale/tunes ]; then \
		for type in reel jig hornpipe march waltz; do \
			if [ -d "corpus/britannique_coloniale/tunes/$$type" ]; then \
				count=$$(ls corpus/britannique_coloniale/tunes/$$type/*.abc 2>/dev/null | wc -l | tr -d ' '); \
				if [ "$$count" -ge 15 ]; then \
					echo "Building trad profile (britannique_coloniale): $$type ($$count tunes)..."; \
					$(LAB) trad-profile \
						--type "$$type" \
						--corpus "corpus/britannique_coloniale" \
						--output "$(REFS_DIR)/trad-britannique_coloniale-$$type/profile.json"; \
				fi; \
			fi; \
		done; \
	fi
	@echo "All trad profiles built."

check-cells: ## Validate a mined CellBank TOML with the engine parser (FILE=path, default target/mined/reel_cells.toml)
	cargo run -q -p harmonium-cli --release --manifest-path $(ENGINE_DIR)/Cargo.toml -- \
		--check-cells $(abspath $(if $(FILE),$(FILE),target/mined/reel_cells.toml))

profile-draft: setup ## Build a preliminary trad style profile (TYPE=..., CORPUS=..., METER=..., EIGHTHS=...)
	@test -n "$(TYPE)" || (echo "Usage: make profile-draft TYPE=jig|waltz|march [CORPUS=dir] [METER=4/4] [EIGHTHS=8]"; exit 2)
	$(LAB) profile-draft --type "$(TYPE)" --corpus "$(if $(CORPUS),$(CORPUS),$(TRAD_DIR))" $(if $(METER),--meter "$(METER)",) $(if $(EIGHTHS),--eighths-per-bar $(EIGHTHS),)

# ════════════════════════════════════════════════════════════════════
# TRAD CORPUS (specs/001-trad-dataset)
# ════════════════════════════════════════════════════════════════════

TRADITION ?= all
trad-corpus: setup ## Download + normalise trad corpus (TRADITION=all|quebecoise|acadienne|britannique_coloniale)
	$(LAB) trad-corpus --tradition $(TRADITION)

trad-render: setup ## Render des airs réels à armes égales → target/trad_render/ (seed fixe; NO_FEET=1 pour omettre les pieds)
	$(LAB) trad-render --type reel --limit 20 $(if $(SOUNDFONT),--soundfont $(SOUNDFONT),) $(if $(NO_FEET),--no-feet,)
	$(LAB) trad-render --type jig --limit 20 $(if $(SOUNDFONT),--soundfont $(SOUNDFONT),) $(if $(NO_FEET),--no-feet,)
	$(LAB) trad-render --type waltz --limit 20 $(if $(SOUNDFONT),--soundfont $(SOUNDFONT),) $(if $(NO_FEET),--no-feet,)

fiddle-samples: setup ## Télécharge les SF2 autorisées du manifeste SK3 (cache privé)
	$(PYTHON) -m harmonium_lab.trad.fiddle_samples $(if $(OFFLINE),--offline,)

fiddle-sf2: setup ## Construit les violons SK4 (VSCO CC0, FluidR3 MIT), cache privé
	$(PYTHON) -m harmonium_lab.trad.fiddle_sf2 $(if $(OFFLINE),--offline,)

fiddle-compare: setup ## Trois vrais reels × violons SK3/SK4 anonymes → target/fiddle_compare/
	$(PYTHON) -m harmonium_lab.trad.fiddle_compare $(if $(OFFLINE),--offline,)

# ── Pieds SK1 : SoundFont podorythmie + écoute de contrôle ──
# FEET_SF2 : sortie (défaut auto : ../harmonium/assets/ si le moteur est
# à côté, sinon target/). SOUNDFONT : GeneralUser pour feet-preview.
trad-sf2: setup ## Échantillons → prepared → ../harmonium/assets/harmonium_trad.sf2
	$(LAB) feet-fetch
	$(LAB) feet-prepare
	$(LAB) feet-sf2 $(if $(FEET_SF2),--output $(FEET_SF2),)

feet-preview: setup ## Pieds seuls (8 mes.) + reel complet avec nouveaux pieds
	$(LAB) feet-preview $(if $(SOUNDFONT),--soundfont $(SOUNDFONT),) $(if $(FEET_SF2),--feet-soundfont $(FEET_SF2),)

# Banques procédurales : le nom vient de BANK, jamais du code Python.
BANK_DIR ?= samples/$(BANK)
bank-sf2: setup ## Construit une banque : BANK=<nom> [BANK_SF2=sortie.sf2]
	@test -n "$(BANK)" || (echo "Usage: make bank-sf2 BANK=<nom> [BANK_SF2=sortie.sf2]"; exit 2)
	$(PYTHON) -m harmonium_lab.bank.prepare --root "$(BANK_DIR)"
	$(PYTHON) -m harmonium_lab.bank.build --root "$(BANK_DIR)" $(if $(BANK_SF2),--output "$(BANK_SF2)",)

bank-compare: setup ## Écoute/mesures : BANK_SF2=banque.sf2 COMPARE_ARGS='--midis ... --tracks ... [--sustain 81:32:6]'
	@test -n "$(BANK_SF2)" || (echo "BANK_SF2 requis"; exit 2)
	$(PYTHON) -m harmonium_lab.bank.compare --bank "$(BANK_SF2)" $(COMPARE_ARGS)

# ── Moteur : exports par style pour trad-compare / blindtest ──
# ENGINE_DIR vaut ../harmonium par défaut ; STYLE est l'id du profil moteur.
ENGINE_DIR ?= ../harmonium
ENGINE_TUNES_DIR := target/engine_tunes
N ?= 20
STYLE ?= reel_quebecois
ENGINE_BARS ?= 36
PERCUSSION ?= 1

engine-tunes: setup ## Exporte N airs moteur (STYLE=id, seeds 1..N) → target/engine_tunes/<id>/
	@test -f "$(ENGINE_DIR)/Cargo.toml" || (echo "Moteur introuvable: $(ENGINE_DIR)"; exit 2)
	@mkdir -p "$(ENGINE_TUNES_DIR)/$(STYLE)"
	@for s in $$(seq 1 $(N)); do \
		cargo run -q -p harmonium-cli --release --manifest-path $(ENGINE_DIR)/Cargo.toml -- \
			--soundfont $(ENGINE_DIR)/assets/GeneralUser-GS.sf2 --export --bars $(ENGINE_BARS) --profile $(ENGINE_DIR)/profiles/$(STYLE) --seed $$s --percussion $(PERCUSSION) \
			--record-wav $(ENGINE_TUNES_DIR)/$(STYLE)/$(STYLE)_seed$${s}.wav \
			--record-midi $(ENGINE_TUNES_DIR)/$(STYLE)/$(STYLE)_seed$${s}.mid \
			--record-truth $(ENGINE_TUNES_DIR)/$(STYLE)/$(STYLE)_seed$${s}.json \
			> "$(ENGINE_TUNES_DIR)/$(STYLE)/$(STYLE)_seed$${s}.log" 2>&1; \
		status=$$?; cat "$(ENGINE_TUNES_DIR)/$(STYLE)/$(STYLE)_seed$${s}.log"; \
		test $$status -eq 0 || exit $$status; \
	done
	@echo "Engine tunes in $(ENGINE_TUNES_DIR)/$(STYLE)/"

engine-reels: ## Compatibilité d'usage : exporte uniquement reel_quebecois
	$(MAKE) engine-tunes STYLE=reel_quebecois N=$(N) ENGINE_BARS=32

# ── Distance d'un profil à son corpus de référence (phase 014, M1) ──
# Rien de spécifique à un jeu : profil, références et pistes viennent des arguments.
#   make style-distance PROFILE=nt_desert REF=nt-desert TRACKS=02_flashyn,19_a_way \
#        STYLE_CORPUS=/chemin/corpus/nuclear_throne CONTEXT="type=zone" \
#        BANKS="nt_desert=$(ENGINE_DIR)/assets/nt_desert.sf2 generaluser=$(ENGINE_DIR)/assets/GeneralUser-GS.sf2"
# STYLE_CORPUS contient manifest.jsonl, les fichiers audio (champ `file`) et
# transcriptions/ (transcriptions et audio hors dépôt, principe VII).
# Sortie versionnée : references/$(REF)/distance-$(PROFILE).json ; rendus et cache hors dépôt.
DIST_SEEDS ?= 10
DIST_BARS ?= 48
BANKS ?= generaluser=$(ENGINE_DIR)/assets/GeneralUser-GS.sf2
STYLE_DIST_DIR := target/style_distance

style-distance: setup ## PROFILE=id|dossier REF=dossier TRACKS=id,id STYLE_CORPUS=dir [BANKS=label=sf2 ...] [CONTEXT=champ=val] [DIST_SEEDS=10] [DIST_BARS=48] [DIST_OUT=fichier.json]
	@test -n "$(PROFILE)" -a -n "$(REF)" -a -n "$(TRACKS)" -a -n "$(STYLE_CORPUS)" || \
		(echo "Usage: make style-distance PROFILE=<id> REF=<dossier references/> TRACKS=<id,id> STYLE_CORPUS=<dir> [BANKS=label=sf2 ...] [CONTEXT=champ=val]"; exit 2)
	@test -f "$(ENGINE_DIR)/Cargo.toml" || (echo "Moteur introuvable: $(ENGINE_DIR)"; exit 2)
	$(PYTHON) -m harmonium_lab.styledist --profile "$(PROFILE)" --tracks "$(TRACKS)" \
		--manifest "$(STYLE_CORPUS)/manifest.jsonl" --corpus-root "$(STYLE_CORPUS)" \
		$(if $(CONTEXT),--context $(CONTEXT),) \
		$(if $(wildcard $(STYLE_CORPUS)/transcriptions),--transcriptions "$(STYLE_CORPUS)/transcriptions",) \
		$(if $(wildcard $(REFS_DIR)/$(REF)/grids.json),--grids "$(REFS_DIR)/$(REF)/grids.json",) \
		$(if $(STEPS_PER_BAR),--steps-per-bar $(STEPS_PER_BAR),) \
		--engine-dir "$(ENGINE_DIR)" $(foreach b,$(BANKS),--bank "$(b)") \
		--seeds $(DIST_SEEDS) --bars $(DIST_BARS) --work-dir "$(STYLE_DIST_DIR)" \
		-o "$(if $(DIST_OUT),$(DIST_OUT),$(REFS_DIR)/$(REF)/distance-$(PROFILE).json)" --markdown

# ── Variété par graine et alternatives extraites P2 (phase 018) ──
# make seed-variety ENGINE_DIR=~/Project/bascanada/harmonium [LABEL=V1] [VARIETY_PROFILES="nt_desert isaac_cellar /tmp/…/isaac_basement_p2"]
#   Graines 1..VARIETY_SEEDS × VARIETY_BARS mesures ; JSON + tableau. ENGINE_BIN : binaire harmonium-cli déjà compilé.
# make p2-extract ENGINE_DIR=… CORPUS_ROOT=~/Project/bascanada/harmonium_lab/corpus [P2_PROFILES="isaac_cellar"]
#   Écrit references/<profil>/proposals/<profil>.toml (transcriptions hors dépôt, principe VII).
# make p2-enrich ENGINE_DIR=… PROFILE=isaac_cellar PROPOSAL=references/isaac-cellar/proposals/isaac_cellar.toml OUT=/tmp/…/isaac_cellar_p2
#   Copie temporaire du profil enrichie des propositions (poids rééquilibrés ; RAW_WEIGHTS=1 pour les effectifs bruts).
VARIETY_PROFILES ?= nt_desert isaac_basement isaac_cellar isaac_burning isaac_downpour
VARIETY_SEEDS ?= 16
VARIETY_BARS ?= 64
VARIETY_DIR ?= target/seed_variety

seed-variety: setup ## Variété par graine : [VARIETY_PROFILES="id|dossier ..."] [LABEL=V1] [VARIETY_SEEDS=16] [VARIETY_BARS=64] [ENGINE_BIN=harmonium-cli]
	$(LAB) seed-variety $(foreach p,$(VARIETY_PROFILES),--profile "$(p)") \
		--seeds $(VARIETY_SEEDS) --bars $(VARIETY_BARS) --engine-dir "$(ENGINE_DIR)" \
		$(if $(ENGINE_BIN),--engine-bin "$(ENGINE_BIN)",) $(if $(LABEL),--label "$(LABEL)",) \
		--work-dir "$(VARIETY_DIR)" -o "$(VARIETY_DIR)/seed-variety$(if $(LABEL),-$(LABEL),).json" --markdown

P2_PROFILES ?= isaac_basement isaac_cellar isaac_burning isaac_downpour nt_desert

p2-extract: setup ## Propositions P2 : CORPUS_ROOT=<dossier avec isaac/ et nuclear_throne/> [P2_PROFILES="id ..."]
	$(LAB) p2-extract $(foreach p,$(P2_PROFILES),--profile $(p)) --engine-dir "$(ENGINE_DIR)" \
		--corpus-root "$(CORPUS_ROOT)" --refs "$(REFS_DIR)"

p2-enrich: setup ## Copie enrichie : PROFILE=id PROPOSAL=toml OUT=dossier [RAW_WEIGHTS=1]
	@test -n "$(PROFILE)" -a -n "$(PROPOSAL)" -a -n "$(OUT)" || (echo "Usage: make p2-enrich PROFILE=<id> PROPOSAL=<toml> OUT=<dossier>"; exit 2)
	$(LAB) p2-enrich --profile "$(PROFILE)" --proposal "$(PROPOSAL)" --out "$(OUT)" \
		--engine-dir "$(ENGINE_DIR)" $(if $(RAW_WEIGHTS),--raw-weights,)

# ── Accompagnement mesuré : profil `wjazzd_swing` (phase 018, E7) ──
# Sources en cache gitignoré (corpus/{wjazzd,gmd,jtd}/raw/), SHA256 vérifié avant toute lecture ;
# manifestes, VERSION et mesures agrégées (references/wjazzd-swing/) versionnés.
# make backing-fetch      télécharge et vérifie WJazzD (ODbL), GMD (CC BY 4.0), JTD (MIT)
# make backing-measures   manifestes + mesures de basse, de batterie et de timing
# make backing-values     percussion.toml et poids de basse du profil, depuis les mesures
#                         (OUT=<fichier> écrit le percussion.toml ; HEADER=<fichier> son en-tête)
# make backing-validate   basse générée par le moteur contre WJazzD : PROFILES="id=dossier ..." [BACKING_SEEDS=8] [BACKING_SEED_START=1]
#                         [BACKING_BARS=56] [BACKING_GROUPS="all blues"] [BACKING_OUT=references/wjazzd-swing/validation-bass.json]
BACKING_SEEDS ?= 8
BACKING_SEED_START ?= 1
BACKING_BARS ?= 56
BACKING_GROUPS ?= all
BACKING_OUT ?= references/wjazzd-swing/validation-bass.json

backing-fetch: setup ## Télécharge et vérifie les sources d'accompagnement (WJazzD, GMD, JTD)
	$(PYTHON) -m harmonium_lab.backing.wjazzd --fetch
	$(PYTHON) -m harmonium_lab.backing.drums --fetch
	$(PYTHON) -m harmonium_lab.backing.timing --fetch

backing-measures: setup ## Manifestes et mesures agrégées (basse, batterie, timing) dans references/wjazzd-swing/
	$(PYTHON) -m harmonium_lab.backing.wjazzd --manifest
	$(PYTHON) -m harmonium_lab.backing.bass_measures
	$(PYTHON) -m harmonium_lab.backing.drums --manifest --measures
	$(PYTHON) -m harmonium_lab.backing.timing --manifest --measures

backing-values: setup ## Poids de basse et percussion.toml du profil : [OUT=fichier] [HEADER=fichier]
	$(PYTHON) -m harmonium_lab.backing.engine_values --table \
		$(if $(OUT),--percussion "$(OUT)",) $(if $(HEADER),--header "$(HEADER)",)

backing-validate: setup ## Basse générée vs WJazzD : PROFILES="id=dossier ..." [ENGINE_BIN=harmonium-cli] [BACKING_SEEDS=8]
	@test -n "$(PROFILES)" || (echo 'Usage: make backing-validate PROFILES="wjazzd_swing=../harmonium/profiles/wjazzd_swing ..."'; exit 2)
	$(PYTHON) -m harmonium_lab.backing.validate --engine-dir "$(ENGINE_DIR)" \
		$(if $(ENGINE_BIN),--engine-bin "$(ENGINE_BIN)",) $(foreach p,$(PROFILES),--profile "$(p)") \
		--seeds $(BACKING_SEEDS) --seed-start $(BACKING_SEED_START) --bars $(BACKING_BARS) $(foreach g,$(BACKING_GROUPS),--group $(g)) \
		-o "$(BACKING_OUT)" --markdown

# ════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════
# ANALYSIS
# ════════════════════════════════════════════════════════════════════

lab-export: ## Generate MIDI+JSON from harmonium (runs Rust tests)
	cd ../harmonium && $(MAKE) test/lab-export

suite: setup ## Run full analysis suite on generated music
	@mkdir -p $(REPORTS_DIR)
	$(LAB) suite \
		-i $(GENERATED_DIR) \
		-o $(REPORTS_DIR) \
		$(if $(PROFILE),--profile $(PROFILE),)

gate: ## Run quality gate on latest reports (REPORT=path required)
	$(LAB) gate \
		--report $(REPORT) \
		$(if $(BASELINE),--baseline $(BASELINE),) \
		$(if $(MIN_COMPOSITE),--min-composite $(MIN_COMPOSITE),)

# ════════════════════════════════════════════════════════════════════
# FULL PIPELINE
# ════════════════════════════════════════════════════════════════════

pipeline: lab-export suite ## Full pipeline: generate music → analyze → report
	@echo ""
	@echo "Pipeline complete. Reports in $(REPORTS_DIR)/"

# ════════════════════════════════════════════════════════════════════
# TESTING
# ════════════════════════════════════════════════════════════════════

test: setup ## Run all Python tests
	$(VENV)/bin/pytest tests/ -v

# ════════════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════════════

clean: ## Remove generated reports and profiles
	rm -rf $(REPORTS_DIR)
	rm -f $(REFS_DIR)/*/profile.json

clean-all: clean ## Remove venv and all generated files
	rm -rf $(VENV) .pytest_cache __pycache__ src/harmonium_lab/__pycache__
