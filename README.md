# Beyond GDP: what really drives national happiness?

BEE2041 Data Science in Economics — Empirical Project, April 2026
Author: Maksim Kitikov, University of Exeter.

This repository contains the full pipeline behind the blog post
*Beyond GDP: what really drives national happiness?*. The project scrapes
chapter metadata from the World Happiness Report website, downloads the
WHR's published Figure 2.1 ranking spreadsheets, queries the World Bank
API for supplementary indicators, integrates the three sources in a small
SQLite database, and finally fits both OLS specifications and a causal
forest (`econml.dml.CausalForestDML`) to study cross-country variation in
life satisfaction.

The blog itself is published as a fully-interactive static website served
from `docs/`. The exact same bundle is mirrored under `huggingface_space/`
for one-click deployment to Hugging Face Spaces (see
[`huggingface_space/DEPLOY.md`](huggingface_space/DEPLOY.md)).

* **Live website (Hugging Face):** <https://mk88889-beyond-gdp.static.hf.space>
* **GitHub Pages mirror:** <https://maksimkitikov.github.io/Data-Science-in-Economics/>
* **Executed notebook:** [`blog.ipynb`](blog.ipynb)
* **Notebook companion (HTML):** [`docs/notebook.html`](docs/notebook.html)
* **Static PDF:** [`Beyond GDP_ What Drives National Happiness_.pdf`](./Beyond%20GDP_%20What%20Drives%20National%20Happiness_.pdf).

---

## 1. Replication in one command

```bash
git clone https://github.com/maksimkitikov/Data-Science-in-Economics.git
cd Data-Science-in-Economics
pip install -r requirements.txt
make all
```

`make all` runs the nine numbered scripts in `src/` in the right order,
rebuilds the SQLite database, regenerates every figure and the regression
table, exports the JSON the website consumes, and re-renders the notebook.
Subsequent runs of `make` only redo the steps whose inputs have changed
(this is the standard `make` semantics described in the
*Workflow, Modelling & Webscraping* lecture).

```bash
make scrape    # network steps only (web-scrape + downloads + WB API)
make data      # build the SQLite database + analysis.csv
make analysis  # regressions + causal forest, regenerate figures
make blog      # render blog.ipynb and docs/index.html
make clean     # wipe everything except raw inputs
make distclean # also wipe the raw HTML cache
```

---

## 2. Repository structure

```
.
├── README.md                       ← this file
├── Makefile                        ← reproducible build pipeline
├── requirements.txt                ← pinned Python dependencies
├── LICENSE                         ← MIT
├── blog.ipynb                      ← the blog post, executed and committed
├── docs/                           ← public website (served by GitHub Pages)
│   ├── index.html
│   ├── style.css
│   ├── site.js
│   ├── plotly.min.js
│   ├── data.js                     ← bundled JSON for offline use
│   ├── data/                       ← per-chart JSON (one file per chart)
│   └── notebook.html               ← executed notebook in HTML form
├── huggingface_space/              ← Hugging Face Space mirror of docs/
├── src/                            ← all source code, numbered in run order
│   ├── 01_scrape_whr_chapters.py
│   ├── 02_download_whr_rankings.py
│   ├── 03_download_worldbank.py
│   ├── 04_build_database.py
│   ├── 05_regressions.py
│   ├── 06_causal_forest.py
│   ├── 07_descriptive_figures.py
│   ├── 08_build_blog.py
│   └── 09_export_json.py
├── data/
│   ├── raw/                        ← never modified after collection
│   └── clean/                      ← derived; rebuildable from raw
├── output/
│   ├── figures/                    ← .pdf and .png twins of every chart
│   └── tables/                     ← LaTeX + tidy CSV companions
├── references/                     ← `sources.md` with every external reference
└── course-materials/               ← the BEE2041 lecture PDFs (uploaded for graders)
```

The directory layout follows the `Workflow, Modelling & Webscraping`
lecture (slide 19, "A Good Directory Structure"): raw data is sacred and
lives only in `data/raw/`, everything else is derived.

---

## 3. Data definition

| Source | What we use | Access | Vintage | Where it lands |
|---|---|---|---|---|
| WHR editions 2020-2026 | chapter metadata: title, authors, affiliations, reading time, DOI | HTTP scrape (`requests` + `BeautifulSoup`) of `worldhappiness.report/ed/{year}/` | snapshot, April 2026 | `data/raw/whr_chapters.csv` (51 chapters) |
| WHR Figure 2.1 spreadsheets | country-level Ladder + 6 explanatory components | HTTP download from `files.worldhappiness.report/` | 2020-2024 | `data/raw/whr_panel.csv` (729 country-years) |
| World Bank WDI | GDP per capita PPP, life expectancy, internet penetration, urbanisation, education spending, FDI | REST API via `wbgapi` | 2022 cross-section | `data/raw/wb_indicators.csv` (266 economies) |

Country names from the three sources are crosswalked to ISO-3 codes in
`src/04_build_database.py`. Unmatched names are explicitly listed in the
console output of that script.

After integration the analysis sample is **136 countries** with full
covariates for the 2023 WHR edition.

---

## 4. Methods

### Web-scraping (`01_scrape_whr_chapters.py`)
`requests` is used (rather than `urllib`) so we can supply a polite
`User-Agent`. Every page is cached to `data/raw/html_cache/`, so the rest
of the build is reproducible offline once the cache exists. Retries use
the exponential back-off pattern recommended in the webscraping lecture
(slide 55).

### SQL integration (`04_build_database.py`)
Three SQLite tables are created (`country_year`, `country_meta`,
`whr_chapters`) with B-tree indexes on the join keys. The analysis sample
is produced by an `INNER JOIN` written in raw SQL.

### Regression (`05_regressions.py`)
Six progressively richer OLS specifications are estimated using
`statsmodels.OLS` with HC3 robust standard errors, exported via `pystout`
to a single LaTeX table.

### Causal forest (`06_causal_forest.py`)
`econml.dml.CausalForestDML` with `GradientBoostingRegressor` /
`GradientBoostingClassifier` nuisance models, 1000 trees, leaf size 5, seed
121316. The "treatment" is a binary indicator for being above the
sample-median GDP per capita PPP; X covers six potential moderators. We
report ATE, CATE histogram, ranked CATEs with 95 % CIs, CATE-vs-GDP, and
the forest's split-importance metric.

---

## 5. Outputs

| File | Description |
|---|---|
| `output/figures/top_bottom_10.png` | Top-10 / bottom-10 happiest countries |
| `output/figures/gdp_vs_ladder.png` | GDP per capita vs Ladder, log-axis + LOWESS |
| `output/figures/decomposition.png` | Variance decomposition for top-15 happiest |
| `output/figures/cate_hist.png` | Distribution of CATEs from the causal forest |
| `output/figures/cate_by_gdp.png` | CATE vs GDP per capita |
| `output/figures/cf_importance.png` | Causal-forest feature importance |
| `output/figures/chapters_trend.png` | Chapters per WHR edition (scraped) |
| `output/figures/ladder_timeseries.png` | Selected countries' Ladder, 2020-2024 |
| `output/tables/regression_table.tex` | Six-spec OLS table (LaTeX, pystout) |
| `output/tables/regression_summary.csv` | Same in tidy CSV |
| `output/tables/cate_summary.csv` | Per-country CATEs with 95 % CIs |
| `output/tables/cf_importance.csv` | Causal-forest split-importance |

---

## 6. Mapping the project to the BEE2041 syllabus

Every script is annotated with the lecture/PDF it draws on; this section
gives the same map at a glance.

| Course unit / lecture | Where it shows up |
|---|---|
| Linux Command Line, Workflow & `make` | `Makefile`, project layout in §2 |
| git & GitHub | repo history, `git/strict-code-review-uaccM` feature branch, atomic commits |
| Python for Data Management | `pd.merge` with `validate="1:1"` in `03_download_worldbank.py`, reshape in `02_download_whr_rankings.py` |
| Relational Database Management Systems | `04_build_database.py` - 3 tables, indexes on join keys, INNER JOIN |
| Workflow, Modelling & Webscraping (causal ML) | `06_causal_forest.py` - `econml.dml.CausalForestDML` |
| Workflow, Modelling & Webscraping (webscrape) | `01_scrape_whr_chapters.py` - requests + BeautifulSoup, cached pages, retry |

A complete reference list is in [`references/sources.md`](references/sources.md).

---

## 7. References (short list)

* World Happiness Report 2020-2026, Sustainable Development Solutions Network.
  <https://worldhappiness.report>
* World Bank, *World Development Indicators*, queried via the
  [`wbgapi`](https://pypi.org/project/wbgapi/) Python client.
* Wager, S. & Athey, S. (2018). Estimation and Inference of Heterogeneous
  Treatment Effects using Random Forests. *JASA* 113(523): 1228-1242.
* Athey, S., Tibshirani, J. & Wager, S. (2019). Generalized Random Forests.
  *Annals of Statistics* 47(2): 1148-1178.
* Davis, J. & Heller, S. (2017). Using Causal Forests to Predict Treatment
  Heterogeneity: An Application to Summer Jobs. *AEA Papers & Proceedings*.
* Gentzkow, M. & Shapiro, J. (2014). Code and Data for the Social Sciences.
* Turrell, A. (2023). *Coding for Economists*.
  <https://aeturrell.github.io/coding-for-economists/>

---

## 8. License

Released under the MIT License (see `LICENSE`).
