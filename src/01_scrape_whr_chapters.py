# 01_scrape_whr_chapters 0.01    BEE2041-empirical-project    yyyy-mm-dd:2026-04-25
#---|----1----|----2----|----3----|----4----|----5----|----6----|----7----|----8
#
# Syntax is: python src/01_scrape_whr_chapters.py
#
# This file scrapes chapter-level metadata from the World Happiness Report (WHR)
# annual editions hosted at https://www.worldhappiness.report/ed/{year}/. For
# each year we (i) download the landing page, (ii) extract the list of chapter
# URLs, (iii) visit each chapter and pull title, authors, affiliations, reading
# time and DOI, and (iv) write a tidy CSV to data/raw/whr_chapters.csv.
#
# The scraping pattern follows scrape_xkcd_bs.py from BEE2041-2026, replacing
# urllib with the requests library (covered in Workflow, Modelling &
# Webscraping.pdf, slide 60) so we can set a polite User-Agent. We also obey the
# polite-scraper guidance from the same lecture: a descriptive UA, a short
# time.sleep() between requests, and try/except blocks around every network
# call. Raw HTML is cached to data/raw/html_cache/ so the rest of the pipeline
# is fully reproducible offline once the cache exists.

#-------------------------------------------------------------------------------
# (0) Imports and directory locations
#-------------------------------------------------------------------------------
import os
import re
import time
import csv

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
DAT  = ROOT + "data/raw/"
CACHE = DAT + "html_cache/"
os.makedirs(CACHE, exist_ok=True)

YEARS    = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
BASE_URL = "https://www.worldhappiness.report"
HEADERS  = {"User-Agent": "BEE2041-student-project/1.0 (educational; contact via GitHub)"}
SLEEP    = 1.0   # polite delay between requests in seconds

#-------------------------------------------------------------------------------
# (1) Helper functions
#-------------------------------------------------------------------------------
def fetch(url, cache_name):
    """Download url, cache HTML to disk and return parsed BeautifulSoup.

    If the cache file already exists we use it (this is what makes the build
    reproducible after a single successful scrape). Otherwise we go to the web
    and write a copy.
    """
    cache_path = CACHE + cache_name
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            html = r.text
        except requests.RequestException as e:
            print(f"  ERROR fetching {url}: {e}")
            return None
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(html)
        time.sleep(SLEEP)
    return BeautifulSoup(html, "html.parser")


def chapter_links_for_year(year):
    """Return the chapter-page paths listed on the year's edition landing page."""
    soup = fetch(f"{BASE_URL}/ed/{year}/", f"ed_{year}.html")
    if soup is None:
        return []
    paths = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0]   # strip in-page anchors
        if href.startswith(f"/ed/{year}/") and href != f"/ed/{year}/":
            paths.add(href)
    return sorted(paths)


def parse_chapter(url, cache_name):
    """Pull title, authors, affiliations, reading time and DOI from a chapter."""
    soup = fetch(url, cache_name)
    if soup is None:
        return None

    record = {"url": url}

    # Title: the first <h1> on the page
    h1 = soup.find("h1")
    record["title"] = h1.get_text(strip=True) if h1 else ""

    # Authors live in <li class="author">Name<span class="author-title">Aff</span></li>.
    # We grab every such <li> after the Authors header and split name from
    # affiliation using the inner span.
    authors, affs = [], []
    for li in soup.select("li.author"):
        span = li.find("span", class_="author-title")
        affil = span.get_text(" ", strip=True) if span else ""
        if span:
            span.extract()
        name = li.get_text(" ", strip=True)
        if name:
            authors.append(name)
            affs.append(affil)
    record["authors"]      = "; ".join(authors)
    record["n_authors"]    = len(authors)
    record["affiliations"] = " | ".join(affs)

    # Reading time appears as e.g. "67 min. read"
    text = soup.get_text(" ", strip=True)
    m = re.search(r"(\d+)\s*min\.\s*read", text)
    record["reading_time_min"] = int(m.group(1)) if m else None

    # DOI: appears either in a link or as plain text "DOI: http://doi.org/..."
    m = re.search(r"10\.\d{4,9}/[^\s\"']+", text)
    record["doi"] = m.group(0).rstrip(".") if m else ""

    return record


#-------------------------------------------------------------------------------
# (2) Crawl each year, extract metadata for every chapter
#-------------------------------------------------------------------------------
all_records = []
for year in YEARS:
    print(f"[{year}] fetching landing page...")
    paths = chapter_links_for_year(year)
    print(f"[{year}] found {len(paths)} chapter links")
    for path in paths:
        slug = path.strip("/").replace("/", "_")
        rec  = parse_chapter(BASE_URL + path, f"{slug}.html")
        if rec is None:
            continue
        rec["year"] = year
        all_records.append(rec)

print(f"\nTotal chapters scraped: {len(all_records)}")

#-------------------------------------------------------------------------------
# (3) Write to a tidy CSV
#-------------------------------------------------------------------------------
out_path = DAT + "whr_chapters.csv"
fields   = ["year", "title", "authors", "n_authors", "affiliations",
            "reading_time_min", "doi", "url"]

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in all_records:
        writer.writerow({k: r.get(k, "") for k in fields})

print(f"Wrote: {out_path}")
