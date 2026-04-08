"""
Scrape chapter-level metadata from each annual edition of the World Happiness
Report. For every year between 2020 and 2026 we visit
https://www.worldhappiness.report/ed/{year}/, pull the list of chapter URLs,
visit each chapter and grab the title, the list of authors and their
affiliations, the reading time and the DOI, and finally drop the lot into
data/raw/whr_chapters.csv.

The basic recipe is borrowed from scrape_xkcd_bs.py in Damian's BEE2041 repo,
with `requests` swapped in for `urllib` so I can set a polite User-Agent.
Pages are cached on disk so the build is reproducible offline after one
successful run.
"""
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

# --- helpers --------------------------------------------------------------
def fetch(url, cache_name, n_tries=4):
    """Download url, cache the HTML on disk, return parsed soup.

    If the cache file already exists we use it (that is what lets the rest
    of the build run offline). Otherwise we hit the web with up to n_tries
    attempts and exponential back-off, in line with the polite-scraper
    guidance from the webscraping lecture.
    """
    cache_path = CACHE + cache_name
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        return BeautifulSoup(html, "html.parser")

    for attempt in range(n_tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            html = r.text
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html)
            time.sleep(SLEEP)
            return BeautifulSoup(html, "html.parser")
        except requests.RequestException as e:
            if attempt == n_tries - 1:
                print(f"  ERROR fetching {url} after {n_tries} attempts: {e}")
                return None
            wait = 2 ** (attempt + 1)
            print(f"   attempt {attempt+1} for {url} failed ({e}); sleeping {wait}s")
            time.sleep(wait)


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


# --- crawl each year ------------------------------------------------------
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

# --- dump to a tidy CSV ---------------------------------------------------
out_path = DAT + "whr_chapters.csv"
fields   = ["year", "title", "authors", "n_authors", "affiliations",
            "reading_time_min", "doi", "url"]

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in all_records:
        writer.writerow({k: r.get(k, "") for k in fields})

print(f"Wrote: {out_path}")
