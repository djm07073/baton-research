TECTONIC ?= tectonic
BUILD := build
ROOT_PDF := ../../output/pdf
TEX_INPUTS := $(wildcard sections/*.tex) $(wildcard figures/*.tex) preamble.tex references.bib usenix2019_v3.sty

.PHONY: all latexmk publish
all: $(BUILD)/main.pdf $(BUILD)/review-notes.pdf $(BUILD)/placement-supplement.pdf

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/main.pdf: main.tex $(TEX_INPUTS) | $(BUILD)
	$(TECTONIC) --keep-logs --keep-intermediates --outdir $(BUILD) main.tex

$(BUILD)/review-notes.pdf: review-notes.tex preamble.tex references.bib | $(BUILD)
	$(TECTONIC) --keep-logs --keep-intermediates --outdir $(BUILD) review-notes.tex

$(BUILD)/placement-supplement.pdf: placement-supplement.tex $(TEX_INPUTS) | $(BUILD)
	$(TECTONIC) --keep-logs --keep-intermediates --outdir $(BUILD) placement-supplement.tex

latexmk: | $(BUILD)
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD) main.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD) review-notes.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD) placement-supplement.tex

publish: all
	mkdir -p $(ROOT_PDF)
	cp $(BUILD)/main.pdf $(ROOT_PDF)/state-finalization-working-draft.pdf
	cp $(BUILD)/review-notes.pdf $(ROOT_PDF)/state-finalization-review-notes.pdf
	cp $(BUILD)/placement-supplement.pdf $(ROOT_PDF)/state-finalization-supplement.pdf
