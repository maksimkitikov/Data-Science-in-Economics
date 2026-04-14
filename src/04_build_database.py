"""
Stitch the three raw inputs into a small SQLite database (data/clean/whr.db).
The schema keeps each country-year observation in country_year and stores
the World-Bank cross-section in country_meta; a single SQL INNER JOIN then
produces the analysis-ready cross-section data/clean/analysis.csv.

Country names are notoriously inconsistent between sources, so I crosswalk
through ISO-3 codes using a hand-coded dictionary for the few names where
the World Bank disagrees with the WHR. Anything still unmatched gets
printed so it's easy to spot.
"""
import os
import sqlite3
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
RAW  = ROOT + "data/raw/"
CLN  = ROOT + "data/clean/"
os.makedirs(CLN, exist_ok=True)

DB_PATH = CLN + "whr.db"

# Load the three raw sources.
whr_panel    = pd.read_csv(RAW + "whr_panel.csv")
wb_indicators = pd.read_csv(RAW + "wb_indicators.csv")
whr_chapters  = pd.read_csv(RAW + "whr_chapters.csv")

print(f"WHR panel:       {whr_panel.shape}")
print(f"WB indicators:   {wb_indicators.shape}")
print(f"WHR chapters:    {whr_chapters.shape}")

# Build a name -> ISO-3 crosswalk. WHR uses display names ("United States",
# "Russia"); WB ships ISO-3. wbgapi already pairs name <-> code, so we start
# from that and only hand-fix the few mismatches (Czechia, Hong Kong, etc.).
crosswalk = wb_indicators[["country_code", "country_name"]].drop_duplicates()
manual = {
    "United States":               "USA",
    "Russia":                      "RUS",
    "Czech Republic":              "CZE",
    "South Korea":                 "KOR",
    "Hong Kong S.A.R. of China":   "HKG",
    "Hong Kong S.A.R., China":     "HKG",
    "Palestinian Territories":     "PSE",
    "State of Palestine":          "PSE",
    "Taiwan Province of China":    "TWN",
    "Iran":                        "IRN",
    "Vietnam":                     "VNM",
    "Slovakia":                    "SVK",
    "Egypt":                       "EGY",
    "Yemen":                       "YEM",
    "Venezuela":                   "VEN",
    "Bolivia":                     "BOL",
    "Tanzania":                    "TZA",
    "Laos":                        "LAO",
    "Moldova":                     "MDA",
    "Syria":                       "SYR",
    "Turkiye":                     "TUR",
    "Türkiye":                     "TUR",
    "Turkey":                      "TUR",
    "Congo (Brazzaville)":         "COG",
    "Congo (Kinshasa)":            "COD",
    "Ivory Coast":                 "CIV",
    "Gambia":                      "GMB",
    "North Cyprus":                "CYP",   # WHR groups together
    "Eswatini, Kingdom of":        "SWZ",
    "Swaziland":                   "SWZ",
    "Cape Verde":                  "CPV",
    "Congo":                       "COG",   # not Congo (Kinshasa)/COD
    "Kyrgyzstan":                  "KGZ",
    "Macedonia":                   "MKD",
    "North Macedonia":             "MKD",
    # NB: "xx" appears as a placeholder row in some WHR files; we just drop it.
}

name_to_iso = dict(zip(crosswalk["country_name"], crosswalk["country_code"]))
name_to_iso.update(manual)


def to_iso(name):
    # WHR sometimes appends "*" to flag small samples; strip before matching
    cleaned = name.replace("*", "").strip()
    return name_to_iso.get(cleaned)


whr_panel["Country name"] = whr_panel["Country name"].str.replace("*", "", regex=False).str.strip()
whr_panel["country_code"] = whr_panel["Country name"].map(to_iso)
unmatched = whr_panel.loc[whr_panel["country_code"].isna(), "Country name"].unique()
print(f"\nUnmatched WHR country names ({len(unmatched)}): {sorted(unmatched)[:10]}")

# Build the SQLite database (three tables: WHR panel, WB cross-section,
# scraped chapter metadata).
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
conn = sqlite3.connect(DB_PATH)

# country_year: WHR ladder + decomposition by year
country_year = whr_panel.dropna(subset=["country_code"]).rename(columns={
    "Country name":                 "country_name",
    "Ladder score":                 "ladder",
    "Logged GDP per capita":        "log_gdp",
    "Social support":               "social_support",
    "Healthy life expectancy":      "life_exp_healthy",
    "Freedom to make life choices": "freedom",
    "Generosity":                   "generosity",
    "Perceptions of corruption":    "corruption",
})
country_year.to_sql("country_year", conn, index=False, if_exists="replace")

# country_meta: WB cross-section for 2022
wb_indicators.to_sql("country_meta", conn, index=False, if_exists="replace")

# whr_chapters: meta about WHR research output
whr_chapters.to_sql("whr_chapters", conn, index=False, if_exists="replace")

# Useful index for join speed (cosmetic on this size, demonstrates the pattern
# discussed in Relational Database Management Systems.pdf)
conn.execute("CREATE INDEX idx_cy_country ON country_year(country_code, year);")
conn.execute("CREATE INDEX idx_cm_country ON country_meta(country_code);")

# Run the analysis JOIN in raw SQL. Restricting to year=2023 because that is
# the most recent WHR file that ships the underlying covariates as well as
# the headline ladder; 2024 only has the "Explained by:" decomposition.
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
WHERE cy.year = 2023        -- 2023 is the latest year with full covariates
ORDER BY cy.ladder DESC;
"""
analysis = pd.read_sql_query(QUERY, conn)
print(f"\nAnalysis cross-section: {analysis.shape}")
print(analysis.head(5))

analysis.to_csv(CLN + "analysis.csv", index=False)

# A couple of SQL-only descriptives. Useful as a sanity check and the
# numbers feed directly into the blog narrative.
SUMMARY = """
SELECT
    ROUND(AVG(ladder), 2)             AS mean_ladder,
    ROUND(MIN(ladder), 2)             AS min_ladder,
    ROUND(MAX(ladder), 2)             AS max_ladder,
    COUNT(*)                          AS n_countries
FROM country_year
WHERE year = 2023;
"""
print("\nSQL summary (year = 2023):")
print(pd.read_sql_query(SUMMARY, conn))

CHAPTERS_BY_YEAR = """
SELECT year,
       COUNT(*)                       AS n_chapters,
       ROUND(AVG(reading_time_min),1) AS mean_read_min,
       ROUND(AVG(n_authors),1)        AS mean_authors
FROM whr_chapters
GROUP BY year
ORDER BY year;
"""
print("\nSQL summary - chapters by year:")
print(pd.read_sql_query(CHAPTERS_BY_YEAR, conn))

conn.close()
print(f"\nDatabase: {DB_PATH}")
print(f"Wrote:    {CLN + 'analysis.csv'}")
