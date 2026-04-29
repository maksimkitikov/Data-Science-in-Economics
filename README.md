# Beyond GDP

BEE2041 empirical project, April 2026. Maksim Kitikov, University of Exeter.

A short data-driven essay asking *what really drives national happiness* once
we look past GDP. The pipeline scrapes chapter metadata from the World
Happiness Report, downloads its Figure 2.1 ranking spreadsheets, pulls
supplementary World Bank indicators, glues the three together in a small
SQLite db, fits OLS and a causal forest on top, and feeds the results into
an interactive Plotly site.

Live version: <https://maksimkitikov.github.io/Data-Science-in-Economics/>

## Reproducing the build

I used Python 3.11. Earlier 3.10 is fine.

```bash
git clone https://github.com/maksimkitikov/Data-Science-in-Economics.git
cd Data-Science-in-Economics
pip install -r requirements.txt
make all
```

`make all` runs the eight numbered scripts in `scripts/` end-to-end (scrape ->
build SQLite -> regressions -> causal forest -> figures -> JSON for the
site). Sub-targets like `make data` or `make analysis` only redo the
relevant steps. There are a handful of pytest sanity checks in `tests/`
(`make test`).

## Data

| Source | What | How |
|---|---|---|
| WHR 2020-2026 chapter pages | titles, authors, affiliations, reading time | `requests` + `BeautifulSoup` |
| WHR Figure 2.1 spreadsheets | Ladder + the six bundled covariates | `pd.read_excel` on the .xls files |
| World Bank WDI 2022 | GDP per capita PPP, life expectancy, internet, urban share, FDI, education | `wbgapi` REST client |

After matching on ISO-3 country codes the analysis sample is 136
countries. Variable-level docs are in
[`references/codebook.md`](references/codebook.md), full reading list in
[`references/sources.md`](references/sources.md).

## Layout

```
scripts/        # eight numbered scripts, run in order
data/raw/       # never modified after download
data/clean/     # derived (analysis.csv, whr.db)
output/figures/ # PNG and PDF for every chart
output/tables/  # LaTeX (pystout) + tidy CSVs
docs/           # the static site (served via GitHub Pages)
tests/          # pytest sanity checks
references/     # codebook + bibliography
```

## Declaration of AI Use

I used Claude and ChatGPT for drafts of the blog text and to debug error
messages from `pystout` and `econml`. The analytical decisions and the
final code are mine.

## License

MIT.
