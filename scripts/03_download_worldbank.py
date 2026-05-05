"""WB indicators (2022 cross-section) -> raw csv."""
import os
import time

import pandas as pd
import wbgapi as wb

RAW = "data/raw/"
os.makedirs(RAW, exist_ok=True)

YEAR = 2022
INDICATORS = {
    "NY.GDP.PCAP.PP.KD":    "gdp_pc_ppp",
    "SP.DYN.LE00.IN":       "life_exp",
    "IT.NET.USER.ZS":       "internet_pct",
    "SP.URB.TOTL.IN.ZS":    "urban_pct",
    "SE.XPD.TOTL.GD.ZS":    "education_spend_pct",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_pct",
}


def fetch(code, n_tries=5):
    for k in range(n_tries):
        try:
            return wb.data.DataFrame(code, time=YEAR, labels=True).reset_index()
        except Exception:
            if k == n_tries - 1:
                raise
            time.sleep(3)


# one indicator at a time, then trim
frames = []
for code, short in INDICATORS.items():
    print(f"  {code}")
    df = fetch(code).rename(columns={"economy": "country_code",
                                     "Country": "country_name",
                                     code: short})
    frames.append(df[["country_code", "country_name", short]])
    time.sleep(0.5)

# validate=1:1 catches duplicate codes
out = frames[0]
for f in frames[1:]:
    out = pd.merge(out, f.drop(columns="country_name"),
                   on="country_code", how="outer", validate="1:1")

print(f"\nshape: {out.shape}")
print("missing per indicator:")
print(out.isna().sum())

out.to_csv(RAW + "wb_indicators.csv", index=False)
print(f"wrote {RAW}wb_indicators.csv")
