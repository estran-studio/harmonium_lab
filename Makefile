VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
LAB := $(VENV)/bin/harmonium-lab
REFS_DIR := references
GENERATED_DIR := ../harmonium/harmonium_core/target/generated_music
REPORTS_DIR := target/quality_reports
TRAD_DIR := corpus/trad

.PHONY: setup corpus profiles trad-corpus trad-render trad-profiles check-cells profile-draft test lab-export suite gate clean help trad-sf2 feet-preview fiddle-samples fiddle-sf2 fiddle-compare engine-tunes engine-reels

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
# ── Moteur : exports par style pour trad-compare / blindtest ──
# ENGINE_DIR vaut ../harmonium par défaut ; STYLE est l'id du profil moteur.
ENGINE_DIR ?= ../harmonium
ENGINE_TUNES_DIR := target/engine_tunes
N ?= 20
STYLE ?= reel_quebecois
ENGINE_BARS ?= 36
FEET ?= 1

engine-tunes: setup ## Exporte N airs moteur (STYLE=id, seeds 1..N) → target/engine_tunes/<id>/
	@test -f "$(ENGINE_DIR)/Cargo.toml" || (echo "Moteur introuvable: $(ENGINE_DIR)"; exit 2)
	@mkdir -p "$(ENGINE_TUNES_DIR)/$(STYLE)"
	@for s in $$(seq 1 $(N)); do \
		cargo run -q -p harmonium-cli --release --manifest-path $(ENGINE_DIR)/Cargo.toml -- \
			--soundfont $(ENGINE_DIR)/assets/GeneralUser-GS.sf2 --export --bars $(ENGINE_BARS) --profile $(ENGINE_DIR)/profiles/$(STYLE) --seed $$s --feet $(FEET) \
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
