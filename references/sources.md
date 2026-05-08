# References

This page collects every reference used in the project, sorted by where it
shows up.

## 1. Course materials (BEE2041 lectures)

| Reading | Used in / Cited from |
|---|---|
| Project brief 2026 | Length and output limits. |
| Workflow, Modelling & Webscraping (lecture) | Project layout, `make` pipeline, retry-with-back-off, ATE/CATE definitions, causal-forest motivation, web-scraping etiquette. |
| Python for Data Management (lecture) | `pd.read_excel`, `pd.merge` with `validate="1:1"` and `indicator=`, reshape and groupby idioms. |
| Relational Database Management Systems (lecture) | SQLite schema design, `PRAGMA foreign_keys=ON`, `CREATE TABLE ... PRIMARY KEY / FOREIGN KEY / NOT NULL`, B-tree indexes, `INNER JOIN`. |
| SQL Teaching Exercises (problem set) | Three-table relational schema with `PRIMARY KEY` / `FOREIGN KEY` constraints, `INNER JOIN` integration query in `04_build_database.py`. |
| git & GitHub (lecture) | Branch naming, "small, descriptive commit messages" convention. |
| The Linux Command Line (lecture) | `make` pipelines, the Unix-philosophy guidelines that shape the project layout. |
| Data Wrangling in Python (problem set) | The `wbgapi.data.DataFrame` recipe (`03_download_worldbank.py` follows it almost line-for-line). |

## 2. Damian Clarke's class GitHub

* `BEE2041-2026/webscrape/scrape_xkcd_bs.py` is the structural model for
  `01_scrape_whr_chapters.py`: a `requests` + `BeautifulSoup` loop over a
  numeric range of pages, with each page parsed for a target field.
  <https://github.com/damiancclarke/BEE2041-2026/tree/main/webscrape>

## 3. External reading and tutorials

* Aeturrell, *Coding for Economists* (2023), Section "Code Best Practice" and
  Section "Plots". <https://aeturrell.github.io/coding-for-economists/>
* Gentzkow, M. & Shapiro, J. (2014). *Code and Data for the Social Sciences:
  A Practitioner's Guide*.
  <https://web.stanford.edu/~gentzkow/research/CodeAndData.pdf>
* VanderPlas, J. *Python Data Science Handbook*, Chapter 4 (matplotlib).
  <https://jakevdp.github.io/PythonDataScienceHandbook/>
* Shotts, W. *The Linux Command Line.* <http://linuxcommand.org/tlcl.php>
* Real Python, *A Practical Introduction to Webscraping with Python.*
  <https://realpython.com/python-web-scraping-practical-introduction/>
* BeautifulSoup documentation.
  <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>
* `pystout` documentation - found while looking for a way to write the OLS
  table out as LaTeX in the same style as the lecture slides.
  <https://pypi.org/project/pystout/>
* Beginners Book, *E-R Model in DBMS.*
  <https://beginnersbook.com/2015/04/e-r-model-in-dbms/>
* Beginners Book, *Relational Algebra in DBMS.*
  <https://beginnersbook.com/2019/02/dbms-relational-algebra/>
* NTU, *A Quick-Start Tutorial on Relational Database Design.*
  <https://www3.ntu.edu.sg/home/ehchua/programming/sql/Relational_Database_Design.html>

## 4. Causal machine-learning references

* Wager, S. & Athey, S. (2018). Estimation and Inference of Heterogeneous
  Treatment Effects using Random Forests. *JASA* 113(523): 1228-1242.
* Athey, S., Tibshirani, J. & Wager, S. (2019). Generalized Random Forests.
  *Annals of Statistics* 47(2): 1148-1178.
* Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C.,
  Newey, W., Robins, J. (2018). Double/Debiased Machine Learning.
  *Econometrics Journal* 21(1): C1-C68.
* Davis, J. & Heller, S. (2017). Using Causal Forests to Predict Treatment
  Heterogeneity: An Application to Summer Jobs. *AEA Papers & Proceedings*.
  <https://www.aeaweb.org/articles?id=10.1257/aer.p20171000>
* EconML documentation. <https://econml.azurewebsites.net>

## 5. Data sources

* Helliwell, J. F., Layard, R., Sachs, J. D., De Neve, J.-E., Aknin, L.,
  & Wang, S. (eds.) (2020-2024). *World Happiness Report.* Sustainable
  Development Solutions Network. <https://worldhappiness.report>
* World Bank, *World Development Indicators*, queried via
  [`wbgapi`](https://pypi.org/project/wbgapi/).
* Cantril, H. (1965). *The Pattern of Human Concerns.* (Original source of
  the Ladder question.)
* Easterlin, R. A. (1974). Does Economic Growth Improve the Human Lot? Some
  Empirical Evidence. *Nations and Households in Economic Growth*.
* Stevenson, B. & Wolfers, J. (2008). Economic Growth and Subjective
  Well-Being: Reassessing the Easterlin Paradox. *Brookings Papers on
  Economic Activity*, Spring 2008.
* Layard, R., Mayraz, G. & Nickell, S. (2009). Does Relative Income Matter?
  Are the Critics Right? CEP Discussion Paper No. 918.
