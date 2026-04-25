# Makefile for the BEE2041 Data-Science-in-Economics empirical project.
#
# Pattern follows the BEE2041-2026 replicationCausalForest/Makefile from the
# course GitHub. A single `make all` rebuilds every figure and table from the
# raw scraped HTML and the World-Bank API.

PY := python3

# Raw inputs produced by the network steps
RAW_CHAPTERS := data/raw/whr_chapters.csv
RAW_PANEL    := data/raw/whr_panel.csv
RAW_WB       := data/raw/wb_indicators.csv

# Cleaned analysis sample
ANALYSIS     := data/clean/analysis.csv

# Output artefacts
BLOG_NB      := blog.ipynb
BLOG_HTML    := docs/index.html
TABLES       := output/tables/regression_summary.csv
FIGS_STAMP   := output/figures/.stamp

.PHONY: all clean scrape data analysis figures blog

all: $(BLOG_NB) $(BLOG_HTML)

#-------------------------------------------------------------------------------
# (1) Acquire raw data
#-------------------------------------------------------------------------------
$(RAW_CHAPTERS): src/01_scrape_whr_chapters.py
	$(PY) src/01_scrape_whr_chapters.py

$(RAW_PANEL): src/02_download_whr_rankings.py
	$(PY) src/02_download_whr_rankings.py

$(RAW_WB): src/03_download_worldbank.py
	$(PY) src/03_download_worldbank.py

scrape: $(RAW_CHAPTERS) $(RAW_PANEL) $(RAW_WB)

#-------------------------------------------------------------------------------
# (2) Build the SQLite database and analysis sample
#-------------------------------------------------------------------------------
$(ANALYSIS): src/04_build_database.py $(RAW_PANEL) $(RAW_WB) $(RAW_CHAPTERS)
	$(PY) src/04_build_database.py

data: $(ANALYSIS)

#-------------------------------------------------------------------------------
# (3) Run the analysis
#-------------------------------------------------------------------------------
$(TABLES): src/05_regressions.py $(ANALYSIS)
	$(PY) src/05_regressions.py

$(FIGS_STAMP): src/06_causal_forest.py src/07_descriptive_figures.py $(ANALYSIS)
	$(PY) src/06_causal_forest.py
	$(PY) src/07_descriptive_figures.py
	@touch $(FIGS_STAMP)

analysis: $(TABLES) $(FIGS_STAMP)
figures:  $(FIGS_STAMP)

#-------------------------------------------------------------------------------
# (4) Render the blog post
#-------------------------------------------------------------------------------
$(BLOG_NB) $(BLOG_HTML): src/08_build_blog.py $(TABLES) $(FIGS_STAMP)
	$(PY) src/08_build_blog.py

blog: $(BLOG_NB) $(BLOG_HTML)

#-------------------------------------------------------------------------------
# Convenience targets
#-------------------------------------------------------------------------------
clean:
	rm -rf data/clean output/figures output/tables docs/index.html blog.ipynb
	@echo "Cleaned. Raw scraped HTML and downloaded XLS files are kept."

distclean: clean
	rm -rf data/raw
	@echo "Wiped raw cache too. Next run will re-scrape from the web."
