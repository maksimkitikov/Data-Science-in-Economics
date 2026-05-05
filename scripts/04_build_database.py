"""build whr.db, join WHR + WB, dump analysis.csv."""
import os
import sqlite3

import pandas as pd

RAW = "data/raw/"
CLN = "data/clean/"
os.makedirs(CLN, exist_ok=True)

DB = CLN + "whr.db"

panel    = pd.read_csv(RAW + "whr_panel.csv")
wb       = pd.read_csv(RAW + "wb_indicators.csv")
chapters = pd.read_csv(RAW + "whr_chapters.csv")

# manual ISO-3 patches for WHR/WB spelling mismatches
extra = {
    "United States": "USA",
    "Russia": "RUS",
    "South Korea": "KOR",
    "Czech Republic": "CZE",
    "Hong Kong S.A.R. of China": "HKG",
    "Hong Kong S.A.R., China": "HKG",
    "Taiwan Province of China": "TWN",
    "Iran": "IRN",
    "Vietnam": "VNM",
    "Slovakia": "SVK",
    "Egypt": "EGY",
    "Yemen": "YEM",
    "Venezuela": "VEN",
    "Bolivia": "BOL",
    "Tanzania": "TZA",
    "Laos": "LAO",
    "Moldova": "MDA",
    "Syria": "SYR",
    "Turkey": "TUR",
    "Turkiye": "TUR",
    "Türkiye": "TUR",
    "Congo (Brazzaville)": "COG",
    "Congo (Kinshasa)": "COD",
    "Ivory Coast": "CIV",
    "Gambia": "GMB",
    "Cape Verde": "CPV",
    "Palestinian Territories": "PSE",
    "State of Palestine": "PSE",
    "Eswatini, Kingdom of": "SWZ",
    "Swaziland": "SWZ",
    "Kyrgyzstan": "KGZ",
    "North Macedonia": "MKD",
}
name2iso = dict(zip(wb["country_name"], wb["country_code"]))
name2iso.update(extra)

panel["Country name"] = panel["Country name"].str.replace("*", "", regex=False).str.strip()
panel["country_code"] = panel["Country name"].map(name2iso)
unmatched = sorted(panel.loc[panel["country_code"].isna(), "Country name"].unique())
print(f"unmatched: {len(unmatched)} -> {unmatched[:5]}")
assert len(unmatched) <= 5, f"unmatched: {unmatched}"

if os.path.exists(DB):
    os.remove(DB)
conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")

conn.executescript("""
CREATE TABLE country_meta (
    country_code         TEXT NOT NULL PRIMARY KEY,
    country_name         TEXT NOT NULL,
    gdp_pc_ppp           REAL,
    life_exp             REAL,
    internet_pct         REAL,
    urban_pct            REAL,
    education_spend_pct  REAL,
    fdi_pct              REAL
);

CREATE TABLE country_year (
    country_code     TEXT    NOT NULL,
    year             INTEGER NOT NULL,
    country_name     TEXT,
    ladder           REAL,
    log_gdp          REAL,
    social_support   REAL,
    life_exp_healthy REAL,
    freedom          REAL,
    generosity       REAL,
    corruption       REAL,
    PRIMARY KEY (country_code, year),
    FOREIGN KEY (country_code) REFERENCES country_meta(country_code)
);

CREATE TABLE whr_chapters (
    year             INTEGER NOT NULL,
    doi              TEXT NOT NULL,
    title            TEXT,
    authors          TEXT,
    n_authors        INTEGER,
    affiliations     TEXT,
    reading_time_min INTEGER,
    url              TEXT,
    PRIMARY KEY (year, doi)
);

CREATE INDEX idx_cy_country ON country_year(country_code);
CREATE INDEX idx_cy_year    ON country_year(year);
""")

# parent first (FK target)
meta = wb[["country_code", "country_name", "gdp_pc_ppp", "life_exp",
           "internet_pct", "urban_pct", "education_spend_pct",
           "fdi_pct"]].drop_duplicates("country_code")
meta.to_sql("country_meta", conn, if_exists="append", index=False)

cy = panel.dropna(subset=["country_code"]).rename(columns={
    "Country name":                 "country_name",
    "Ladder score":                 "ladder",
    "Logged GDP per capita":        "log_gdp",
    "Social support":               "social_support",
    "Healthy life expectancy":      "life_exp_healthy",
    "Freedom to make life choices": "freedom",
    "Generosity":                   "generosity",
    "Perceptions of corruption":    "corruption",
})
# keep only rows whose code exists in country_meta (FK)
known = set(meta["country_code"])
cy = cy[cy["country_code"].isin(known)]
cy[["country_code", "year", "country_name", "ladder", "log_gdp",
    "social_support", "life_exp_healthy", "freedom", "generosity",
    "corruption"]].to_sql("country_year", conn, if_exists="append", index=False)

# a few chapters have no DOI: synthesise one from the URL so PK still works
chapters = chapters.copy()
chapters["doi"] = chapters["doi"].fillna("nodoi:" + chapters["url"])
chapters[["year", "doi", "title", "authors", "n_authors",
          "affiliations", "reading_time_min", "url"]].to_sql(
    "whr_chapters", conn, if_exists="append", index=False)

# cross-section join WHR x WB on ISO-3, year=2023
analysis = pd.read_sql_query("""
    SELECT cy.country_code, cy.country_name, cy.year,
           cy.ladder, cy.log_gdp, cy.social_support, cy.life_exp_healthy,
           cy.freedom, cy.generosity, cy.corruption,
           cm.gdp_pc_ppp, cm.life_exp, cm.internet_pct,
           cm.urban_pct, cm.education_spend_pct, cm.fdi_pct
    FROM country_year cy
    INNER JOIN country_meta cm ON cy.country_code = cm.country_code
    WHERE cy.year = 2023
    ORDER BY cy.ladder DESC
""", conn)
print(f"analysis: {analysis.shape}")
analysis.to_csv(CLN + "analysis.csv", index=False)

# panel sanity check
print(pd.read_sql_query("""
    SELECT year,
           COUNT(*)             AS n,
           ROUND(AVG(ladder),2) AS mean_ladder
    FROM country_year
    GROUP BY year
    ORDER BY year
""", conn))

conn.close()
print(f"wrote {DB} and {CLN}analysis.csv")
