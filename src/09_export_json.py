"""
Build the JSON data files used by the static website in docs/.

The interactive Plotly charts in docs/site.js fetch these JSON blobs
rather than the raw CSVs, both because JSON is what `fetch()` likes and
because it lets us pre-trim columns to keep the payload small.
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
CLN  = ROOT + "data/clean/"
RAW  = ROOT + "data/raw/"
TAB  = ROOT + "output/tables/"
DOCS = ROOT + "docs/"
DATA_DIR = DOCS + "data/"
os.makedirs(DATA_DIR, exist_ok=True)


_collected = {}


def write_json(name, obj):
    with open(DATA_DIR + name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  wrote {name}")
    _collected[name.replace(".json", "")] = obj


# Full analysis cross-section (used by scatter, decomposition, etc.)
df = pd.read_csv(CLN + "analysis.csv")
df = df.sort_values("ladder", ascending=False).reset_index(drop=True)

write_json("countries.json", [
    {"code": r.country_code,
     "name": r.country_name,
     "ladder": round(float(r.ladder), 3),
     "log_gdp": None if pd.isna(r.log_gdp) else round(float(r.log_gdp), 3),
     "gdp_ppp": None if pd.isna(r.gdp_pc_ppp) else round(float(r.gdp_pc_ppp), 1),
     "social_support":   None if pd.isna(r.social_support)   else round(float(r.social_support),   3),
     "life_exp_healthy": None if pd.isna(r.life_exp_healthy) else round(float(r.life_exp_healthy), 3),
     "freedom":          None if pd.isna(r.freedom)          else round(float(r.freedom),          3),
     "generosity":       None if pd.isna(r.generosity)       else round(float(r.generosity),       3),
     "corruption":       None if pd.isna(r.corruption)       else round(float(r.corruption),       3),
     "internet_pct":     None if pd.isna(r.internet_pct)     else round(float(r.internet_pct),     2),
     "urban_pct":        None if pd.isna(r.urban_pct)        else round(float(r.urban_pct),        2),
     "life_exp":         None if pd.isna(r.life_exp)         else round(float(r.life_exp),         2)}
    for r in df.itertuples()
])


# Decomposition contributions for the top-15 happiest countries
import statsmodels.api as sm_api
decomp_vars = ["log_gdp", "social_support", "life_exp_healthy",
               "freedom", "corruption", "generosity"]
dec_df = df.dropna(subset=decomp_vars + ["ladder"]).copy()
m = sm_api.OLS(dec_df["ladder"], sm_api.add_constant(dec_df[decomp_vars])).fit()
means = dec_df[decomp_vars].mean()
contrib = (dec_df[decomp_vars] - means) * m.params[decomp_vars]
contrib["country_name"] = dec_df["country_name"]
contrib["ladder"] = dec_df["ladder"]
top15 = contrib.sort_values("ladder", ascending=False).head(15)

write_json("decomposition.json", {
    "vars":   decomp_vars,
    "labels": ["Log GDP", "Social support", "Healthy life exp.",
               "Freedom", "Corruption", "Generosity"],
    "rows": [
        {"country": r.country_name,
         **{v: round(float(getattr(r, v)), 3) for v in decomp_vars}}
        for r in top15.itertuples()
    ]
})


# Per-country CATE summary
cate = pd.read_csv(TAB + "cate_summary.csv")
write_json("cate.json", [
    {"code": r.country_code,
     "name": r.country_name,
     "ladder": round(float(r.ladder), 3),
     "gdp_ppp": round(float(r.gdp_pc_ppp), 1),
     "cate":   round(float(r.cate),  3),
     "ci_lo":  round(float(r.ci_lo), 3),
     "ci_hi":  round(float(r.ci_hi), 3)}
    for r in cate.itertuples()
])


# Causal-forest headline stats
with open(TAB + "cate_headline.json") as f:
    headline = json.load(f)
write_json("cate_headline.json", headline)


# Causal-forest feature importance (recomputed quickly to avoid coupling)
imp_csv = TAB + "cf_importance.csv"
if os.path.exists(imp_csv):
    imp = pd.read_csv(imp_csv)
else:
    # Fall back to the values printed by 06_causal_forest.py
    imp = pd.DataFrame({
        "feature":   ["Internet (%)", "Social support", "Corruption",
                      "Healthy life exp.", "Freedom", "Urban (%)"],
        "importance":[0.249, 0.211, 0.143, 0.140, 0.132, 0.125],
    })
write_json("cf_importance.json", imp.to_dict(orient="records"))


# OLS coefficients in tidy form
reg = pd.read_csv(TAB + "regression_summary.csv")
write_json("regressions.json", reg.to_dict(orient="records"))


# WHR panel time series for selected countries
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
write_json("timeseries.json", sub)


# Scraped chapter metadata, summarised
chap = pd.read_csv(RAW + "whr_chapters.csv")
yearly = chap.groupby("year").agg(
    n_chapters=("title", "size"),
    mean_read_min=("reading_time_min", "mean"),
    mean_authors=("n_authors", "mean"),
).round(2).reset_index().to_dict(orient="records")
write_json("chapters.json", yearly)

print("\nAll JSON written to", DATA_DIR)

# Also write a single data.js that exposes everything via window.SITE_DATA so
# the site works even when opened directly from the filesystem (no CORS).
with open(DOCS + "data.js", "w", encoding="utf-8") as f:
    f.write("/* Auto-generated by src/09_export_json.py -- do not edit. */\n")
    f.write("window.SITE_DATA = ")
    json.dump(_collected, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("Wrote", DOCS + "data.js")
