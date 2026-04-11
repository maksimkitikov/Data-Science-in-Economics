"""
Pull the country-level data behind Figure 2.1 of the World Happiness Report
editions 2020-2024 directly from the WHR file server. We save each yearly
.xls under data/raw/, then stack the comparable columns into a tidy panel
in data/raw/whr_panel.csv.

The naming convention WHR{YY}_Data_Figure_2.1.xls turned up while inspecting
each chapter page in 01_scrape_whr_chapters.py, which is why this download
script lives next to the scrapes rather than under data preparation.
"""
import os
import time
import requests
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
DAT  = ROOT + "data/raw/"
os.makedirs(DAT, exist_ok=True)

YEARS    = [2020, 2021, 2022, 2023, 2024]
HEADERS  = {"User-Agent": "BEE2041-student-project/1.0 (educational)"}
URL_TPL  = "https://files.worldhappiness.report/WHR{yy}_Data_Figure_2.1.xls"


def get_with_retry(url, n_tries=4):
    """GET url with exponential backoff on transient HTTP errors.

    Backoff schedule: 2s, 4s, 8s. Final attempt raises if it still fails. The
    polite-scraper guidance comes directly from Workflow, Modelling &
    Webscraping.pdf, slide 56 ("A good webscraping script handles errors
    gracefully -- use try/except blocks and build in retry logic").
    """
    for attempt in range(n_tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == n_tries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"   attempt {attempt+1} failed ({e}); sleeping {wait}s")
            time.sleep(wait)


# Download each year's .xls (skip if cached) and collect into one panel.
panel = []
for year in YEARS:
    url   = URL_TPL.format(yy=str(year)[2:])
    fname = DAT + f"whr{year}_fig21.xls"

    if not os.path.exists(fname):
        print(f"[{year}] downloading {url}")
        r = get_with_retry(url)
        with open(fname, "wb") as f:
            f.write(r.content)
        time.sleep(1.0)
    else:
        print(f"[{year}] using cached {fname}")

    df = pd.read_excel(fname)

    # The 2022 file has a different schema: rename to a common one
    if year == 2022:
        df = df.rename(columns={
            "Country":         "Country name",
            "Happiness score": "Ladder score",
        })

    # The 2020-2023 files include the underlying covariates; 2024 only the
    # "Explained by:" decomposition. We keep what is available.
    keep = ["Country name", "Ladder score",
            "Logged GDP per capita", "Social support",
            "Healthy life expectancy", "Freedom to make life choices",
            "Generosity", "Perceptions of corruption"]
    df   = df[[c for c in keep if c in df.columns]].copy()
    df["year"] = year
    panel.append(df)

# Stack and write the tidy panel.
panel_df = pd.concat(panel, ignore_index=True)
print(f"\nPanel shape: {panel_df.shape}")
print("Coverage by year:")
print(panel_df.groupby("year").size())

out = DAT + "whr_panel.csv"
panel_df.to_csv(out, index=False)
print(f"Wrote: {out}")
