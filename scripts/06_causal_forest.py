"""Causal forest of Ladder on a 1{GDP > median} treatment, plus a 75th percentile robustness refit."""
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

SEED = 121316
np.random.seed(SEED)

df = pd.read_csv(CLN + "analysis.csv")

needed = ["ladder", "gdp_pc_ppp", "life_exp_healthy", "social_support",
          "freedom", "corruption", "internet_pct", "urban_pct"]
df = df.dropna(subset=needed).reset_index(drop=True)
print(f"n = {len(df)}")

Y = df["ladder"].values * 1.0
X = df[["life_exp_healthy", "social_support", "freedom",
        "corruption", "internet_pct", "urban_pct"]].values
X_pretty = ["Healthy life exp.", "Social support", "Freedom",
            "Corruption", "Internet (%)", "Urban (%)"]


def make_forest():
    """One place to keep the hyperparameters so the headline and robustness fits are guaranteed identical."""
    return CausalForestDML(
        model_y=GradientBoostingRegressor(random_state=SEED),
        model_t=GradientBoostingClassifier(random_state=SEED),
        discrete_treatment=True,
        n_estimators=1000,
        min_samples_leaf=5,
        random_state=SEED,
    )


def fit_at(quantile):
    """Refit the forest with a different binarisation of GDP per capita."""
    cutoff = float(np.quantile(df["gdp_pc_ppp"], quantile))
    D = (df["gdp_pc_ppp"] > cutoff).astype(int).values
    cf = make_forest()
    cf.fit(Y, D, X=X)
    a = float(cf.ate(X))
    lo, hi = cf.ate_interval(X)
    return cf, cutoff, a, float(lo), float(hi)


# headline fit: above-median income as the treatment
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

# robustness check: same forest with a 75th percentile cutoff instead of the median
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

# split-importance tells us which moderators the forest actually uses, this is the diagnostic suggested in the modelling lecture
imp = pd.DataFrame({"feature": X_pretty,
                    "importance": [round(float(x), 4) for x in cf.feature_importances_]})
imp.sort_values("importance", ascending=False).to_csv(TAB + "cf_importance.csv", index=False)


def save(name):
    plt.tight_layout()
    plt.savefig(FIG + name + ".pdf")
    plt.savefig(FIG + name + ".png", dpi=160)
    plt.clf()


# distribution of CATEs across countries
plt.figure(figsize=(8, 5))
plt.hist(cate, bins=25, color="#3380FF", alpha=0.85, edgecolor="white")
plt.axvline(ate, color="#FFC300", linestyle="--", linewidth=2, label=f"ATE = {ate:.2f}")
plt.xlabel("CATE: Ladder gain from being above median GDP per capita")
plt.ylabel("Number of countries")
plt.title("Heterogeneity in the GDP -> Happiness gradient", loc="left")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
save("cate_hist")

# every country's CATE with its 95 percent confidence interval
ranked = out.sort_values("cate", ascending=False).reset_index(drop=True)
plt.figure(figsize=(8, 6))
plt.errorbar(np.arange(len(ranked)), ranked["cate"],
             yerr=[ranked["cate"] - ranked["ci_lo"], ranked["ci_hi"] - ranked["cate"]],
             fmt="o", color="#3380FF", ecolor="#999999",
             markersize=3, elinewidth=0.6, capsize=0)
plt.axhline(0, color="black", linewidth=0.6)
plt.axhline(ate, color="#FFC300", linestyle="--", linewidth=1.5, label=f"ATE = {ate:.2f}")
plt.xlabel("Country rank (sorted by CATE)")
plt.ylabel("CATE (Ladder points)")
plt.title("Ranked country-level CATEs with 95% CIs", loc="left")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
save("cate_ranked")

# CATE plotted against GDP on a log axis
plt.figure(figsize=(8, 5))
plt.scatter(df["gdp_pc_ppp"], cate, color="#3380FF", alpha=0.7, s=30, edgecolor="white")
plt.axhline(ate, color="#FFC300", linestyle="--", linewidth=1.5, label=f"ATE = {ate:.2f}")
plt.xscale("log")
plt.xlabel("GDP per capita, PPP (log axis, US$)")
plt.ylabel("Estimated CATE")
plt.title("Where is the GDP -> Happiness gradient steepest?", loc="left")
plt.legend(loc="upper right")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
for _, row in df.assign(cate=cate).iterrows():
    if row["country_name"] in ["Finland", "United States", "India",
                               "Costa Rica", "Brazil", "Norway"]:
        plt.annotate(row["country_code"], xy=(row["gdp_pc_ppp"], row["cate"]),
                     xytext=(5, 3), textcoords="offset points",
                     fontsize=9, color="#222222")
save("cate_by_gdp")

# feature importance bar chart
order = np.argsort(cf.feature_importances_)
plt.figure(figsize=(7, 4))
plt.barh(np.array(X_pretty)[order], cf.feature_importances_[order], color="#3380FF")
plt.xlabel("Feature importance")
plt.title("Causal forest: which moderators drive heterogeneity?", loc="left")
plt.grid(True, axis="x", linestyle="--", linewidth=0.5, alpha=0.5)
save("cf_importance")

print(f"\nfigures -> {FIG}")
