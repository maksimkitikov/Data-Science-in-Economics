"""Six progressively richer OLS specs of the Ladder on its candidate covariates.

Standard errors are HC3 throughout. m6 is on z-scored variables so the
coefficients can be compared in standard-deviation units. Output:
output/tables/regression_table.tex (via pystout) plus a tidy CSV companion.
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from pystout import pystout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
CLN = ROOT + "data/clean/"
TAB = ROOT + "output/tables/"
os.makedirs(TAB, exist_ok=True)

df = pd.read_csv(CLN + "analysis.csv")

required = ["ladder", "log_gdp", "life_exp_healthy", "social_support",
            "freedom", "corruption", "gdp_pc_ppp"]
for col in required:
    assert col in df.columns, f"missing column: {col}"

# Cross-source sanity on log-GDP: WHR ships a bundled value but the World
# Bank PPP series is the cleaner benchmark. Use it in m5 to check the
# coefficient does not move much.
df["log_gdp_wb"] = np.log(df["gdp_pc_ppp"])

needed = ["ladder", "log_gdp", "life_exp_healthy", "social_support",
          "freedom", "corruption", "log_gdp_wb"]
df = df.dropna(subset=needed).reset_index(drop=True)
print(f"n = {len(df)}")

Y = df["ladder"]


def fit(rhs):
    X = sm.add_constant(df[rhs])
    return sm.OLS(Y, X).fit(cov_type="HC3")


m1 = fit(["log_gdp"])
m2 = fit(["log_gdp", "life_exp_healthy"])
m3 = fit(["log_gdp", "life_exp_healthy", "social_support"])
m4 = fit(["log_gdp", "life_exp_healthy", "social_support", "freedom",
          "corruption"])
m5 = fit(["log_gdp_wb", "life_exp_healthy", "social_support", "freedom",
          "corruption"])

# m6: same right-hand side as m4 but with z-scored variables, so each
# coefficient reads as "Ladder SDs per 1 SD of X".
z = (df[needed] - df[needed].mean()) / df[needed].std()
m6 = sm.OLS(z["ladder"],
            sm.add_constant(z[["log_gdp", "life_exp_healthy",
                               "social_support", "freedom",
                               "corruption"]])).fit(cov_type="HC3")

for name, m in [("m1", m1), ("m2", m2), ("m3", m3), ("m4", m4),
                ("m5", m5), ("m6", m6)]:
    print(f"\n=== {name} (n={m.nobs:.0f}, R^2={m.rsquared:.3f}) ===")
    print(m.summary().tables[1])

varlabels = {
    "const": "Constant",
    "log_gdp": "Log GDP per capita (WHR)",
    "log_gdp_wb": "Log GDP per capita PPP (WB)",
    "life_exp_healthy": "Healthy life expectancy",
    "social_support": "Social support",
    "freedom": "Freedom",
    "corruption": "Corruption (perceptions)",
}

pystout(
    models=[m1, m2, m3, m4, m5, m6],
    file=TAB + "regression_table.tex",
    addnotes=[
        "Robust (HC3) standard errors in parentheses.",
        r"Specification (6) uses standardised variables.",
        r"$^*\,p<0.10$, $^{**}\,p<0.05$, $^{***}\,p<0.01$.",
    ],
    digits=3,
    endog_names=["WHR Ladder score (2023)"] * 6,
    varlabels=varlabels,
    mgroups={
        "WHR covariates": [1, 4],
        "WB cross-check": [5, 5],
        "Standardised": [6, 6],
    },
    modstat={"nobs": "Obs.", "rsquared_adj": r"Adj. R$^2$"},
    title="OLS regressions of life-satisfaction (Ladder) on candidate covariates",
    label="tab:ols",
    stars={.1: "*", .05: "**", .01: "***"},
)

# Tidy CSV companion. The website JSON pipeline reads this rather than
# the .tex file.
rows = []
for name, m in [("m1", m1), ("m2", m2), ("m3", m3), ("m4", m4),
                ("m5", m5), ("m6", m6)]:
    for var in m.params.index:
        rows.append({
            "model": name,
            "term":  var,
            "coef":  round(m.params[var], 4),
            "se":    round(m.bse[var], 4),
            "p":     round(m.pvalues[var], 4),
            "r2":    round(m.rsquared, 4),
            "n":     int(m.nobs),
        })
pd.DataFrame(rows).to_csv(TAB + "regression_summary.csv", index=False)
print(f"\nwrote {TAB}regression_table.tex")
print(f"wrote {TAB}regression_summary.csv")
