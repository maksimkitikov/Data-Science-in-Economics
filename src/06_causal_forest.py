# 06_causal_forest 0.01    BEE2041-empirical-project    yyyy-mm-dd:2026-04-25
#---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8
#
# Syntax is: python src/06_causal_forest.py
#
# This file estimates a causal forest (CausalForestDML) following the recipe
# in Damian Clarke's BEE2041-2026 file replicationCausalForest/source/
# immigrantEffects.py. The canonical use of a causal forest in that file is to
# uncover heterogeneity in the treatment effect of being a Canadian-named
# resume; we use the same machinery to ask: how does the partial association
# between log GDP per capita and life satisfaction (the "Ladder" score) vary
# across countries with different baseline characteristics?
#
# Concretely:
#   Y    = WHR Ladder score (2023)
#   D    = Indicator for "high GDP per capita PPP" (1 if above sample median)
#   X    = Healthy life expectancy, social support, freedom, corruption,
#          internet penetration, urbanisation
#
# This framing is best understood as descriptive heterogeneity rather than a
# clean causal estimand: cross-country comparisons are not random assignments.
# The causal-forest is therefore used here as a flexible non-parametric tool
# to surface which moderators predict differences in the Ladder-GDP gradient,
# in the same spirit as Davis & Heller (AEA P&P, 2017) - referenced in the
# project brief as relevant background reading.
#
# Outputs:
#   output/tables/cate_summary.csv  - per-country CATEs and intervals
#   output/figures/cate_hist.pdf    - histogram of CATEs
#   output/figures/cate_ranked.pdf  - ranked CATEs with 95% CIs
#   output/figures/cate_by_gdp.pdf  - CATE versus GDP per capita (PPP)
#   output/figures/cf_importance.pdf - SHAP-like permutation importance plot

#-------------------------------------------------------------------------------
# (0) Imports and directory locations
#-------------------------------------------------------------------------------
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from econml.dml import CausalForestDML

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
CLN  = ROOT + "data/clean/"
FIG  = ROOT + "output/figures/"
TAB  = ROOT + "output/tables/"
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

SEED = 121316    # seed used by Clarke in immigrantEffects.py
np.random.seed(SEED)

#-------------------------------------------------------------------------------
# (1) Build modelling sample
#-------------------------------------------------------------------------------
df = pd.read_csv(CLN + "analysis.csv")

needed = ["ladder", "gdp_pc_ppp", "life_exp_healthy", "social_support",
          "freedom", "corruption", "internet_pct", "urban_pct"]
df = df.dropna(subset=needed).reset_index(drop=True)
print(f"Causal-forest sample: n = {len(df)}")

Y = df["ladder"].values * 1.0
D = (df["gdp_pc_ppp"] > df["gdp_pc_ppp"].median()).astype(int).values
X = df[["life_exp_healthy", "social_support", "freedom", "corruption",
        "internet_pct", "urban_pct"]].values
X_cols = ["Healthy life exp.", "Social support", "Freedom", "Corruption",
          "Internet (%)", "Urban (%)"]

#-------------------------------------------------------------------------------
# (2) Fit a causal forest using the Clarke recipe
#-------------------------------------------------------------------------------
cf = CausalForestDML(
    model_y           = GradientBoostingRegressor(random_state=SEED),
    model_t           = GradientBoostingClassifier(random_state=SEED),
    discrete_treatment= True,
    n_estimators      = 1000,
    min_samples_leaf  = 5,
    random_state      = SEED,
)
cf.fit(Y, D, X=X)

ate    = cf.ate(X)
cate   = cf.effect(X)
ci_lo, ci_hi = cf.effect_interval(X, alpha=0.05)

print(f"\nAverage treatment effect (high-GDP indicator on Ladder): {ate:.3f}")
print(f"  95% CI: [{cf.ate_interval(X)[0]:.3f}, {cf.ate_interval(X)[1]:.3f}]")
print(f"CATE distribution:  min={cate.min():.2f}  median={np.median(cate):.2f}  max={cate.max():.2f}")

#-------------------------------------------------------------------------------
# (3) Persist per-country CATEs
#-------------------------------------------------------------------------------
out = df[["country_code", "country_name", "ladder", "gdp_pc_ppp"]].copy()
out["cate"]  = cate
out["ci_lo"] = ci_lo
out["ci_hi"] = ci_hi
out = out.sort_values("cate", ascending=False).reset_index(drop=True)
out.to_csv(TAB + "cate_summary.csv", index=False)

# Persist headline numbers so the blog can quote them dynamically
import json
ate_lo, ate_hi = cf.ate_interval(X)
with open(TAB + "cate_headline.json", "w") as f:
    json.dump({"ate":      round(float(ate),  3),
               "ate_ci":   [round(float(ate_lo), 3), round(float(ate_hi), 3)],
               "cate_min": round(float(cate.min()),    3),
               "cate_med": round(float(np.median(cate)), 3),
               "cate_max": round(float(cate.max()),    3),
               "n":        int(len(cate))}, f, indent=2)
print(f"Wrote: {TAB}cate_summary.csv")
print(f"Wrote: {TAB}cate_headline.json")

#-------------------------------------------------------------------------------
# (4) Plots: histogram of CATEs (Clarke's first plot pattern)
#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
# (5) Plot: ranked CATEs with 95% CIs (Clarke's second plot pattern)
#-------------------------------------------------------------------------------
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

#-------------------------------------------------------------------------------
# (6) Plot: CATE vs GDP per capita PPP (visualises the moderation)
#-------------------------------------------------------------------------------
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
# Highlight a few illustrative countries
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

#-------------------------------------------------------------------------------
# (7) Permutation feature importance (built-in econml utility)
#-------------------------------------------------------------------------------
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

print(f"\nFigures written to {FIG}")
