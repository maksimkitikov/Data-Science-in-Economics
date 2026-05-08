"""Build blog.ipynb programmatically from the figures and tables under output/."""
import os
# silence the noisy debugpy/frozen-modules notice from the kernel that nbconvert spawns
os.environ.setdefault("PYDEVD_DISABLE_FILE_VALIDATION", "1")

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

NB_PATH = "blog.ipynb"

nb = nbf.v4.new_notebook()
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python",
                   "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
    "title": "Beyond GDP: What Drives National Happiness?",
}
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(src):
    cells.append(nbf.v4.new_code_cell(src))


md("""# Beyond GDP: what really drives national happiness?

*BEE2041 Data Science in Economics, empirical project, April 2026*

The World Happiness Report (WHR) has crowned Finland the happiest country on
earth for seven years running. Two questions follow naturally. *How* do we
know? And *why* this country and not another? National wealth is the obvious
suspect, but Afghanistan sits at the bottom with a twentieth of US income, so
money cannot be the whole story.

The puzzle is older than the data. Richard Easterlin (1974) noticed that as
post-war America roughly tripled its GDP per capita, the share of Americans
calling themselves "very happy" barely moved. Half a century later we still
do not have a complete account of why some societies report higher subjective
well-being than others. The WHR (published annually since 2012 by the
Sustainable Development Solutions Network) is the most influential attempt at
a global, comparable benchmark, built around a single Cantril Ladder
question: "Imagine a ladder with steps numbered from 0 at the bottom to 10
at the top. Suppose we say that the top of the ladder represents the best
possible life for you and the bottom of the ladder represents the worst
possible life for you. On which step would you say you personally feel you
stand at this time?"

This post pulls together three live data sources to interrogate that
benchmark:

1. Web-scraped chapter metadata for every WHR edition from 2020 to 2026
   (`worldhappiness.report/ed/{year}/`).
2. The official WHR ranking spreadsheets for the same period
   (`files.worldhappiness.report/`).
3. World-Bank cross-country indicators retrieved through the
   [`wbgapi`](https://pypi.org/project/wbgapi/) Python client.

I integrate the three in a small SQLite database, fit a sequence of OLS
regressions, and finally use a causal forest to ask which countries see the
biggest happiness premium from being above the income median. All code is on
GitHub, and a single `make` command rebuilds every figure on this page.""")

md("""## How the data were assembled

The three sources are different in kind: a scrape, a bulk download and a
REST API.

| Step | Tool |
|---|---|
| Scraping HTML | `requests` + `BeautifulSoup` |
| Downloading the WHR `.xls` files | `requests` + `pandas.read_excel` |
| World-Bank pull | `wbgapi` |
| Integration | `sqlite3` + a SQL JOIN |
| Causal forest | `econml.dml.CausalForestDML` |

The scraper caches every page to `data/raw/html_cache/`, so once it has run
once the rest of the build works offline.""")

code("""import pandas as pd, numpy as np, sqlite3
from IPython.display import Image, display

CLN = "data/clean/"
TAB = "output/tables/"
FIG = "output/figures/"

df = pd.read_csv(CLN + "analysis.csv")
print(f"Cross-section: {df.shape[0]} countries, {df.shape[1]} variables")
df.head(5)""")

md("""### The headlines, scraped and ranked

Before doing any modelling, it pays to look at the raw numbers. Finland
tops the table with a Ladder score of 7.8 against Afghanistan's 1.9.
That is a six-point gap on a ten-point scale, which is huge for any
explanation to close.""")

code("""display(Image(filename=FIG + "top_bottom_10.png"))""")

md("""### Money matters, but with diminishing returns

Plotting the Ladder against GDP per capita on a log axis (the usual
choice, since income enters utility logarithmically) gives a clear
upward relationship, but the LOWESS smoother flattens noticeably above
roughly US&#36;30,000 PPP. Costa Rica nearly matches the United States on
the Ladder (6.6 versus 6.9) on roughly a third of US income, a
small-scale version of the Easterlin paradox.""")

code("""display(Image(filename=FIG + "gdp_vs_ladder.png"))""")

md("""Two features complicate the simple "money buys happiness" reading.
The curve clearly bends: doubling income from US&#36;2,000 to US&#36;4,000
PPP buys roughly the same Ladder-point increase as doubling from
US&#36;32,000 to US&#36;64,000, which is what we would expect from
logarithmic utility. And the vertical scatter is wide; countries with
similar income levels routinely differ by close to two Ladder points.
That residual variation is where the rest of this post lives.""")

md("""## Decomposing the Ladder: what carries the rich-country premium?

Alongside the Ladder score the WHR ships six explanatory variables: log GDP
per capita, social support, healthy life expectancy, freedom to make life
choices, perceptions of corruption, and generosity. To see how each one
contributes I fit a plain OLS regression of the Ladder on these six,
multiply each country's covariate (centred on the sample mean) by the fitted
coefficient, and stack the contributions. The chart below shows the
breakdown for the top-15 happiest countries.""")

code("""display(Image(filename=FIG + "decomposition.png"))""")

md("""Two things stand out. First, *social support* (the share of
respondents who say they have someone to count on in times of trouble) is
the single biggest contributor in almost every Nordic country, with income
only third. Second, *freedom* is large and stable across the whole top-15;
the highest-ranked country with low freedom is Israel (4th), and it makes
up the difference through unusually high social support and life
expectancy.

The wider implication is that the gap between the world average and
Finland's score is mostly *not* bought with money. Trust in institutions
and in other people does most of the work, which lines up with Robert
Putnam's social-capital research and Bo Rothstein's account of the Nordic
"high-trust equilibrium".""")

md("""## OLS, six ways

I fit six specifications, adding one block of regressors at a time, with
robust (HC3) standard errors throughout. The full LaTeX-formatted table is
in `output/tables/regression_table.tex`.""")

code("""reg = pd.read_csv(TAB + "regression_summary.csv")
piv = (reg[reg.term != "const"]
       .pivot(index="term", columns="model", values="coef")
       .round(3)
       .fillna("-"))
fit = reg[["model", "r2", "n"]].drop_duplicates().set_index("model")
fit_summary = pd.DataFrame({
    "R²": fit["r2"].round(3).astype(str),
    "N": fit["n"].astype(int).astype(str),
}).T
display(piv)
display(fit_summary)""")

md("""A few things to notice. The log-GDP coefficient falls from about
0.80 on its own to 0.27 once social support, freedom and corruption are
controlled for: most of the apparent income premium is mediated through
those other channels. Social support, freedom and corruption stay
significant in every column where they appear, and in the standardised
specification (m6) social support has the largest absolute coefficient
(0.42). It is reassuring that the two independent log-GDP measures (the
WHR's bundled value and the World Bank's PPP series) give nearly identical
estimates.

The pattern is consistent with a long line of work in the economics of
well-being. Easterlin (1974) first noted that within rich countries the
income–happiness relationship flattens after basic needs are met; later
work (Stevenson & Wolfers, 2008; Layard, Mayraz & Nickell, 2009) finds
the gradient survives in *cross*-country data but is much smaller once
mediating institutions are accounted for. Specification (6) makes the
effect sizes comparable: a one-standard-deviation rise in social support
is worth roughly the same as a one-standard-deviation rise in log GDP,
and freedom is not far behind.""")

md("""## A causal forest: when does income still buy happiness?

Cross-country comparisons are obviously not a randomised trial; rich and
poor countries differ on dozens of margins at once. To probe heterogeneity
in a flexible, non-parametric way I fit a causal forest (Wager & Athey,
2018; Athey, Tibshirani & Wager, 2019) with `econml.dml.CausalForestDML`.

I encode the "treatment" as a binary indicator for being above the
sample-median GDP per capita PPP. The conditioning set X has six potential
moderators: healthy life expectancy, social support, freedom, corruption,
internet penetration and urban share. The CATE we recover should be read
as *descriptive*: the conditional difference in Ladder score between
high- and low-income countries with the same values of the six
moderators.""")

code("""display(Image(filename=FIG + "cate_hist.png"))""")

code("""import json
with open(TAB + "cate_headline.json") as f: hdl = json.load(f)
print(f"ATE = {hdl['ate']:+.3f}  (95% CI: [{hdl['ate_ci'][0]:+.3f}, {hdl['ate_ci'][1]:+.3f}])")
print(f"CATEs: min = {hdl['cate_min']:+.2f}, median = {hdl['cate_med']:+.2f}, max = {hdl['cate_max']:+.2f}")""")

md("""The forest's average treatment effect lands very close to zero
once we condition on the six moderators, far below the raw 0.80 OLS
coefficient on log GDP. Almost all of the apparent income premium runs
through those other covariates. The histogram above is the **main result**
of this section; the next two figures and the robustness table are
diagnostics that probe the same number from different angles.

### Diagnostics

There *is* still genuine heterogeneity across countries. Which countries
get the biggest happiness boost from being above the income median, and
what predicts the size of that boost?""")

code("""display(Image(filename=FIG + "cate_by_gdp.png"))""")

md("""Plotting each country's CATE against its income produces no clean
monotone pattern. Some rich countries (Norway, Australia) come out
modestly above the ATE line, others (the United States) sit close to or
below zero. The poorest end is just as mixed: India is well *above* the
average gradient while several sub-Saharan economies sit well below.
Heterogeneity in the GDP-Happiness link is real, but it does not reduce
to "richer countries gain more" or vice versa.

So what does explain the heterogeneity? The forest's split-importance
gives us a direct answer.""")

code("""display(Image(filename=FIG + "cf_importance.png"))""")

md("""Internet penetration is the most important moderator, ahead of
social support, corruption and the others. That fits a small but growing
literature on digital connectivity and well-being: once we know whether a
country's residents are *online*, the leftover role of GDP per capita
shrinks a lot.""")

md("""### Robustness: where exactly is *rich*?

The "above median" treatment was a convenient but arbitrary cut. The
obvious alternative is the top quartile (around &#36;44k PPP). Re-fitting
the forest with that threshold produces a real surprise:""")

code("""import json
with open(TAB + "ate_sensitivity.json") as f: sens = json.load(f)
rows = []
for k in ["headline", "robust"]:
    r = sens[k]
    rows.append({
        "Treatment": r["label"],
        "Cut-off (USD PPP)": f\"\"\"${r['cutoff_usd']:,.0f}\"\"\",
        "ATE": f\"\"\"{r['ate']:+.3f}\"\"\",
        "95% CI": f\"\"\"[{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]\"\"\",
    })
display(pd.DataFrame(rows))""")

md("""So the median split was masking a real, positive income effect at
the very top of the income distribution: an extra 0.32 Ladder points
with a 95% CI clear of zero. The conclusion is not that money does not
matter; it is that the link is non-linear and concentrated at the
rich-rich end. That is exactly the shape the LOWESS smoother had been
hinting at all along.""")

md("""## A bonus from the scrape: the Report itself

The rankings spreadsheet is the core of the analysis, but the chapter
metadata I scraped from the seven editions has its own story. The crawler
collected 51 chapters across 2020-2026 with author lists, affiliations and
reading times. As far as I can tell that table does not exist anywhere
else, and it lets us watch how a flagship interdisciplinary report has
shifted over half a decade.""")

code("""display(Image(filename=FIG + "chapters_trend.png"))""")

md("""A couple of things to notice. The number of chapters per edition is
volatile (2024 was unusually slim, with just five chapters), but average
reading time has risen sharply, from about 27 minutes in 2020 to about 40
in 2024. The Report is, quite literally, a longer read. The affiliations
field shows that John Helliwell, Jan-Emmanuel De Neve and Richard Layard
have continued to anchor the editorial team, while recent editions have
brought in a wider circle of specialists, especially social psychologists
working on adolescents and digital well-being. The 2026 edition is more
or less a thematic deep-dive on social media, and that pivot shows up
clearly in the titles of the scraped chapter list.""")

md("""## Time series: where has happiness moved?

Because the scraper grabbed every annual `Figure_2.1.xls`, we can also
compare country trajectories across editions. The plot is unremarkable
at the very top (Finland is almost flat), but it does show the slow
erosion of US scores relative to Northern Europe and a small
post-pandemic recovery in parts of Latin America.""")

code("""display(Image(filename=FIG + "ladder_timeseries.png"))""")

md("""## Take-aways

1. Money matters, but mostly *indirectly*. Once you control for social
   support, freedom, life expectancy and trust in institutions, the
   marginal contribution of income at the median split is statistically
   indistinguishable from zero.
2. But the link is non-linear: at the top quartile of income (>~&#36;44k
   PPP) the conditional effect rises to about +0.32 Ladder points with a
   95% CI clear of zero. The Easterlin paradox bites in the middle of
   the distribution; among the rich-rich it does not.
3. Social capital is at least as potent as material wealth. In every
   Nordic country the biggest single contributor to the Ladder gap above
   the world mean is *social support*, not GDP.
4. Internet penetration is the dominant moderator. Split-importance ranks
   it ahead of social support, corruption, life expectancy, freedom and
   urbanisation, which lines up with the WHR 2026 edition's own pivot
   towards social-media research.
5. The Report itself is changing. Chapters have got longer and the 2026
   edition pivots sharply onto social media; the scrape lets us watch
   that shift happen.

### Replication

```bash
git clone https://github.com/maksimkitikov/Data-Science-in-Economics.git
cd Data-Science-in-Economics
pip install -r requirements.txt
make all
```

### Sources

* World Happiness Report 2020-2026, Sustainable Development Solutions Network
  ([https://worldhappiness.report](https://worldhappiness.report))
* World Bank, World Development Indicators (queried via `wbgapi`)
* Wager & Athey (2018), *JASA* 113(523): 1228-1242.
* Athey, Tibshirani & Wager (2019), *Annals of Statistics* 47(2): 1148-1178.
* Davis & Heller (2017), *AEA P&P*.""")

nb["cells"] = cells

ep = ExecutePreprocessor(timeout=300, kernel_name="python3")
ep.preprocess(nb, {"metadata": {"path": "."}})

with open(NB_PATH, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote {NB_PATH}")
