"""
02_download_whr_rankings.py
---------------------------
Download the official "Figure 2.1" spreadsheets the WHR publishes alongside
each annual edition (2020-2024) and stack them into a tidy long panel.

These are the country-level Ladder scores plus the six explanatory components
(log GDP, social support, healthy life expectancy, freedom, generosity,
perceptions of corruption).

Course references followed here
    * Python for Data Management (Clarke, 2026):
        - pd.read_excel for spreadsheet input (slide 19)
        - pd.concat for stacking comparable frames (slide 41)
    * Workflow, Modelling & Webscraping (Clarke, 2026), slide 55: build in
      retry logic with exponential back-off, never assume a request will
      succeed.
"""
import os
import time

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
DAT  = ROOT + "data/raw/"
os.makedirs(DAT, exist_ok=True)

YEARS    = [2020, 2021, 2022, 2023, 2024]
HEADERS  = {"User-Agent": "bee2041-empirical-project/1.0"}
URL_TPL  = "https://files.worldhappiness.report/WHR{yy}_Data_Figure_2.1.xls"

# Columns we keep in the final panel.  The 2022 edition uses different headers,
# so we rename them to match the rest of the panel before stacking.
KEEP_COLS = [
    "Country name", "Ladder score",
    "Logged GDP per capita", "Social support",
    "Healthy life expectancy", "Freedom to make life choices",
    "Generosity", "Perceptions of corruption",
]


def get_with_retry(url, n_tries=4):
    """GET with up to four tries and exponential back-off (Workflow, sl. 55)."""
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
    url   = URL_TPL.format(yy=str(year)[2:])
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

    # 2022 file uses "Country" / "Happiness score" instead of the conventional
    # WHR labels.  Rename so the stack below works on a single column schema.
    if year == 2022:
        df = df.rename(columns={
            "Country":         "Country name",
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
