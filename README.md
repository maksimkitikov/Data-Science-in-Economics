# Beyond GDP

BEE2041 empirical project, April 2026. Maksim Kitikov, University of Exeter.

A short data-driven essay asking *what really drives national happiness* once
we look past GDP. The pipeline scrapes chapter metadata from the World
Happiness Report, downloads its Figure 2.1 ranking spreadsheets, pulls
supplementary World Bank indicators, glues the three together in a small
SQLite db, fits OLS and a causal forest on top, and renders a notebook
plus an interactive Plotly site.

Live versions:

- GitHub Pages: <https://maksimkitikov.github.io/Data-Science-in-Economics/>
- Notebook: [`blog.ipynb`](blog.ipynb) (executed and committed)

## Reproducing the build

I used Python 3.11. Earlier 3.10 is fine.

```bash
git clone https://github.com/maksimkitikov/Data-Science-in-Economics.git
cd Data-Science-in-Economics
pip install -r requirements.txt
make all
```

`make all` runs the nine numbered scripts in `scripts/` end-to-end (scrape ->
build SQLite -> regressions -> causal forest -> figures -> blog -> JSON
for the website). Sub-targets like `make data` or `make analysis` only
redo the relevant steps. There are a handful of pytest sanity checks in
`tests/` (`make test`).

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
scripts/        # nine numbered scripts, run in order
data/raw/       # never modified after download
data/clean/     # derived (analysis.csv, whr.db)
output/figures/ # PNG and PDF for every chart
output/tables/  # LaTeX (pystout) + tidy CSVs
docs/           # the static site (served via GitHub Pages)
tests/          # pytest sanity checks
references/     # codebook + bibliography
```

## Declaration of AI Use

I declare that I have used generative AI tools in the preparation of this
submission, in accordance with the University of Exeter's *AI-Assisted*
classification of this assessment and the guidance set out in the BEE2041
lectures (Workflow lecture, slides 30, 34, 66; Python lecture, slide 78).

## License

MIT.
