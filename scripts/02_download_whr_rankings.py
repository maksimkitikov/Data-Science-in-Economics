"""WHR Figure 2.1 xls files for 2020-2024, stacked into one panel."""
import os
import time

import pandas as pd
import requests

RAW = "data/raw/"
os.makedirs(RAW, exist_ok=True)

YEARS = [2020, 2021, 2022, 2023, 2024]
URL_TPL = "https://files.worldhappiness.report/WHR{yy}_Data_Figure_2.1.xls"
HEAD = {"User-Agent": "bee2041-empirical-project/1.0"}

KEEP = ["Country name", "Ladder score", "Logged GDP per capita",
        "Social support", "Healthy life expectancy",
        "Freedom to make life choices", "Generosity",
        "Perceptions of corruption"]


def download(url, n_tries=4):
    for k in range(n_tries):
        try:
            r = requests.get(url, headers=HEAD, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if k == n_tries - 1:
                raise
            time.sleep(3)


frames = []
for y in YEARS:
    fname = RAW + f"whr{y}_fig21.xls"
    if not os.path.exists(fname):
        print(f"[{y}] downloading")
        with open(fname, "wb") as f:
            f.write(download(URL_TPL.format(yy=str(y)[2:])).content)
        time.sleep(1)
    else:
        print(f"[{y}] cached")

    df = pd.read_excel(fname)

    # only the country/score columns disagree across editions
    rename_map = {
        "Country": "Country name",
        "Happiness score": "Ladder score",
    }
    df = df.rename(columns=rename_map)

    # 2022 and 2024 ship only the "Explained by:" decomposition columns,
    # not the raw covariates. Those are contributions to Ladder, not the
    # raw values, so leave them as NaN rather than miscategorising them.
    for c in KEEP:
        if c not in df.columns:
            df[c] = pd.NA

    assert "Country name" in df.columns and "Ladder score" in df.columns

    df = df[KEEP].copy()
    df["year"] = y
    frames.append(df)

panel = pd.concat(frames, ignore_index=True)
print(f"panel shape: {panel.shape}")
print(panel.groupby("year").size())

panel.to_csv(RAW + "whr_panel.csv", index=False)
print(f"wrote {RAW}whr_panel.csv")
