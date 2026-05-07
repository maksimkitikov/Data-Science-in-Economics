"""Download WHR Figure 2.1 spreadsheets (2020-2024) and stack them into data/raw/whr_panel.csv."""
import os
import time

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
DAT = ROOT + "data/raw/"
os.makedirs(DAT, exist_ok=True)

YEARS = [2020, 2021, 2022, 2023, 2024]
HEADERS = {"User-Agent": "bee2041-empirical-project/1.0"}
URL_TPL = "https://files.worldhappiness.report/WHR{yy}_Data_Figure_2.1.xls"

KEEP_COLS = [
    "Country name", "Ladder score",
    "Logged GDP per capita", "Social support",
    "Healthy life expectancy", "Freedom to make life choices",
    "Generosity", "Perceptions of corruption",
]


def get_with_retry(url, n_tries=4):
    """Up to four attempts at a download with exponential back-off."""
    for attempt in range(n_tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == n_tries - 1:
                raise
            time.sleep(2 ** (attempt + 1))


panel = []
for year in YEARS:
    url = URL_TPL.format(yy=str(year)[2:])
    fname = DAT + f"whr{year}_fig21.xls"

    if not os.path.exists(fname):
        print(f"[{year}] download {url}")
        r = get_with_retry(url)
        with open(fname, "wb") as f:
            f.write(r.content)
        time.sleep(1.0)
    else:
        print(f"[{year}] cached")

    df = pd.read_excel(fname)

    # 2022 ships different column names; rename so the concat schema is uniform.
    if year == 2022:
        df = df.rename(columns={
            "Country": "Country name",
            "Happiness score": "Ladder score",
        })

    df = df[[c for c in KEEP_COLS if c in df.columns]].copy()
    df["year"] = year
    panel.append(df)

panel_df = pd.concat(panel, ignore_index=True)
print(f"\npanel shape: {panel_df.shape}")
print(panel_df.groupby("year").size())

out = DAT + "whr_panel.csv"
panel_df.to_csv(out, index=False)
print(f"wrote {out}")
