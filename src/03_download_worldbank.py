"""
03_download_worldbank.py
------------------------
Pull a 2022 cross-section of World Bank indicators via the `wbgapi` Python
client. We use these as supplementary covariates that are *not* already in
the WHR Figure 2.1 file: GDP per capita PPP (independent benchmark for the
WHR's bundled log-GDP), life expectancy, internet penetration, urban share,
education spending and FDI.

Course references followed here
    * "Problem Set Solutions: Data Wrangling in Python" (Clarke, 2026),
      Question 2 - this is exactly the wbgapi.data.DataFrame call shown
      there.
    * Python for Data Management (Clarke, 2026), slide 53/54: always pass
      `validate="1:1"` to pd.merge so the merge breaks loudly when
      assumptions are wrong, not silently.
"""
import os
import time

import pandas as pd
import wbgapi as wb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
DAT  = ROOT + "data/raw/"
os.makedirs(DAT, exist_ok=True)

YEAR = 2022

# (World Bank indicator code -> friendlier short name we use downstream).
INDICATORS = {
    "NY.GDP.PCAP.PP.KD":    "gdp_pc_ppp",
    "SP.DYN.LE00.IN":       "life_exp",
    "IT.NET.USER.ZS":       "internet_pct",
    "SP.URB.TOTL.IN.ZS":    "urban_pct",
    "SE.XPD.TOTL.GD.ZS":    "education_spend_pct",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_pct",
}


def fetch_with_retry(code, n_tries=5):
    """Up to five attempts at the wb endpoint, doubling the wait each time."""
    last_err = None
    for attempt in range(n_tries):
        try:
            return wb.data.DataFrame(code, time=YEAR, labels=True).reset_index()
        except Exception as e:
            last_err = e
            time.sleep(2 ** (attempt + 1))
    raise last_err


frames = []
for code, short in INDICATORS.items():
    print(f"  {code}")
    df = fetch_with_retry(code)
    df = df.rename(columns={
        "economy": "country_code",
        "Country": "country_name",
        code:      short,
    })
    frames.append(df[["country_code", "country_name", short]])
    time.sleep(0.5)

# One-to-one merge on country_code is the right relationship: every country
# appears once per indicator. validate="1:1" makes the merge fail loudly if
# that assumption is ever broken (Python for Data Management, slide 53).
wb_df = frames[0]
for f in frames[1:]:
    wb_df = pd.merge(
        wb_df,
        f.drop(columns="country_name"),
        on="country_code", how="left",
        validate="1:1",
    )

print(f"\nshape: {wb_df.shape}")
print(wb_df.head())
print("\nmissing:")
print(wb_df.isna().sum())

out = DAT + "wb_indicators.csv"
wb_df.to_csv(out, index=False)
print(f"wrote {out}")
