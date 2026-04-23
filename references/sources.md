# References & reading materials

This file collects every external resource that influenced the project, with a
short note on *where in the code* it shows up. The aim is full transparency:
the marker should be able to follow any line of code back to the lecture
slide or paper that motivated it.

## Course-internal materials (in `course-materials/`)

| File | What I took from it |
|---|---|
| `empiricalProject_2026.pdf` | Project brief — assignment requirements, marking rubric, length and output guidance |
| `Workflow, Modelling & Webscraping.pdf` | Project structure (slide 19), Makefile pattern (slide 13), `requests` + `BeautifulSoup` recipe (60-64), causal-forest motivation (40-47) |
| `Python for Data Management.pdf` | `pd.merge(... validate, indicator)` pattern (51-56), `melt`/`pivot` (35-39), groupby (60-62) |
| `Relational Database Management Systems.pdf` | SQLite schema design, JOIN syntax, ERD reasoning |
| `SQL Teaching Exercises- Students, Modules & Lecturers.pdf` | Reference SQL syntax for the JOIN in `04_build_database.py` |
| `git & GitHub.pdf` | Branch / commit conventions, `.gitignore` discipline (slide 39) |
| `The Linux Command Line.pdf` | `make`-style pipelines, command-line philosophy |
| `Problem Set Solutions: Data Wrangling in Python.pdf` | `wbgapi` usage in Q2 — copied directly into `03_download_worldbank.py` |

## External materials (referenced from PDFs and project brief)

* Damian Clarke, BEE2041-2026 GitHub.
  <https://github.com/damiancclarke/BEE2041-2026>
  * `webscrape/scrape_xkcd_bs.py` — file-header style, parser pattern
  * `replicationCausalForest/source/immigrantEffects.py` — `CausalForestDML`
    recipe, `pystout` table layout, plot styling
  * `replicationCausalForest/Makefile` — pipeline pattern
  * `replicationCausalForest/README.md` — README structure
  * `python/developmentMortality.py` — merge diagnostics with
    `validate="1:1", indicator=True`

* Aeturrell (2023). *Coding for Economists*.
  <https://aeturrell.github.io/coding-for-economists/code-best-practice.html>
  — code-style recommendations.

* Gentzkow, M. & Shapiro, J. (2014).
  *Code and Data for the Social Sciences: A Practitioner's Guide.*
  <https://web.stanford.edu/~gentzkow/research/CodeAndData.pdf>
  — directory structure, automation philosophy.

* VanderPlas, J. *Python Data Science Handbook.*
  <https://jakevdp.github.io/PythonDataScienceHandbook/>
  — pandas idioms.

* Shotts, W. *The Linux Command Line.* <http://linuxcommand.org/tlcl.php>
  — `make`, pipes, scripting.

* BeginnersBook (2015–2019). E-R model, relational algebra, DBMS theory.
  * <https://beginnersbook.com/2015/04/e-r-model-in-dbms/>
  * <https://beginnersbook.com/2019/02/dbms-relational-algebra/>
  — ER reasoning behind `04_build_database.py`.

* Ngu, C. K. (NTU). *A Quick-Start Tutorial on Relational Database Design.*
  <https://www3.ntu.edu.sg/home/ehchua/programming/sql/Relational_Database_Design.html>

* Real Python. *A Practical Introduction to Webscraping with Python.*
  <https://realpython.com/python-web-scraping-practical-introduction/>

* Oxford Research Encyclopedia chapter on webscraping.
  <https://academic.oup.com/edited-volume/61801/chapter-abstract/546448054>

* Davis, J. & Heller, S. (2017). *Using Causal Forests to Predict Treatment
  Heterogeneity: An Application to Summer Jobs.* AEA P&P.
  — recommended in the project brief; framing for the heterogeneity story.

## Causal-machine-learning theory

* Wager, S. & Athey, S. (2018). Estimation and Inference of Heterogeneous
  Treatment Effects using Random Forests. *JASA* 113(523): 1228-1242.
* Athey, S., Tibshirani, J. & Wager, S. (2019). Generalized Random Forests.
  *Annals of Statistics* 47(2): 1148-1178.
* Chernozhukov, V., et al. (2018). Double/Debiased Machine Learning for
  Treatment and Structural Parameters. *Econometrics Journal* 21(1): C1-C68.
* EconML documentation. <https://econml.azurewebsites.net>

## Data sources

* World Happiness Report. <https://worldhappiness.report>
* Helliwell, J. F., Layard, R., Sachs, J. D., De Neve, J.-E., Aknin, L., &
  Wang, S. (eds.) (2024). *World Happiness Report 2024.* University of Oxford
  Wellbeing Research Centre.
* World Bank. *World Development Indicators.* Queried via the
  [`wbgapi`](https://pypi.org/project/wbgapi/) Python client.
