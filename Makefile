VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
LAB := $(VENV)/bin/harmonium-lab
REFS_DIR := references
GENERATED_DIR := ../harmonium/harmonium_core/target/generated_music
REPORTS_DIR := target/quality_reports
TRAD_DIR := corpus/trad

.PHONY: setup corpus profiles trad-corpus trad-render trad-profiles test lab-export suite gate clean help

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

trad-profiles: setup ## Build trad type profiles from corpus/trad (DS-T3/D5)
	@if [ ! -d corpus/trad/tunes ]; then \
		echo "corpus/trad/tunes missing (run \`make trad-corpus' first)"; \
		exit 1; \
	fi
	@for type in reel jig waltz march quadrille cotillon; do \
		if [ -d "corpus/trad/tunes/$$type" ]; then \
			echo "Building trad profile: $$type..."; \
			$(LAB) trad-profile \
				--type "$$type" \
				--corpus "corpus/trad" \
				--output "$(REFS_DIR)/trad-$$type/profile.json"; \
		else \
			echo "Skipping $$type (no tunes)"; \
		fi; \
	done
	@echo "Trad profiles built."

# ════════════════════════════════════════════════════════════════════
# TRAD CORPUS (specs/001-trad-dataset)
# ════════════════════════════════════════════════════════════════════

trad-corpus: setup ## Download + normalise trad québécois corpus → corpus/trad/manifest.jsonl
	$(LAB) trad-corpus --root $(TRAD_DIR)

trad-render: setup ## Render 20 tunes per type at parity → target/trad_render/ (seed fixe)
	$(LAB) trad-render --type reel --limit 20 $(if $(SOUNDFONT),--soundfont $(SOUNDFONT),)
	$(LAB) trad-render --type jig --limit 20 $(if $(SOUNDFONT),--soundfont $(SOUNDFONT),)
	$(LAB) trad-render --type waltz --limit 20 $(if $(SOUNDFONT),--soundfont $(SOUNDFONT),)

# ── Moteur : reels générés pour trad-compare / blindtest (DS-T4) ──
# ENGINE_DIR vaut ../harmonium sur machine du propriétaire (repo frère).
ENGINE_DIR ?= ../harmonium
ENGINE_REELS_DIR := target/engine_reels
N ?= 10

engine-reels: setup ## Exporte N reels du moteur (seeds 1..N, 32 mesures) → target/engine_reels/
	@mkdir -p $(ENGINE_REELS_DIR)
	@for s in $$(seq 1 $(N)); do \
		echo "Export reel seed $$s..."; \
		cargo run -q -p harmonium-cli --release --manifest-path $(ENGINE_DIR)/Cargo.toml -- \
			--export --bars 32 --style reel --seed $$s \
			--record-wav $(ENGINE_REELS_DIR)/reel_seed$${s}.wav \
			--record-midi $(ENGINE_REELS_DIR)/reel_seed$${s}.mid || exit 1; \
	done
	@echo "Engine reels in $(ENGINE_REELS_DIR)/"

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
