"""Six OLS specifications of WHR Ladder on its covariates with HC3 robust standard errors."""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from pystout import pystout

CLN = "data/clean/"
TAB = "output/tables/"
os.makedirs(TAB, exist_ok=True)

df = pd.read_csv(CLN + "analysis.csv")

# WB log GDP serves as an independent cross-check on the WHR's bundled value
df["log_gdp_wb"] = np.log(df["gdp_pc_ppp"])

needed = ["ladder", "log_gdp", "life_exp_healthy", "social_support",
          "freedom", "corruption", "log_gdp_wb"]
for c in needed:
    assert c in df.columns, f"missing column: {c}"
df = df.dropna(subset=needed).reset_index(drop=True)
print(f"n = {len(df)}")

Y = df["ladder"]


def fit(rhs):
    """OLS with HC3 robust standard errors, the spec from the modelling lecture."""
    return sm.OLS(Y, sm.add_constant(df[rhs])).fit(cov_type="HC3")


# add covariates one block at a time, so that each column shows the marginal contribution of the new regressor
m1 = fit(["log_gdp"])
m2 = fit(["log_gdp", "life_exp_healthy"])
m3 = fit(["log_gdp", "life_exp_healthy", "social_support"])
m4 = fit(["log_gdp", "life_exp_healthy", "social_support", "freedom", "corruption"])
m5 = fit(["log_gdp_wb", "life_exp_healthy", "social_support", "freedom", "corruption"])

# m6 uses z-scored variables so that the coefficients are in standard-deviation units and directly comparable
z = (df[needed] - df[needed].mean()) / df[needed].std()
m6 = sm.OLS(z["ladder"],
            sm.add_constant(z[["log_gdp", "life_exp_healthy",
                               "social_support", "freedom",
                               "corruption"]])).fit(cov_type="HC3")

models = {"m1": m1, "m2": m2, "m3": m3, "m4": m4, "m5": m5, "m6": m6}

for name, m in models.items():
    print(f"\n{name} (n={m.nobs:.0f}, R^2={m.rsquared:.3f})")
    print(m.summary().tables[1])

labels = {
    "const":            "Constant",
    "log_gdp":          "Log GDP per capita (WHR)",
    "log_gdp_wb":       "Log GDP per capita PPP (WB)",
    "life_exp_healthy": "Healthy life expectancy",
    "social_support":   "Social support",
    "freedom":          "Freedom",
    "corruption":       "Corruption (perceptions)",
}

pystout(
    models=list(models.values()),
    file=TAB + "regression_table.tex",
    addnotes=["Robust (HC3) standard errors in parentheses.",
              r"Specification (6) uses standardised variables.",
              r"$^*\,p<0.10$, $^{**}\,p<0.05$, $^{***}\,p<0.01$."],
    digits=3,
    endog_names=["WHR Ladder score (2023)"] * 6,
    varlabels=labels,
    mgroups={"WHR covariates": [1, 4],
             "WB cross-check": [5, 5],
             "Standardised":   [6, 6]},
    modstat={"nobs": "Obs.", "rsquared_adj": r"Adj. R$^2$"},
    title="OLS regressions of life-satisfaction (Ladder) on candidate covariates",
    label="tab:ols",
    stars={.1: "*", .05: "**", .01: "***"},
)

# tidy long CSV that the website JSON pipeline reads
rows = []
for name, m in models.items():
    for var in m.params.index:
        rows.append({"model": name, "term": var,
                     "coef": round(m.params[var], 4),
                     "se":   round(m.bse[var], 4),
                     "p":    round(m.pvalues[var], 4),
                     "r2":   round(m.rsquared, 4),
                     "n":    int(m.nobs)})
pd.DataFrame(rows).to_csv(TAB + "regression_summary.csv", index=False)
print(f"wrote {TAB}regression_table.tex and regression_summary.csv")
