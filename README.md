# Beyond GDP: what really drives national happiness?

BEE2041 Data Science in Economics, empirical project, April 2026.
Author: Maksim Kitikov, University of Exeter.

This repository contains the full pipeline behind the blog post
[*Beyond GDP: what really drives national happiness?*](docs/index.html).
The project scrapes the World Happiness Report website, downloads the
WHR's published ranking spreadsheets, queries the World Bank API for some
supplementary indicators, stitches the three sources together with a small
SQLite database, and finally fits both OLS and a causal forest
(`econml.dml.CausalForestDML`) to explore cross-country variation in life
satisfaction.

The blog is published as a fully-interactive static website served from
`docs/`. The exact same bundle is also mirrored under `huggingface_space/`,
ready for one-click deployment to Hugging Face Spaces (see
[`huggingface_space/DEPLOY.md`](huggingface_space/DEPLOY.md)).

* **Live website (Hugging Face):** <https://mk88889-beyond-gdp.static.hf.space>
  (also embedded at <https://huggingface.co/spaces/mk88889/beyond-gdp>).
* **GitHub Pages mirror:** <https://maksimkitikov.github.io/Data-Science-in-Economics/>
  (same site, served from `docs/`; responsive and Plotly-powered).
* **Executed notebook:** [`blog.ipynb`](blog.ipynb) at the repository root,
  with the same prose plus every code cell.
* **Notebook companion (HTML):** [`docs/notebook.html`](docs/notebook.html)
  for readers who want the rendered notebook in the browser.
* **Static PDF:** [`Beyond GDP_ What Drives National Happiness_.pdf`](./Beyond%20GDP_%20What%20Drives%20National%20Happiness_.pdf).

---

## 1. Replication in one command

```bash
git clone https://github.com/maksimkitikov/Data-Science-in-Economics.git
cd Data-Science-in-Economics
pip install -r requirements.txt
make all
```

`make all` runs the nine numbered scripts in `src/`, rebuilds the SQLite
database, regenerates every figure and the regression table, exports the
JSON data the website consumes, and re-renders the notebook. Subsequent
runs of `make` only redo the steps whose inputs have changed (the usual
incremental-build behaviour discussed in the workflow
lecture).

```bash
make scrape    # only the network steps (web-scrape + downloads + WB API)
make data      # build the SQLite database + analysis.csv
make analysis  # run regressions + causal forest, regenerate figures
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
├── docs/                           ← the public website (served by GitHub Pages)
│   ├── index.html                  ← landing page, hand-written, responsive
│   ├── style.css                   ← design system
│   ├── site.js                     ← interactive Plotly chart code
│   ├── plotly.min.js               ← Plotly v2.35.2, vendored locally
│   ├── data.js                     ← bundled JSON for the charts
│   ├── data/                       ← same data as separate JSON files
│   └── notebook.html               ← rendered notebook companion
├── src/
│   ├── 01_scrape_whr_chapters.py   ← BeautifulSoup scrape of WHR editions
│   ├── 02_download_whr_rankings.py ← bulk download of Figure_2.1.xls files
│   ├── 03_download_worldbank.py    ← wbgapi (WB API) cross-section
│   ├── 04_build_database.py        ← SQLite schema + JOIN to analysis.csv
│   ├── 05_regressions.py           ← OLS specifications (m1..m6) + pystout
│   ├── 06_causal_forest.py         ← econml.CausalForestDML
│   ├── 07_descriptive_figures.py   ← top-bottom-10, scatter, decomposition
│   ├── 08_build_blog.py            ← assembles & renders blog.ipynb
│   └── 09_export_json.py           ← exports JSON data for the website
├── data/
│   ├── raw/
│   │   ├── html_cache/             ← cached HTML of every scraped page
│   │   ├── whr_chapters.csv        ← scraped chapter metadata, 2020-2026
│   │   ├── whr20..24_fig21.xls     ← downloaded WHR ranking files
│   │   ├── whr_panel.csv           ← stacked WHR panel
│   │   └── wb_indicators.csv       ← WB cross-section, 2022
│   └── clean/
│       ├── whr.db                  ← SQLite database
│       └── analysis.csv            ← analysis-ready cross-section
├── output/
│   ├── figures/                    ← PDF + PNG figures, used by the blog
│   └── tables/                     ← regression_table.tex,
│                                     regression_summary.csv,
│                                     cate_summary.csv
├── references/                     ← reading materials cited in code
└── course-materials/               ← Damian Clarke's BEE2041 lecture PDFs
```

The structure follows the recommended layout from *Workflow, Modelling &
Webscraping.pdf* (slide 19): **raw data is sacred** and lives only in
`data/raw/`; everything in `data/clean/` and `output/` can be regenerated.

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
covariates for the 2023 WHR edition (the latest year for which the WHR ships
the underlying Logged-GDP, Social-support and Freedom variables alongside the
Ladder score).

---

## 4. Methods

### Web-scraping
Pattern follows `scrape_xkcd_bs.py` from
[damiancclarke/BEE2041-2026](https://github.com/damiancclarke/BEE2041-2026/tree/main/webscrape):
`requests` is used (rather than `urllib`) so we can supply a polite
`User-Agent`. Every page is cached to `data/raw/html_cache/`, so the rest of
the build is reproducible offline once the cache exists.

### SQL integration
Three SQLite tables are created (`country_year`, `country_meta`,
`whr_chapters`) with B-tree indexes on the join keys and the analysis sample
is produced by an `INNER JOIN` written in raw SQL. Pattern of relational
algebra discussed in *Relational Database Management Systems.pdf*.

### Regression
Six progressively richer OLS specifications are estimated using
`statsmodels.OLS`, robust standard errors of type `HC3`, exported via
`pystout` to a single LaTeX table, in the same style as Damian's
`immigrantEffects.py`.

### Causal forest
`econml.dml.CausalForestDML` with `GradientBoostingRegressor` /
`GradientBoostingClassifier` nuisance models, 1000 trees, leaf size 5, seed
121316 (Clarke's seed). The "treatment" is a binary indicator for being above
the sample-median GDP per capita PPP; X covers six potential moderators. We
report ATE, CATE histogram, ranked CATEs with 95 % CIs, CATE-vs-GDP, and the
forest's split-importance metric.

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

---

## 6. References

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
* Damian Clarke, BEE2041-2026 GitHub.
  <https://github.com/damiancclarke/BEE2041-2026>

---

## 7. Course-materials trail

Each source script lists the BEE2041 PDF whose slides directly informed it.
Specifically:

| Code element | Course slide / file |
|---|---|
| 80-column file header & numbered banners | Clarke, `scrape_xkcd_bs.py` |
| `requests.get` polite scrape | *Workflow, Modelling & Webscraping.pdf*, slide 60 |
| `BeautifulSoup` parsing of `<li class="author">` | same file, slides 63-64 |
| `pd.merge(... validate="1:1", indicator=True)` | *Python for Data Management.pdf*, slides 53-56 |
| SQLite schema + JOIN | *Relational Database Management Systems.pdf* |
| `wbgapi` cross-section | BEE2041 Problem-Set Solutions, Q2 |
| `CausalForestDML` recipe | Clarke, `replicationCausalForest/source/immigrantEffects.py` |
| `Makefile` build pipeline | Clarke, `replicationCausalForest/Makefile` |
| README structure | Clarke, `replicationCausalForest/README.md` |

---

## 8. License

Released under the MIT License (see `LICENSE`).
