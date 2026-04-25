# 05_regressions 0.01    BEE2041-empirical-project    yyyy-mm-dd:2026-04-25
#---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8
#
# Syntax is: python src/05_regressions.py
#
# This file estimates a sequence of OLS regressions of the WHR Ladder score on
# economic and social covariates. The structure follows immigrantEffects.py
# from Damian Clarke's BEE2041-2026 GitHub (replicationCausalForest/source/),
# in particular the m1..m6 specification ladder and the use of pystout to
# export a single LaTeX-ready coefficient table.
#
# Specifications:
#   (1) ladder ~ log_gdp
#   (2)        + life_exp_healthy
#   (3)        + social_support
#   (4)        + freedom + corruption
#   (5)        + log(GDP per capita PPP) from WB (validation against WHR's
#                 own Logged GDP per capita variable)
#   (6) Full model with all covariates and standardised coefficients
#
# Robust standard errors (HC3) are reported throughout as recommended in
# Workflow, Modelling & Webscraping.pdf, Testing/Debugging slides.

#-------------------------------------------------------------------------------
# (0) Imports and directory locations
#-------------------------------------------------------------------------------
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pystout import pystout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
CLN  = ROOT + "data/clean/"
TAB  = ROOT + "output/tables/"
os.makedirs(TAB, exist_ok=True)

#-------------------------------------------------------------------------------
# (1) Load and prepare analysis sample
#-------------------------------------------------------------------------------
df = pd.read_csv(CLN + "analysis.csv")

# Defensive checks - fail loudly if columns we depend on are missing
for col in ["ladder", "log_gdp", "life_exp_healthy", "social_support",
            "freedom", "corruption", "gdp_pc_ppp"]:
    assert col in df.columns, f"Missing column '{col}' in analysis.csv"

# Compute log GDP from the WB source for spec (5)
df["log_gdp_wb"] = np.log(df["gdp_pc_ppp"])

# Keep only complete cases for the full specification (Clarke pattern: drop NA
# once on the largest variable set so the m1..m6 sample is held constant)
needed = ["ladder", "log_gdp", "life_exp_healthy", "social_support",
          "freedom", "corruption", "log_gdp_wb"]
df = df.dropna(subset=needed).reset_index(drop=True)
print(f"Analysis sample: n = {len(df)}")

Y = df["ladder"]

#-------------------------------------------------------------------------------
# (2) Estimate progressive specifications
#-------------------------------------------------------------------------------
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

# Standardised version: z-score every regressor and outcome
z   = (df[needed] - df[needed].mean()) / df[needed].std()
m6  = sm.OLS(z["ladder"],
             sm.add_constant(z[["log_gdp", "life_exp_healthy",
                                "social_support", "freedom",
                                "corruption"]])).fit(cov_type="HC3")

#-------------------------------------------------------------------------------
# (3) Print a quick console summary so we can sanity-check while developing
#-------------------------------------------------------------------------------
for name, m in [("m1", m1), ("m2", m2), ("m3", m3), ("m4", m4),
                ("m5", m5), ("m6", m6)]:
    print(f"\n=== {name} ({m.nobs:.0f} obs, R^2 = {m.rsquared:.3f}) ===")
    print(m.summary().tables[1])

#-------------------------------------------------------------------------------
# (4) Export combined regression table with pystout (Clarke style)
#-------------------------------------------------------------------------------
varlabels = {
    "const":            "Constant",
    "log_gdp":          "Log GDP per capita (WHR)",
    "log_gdp_wb":       "Log GDP per capita PPP (WB)",
    "life_exp_healthy": "Healthy life expectancy",
    "social_support":   "Social support",
    "freedom":          "Freedom",
    "corruption":       "Corruption (perceptions)",
}

pystout(
    models    = [m1, m2, m3, m4, m5, m6],
    file      = TAB + "regression_table.tex",
    addnotes  = ["Robust (HC3) standard errors in parentheses.",
                 r"Specification (6) uses standardised variables.",
                 r"$^*\,p<0.10$, $^{**}\,p<0.05$, $^{***}\,p<0.01$."],
    digits    = 3,
    endog_names = ["WHR Ladder score (2023)"] * 6,
    varlabels = varlabels,
    mgroups   = {"WHR covariates": [1, 4],
                 "WB cross-check": [5, 5],
                 "Standardised":   [6, 6]},
    modstat   = {"nobs": "Obs.",
                 "rsquared_adj": r"Adj. R$^2$"},
    title     = "OLS regressions of life-satisfaction (Ladder) on candidate covariates",
    label     = "tab:ols",
    stars     = {.1: "*", .05: "**", .01: "***"},
)

#-------------------------------------------------------------------------------
# (5) Also save a CSV summary that the blog notebook can render directly
#-------------------------------------------------------------------------------
rows = []
for name, m in [("m1", m1), ("m2", m2), ("m3", m3), ("m4", m4),
                ("m5", m5), ("m6", m6)]:
    for var in m.params.index:
        rows.append({
            "model":   name,
            "term":    var,
            "coef":    round(m.params[var], 4),
            "se":      round(m.bse[var], 4),
            "p":       round(m.pvalues[var], 4),
            "r2":      round(m.rsquared, 4),
            "n":       int(m.nobs),
        })
pd.DataFrame(rows).to_csv(TAB + "regression_summary.csv", index=False)
print(f"\nWrote: {TAB}regression_table.tex")
print(f"Wrote: {TAB}regression_summary.csv")
