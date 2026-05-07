# Build the project end-to-end. `make all` does scrape -> SQLite -> analysis ->
# JSON for docs -> notebook + companion HTML.

PY := python3

RAW_CHAPTERS  := data/raw/whr_chapters.csv
RAW_PANEL     := data/raw/whr_panel.csv
RAW_WB        := data/raw/wb_indicators.csv
ANALYSIS      := data/clean/analysis.csv
REG_TABLE     := output/tables/regression_summary.csv
CF_IMPORTANCE := output/tables/cf_importance.csv
SITE_JSON     := docs/data/countries.json
NOTEBOOK      := blog.ipynb
NOTEBOOK_HTML := docs/notebook.html

.PHONY: all scrape data analysis figures site blog hf-bundle test pdf clean distclean

all: $(NOTEBOOK) $(NOTEBOOK_HTML) $(SITE_JSON) hf-bundle

$(RAW_CHAPTERS): src/01_scrape_whr_chapters.py
	$(PY) src/01_scrape_whr_chapters.py

$(RAW_PANEL): src/02_download_whr_rankings.py
	$(PY) src/02_download_whr_rankings.py

$(RAW_WB): src/03_download_worldbank.py
	$(PY) src/03_download_worldbank.py

scrape: $(RAW_CHAPTERS) $(RAW_PANEL) $(RAW_WB)

$(ANALYSIS): src/04_build_database.py $(RAW_PANEL) $(RAW_WB) $(RAW_CHAPTERS)
	$(PY) src/04_build_database.py

data: $(ANALYSIS)

$(REG_TABLE): src/05_regressions.py $(ANALYSIS)
	$(PY) src/05_regressions.py

$(CF_IMPORTANCE): src/06_causal_forest.py src/07_descriptive_figures.py $(ANALYSIS)
	$(PY) src/06_causal_forest.py
	$(PY) src/07_descriptive_figures.py

analysis: $(REG_TABLE) $(CF_IMPORTANCE)
figures: $(CF_IMPORTANCE)

$(SITE_JSON): src/09_export_json.py $(ANALYSIS) $(REG_TABLE) $(CF_IMPORTANCE)
	$(PY) src/09_export_json.py

site: $(SITE_JSON)

$(NOTEBOOK) $(NOTEBOOK_HTML): src/08_build_blog.py $(REG_TABLE) $(CF_IMPORTANCE)
	$(PY) src/08_build_blog.py

blog: $(NOTEBOOK) $(NOTEBOOK_HTML)

# Mirror docs/ into huggingface_space/ for HF Space deployment.
hf-bundle: $(SITE_JSON) docs/index.html docs/style.css docs/site.js docs/plotly.min.js docs/favicon.svg
	@mkdir -p huggingface_space
	@cp docs/index.html docs/style.css docs/site.js docs/plotly.min.js \
	    docs/data.js docs/favicon.svg huggingface_space/
	@rm -rf huggingface_space/data
	@cp -r docs/data huggingface_space/data
	@echo "huggingface_space/ synced"

test: $(ANALYSIS) $(REG_TABLE) $(CF_IMPORTANCE)
	$(PY) -m pytest tests/ -q

pdf: $(NOTEBOOK)
	$(PY) -m nbconvert --to pdf $(NOTEBOOK) \
	    --output "Beyond GDP_ What Drives National Happiness_.pdf"

clean:
	rm -rf data/clean output/figures output/tables \
	       docs/notebook.html docs/data \
	       blog.ipynb

distclean: clean
	rm -rf data/raw
