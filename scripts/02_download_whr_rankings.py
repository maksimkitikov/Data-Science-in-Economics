"""Download WHR Figure 2.1 spreadsheets for 2020-2024 and stack them into one panel."""
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
    """Try a few times in case the WHR origin is flaky, this is the retry-with-back-off pattern from the Workflow lecture."""
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

    # different WHR editions ship different column names, so we standardise them with a single rename map
    rename_map = {
        "Country": "Country name",
        "Happiness score": "Ladder score",
        "Explained by: GDP per capita": "Logged GDP per capita",
        "Explained by: Log GDP per capita": "Logged GDP per capita",
        "Explained by: Social support": "Social support",
        "Explained by: Healthy life expectancy": "Healthy life expectancy",
        "Explained by: Freedom to make life choices": "Freedom to make life choices",
        "Explained by: Generosity": "Generosity",
        "Explained by: Perceptions of corruption": "Perceptions of corruption",
    }
    drop_cols = [src for src, dst in rename_map.items()
                 if src in df.columns and dst in df.columns]
    df = df.drop(columns=drop_cols).rename(columns=rename_map)

    # fail loudly if WHR ever changes its schema again, this is the assertion idea from Workflow lecture slide 33
    missing = [c for c in KEEP if c not in df.columns]
    assert not missing, f"WHR {y} missing columns: {missing}"

    df = df[KEEP].copy()
    df["year"] = y
    frames.append(df)

panel = pd.concat(frames, ignore_index=True)
print(f"panel shape: {panel.shape}")
print(panel.groupby("year").size())

panel.to_csv(RAW + "whr_panel.csv", index=False)
print(f"wrote {RAW}whr_panel.csv")
