# 03_download_worldbank 0.01    BEE2041-empirical-project    yyyy-mm-dd:2026-04-25
#---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8
#
# Syntax is: python src/03_download_worldbank.py
#
# This file pulls a small set of additional country-level indicators from the
# World Bank using the wbgapi library, exactly as demonstrated in the BEE2041
# Problem Set Solutions: Data Wrangling in Python (Question 2 - Merging with
# Diagnostics). For the year 2022 (the latest with broad cross-country coverage
# at the moment of writing) we collect:
#
#     NY.GDP.PCAP.PP.KD     GDP per capita, PPP (constant 2021 international $)
#     SP.DYN.LE00.IN        Life expectancy at birth, total (years)
#     IT.NET.USER.ZS        Individuals using the internet (% of population)
#     SP.URB.TOTL.IN.ZS     Urban population (% of total)
#     SE.XPD.TOTL.GD.ZS     Government expenditure on education (% of GDP)
#     BX.KLT.DINV.WD.GD.ZS  Foreign direct investment, net inflows (% of GDP)
#
# Output: data/raw/wb_indicators.csv with one row per country.

#-------------------------------------------------------------------------------
# (0) Imports and directory locations
#-------------------------------------------------------------------------------
import os
import time
import pandas as pd
import wbgapi as wb
from wbgapi import APIError, APIResponseError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
DAT  = ROOT + "data/raw/"
os.makedirs(DAT, exist_ok=True)

YEAR        = 2022
INDICATORS  = {
    "NY.GDP.PCAP.PP.KD":    "gdp_pc_ppp",
    "SP.DYN.LE00.IN":       "life_exp",
    "IT.NET.USER.ZS":       "internet_pct",
    "SP.URB.TOTL.IN.ZS":    "urban_pct",
    "SE.XPD.TOTL.GD.ZS":    "education_spend_pct",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_pct",
}

def fetch_with_retry(code, n_tries=4):
    """Pull one WB indicator with exponential back-off on transient API errors.

    The World-Bank API occasionally returns 503 Service Unavailable; we retry
    with the same back-off schedule used elsewhere in the pipeline.
    """
    for attempt in range(n_tries):
        try:
            return wb.data.DataFrame(code, time=YEAR, labels=True).reset_index()
        except (APIError, APIResponseError) as e:
            if attempt == n_tries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"   attempt {attempt+1} for {code} failed ({e}); sleeping {wait}s")
            time.sleep(wait)


#-------------------------------------------------------------------------------
# (1) Pull each indicator with wbgapi, merge into a single wide cross-section
#-------------------------------------------------------------------------------
frames = []
for code, short in INDICATORS.items():
    print(f"  fetching {code}...")
    df = fetch_with_retry(code)
    df = df.rename(columns={
        "economy": "country_code",
        "Country": "country_name",
        code:      short,
    })
    frames.append(df[["country_code", "country_name", short]])
    time.sleep(0.5)    # gentle pacing between API calls

# Sequential left-merge to combine indicators
wb_df = frames[0]
for f in frames[1:]:
    wb_df = pd.merge(wb_df, f.drop(columns="country_name"),
                     on="country_code", how="left",
                     validate="1:1")     # cf. Python for Data Management.pdf, p.53-56

#-------------------------------------------------------------------------------
# (2) Write
#-------------------------------------------------------------------------------
print(f"\nIndicator cross-section shape: {wb_df.shape}")
print(wb_df.head())
print("\nMissing values per indicator:")
print(wb_df.isna().sum())

out = DAT + "wb_indicators.csv"
wb_df.to_csv(out, index=False)
print(f"Wrote: {out}")
