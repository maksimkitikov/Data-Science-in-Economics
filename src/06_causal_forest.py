"""
06_causal_forest.py
-------------------
Fit a causal forest on the WHR cross-section to look at heterogeneity in the
GDP -> Ladder gradient.

Treatment definition. The "treatment" is a binary indicator for being above
the sample-median GDP per capita PPP. The conditioning set X covers six
potential moderators (healthy life expectancy, social support, freedom,
corruption, internet penetration, urban share). The CATE we recover should
be read as *descriptive* heterogeneity, conditional on those moderators -
not as a causal effect of "becoming richer" since we are working with a
cross-section.

Course references followed here
    * Workflow, Modelling & Webscraping (Clarke, 2026), slides 41-46:
      definition of ATE/CATE, motivation for the honest tree, key
      references.
    * Wager & Athey (2018), JASA 113(523): 1228-1242 - the inferential
      backbone of `econml.dml.CausalForestDML`.
    * Athey, Tibshirani & Wager (2019), Annals of Statistics 47(2):
      1148-1178 - generalisation to non-binary treatments.
    * Davis & Heller (2017), AEA P&P - applied template; their treatment is
      also a discrete indicator.
"""
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from econml.dml import CausalForestDML
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
CLN  = ROOT + "data/clean/"
FIG  = ROOT + "output/figures/"
TAB  = ROOT + "output/tables/"
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

SEED = 121316
np.random.seed(SEED)

df = pd.read_csv(CLN + "analysis.csv")

needed = ["ladder", "gdp_pc_ppp", "life_exp_healthy", "social_support",
          "freedom", "corruption", "internet_pct", "urban_pct"]
df = df.dropna(subset=needed).reset_index(drop=True)
print(f"n = {len(df)}")

Y = df["ladder"].values * 1.0
D = (df["gdp_pc_ppp"] > df["gdp_pc_ppp"].median()).astype(int).values
X = df[["life_exp_healthy", "social_support", "freedom", "corruption",
        "internet_pct", "urban_pct"]].values
X_cols = ["Healthy life exp.", "Social support", "Freedom", "Corruption",
          "Internet (%)", "Urban (%)"]

# Gradient-boosted nuisance models (model_y for E[Y|X], model_t for the
# propensity P(D=1|X)).  Discrete treatment because D is a 0/1 indicator.
cf = CausalForestDML(
    model_y            = GradientBoostingRegressor(random_state=SEED),
    model_t            = GradientBoostingClassifier(random_state=SEED),
    discrete_treatment = True,
    n_estimators       = 1000,
    min_samples_leaf   = 5,
    random_state       = SEED,
)
cf.fit(Y, D, X=X)

ate            = cf.ate(X)
cate           = cf.effect(X)
ci_lo, ci_hi   = cf.effect_interval(X, alpha=0.05)
ate_lo, ate_hi = cf.ate_interval(X)

print(f"\nATE = {ate:.3f}  (95% CI [{ate_lo:.3f}, {ate_hi:.3f}])")
print(f"CATE: min={cate.min():.2f}  median={np.median(cate):.2f}  max={cate.max():.2f}")

out = df[["country_code", "country_name", "ladder", "gdp_pc_ppp"]].copy()
out["cate"]  = cate
out["ci_lo"] = ci_lo
out["ci_hi"] = ci_hi
out = out.sort_values("cate", ascending=False).reset_index(drop=True)
out.to_csv(TAB + "cate_summary.csv", index=False)

with open(TAB + "cate_headline.json", "w") as f:
    json.dump({"ate":      round(float(ate), 3),
               "ate_ci":   [round(float(ate_lo), 3), round(float(ate_hi), 3)],
               "cate_min": round(float(cate.min()),    3),
               "cate_med": round(float(np.median(cate)), 3),
               "cate_max": round(float(cate.max()),    3),
               "n":        int(len(cate))}, f, indent=2)
print(f"wrote {TAB}cate_summary.csv")
print(f"wrote {TAB}cate_headline.json")

# Persist feature importance so the static-site exporter does not have to
# refit the forest just to reproduce the bar chart.
imp_df = pd.DataFrame({
    "feature":    X_cols,
    "importance": [round(float(x), 4) for x in cf.feature_importances_],
}).sort_values("importance", ascending=False)
imp_df.to_csv(TAB + "cf_importance.csv", index=False)
print(f"wrote {TAB}cf_importance.csv")

# ---- Figures ---------------------------------------------------------------

# (1) Histogram of CATEs.
plt.figure(figsize=(8, 5))
plt.hist(cate, bins=25, color="#3380FF", alpha=0.85, edgecolor="white")
plt.axvline(ate, color="#FFC300", linestyle="--", linewidth=2,
            label=f"ATE = {ate:.2f}")
plt.xlabel("CATE: Ladder gain from being above median GDP per capita")
plt.ylabel("Number of countries")
plt.title("Heterogeneity in the GDP -> Happiness gradient", loc="left")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
plt.tight_layout()
plt.savefig(FIG + "cate_hist.pdf")
plt.savefig(FIG + "cate_hist.png", dpi=160)
plt.clf()

# (2) Ranked CATEs with 95% confidence intervals.
ranked = out.copy()
plt.figure(figsize=(8, 6))
xs = np.arange(len(ranked))
plt.errorbar(xs, ranked["cate"],
             yerr=[ranked["cate"] - ranked["ci_lo"],
                   ranked["ci_hi"] - ranked["cate"]],
             fmt="o", color="#3380FF", ecolor="#999999",
             markersize=3, elinewidth=0.6, capsize=0)
plt.axhline(0, color="black", linewidth=0.6)
plt.axhline(ate, color="#FFC300", linestyle="--", linewidth=1.5,
            label=f"ATE = {ate:.2f}")
plt.xlabel("Country rank (sorted by CATE)")
plt.ylabel("CATE (Ladder points)")
plt.title("Ranked country-level CATEs with 95% confidence intervals", loc="left")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
plt.tight_layout()
plt.savefig(FIG + "cate_ranked.pdf")
plt.savefig(FIG + "cate_ranked.png", dpi=160)
plt.clf()

# (3) CATE vs GDP per capita (log axis).
plt.figure(figsize=(8, 5))
plt.scatter(df["gdp_pc_ppp"], cate, color="#3380FF", alpha=0.7, s=30,
            edgecolor="white")
plt.axhline(ate, color="#FFC300", linestyle="--", linewidth=1.5,
            label=f"ATE = {ate:.2f}")
plt.xscale("log")
plt.xlabel("GDP per capita, PPP (log axis, US$)")
plt.ylabel("Estimated CATE")
plt.title("Where is the GDP -> Happiness gradient steepest?", loc="left")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
for _, row in df.assign(cate=cate).iterrows():
    if row["country_name"] in ["Finland", "United States", "India",
                                "Costa Rica", "Brazil", "Norway"]:
        plt.annotate(row["country_code"],
                     xy=(row["gdp_pc_ppp"], row["cate"]),
                     xytext=(5, 3), textcoords="offset points",
                     fontsize=9, color="#222222")
plt.tight_layout()
plt.savefig(FIG + "cate_by_gdp.pdf")
plt.savefig(FIG + "cate_by_gdp.png", dpi=160)
plt.clf()

# (4) Forest split-importance.
imp = cf.feature_importances_
order = np.argsort(imp)
plt.figure(figsize=(7, 4))
plt.barh(np.array(X_cols)[order], imp[order], color="#3380FF")
plt.xlabel("Feature importance")
plt.title("Causal forest: which moderators drive heterogeneity?", loc="left")
plt.grid(True, axis="x", linestyle="--", linewidth=0.5, alpha=0.5)
plt.tight_layout()
plt.savefig(FIG + "cf_importance.pdf")
plt.savefig(FIG + "cf_importance.png", dpi=160)
plt.clf()

print(f"\nfigures -> {FIG}")
