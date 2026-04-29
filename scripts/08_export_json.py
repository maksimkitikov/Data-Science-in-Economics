"""dump data.js for the static site."""
import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm_api
from statsmodels.nonparametric.smoothers_lowess import lowess

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
     "gdp_ppp": safe_round(r.gdp_pc_ppp, 1)}
    for r in df.itertuples()
])

# lowess for the GDP scatter
gdp_df = df.dropna(subset=["gdp_pc_ppp", "ladder"]).copy()
sm_arr = lowess(gdp_df["ladder"], np.log(gdp_df["gdp_pc_ppp"]),
                frac=0.5, it=2, return_sorted=True)
add("gdp_smoother", [
    {"gdp_ppp": round(float(np.exp(x)), 1), "ladder": round(float(y), 3)}
    for x, y in sm_arr
])

# decomposition for top 15
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
    add("cate_headline", json.load(f))

reg = pd.read_csv(TAB + "regression_summary.csv")
add("regressions", reg.to_dict(orient="records"))

with open(DOCS + "data.js", "w", encoding="utf-8") as f:
    f.write("window.SITE_DATA = ")
    json.dump(bundle, f, ensure_ascii=False, indent=2)
    f.write(";\n")
print(f"wrote {DOCS}data.js")
