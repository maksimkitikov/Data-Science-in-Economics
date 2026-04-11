"""
Download a handful of supplementary cross-country indicators from the World
Bank using `wbgapi`, the same library used in the BEE2041 wrangling problem
set. We pull the 2022 cross-section (last year with broad coverage) for:

    NY.GDP.PCAP.PP.KD     GDP per capita, PPP (constant 2021 USD)
    SP.DYN.LE00.IN        Life expectancy at birth, total (years)
    IT.NET.USER.ZS        Individuals using the internet (% of population)
    SP.URB.TOTL.IN.ZS     Urban population (% of total)
    SE.XPD.TOTL.GD.ZS     Government expenditure on education (% of GDP)
    BX.KLT.DINV.WD.GD.ZS  Foreign direct investment, net inflows (% of GDP)

Output: data/raw/wb_indicators.csv, one row per country.
"""
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

def fetch_with_retry(code, n_tries=5):
    """Pull one WB indicator, retrying on transient API errors.

    The World Bank's REST endpoint sometimes returns 503 (especially the
    first call, where wbgapi also pulls the source concepts). We back off
    exponentially and try again.
    """
    last_err = None
    for attempt in range(n_tries):
        try:
            return wb.data.DataFrame(code, time=YEAR, labels=True).reset_index()
        except Exception as e:    # APIError, APIResponseError, ConnectionError, ...
            last_err = e
            wait = 2 ** (attempt + 1)
            print(f"   attempt {attempt+1} for {code} failed ({e}); sleeping {wait}s")
            time.sleep(wait)
    raise last_err


# Pull each indicator and merge into a wide cross-section.
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
                     validate="1:1")    # validate=1:1 catches duplicate ISO codes

print(f"\nIndicator cross-section shape: {wb_df.shape}")
print(wb_df.head())
print("\nMissing values per indicator:")
print(wb_df.isna().sum())

out = DAT + "wb_indicators.csv"
wb_df.to_csv(out, index=False)
print(f"Wrote: {out}")
