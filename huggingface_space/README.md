---
title: Beyond GDP
emoji: 🌍
colorFrom: blue
colorTo: yellow
sdk: static
pinned: false
license: mit
short_description: What really drives national happiness?
---

# Beyond GDP - what really drives national happiness?

A data-driven web essay built for the BEE2041 *Data Science in Economics*
empirical project, University of Exeter, April 2026.

The site combines:

- Web-scraped chapter metadata for every World Happiness Report edition
  from 2020 through 2026 (`requests` + `BeautifulSoup`)
- The official WHR ranking spreadsheets for 2020-2024
- World Bank cross-country indicators queried through `wbgapi`

It integrates the three sources in a small SQLite database, fits both an OLS
sequence and a causal forest (`econml.dml.CausalForestDML`), and asks: once
we control for everything else, when does income still buy happiness?

All charts are interactive (Plotly), and the page is fully responsive.

## Source code

<https://github.com/maksimkitikov/Data-Science-in-Economics>

## License

MIT.
