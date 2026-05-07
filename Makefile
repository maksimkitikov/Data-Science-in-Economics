# Build the project end-to-end. `make all` does scrape -> SQLite -> analysis ->
# data.js for the static site -> notebook.

PY := python3

RAW_CHAPTERS  := data/raw/whr_chapters.csv
RAW_PANEL     := data/raw/whr_panel.csv
RAW_WB        := data/raw/wb_indicators.csv
ANALYSIS      := data/clean/analysis.csv
REG_TABLE     := output/tables/regression_summary.csv
CF_IMPORTANCE := output/tables/cf_importance.csv
SITE_DATA     := docs/data.js
NOTEBOOK      := blog.ipynb

.PHONY: all scrape data analysis figures site blog test clean distclean

all: $(NOTEBOOK) $(SITE_DATA)

$(RAW_CHAPTERS): scripts/01_scrape_whr_chapters.py
	$(PY) scripts/01_scrape_whr_chapters.py

$(RAW_PANEL): scripts/02_download_whr_rankings.py
	$(PY) scripts/02_download_whr_rankings.py

$(RAW_WB): scripts/03_download_worldbank.py
	$(PY) scripts/03_download_worldbank.py

scrape: $(RAW_CHAPTERS) $(RAW_PANEL) $(RAW_WB)

$(ANALYSIS): scripts/04_build_database.py $(RAW_PANEL) $(RAW_WB) $(RAW_CHAPTERS)
	$(PY) scripts/04_build_database.py

data: $(ANALYSIS)

$(REG_TABLE): scripts/05_regressions.py $(ANALYSIS)
	$(PY) scripts/05_regressions.py

$(CF_IMPORTANCE): scripts/06_causal_forest.py scripts/07_descriptive_figures.py $(ANALYSIS)
	$(PY) scripts/06_causal_forest.py
	$(PY) scripts/07_descriptive_figures.py

analysis: $(REG_TABLE) $(CF_IMPORTANCE)
figures: $(CF_IMPORTANCE)

$(SITE_DATA): scripts/09_export_json.py $(ANALYSIS) $(REG_TABLE) $(CF_IMPORTANCE)
	$(PY) scripts/09_export_json.py

site: $(SITE_DATA)

$(NOTEBOOK): scripts/08_build_blog.py $(REG_TABLE) $(CF_IMPORTANCE)
	$(PY) scripts/08_build_blog.py

blog: $(NOTEBOOK)

test: $(ANALYSIS) $(REG_TABLE) $(CF_IMPORTANCE)
	$(PY) -m pytest tests/ -q

clean:
	rm -rf data/clean output/figures output/tables \
	       docs/data.js \
	       blog.ipynb

distclean: clean
	rm -rf data/raw
