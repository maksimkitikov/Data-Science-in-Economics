"""Pull a 2022 cross-section of World Bank indicators via wbgapi."""
import os
import time
import pandas as pd
import wbgapi as wb

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

wb_df = frames[0]
for f in frames[1:]:
    wb_df = pd.merge(wb_df, f.drop(columns="country_name"),
                     on="country_code", how="left",
                     validate="1:1")

print(f"\nshape: {wb_df.shape}")
print(wb_df.head())
print("\nmissing:")
print(wb_df.isna().sum())

out = DAT + "wb_indicators.csv"
wb_df.to_csv(out, index=False)
print(f"wrote {out}")
