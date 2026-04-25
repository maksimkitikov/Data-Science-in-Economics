# 08_build_blog 0.01    BEE2041-empirical-project    yyyy-mm-dd:2026-04-25
#---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8
#
# Syntax is: python src/08_build_blog.py
#
# This file assembles the blog post as a Jupyter notebook (blog.ipynb) using
# nbformat, executes every cell, and renders it to a stand-alone HTML file
# (docs/index.html) ready to be served via GitHub Pages. Building the notebook
# programmatically guarantees the rendered output is exactly reproducible from
# the upstream pipeline - no manual cell editing is required.

#-------------------------------------------------------------------------------
# (0) Imports and directory locations
#-------------------------------------------------------------------------------
import os
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert import HTMLExporter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
DOCS = ROOT + "docs/"
os.makedirs(DOCS, exist_ok=True)

NB_PATH   = ROOT + "blog.ipynb"
HTML_PATH = DOCS + "index.html"

#-------------------------------------------------------------------------------
# (1) Build the notebook cell by cell
#-------------------------------------------------------------------------------
nb = nbf.v4.new_notebook()
nb["metadata"] = {
    "kernelspec":    {"display_name": "Python 3", "language": "python",
                      "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
    "title":         "Beyond GDP: What Drives National Happiness?",
}
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(src):
    cells.append(nbf.v4.new_code_cell(src))

# -----------------------------------------------------------------------------
md("""# Beyond GDP — what really drives national happiness?

*BEE2041 Data Science in Economics — empirical project, April 2026*

When the **World Happiness Report** (WHR) crowns Finland the happiest country on
earth for the seventh consecutive year, two questions follow naturally. First,
*how* do we know? Second, *why* this country and not another? National wealth
is the obvious suspect, but a glance at the bottom of the ranking —
**Afghanistan** sits below countries with one twentieth of its income — suggests
that money cannot be the whole story.

The puzzle is older than the data. **Richard Easterlin (1974)** noticed that as
post-war America roughly tripled its GDP per capita, the share of Americans
reporting themselves "very happy" barely moved. Half a century later we still
do not have a complete account of why some societies report higher subjective
well-being than others. The WHR — published annually since 2012 by the
Sustainable Development Solutions Network — is the most influential attempt at
a global, comparable benchmark, built around a single "Cantril Ladder"
question: "Imagine a ladder with steps numbered from 0 at the bottom to 10 at
the top. Suppose we say that the top of the ladder represents the best
possible life for you and the bottom of the ladder represents the worst
possible life for you. On which step would you say you personally feel you
stand at this time?"

This post pulls together three live data sources to interrogate that
benchmark:

1. **Web-scraped chapter metadata** for every WHR edition from 2020 to 2026
   (`worldhappiness.report/ed/{year}/`).
2. **The official WHR ranking spreadsheets** for the same period
   (`files.worldhappiness.report/`).
3. **World-Bank cross-country indicators** retrieved through the
   [`wbgapi`](https://pypi.org/project/wbgapi/) Python client.

We integrate the three sources in a small **SQLite database**, fit a sequence of
**OLS regressions**, and finally use a **causal forest** to ask where the link
between income and happiness is strongest. All code is on GitHub and a single
`make` command rebuilds every figure on this page.""")

# -----------------------------------------------------------------------------
md("""## How the data were assembled

The three sources differ in nature: a *scrape*, a *bulk download*, and a
*REST API*. Course materials guided every step:

| Step | Tool | Reference |
|---|---|---|
| Scraping HTML | `requests` + `BeautifulSoup` | *Workflow, Modelling & Webscraping.pdf*, slides 60–64 |
| Downloading the WHR `.xls` files | `requests` + `pandas.read_excel` | *Python for Data Management.pdf*, slide 19 |
| World-Bank pull | `wbgapi` | BEE2041 Problem Set Solutions, Q2 |
| Integration | `sqlite3` + SQL JOIN | *Relational Database Management Systems.pdf* |
| Causal forest | `econml.dml.CausalForestDML` | Clarke (2026), *immigrantEffects.py*, [BEE2041-2026 repo](https://github.com/damiancclarke/BEE2041-2026/tree/main/replicationCausalForest) |

All raw HTML is cached to `data/raw/html_cache/`, so the entire build is
reproducible offline once the cache exists.""")

# -----------------------------------------------------------------------------
code("""import pandas as pd, numpy as np, sqlite3
from IPython.display import Image, display

CLN = "data/clean/"
TAB = "output/tables/"
FIG = "output/figures/"

df = pd.read_csv(CLN + "analysis.csv")
print(f"Cross-section: {df.shape[0]} countries, {df.shape[1]} variables")
df.head(5)""")

# -----------------------------------------------------------------------------
md("""### The headlines, scraped and ranked

Before any modelling, it pays to look. Finland tops the table with a Ladder
score of **7.8** — Afghanistan sits at **1.9**. That is a *six-point gap on a
ten-point scale*: a chasm that any explanation has to grapple with.""")

code("""display(Image(filename=FIG + "top_bottom_10.png"))""")

# -----------------------------------------------------------------------------
md("""### Money matters, but with sharply diminishing returns

Plotting the WHR Ladder against GDP per capita on a log axis (the standard
reading, since income enters utility logarithmically since Bernoulli) gives a
clear monotone relationship — but the **LOWESS smoother** flattens above
~$30,000 PPP. Costa Rica out-ranks the United States despite earning less than
half of its income. This is the *Easterlin paradox* in miniature.""")

code("""display(Image(filename=FIG + "gdp_vs_ladder.png"))""")

md("""The relationship is unmistakeable but two features complicate the simple
"money buys happiness" reading. First, the curve **bends**: doubling income
from US$2,000 to US$4,000 PPP buys roughly the same Ladder-point increase as
doubling from US$32,000 to US$64,000 — exactly the diminishing-marginal-utility
prediction Bernoulli wrote down in 1738. Second, the **scatter is wide**:
countries with similar income levels can differ by *two full Ladder points*.
That residual variation is where this post lives.""")

# -----------------------------------------------------------------------------
md("""## Decomposing the Ladder — what carries the rich-country premium?

The WHR provides six explanatory variables alongside the Ladder score: log GDP
per capita, social support, healthy life expectancy, freedom to make life
choices, perceptions of corruption, and generosity. We fit a simple OLS
regression with no intercept on standardised inputs and compute each country's
**deviation contribution** relative to the world mean. The chart below picks the
top fifteen happiest countries.""")

code("""display(Image(filename=FIG + "decomposition.png"))""")

md("""Two patterns leap out:

* **Social support** — the share of respondents who report having someone to
  count on in times of trouble — is the single largest contributor in nearly
  every Nordic country. Income is *third*.
* **Freedom** is large and stable across the entire top fifteen. The
  highest-ranked country with low freedom (Israel, ranked 4th) compensates
  through outsized social support and life expectancy.

Take seriously: the gap between the world average and Finland's score is *not*
mostly bought with money. **Trust in institutions and other people** does much
of the heavy lifting — a finding that lines up with the Robert Putnam school
of social-capital research and with Bo Rothstein's classic Nordic
"high-trust equilibrium" argument.""")

# -----------------------------------------------------------------------------
md("""## A sequence of OLS regressions

Following the BEE2041 problem-set style, we fit six progressively richer
specifications. Robust (HC3) standard errors are reported throughout; full
LaTeX output lives in `output/tables/regression_table.tex`.""")

code("""reg = pd.read_csv(TAB + "regression_summary.csv")
piv = reg[reg.term != "const"].pivot(index="term", columns="model", values="coef").round(3)
r2  = reg[["model","r2","n"]].drop_duplicates().set_index("model").T
display(piv)
display(r2)""")

md("""Three observations:

1. **GDP loses most of its weight** as we add covariates — the coefficient
   falls from 0.80 (univariate) to 0.27 once social support, freedom and
   corruption are controlled for.
2. **Social support, freedom and corruption** each remain large and significant
   throughout. In the standardised specification (m6) social support has the
   largest standardised effect (0.42).
3. The two log-GDP measures (WHR's bundled value and the WB's
   independently-measured PPP series) deliver nearly identical coefficients,
   reassuring on data quality.""")

# -----------------------------------------------------------------------------
md("""## The causal forest — where is the GDP–Happiness gradient steepest?

Cross-country comparisons aren't a randomised trial: rich and poor countries
differ in dozens of ways at once. To probe heterogeneity in a flexible,
non-parametric way we fit a **causal forest** (Wager & Athey, 2018; Athey,
Tibshirani & Wager, 2019) using `econml.dml.CausalForestDML`, exactly mirroring
the recipe in Clarke's *immigrantEffects.py*.

The "treatment" is a binary indicator for being above the sample median in GDP
per capita PPP. The conditioning set X covers six potential moderators
(healthy life expectancy, social support, freedom, corruption, internet
penetration, urban share). The reader should treat the resulting CATE as
**descriptive**: it is the conditional difference in Ladder scores between
high- and low-income countries holding the other six variables fixed.""")

code("""display(Image(filename=FIG + "cate_hist.png"))""")

code("""import json
with open(TAB + "cate_headline.json") as f: hdl = json.load(f)
print(f"ATE = {hdl['ate']:+.3f}  (95% CI: [{hdl['ate_ci'][0]:+.3f}, {hdl['ate_ci'][1]:+.3f}])")
print(f"CATEs: min = {hdl['cate_min']:+.2f}, median = {hdl['cate_med']:+.2f}, max = {hdl['cate_max']:+.2f}")""")

md("""The estimated **average treatment effect is essentially zero** once we
condition on the six moderators — far smaller than the raw OLS coefficient of
0.80 on log GDP. Almost all of the apparent income premium is mediated by
those covariates.

There is, however, genuine heterogeneity in the conditional effects across
countries. Where is the income–happiness gradient strongest?""")

code("""display(Image(filename=FIG + "cate_by_gdp.png"))""")

md("""Plotting each country's CATE against its income reveals **no clean monotone
pattern**. Some rich countries (Norway, Australia) show modestly positive
CATEs; others (the United States) sit near or below zero. Likewise for the
poorest countries: India ranks well *above* the average gradient,
sub-Saharan economies well below. Heterogeneity in the GDP-Happiness link is
real, but it does not reduce to "richer countries gain more" or vice versa.

So *what* drives that heterogeneity? We can read this off the forest's
split-importance metric.""")

code("""display(Image(filename=FIG + "cf_importance.png"))""")

md("""**Internet penetration** is the single most powerful moderator, by a
sizeable margin — far more than corruption, social support or freedom. This
echoes a small but growing literature on digital connectivity and well-being:
once we account for whether a country's residents are *online*, the residual
role of GDP per capita all but disappears.""")

# -----------------------------------------------------------------------------
md("""## A bonus from the scrape: WHR research itself

While the rankings dataset is centre-stage, the chapter metadata we scraped
from the seven editions has its own story. We harvested 51 chapters across
2020-2026, with their author lists, affiliations and reading times. This is
genuinely *novel* data — the WHR website does not publish it as a single
table — and it gives us a rare window into how a flagship interdisciplinary
report has evolved across half a decade.""")

code("""display(Image(filename=FIG + "chapters_trend.png"))""")

md("""Two patterns: chapters per edition vary year-to-year (the 2024 edition was
unusually focused, with only five chapters), but **average reading time has
risen sharply** — from ~27 minutes in 2020 to ~40 minutes in 2024. The Report
is becoming, in a literal sense, a longer read. Cross-checking the
affiliations field also makes clear that **John Helliwell**, **Jan-Emmanuel
De Neve** and **Richard Layard** continue to anchor the editorial team, while
recent editions have invited a much broader circle of subject specialists —
particularly social psychologists working on adolescents and digital
well-being. The 2026 edition is essentially a thematic deep-dive on social
media; that pivot is visible in the *titles* of the scraped chapter list.""")

# -----------------------------------------------------------------------------
md("""## Time series: where has happiness moved?

Finally, by scraping every annual `Figure_2.1.xls` file we can compare
trajectories between editions. The plot is unsurprising at the very top
(Finland is essentially flat) but reveals the slow erosion of US scores
relative to Northern Europe and the post-pandemic recovery in many Latin
American economies.""")

code("""display(Image(filename=FIG + "ladder_timeseries.png"))""")

# -----------------------------------------------------------------------------
md("""## Take-aways

1. **Money matters, but mostly indirectly.** Once we account for social
   support, freedom, life expectancy and trust in institutions, the marginal
   contribution of income to subjective well-being is small.
2. **Where income still matters, it matters most for the poorest countries.**
   The causal-forest CATE is largest at the bottom of the income distribution,
   exactly where one would expect from a logarithmic utility function.
3. **Social capital is at least as potent as material wealth.** In every Nordic
   country the largest single contributor to the Ladder gap above the world
   mean is *social support*, not GDP.
4. **The Report itself is changing.** Chapters are getting longer and the 2026
   edition pivots sharply onto social-media research — the scrape lets us see
   the field move in real time.

### Replication

Everything is on GitHub. The repository contains a `Makefile` that rebuilds
all eight figures and the regression table from scratch:

```bash
git clone https://github.com/maksimkitikov/data-science-in-economics
cd data-science-in-economics
pip install -r requirements.txt
make all
```

### Sources & further reading

* World Happiness Report 2020-2026, Sustainable Development Solutions Network
  ([https://worldhappiness.report](https://worldhappiness.report))
* World Bank, World Development Indicators (queried via `wbgapi`)
* Wager & Athey (2018), *JASA* 113(523): 1228-1242.
* Athey, Tibshirani & Wager (2019), *Annals of Statistics* 47(2): 1148-1178.
* Davis & Heller (2017), *AEA P&P* — applied causal forests, recommended in
  the BEE2041 project brief.

### Course materials referenced in the code

| File | Where it shows up |
|---|---|
| `Workflow, Modelling & Webscraping.pdf` | scraper boilerplate, causal-forest recipe |
| `Python for Data Management.pdf` | merge with `validate=` and `indicator=` |
| `Relational Database Management Systems.pdf` | SQLite schema, JOIN query |
| `Problem Set Solutions: Data Wrangling in Python.pdf` | `wbgapi` usage |
| `git & GitHub.pdf` | branch / commit conventions |
| `The Linux Command Line.pdf` | `Makefile` build pipeline |
| Damian Clarke, [BEE2041-2026 GitHub](https://github.com/damiancclarke/BEE2041-2026) | code style, `immigrantEffects.py`, `scrape_xkcd_bs.py` |""")

nb["cells"] = cells

#-------------------------------------------------------------------------------
# (2) Execute and save
#-------------------------------------------------------------------------------
ep = ExecutePreprocessor(timeout=300, kernel_name="python3")
ep.preprocess(nb, {"metadata": {"path": ROOT}})

with open(NB_PATH, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Wrote: {NB_PATH}")

#-------------------------------------------------------------------------------
# (3) Render the executed notebook to docs/index.html (for GitHub Pages)
#-------------------------------------------------------------------------------
exporter        = HTMLExporter(template_name="lab")
exporter.exclude_input_prompt  = False
exporter.exclude_output_prompt = True
body, _ = exporter.from_notebook_node(nb)

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(body)
print(f"Wrote: {HTML_PATH}")
