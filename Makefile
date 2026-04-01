# Build the BEE2041 empirical project end-to-end.
# `make all` rebuilds the data, the analysis, the JSON used by docs/, the
# executed notebook (blog.ipynb) and the rendered companion (docs/notebook.html).

PY := python3

RAW_CHAPTERS := data/raw/whr_chapters.csv
RAW_PANEL    := data/raw/whr_panel.csv
RAW_WB       := data/raw/wb_indicators.csv

ANALYSIS     := data/clean/analysis.csv

TABLES       := output/tables/regression_summary.csv
FIGS_STAMP   := output/figures/.stamp

SITE_DATA     := docs/data/.stamp
NOTEBOOK      := blog.ipynb
NOTEBOOK_HTML := docs/notebook.html

.PHONY: all clean distclean scrape data analysis figures site blog hf-bundle

all: $(NOTEBOOK) $(NOTEBOOK_HTML) $(SITE_DATA) hf-bundle

# raw data
$(RAW_CHAPTERS): src/01_scrape_whr_chapters.py
	$(PY) src/01_scrape_whr_chapters.py

$(RAW_PANEL): src/02_download_whr_rankings.py
	$(PY) src/02_download_whr_rankings.py

$(RAW_WB): src/03_download_worldbank.py
	$(PY) src/03_download_worldbank.py

scrape: $(RAW_CHAPTERS) $(RAW_PANEL) $(RAW_WB)

# SQLite + analysis sample
$(ANALYSIS): src/04_build_database.py $(RAW_PANEL) $(RAW_WB) $(RAW_CHAPTERS)
	$(PY) src/04_build_database.py

data: $(ANALYSIS)

# regressions and figures
$(TABLES): src/05_regressions.py $(ANALYSIS)
	$(PY) src/05_regressions.py

$(FIGS_STAMP): src/06_causal_forest.py src/07_descriptive_figures.py $(ANALYSIS)
	$(PY) src/06_causal_forest.py
	$(PY) src/07_descriptive_figures.py
	@touch $(FIGS_STAMP)

analysis: $(TABLES) $(FIGS_STAMP)
figures:  $(FIGS_STAMP)

# JSON for the static site
$(SITE_DATA): src/09_export_json.py $(ANALYSIS) $(TABLES) $(FIGS_STAMP)
	$(PY) src/09_export_json.py
	@touch $(SITE_DATA)

site: $(SITE_DATA)

# blog notebook + companion HTML
$(NOTEBOOK) $(NOTEBOOK_HTML): src/08_build_blog.py $(TABLES) $(FIGS_STAMP)
	$(PY) src/08_build_blog.py

blog: $(NOTEBOOK) $(NOTEBOOK_HTML)

# Hugging Face bundle: mirror of docs/ + Space-specific README
hf-bundle: $(SITE_DATA) docs/index.html docs/style.css docs/site.js docs/plotly.min.js docs/favicon.svg
	@mkdir -p huggingface_space
	@cp docs/index.html docs/style.css docs/site.js docs/plotly.min.js \
	    docs/data.js docs/favicon.svg huggingface_space/
	@rm -rf huggingface_space/data
	@cp -r docs/data huggingface_space/data
	@echo "huggingface_space/ synced"

clean:
	rm -rf data/clean output/figures output/tables \
	       docs/notebook.html docs/data \
	       blog.ipynb

distclean: clean
	rm -rf data/raw
