# Codebook - `data/clean/analysis.csv`

The analysis cross-section contains 136 countries x 16 columns. Below is what
each column means and where it comes from. The integration query that produces
this table lives in `src/04_build_database.py`.

## Identifiers

| Column | Type | Source | Notes |
|---|---|---|---|
| `country_code` | text | World Bank `economy` field | ISO-3 country code, primary key |
| `country_name` | text | WHR Figure 2.1 | spelling matches the WHR convention; mapped to ISO-3 in `src/04_build_database.py` |
| `year` | int | WHR edition year | 2023 throughout in this cross-section |

## WHR Ladder + components (six explanatory variables shipped with the WHR ranking)

These six variables come from the WHR's own `Figure_2.1.xls` panel (in
`data/raw/whr_panel.csv`). They are the WHR team's preferred operationalisation
of the right-hand side of their headline regression.

| Column | Type | Range | Source |
|---|---|---|---|
| `ladder` | float | 0-10 | National-average response to the Cantril Ladder question; the Report's headline outcome. |
| `log_gdp` | float | ~7 to 12 | Logged GDP per capita as bundled by the WHR (constant 2017 international US$). |
| `social_support` | float | 0-1 | Share of respondents who say they have someone to count on in times of trouble. |
| `life_exp_healthy` | float | 50-80 | Healthy-life expectancy at birth, WHO. |
| `freedom` | float | 0-1 | Share of respondents satisfied with their freedom to make life choices. |
| `generosity` | float | -0.4 to +0.7 | Residual from regressing "donated to charity last month" on GDP per capita. |
| `corruption` | float | 0-1 | Average of "is corruption widespread in government / business" responses. |

## World Bank cross-section (queried via `wbgapi`)

These are the supplementary covariates I pulled to (a) cross-check the WHR's
bundled log-GDP and (b) give the causal forest moderators that are *not*
already in the WHR file (internet, urban share, FDI, education).

| Column | Type | WB indicator code | Vintage |
|---|---|---|---|
| `gdp_pc_ppp` | float | `NY.GDP.PCAP.PP.KD` | 2022 |
| `life_exp` | float | `SP.DYN.LE00.IN` | 2022 |
| `internet_pct` | float | `IT.NET.USER.ZS` | 2022 |
| `urban_pct` | float | `SP.URB.TOTL.IN.ZS` | 2022 |
| `education_spend_pct` | float | `SE.XPD.TOTL.GD.ZS` | 2022 |
| `fdi_pct` | float | `BX.KLT.DINV.WD.GD.ZS` | 2022 |

## Treatment definition (causal forest)

`src/06_causal_forest.py` constructs:

* **Treatment `D`** - `1` if `gdp_pc_ppp` is above the sample median, `0` otherwise.
* **Outcome `Y`** - the WHR `ladder` score.
* **Conditioning set `X`** - six potential moderators: `life_exp_healthy`,
  `social_support`, `freedom`, `corruption`, `internet_pct`, `urban_pct`.

The CATE recovered by the forest is therefore: *"by how many Ladder points
does a country at above-median income exceed the world average, holding the
six moderators fixed?"*

## Sample notes

* Sample is WHR-2023 edition x WB-2022 covariates, intersected on ISO-3 codes:
  **136 countries** (full WHR ranking is 137; we lose Taiwan because it has
  no WB record, and we lose any country with missing WB data).
* The OLS specifications drop two more countries due to missingness in
  `corruption` (n = 134).
* The causal forest drops to **n = 130** because internet and urban shares
  are missing for a few small economies.
