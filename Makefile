# Build the BEE2041 empirical project end-to-end.
#
# `make all` rebuilds the data, the analysis, the JSON files used by the
# interactive site in docs/, the executed notebook (blog.ipynb) and the
# rendered notebook companion (docs/notebook.html).

PY := python3

# Raw network inputs
RAW_CHAPTERS := data/raw/whr_chapters.csv
RAW_PANEL    := data/raw/whr_panel.csv
RAW_WB       := data/raw/wb_indicators.csv

# Cleaned outputs
ANALYSIS     := data/clean/analysis.csv

# Tables / figures stamp
TABLES       := output/tables/regression_summary.csv
FIGS_STAMP   := output/figures/.stamp

# Site assets
SITE_DATA    := docs/data/.stamp
NOTEBOOK     := blog.ipynb
NOTEBOOK_HTML := docs/notebook.html

.PHONY: all clean distclean scrape data analysis figures site blog hf-bundle

all: $(NOTEBOOK) $(NOTEBOOK_HTML) $(SITE_DATA) hf-bundle

# ---------------------------------------------------------------- raw data
$(RAW_CHAPTERS): src/01_scrape_whr_chapters.py
	$(PY) src/01_scrape_whr_chapters.py

$(RAW_PANEL): src/02_download_whr_rankings.py
	$(PY) src/02_download_whr_rankings.py

$(RAW_WB): src/03_download_worldbank.py
	$(PY) src/03_download_worldbank.py

scrape: $(RAW_CHAPTERS) $(RAW_PANEL) $(RAW_WB)

# ----------------------------------------------------------------- SQLite
$(ANALYSIS): src/04_build_database.py $(RAW_PANEL) $(RAW_WB) $(RAW_CHAPTERS)
	$(PY) src/04_build_database.py

data: $(ANALYSIS)

# ---------------------------------------------------------------- analysis
$(TABLES): src/05_regressions.py $(ANALYSIS)
	$(PY) src/05_regressions.py

$(FIGS_STAMP): src/06_causal_forest.py src/07_descriptive_figures.py $(ANALYSIS)
	$(PY) src/06_causal_forest.py
	$(PY) src/07_descriptive_figures.py
	@touch $(FIGS_STAMP)

analysis: $(TABLES) $(FIGS_STAMP)
figures:  $(FIGS_STAMP)

# ---------------------------------------------------------- site JSON data
$(SITE_DATA): src/09_export_json.py $(ANALYSIS) $(TABLES) $(FIGS_STAMP)
	$(PY) src/09_export_json.py
	@touch $(SITE_DATA)

site: $(SITE_DATA)

# ---------------------------------------------------------------- blog
$(NOTEBOOK) $(NOTEBOOK_HTML): src/08_build_blog.py $(TABLES) $(FIGS_STAMP)
	$(PY) src/08_build_blog.py

blog: $(NOTEBOOK) $(NOTEBOOK_HTML)

# ----------------------------------------------------- Hugging Face bundle
# Sync docs/ -> huggingface_space/ so the Space directory is always a
# faithful mirror of the public site, plus the Space-specific README.md.
hf-bundle: $(SITE_DATA) docs/index.html docs/style.css docs/site.js docs/plotly.min.js docs/favicon.svg
	@mkdir -p huggingface_space
	@cp docs/index.html docs/style.css docs/site.js docs/plotly.min.js \
	    docs/data.js docs/favicon.svg huggingface_space/
	@rm -rf huggingface_space/data
	@cp -r docs/data huggingface_space/data
	@echo "Hugging Face bundle synced to huggingface_space/"

# ---------------------------------------------------------------- clean
clean:
	rm -rf data/clean output/figures output/tables \
	       docs/notebook.html docs/data \
	       blog.ipynb
	@echo "Cleaned. The hand-written site (docs/index.html, docs/style.css,"
	@echo "docs/site.js) and the raw scraped/downloaded inputs are kept."

distclean: clean
	rm -rf data/raw
	@echo "Wiped raw cache too. Next run will re-scrape from the web."
