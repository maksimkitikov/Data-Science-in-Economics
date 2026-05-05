"""causal forest: Ladder ~ 1{GDP > median} | X. also a 75-pct refit."""
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from econml.dml import CausalForestDML
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

CLN = "data/clean/"
FIG = "output/figures/"
TAB = "output/tables/"
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

SEED = 42
np.random.seed(SEED)

df = pd.read_csv(CLN + "analysis.csv")

needed = ["ladder", "gdp_pc_ppp", "life_exp_healthy", "social_support",
          "freedom", "corruption", "internet_pct", "urban_pct"]
df = df.dropna(subset=needed).reset_index(drop=True)
print(f"n = {len(df)}")

Y = df["ladder"].astype(float).values
X = df[["life_exp_healthy", "social_support", "freedom",
        "corruption", "internet_pct", "urban_pct"]].values
feature_labels = ["Healthy life exp.", "Social support", "Freedom",
                  "Corruption", "Internet (%)", "Urban (%)"]


def make_forest():
    return CausalForestDML(
        model_y=GradientBoostingRegressor(random_state=SEED),
        model_t=GradientBoostingClassifier(random_state=SEED),
        discrete_treatment=True,
        n_estimators=1000,
        min_samples_leaf=5,
        random_state=SEED,
    )


def fit_at(quantile):
    cutoff = float(np.quantile(df["gdp_pc_ppp"], quantile))
    D = (df["gdp_pc_ppp"] > cutoff).astype(int).values
    cf = make_forest()
    cf.fit(Y, D, X=X)
    a = float(cf.ate(X))
    lo, hi = cf.ate_interval(X)
    return cf, cutoff, a, float(lo), float(hi)


# headline fit
cf, cut50, ate, lo50, hi50 = fit_at(0.50)
cate = cf.effect(X)
ci_lo, ci_hi = cf.effect_interval(X, alpha=0.05)
print(f"\nATE = {ate:.3f} (95% CI [{lo50:.3f}, {hi50:.3f}])")
print(f"CATE: min={cate.min():.2f} median={np.median(cate):.2f} max={cate.max():.2f}")

out = df[["country_code", "country_name", "ladder", "gdp_pc_ppp"]].copy()
out["cate"]  = cate.round(6)
out["ci_lo"] = ci_lo.round(6)
out["ci_hi"] = ci_hi.round(6)
out["ladder"]     = out["ladder"].round(4)
out["gdp_pc_ppp"] = out["gdp_pc_ppp"].round(2)
out.sort_values("cate", ascending=False).to_csv(TAB + "cate_summary.csv", index=False)

with open(TAB + "cate_headline.json", "w") as f:
    json.dump({"ate": round(ate, 3),
               "ate_ci": [round(lo50, 3), round(hi50, 3)],
               "cate_min": round(float(cate.min()), 3),
               "cate_med": round(float(np.median(cate)), 3),
               "cate_max": round(float(cate.max()), 3),
               "n": int(len(cate))}, f, indent=2)

# robustness: top quartile instead of median
_, cut75, ate75, lo75, hi75 = fit_at(0.75)
print(f"\nthreshold sensitivity:")
print(f"  median = ${cut50:.0f}, ATE = {ate:.3f}, CI [{lo50:.3f}, {hi50:.3f}]")
print(f"  75-pct = ${cut75:.0f}, ATE = {ate75:.3f}, CI [{lo75:.3f}, {hi75:.3f}]")

with open(TAB + "ate_sensitivity.json", "w") as f:
    json.dump({
        "headline": {"label": "Above-median GDP", "cutoff_usd": round(cut50, 0),
                     "ate": round(ate, 3), "ci": [round(lo50, 3), round(hi50, 3)]},
        "robust":   {"label": "Above 75th percentile", "cutoff_usd": round(cut75, 0),
                     "ate": round(ate75, 3), "ci": [round(lo75, 3), round(hi75, 3)]},
    }, f, indent=2)

# split-importance
imp = pd.DataFrame({"feature": feature_labels,
                    "importance": [round(float(x), 4) for x in cf.feature_importances_]})
imp.sort_values("importance", ascending=False).to_csv(TAB + "cf_importance.csv", index=False)


# cate histogram
plt.figure(figsize=(8, 5))
plt.hist(cate, bins=25, color="#3380FF", alpha=0.85, edgecolor="white")
plt.axvline(ate, color="#FFC300", linestyle="--", linewidth=2, label=f"ATE = {ate:.2f}")
plt.xlabel("CATE: Ladder gain from being above median GDP per capita")
plt.ylabel("Number of countries")
plt.title("Heterogeneity in the GDP -> Happiness gradient", loc="left")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
plt.tight_layout()
plt.savefig(FIG + "cate_hist.pdf")
plt.savefig(FIG + "cate_hist.png", dpi=160)
plt.clf()

print(f"\nfigures -> {FIG}")
