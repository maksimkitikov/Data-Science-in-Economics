# 07_descriptive_figures 0.01    BEE2041-empirical-project    yyyy-mm-dd:2026-04-25
#---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8
#
# Syntax is: python src/07_descriptive_figures.py
#
# This file generates the descriptive figures that open the blog post:
#   (1) Top-10 vs bottom-10 happiest countries (horizontal bar chart)
#   (2) GDP per capita vs Ladder score (scatter with non-linear LOWESS fit)
#   (3) Variance decomposition: which factors "explain" the Ladder?
#       (stacked bar chart for the top-15 happiest countries)
#   (4) Time trend: number of WHR chapters per year & average reading time,
#       built directly from the scraped chapter table.
#
# The plotting style mirrors developmentMortality.py from the BEE2041-2026
# repo: clean grids, country code annotations, tight_layout, dual PDF + PNG
# output for both reproducibility and quick blog inclusion.

#-------------------------------------------------------------------------------
# (0) Imports and directory locations
#-------------------------------------------------------------------------------
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.nonparametric.smoothers_lowess import lowess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
RAW  = ROOT + "data/raw/"
CLN  = ROOT + "data/clean/"
FIG  = ROOT + "output/figures/"
os.makedirs(FIG, exist_ok=True)

# Repo-wide plot defaults
plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "axes.titlesize":   12,
    "axes.titleweight": "bold",
    "axes.labelsize":   11,
    "xtick.labelsize":  10,
    "ytick.labelsize":  10,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})

NAVY  = "#1f3a5f"
GOLD  = "#FFC300"
TEAL  = "#3380FF"
GREY  = "#888888"

#-------------------------------------------------------------------------------
# (1) Load
#-------------------------------------------------------------------------------
df       = pd.read_csv(CLN + "analysis.csv")
panel    = pd.read_csv(RAW + "whr_panel.csv")
chapters = pd.read_csv(RAW + "whr_chapters.csv")

#-------------------------------------------------------------------------------
# (2) Top-10 vs bottom-10 happiest countries
#-------------------------------------------------------------------------------
ranked = df.sort_values("ladder", ascending=False)
top    = ranked.head(10).iloc[::-1]
bot    = ranked.tail(10)

fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharex=True)

axes[0].barh(top["country_name"], top["ladder"], color=NAVY)
axes[0].set_title("Top 10 happiest countries (WHR 2023)", loc="left")
axes[0].set_xlabel("Ladder score")
axes[0].grid(True, axis="x", linestyle="--", linewidth=0.5, alpha=0.5)

axes[1].barh(bot["country_name"], bot["ladder"], color=GOLD)
axes[1].set_title("Bottom 10 happiest countries (WHR 2023)", loc="left")
axes[1].set_xlabel("Ladder score")
axes[1].grid(True, axis="x", linestyle="--", linewidth=0.5, alpha=0.5)

plt.tight_layout()
plt.savefig(FIG + "top_bottom_10.pdf")
plt.savefig(FIG + "top_bottom_10.png", dpi=160)
plt.clf()

#-------------------------------------------------------------------------------
# (3) GDP vs Ladder scatter, with LOWESS fit
#-------------------------------------------------------------------------------
df_plot = df.dropna(subset=["gdp_pc_ppp", "ladder"]).copy()
df_plot["log_gdp_wb"] = np.log(df_plot["gdp_pc_ppp"])
sm   = lowess(df_plot["ladder"], df_plot["log_gdp_wb"], frac=0.5, it=2,
              return_sorted=True)

plt.figure(figsize=(8.5, 5.5))
plt.scatter(df_plot["gdp_pc_ppp"], df_plot["ladder"],
            color=TEAL, alpha=0.7, s=35, edgecolor="white",
            label="Country observation")
plt.plot(np.exp(sm[:, 0]), sm[:, 1], color=NAVY, linewidth=2,
         label="LOWESS smoother (frac=0.5)")
plt.xscale("log")
plt.xlabel("GDP per capita, PPP — log axis (US$, World Bank 2022)")
plt.ylabel("WHR Ladder score (2023)")
plt.title("Money buys happiness — but at a sharply decreasing rate", loc="left")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
plt.legend(loc="lower right", frameon=False)

# Annotate a few illustrative countries
highlight = ["FIN", "USA", "DNK", "IND", "ZWE", "AFG", "CRI", "BRA", "QAT"]
for _, row in df_plot.iterrows():
    if row["country_code"] in highlight:
        plt.annotate(row["country_code"],
                     xy=(row["gdp_pc_ppp"], row["ladder"]),
                     xytext=(5, 3), textcoords="offset points",
                     fontsize=9, color="#222222")

plt.tight_layout()
plt.savefig(FIG + "gdp_vs_ladder.pdf")
plt.savefig(FIG + "gdp_vs_ladder.png", dpi=160)
plt.clf()

#-------------------------------------------------------------------------------
# (4) Stacked-bar variance decomposition for the top-15 happiest countries.
#     We fit a small linear regression (no intercept) of the WHR Ladder onto
#     its six standard explanatory components, then break down each country's
#     score into beta_k * X_k contributions. A simpler alternative would be
#     to use the WHR-published "Explained by:" columns directly, but those
#     are only present for some yearly files.
#-------------------------------------------------------------------------------
import statsmodels.api as sm_api

decomp_vars = ["log_gdp", "social_support", "life_exp_healthy",
               "freedom", "corruption", "generosity"]
decomp_lbls = ["Log GDP", "Social support", "Healthy life exp.",
               "Freedom", "Corruption", "Generosity"]

dec_df = df.dropna(subset=decomp_vars + ["ladder"]).copy()
X_dec  = sm_api.add_constant(dec_df[decomp_vars])
m_dec  = sm_api.OLS(dec_df["ladder"], X_dec).fit()
print("Decomposition model R^2:", round(m_dec.rsquared, 3))

# Construct contribution per country: beta_k * X_k (centred on mean)
means = dec_df[decomp_vars].mean()
contrib = (dec_df[decomp_vars] - means) * m_dec.params[decomp_vars]
contrib["country_name"] = dec_df["country_name"]
contrib["country_code"] = dec_df["country_code"]
contrib["ladder"]       = dec_df["ladder"]

# Pick the top-15 happiest countries
top15 = contrib.sort_values("ladder", ascending=False).head(15).iloc[::-1]

palette = ["#1f3a5f", "#3380FF", "#7faaff", "#FFC300", "#ff7f50", "#888888"]
fig, ax = plt.subplots(figsize=(9, 6))

bottom_pos = np.zeros(len(top15))
bottom_neg = np.zeros(len(top15))
for v, lab, col in zip(decomp_vars, decomp_lbls, palette):
    vals = top15[v].values
    pos  = np.where(vals > 0, vals, 0)
    neg  = np.where(vals < 0, vals, 0)
    ax.barh(top15["country_name"], pos, left=bottom_pos, color=col, label=lab)
    ax.barh(top15["country_name"], neg, left=bottom_neg, color=col)
    bottom_pos += pos
    bottom_neg += neg

ax.axvline(0, color="black", linewidth=0.6)
ax.set_xlabel("Contribution to Ladder score (deviation from sample mean)")
ax.set_title("What lifts the world's happiest countries above the global average?",
             loc="left")
ax.grid(True, axis="x", linestyle="--", linewidth=0.5, alpha=0.5)
ax.legend(loc="lower right", frameon=False, fontsize=9)
plt.tight_layout()
plt.savefig(FIG + "decomposition.pdf")
plt.savefig(FIG + "decomposition.png", dpi=160)
plt.clf()

#-------------------------------------------------------------------------------
# (5) WHR research output over time (built from the scraped chapter table)
#-------------------------------------------------------------------------------
yearly = chapters.groupby("year").agg(
    n_chapters=("title", "size"),
    mean_read_min=("reading_time_min", "mean"),
    mean_authors=("n_authors", "mean"),
).reset_index()

fig, ax1 = plt.subplots(figsize=(8, 4.5))
ax1.bar(yearly["year"], yearly["n_chapters"], color=TEAL, alpha=0.85,
        label="Chapters per edition")
ax1.set_xlabel("WHR edition year")
ax1.set_ylabel("Chapters per edition", color=TEAL)
ax1.tick_params(axis="y", labelcolor=TEAL)
ax1.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.5)

ax2 = ax1.twinx()
ax2.plot(yearly["year"], yearly["mean_read_min"], color=GOLD, marker="o",
         linewidth=2, label="Mean reading time (min)")
ax2.set_ylabel("Mean reading time (min)", color=GOLD)
ax2.tick_params(axis="y", labelcolor=GOLD)
ax2.spines["top"].set_visible(False)

plt.title("Scraped from worldhappiness.report: how WHR research has grown",
          loc="left")
plt.tight_layout()
plt.savefig(FIG + "chapters_trend.pdf")
plt.savefig(FIG + "chapters_trend.png", dpi=160)
plt.clf()

#-------------------------------------------------------------------------------
# (6) Time series: WHR Ladder for a handful of countries 2020-2024
#-------------------------------------------------------------------------------
panel_clean = panel.copy()
panel_clean["Country name"] = panel_clean["Country name"].str.replace(
    "*", "", regex=False).str.strip()

watch = ["Finland", "Denmark", "United States", "United Kingdom",
         "China", "India", "Brazil", "Costa Rica"]
sub   = panel_clean[panel_clean["Country name"].isin(watch)]

plt.figure(figsize=(9, 5))
for c in watch:
    s = sub[sub["Country name"] == c].sort_values("year")
    plt.plot(s["year"], s["Ladder score"], marker="o", linewidth=2,
             label=c)
plt.xlabel("WHR edition year")
plt.ylabel("Ladder score")
plt.title("Selected countries: how happiness has moved 2020-2024", loc="left")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
plt.legend(loc="lower left", frameon=False, ncol=2, fontsize=9)
plt.tight_layout()
plt.savefig(FIG + "ladder_timeseries.pdf")
plt.savefig(FIG + "ladder_timeseries.png", dpi=160)
plt.clf()

print(f"All descriptive figures written to {FIG}")
