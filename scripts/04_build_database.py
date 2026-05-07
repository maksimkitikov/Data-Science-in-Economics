"""Build whr.db (country_year + country_meta + whr_chapters) and write the
2023 cross-section (WHR INNER JOIN World Bank) to data/clean/analysis.csv."""
import os
import sqlite3

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
RAW = ROOT + "data/raw/"
CLN = ROOT + "data/clean/"
os.makedirs(CLN, exist_ok=True)

DB_PATH = CLN + "whr.db"

whr_panel = pd.read_csv(RAW + "whr_panel.csv")
wb_indicators = pd.read_csv(RAW + "wb_indicators.csv")
whr_chapters = pd.read_csv(RAW + "whr_chapters.csv")

print(f"whr_panel:     {whr_panel.shape}")
print(f"wb_indicators: {wb_indicators.shape}")
print(f"whr_chapters:  {whr_chapters.shape}")

# wbgapi gives most of the country-name -> ISO mapping; the rest are WHR oddities.
crosswalk = wb_indicators[["country_code", "country_name"]].drop_duplicates()
manual = {
    "United States": "USA",
    "Russia": "RUS",
    "Czech Republic": "CZE",
    "South Korea": "KOR",
    "Hong Kong S.A.R. of China": "HKG",
    "Hong Kong S.A.R., China": "HKG",
    "Palestinian Territories": "PSE",
    "State of Palestine": "PSE",
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
    "Turkiye": "TUR",
    "Türkiye": "TUR",
    "Turkey": "TUR",
    "Congo (Brazzaville)": "COG",
    "Congo (Kinshasa)": "COD",
    "Ivory Coast": "CIV",
    "Gambia": "GMB",
    "North Cyprus": "CYP",
    "Eswatini, Kingdom of": "SWZ",
    "Swaziland": "SWZ",
    "Cape Verde": "CPV",
    "Congo": "COG",
    "Kyrgyzstan": "KGZ",
    "Macedonia": "MKD",
    "North Macedonia": "MKD",
}

name_to_iso = dict(zip(crosswalk["country_name"], crosswalk["country_code"]))
name_to_iso.update(manual)


def to_iso(name):
    return name_to_iso.get(name.replace("*", "").strip())


whr_panel["Country name"] = whr_panel["Country name"].str.replace("*", "", regex=False).str.strip()
whr_panel["country_code"] = whr_panel["Country name"].map(to_iso)
unmatched = whr_panel.loc[whr_panel["country_code"].isna(), "Country name"].unique()
print(f"\nunmatched ({len(unmatched)}): {sorted(unmatched)[:10]}")

# Always rebuild so the result is deterministic.
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
conn = sqlite3.connect(DB_PATH)

country_year = whr_panel.dropna(subset=["country_code"]).rename(columns={
    "Country name": "country_name",
    "Ladder score": "ladder",
    "Logged GDP per capita": "log_gdp",
    "Social support": "social_support",
    "Healthy life expectancy": "life_exp_healthy",
    "Freedom to make life choices": "freedom",
    "Generosity": "generosity",
    "Perceptions of corruption": "corruption",
})
country_year.to_sql("country_year", conn, index=False, if_exists="replace")
wb_indicators.to_sql("country_meta", conn, index=False, if_exists="replace")
whr_chapters.to_sql("whr_chapters", conn, index=False, if_exists="replace")

# Indexes on the join keys.
conn.execute("CREATE INDEX idx_cy_country ON country_year(country_code, year);")
conn.execute("CREATE INDEX idx_cm_country ON country_meta(country_code);")

QUERY = """
SELECT
    cy.country_code,
    cy.country_name,
    cy.year,
    cy.ladder,
    cy.log_gdp,
    cy.social_support,
    cy.life_exp_healthy,
    cy.freedom,
    cy.generosity,
    cy.corruption,
    cm.gdp_pc_ppp,
    cm.life_exp,
    cm.internet_pct,
    cm.urban_pct,
    cm.education_spend_pct,
    cm.fdi_pct
FROM country_year AS cy
INNER JOIN country_meta AS cm
    ON cy.country_code = cm.country_code
WHERE cy.year = 2023
ORDER BY cy.ladder DESC;
"""
analysis = pd.read_sql_query(QUERY, conn)
print(f"\nanalysis: {analysis.shape}")
print(analysis.head(5))

analysis.to_csv(CLN + "analysis.csv", index=False)

print("\nyear=2023 summary:")
print(pd.read_sql_query("""
SELECT ROUND(AVG(ladder), 2) AS mean_ladder,
       ROUND(MIN(ladder), 2) AS min_ladder,
       ROUND(MAX(ladder), 2) AS max_ladder,
       COUNT(*) AS n_countries
FROM country_year
WHERE year = 2023;
""", conn))

print("\nchapters by year:")
print(pd.read_sql_query("""
SELECT year,
       COUNT(*) AS n_chapters,
       ROUND(AVG(reading_time_min), 1) AS mean_read_min,
       ROUND(AVG(n_authors), 1) AS mean_authors
FROM whr_chapters
GROUP BY year
ORDER BY year;
""", conn))

conn.close()
print(f"\ndb:    {DB_PATH}")
print(f"wrote: {CLN + 'analysis.csv'}")
