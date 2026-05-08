"""Export the data.js bundle the static site reads."""
import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm_api
from statsmodels.nonparametric.smoothers_lowess import lowess

RAW = "data/raw/"
CLN = "data/clean/"
TAB = "output/tables/"
DOCS = "docs/"
os.makedirs(DOCS, exist_ok=True)

bundle = {}


def add(name, obj):
    bundle[name] = obj
    print(f"  + {name}")


def safe_round(v, n):
    return None if pd.isna(v) else round(float(v), n)


df = pd.read_csv(CLN + "analysis.csv")
df = df.sort_values("ladder", ascending=False).reset_index(drop=True)

add("countries", [
    {"code": r.country_code,
     "name": r.country_name,
     "ladder": round(float(r.ladder), 3),
     "log_gdp": safe_round(r.log_gdp, 3),
     "gdp_ppp": safe_round(r.gdp_pc_ppp, 1),
     "social_support": safe_round(r.social_support, 3),
     "life_exp_healthy": safe_round(r.life_exp_healthy, 3),
     "freedom": safe_round(r.freedom, 3),
     "generosity": safe_round(r.generosity, 3),
     "corruption": safe_round(r.corruption, 3),
     "internet_pct": safe_round(r.internet_pct, 2),
     "urban_pct": safe_round(r.urban_pct, 2),
     "life_exp": safe_round(r.life_exp, 2)}
    for r in df.itertuples()
])


# LOWESS smoother for the GDP-vs-Ladder scatter.
gdp_df = df.dropna(subset=["gdp_pc_ppp", "ladder"]).copy()
sm_arr = lowess(gdp_df["ladder"], np.log(gdp_df["gdp_pc_ppp"]),
                frac=0.5, it=2, return_sorted=True)
add("gdp_smoother", [
    {"gdp_ppp": round(float(np.exp(x)), 1), "ladder": round(float(y), 3)}
    for x, y in sm_arr
])


# Decomposition contributions for top-15.
decomp_vars = ["log_gdp", "social_support", "life_exp_healthy",
               "freedom", "corruption", "generosity"]
dec_df = df.dropna(subset=decomp_vars + ["ladder"]).copy()
m = sm_api.OLS(dec_df["ladder"], sm_api.add_constant(dec_df[decomp_vars])).fit()
means = dec_df[decomp_vars].mean()
contrib = (dec_df[decomp_vars] - means) * m.params[decomp_vars]
contrib["country_name"] = dec_df["country_name"]
contrib["ladder"] = dec_df["ladder"]
top15 = contrib.sort_values("ladder", ascending=False).head(15)

add("decomposition", {
    "vars": decomp_vars,
    "labels": ["Log GDP", "Social support", "Healthy life exp.",
               "Freedom", "Corruption", "Generosity"],
    "rows": [
        {"country": r.country_name,
         **{v: round(float(getattr(r, v)), 3) for v in decomp_vars}}
        for r in top15.itertuples()
    ]
})


# Per-country CATEs.
cate = pd.read_csv(TAB + "cate_summary.csv")
add("cate", [
    {"code": r.country_code,
     "name": r.country_name,
     "ladder": round(float(r.ladder), 3),
     "gdp_ppp": round(float(r.gdp_pc_ppp), 1),
     "cate": round(float(r.cate), 3),
     "ci_lo": round(float(r.ci_lo), 3),
     "ci_hi": round(float(r.ci_hi), 3)}
    for r in cate.itertuples()
])


with open(TAB + "cate_headline.json") as f:
    headline = json.load(f)
add("cate_headline", headline)


# Treatment-threshold sensitivity (median vs 75th percentile).
sensitivity_path = TAB + "ate_sensitivity.json"
if os.path.exists(sensitivity_path):
    with open(sensitivity_path) as f:
        add("ate_sensitivity", json.load(f))


# Causal-forest split-importance.
imp = pd.read_csv(TAB + "cf_importance.csv")
add("cf_importance", imp.to_dict(orient="records"))


# OLS coefficients.
reg = pd.read_csv(TAB + "regression_summary.csv")
add("regressions", reg.to_dict(orient="records"))


# Time series for the watch list.
panel = pd.read_csv(RAW + "whr_panel.csv")
panel["Country name"] = panel["Country name"].str.replace("*", "", regex=False).str.strip()
watch = ["Finland", "Denmark", "United States", "United Kingdom",
         "China", "India", "Brazil", "Costa Rica"]
sub = (panel[panel["Country name"].isin(watch)]
       .groupby("Country name")
       .apply(lambda g: g.sort_values("year")[["year", "Ladder score"]]
              .rename(columns={"Ladder score": "ladder"})
              .to_dict(orient="records"))
       .to_dict())
add("timeseries", sub)


# Scraped chapter trend.
chap = pd.read_csv(RAW + "whr_chapters.csv")
yearly = chap.groupby("year").agg(
    n_chapters=("title", "size"),
    mean_read_min=("reading_time_min", "mean"),
    mean_authors=("n_authors", "mean"),
).round(2).reset_index().to_dict(orient="records")
add("chapters", yearly)

# Per-year chapter list, used by the hover-card on the chapters chart.
chapters_by_year = {}
for year, group in chap.groupby("year"):
    chapters_by_year[int(year)] = [
        {
            "title": row["title"],
            "authors": row["authors"] if pd.notna(row["authors"]) else "",
            "n_authors": int(row["n_authors"]) if pd.notna(row["n_authors"]) else 0,
            "reading_time_min": int(row["reading_time_min"]) if pd.notna(row["reading_time_min"]) else None,
            "url": row["url"] if pd.notna(row["url"]) else "",
        }
        for _, row in group.iterrows()
    ]
add("chapters_by_year", chapters_by_year)


with open(DOCS + "data.js", "w", encoding="utf-8") as f:
    f.write("window.SITE_DATA = ")
    json.dump(bundle, f, ensure_ascii=False, indent=2)
    f.write(";\n")
print(f"wrote {DOCS}data.js")
