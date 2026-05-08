"""Scrape WHR chapter metadata (title, authors, reading time, DOI) for 2020-2026.
Output: data/raw/whr_chapters.csv."""
import csv
import os
import re
import time

import requests
from bs4 import BeautifulSoup

DAT = "data/raw/"
CACHE = DAT + "html_cache/"
os.makedirs(CACHE, exist_ok=True)

YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
BASE_URL = "https://www.worldhappiness.report"
HEADERS = {"User-Agent": "bee2041-empirical-project/1.0"}
# one second between live requests so we are not rude to the WHR origin
SLEEP = 1.0


def fetch(url, cache_name, n_tries=4):
    """Get a page once, then read the cached copy on every subsequent run."""
    cache_path = CACHE + cache_name
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")

    for attempt in range(n_tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            time.sleep(SLEEP)
            return BeautifulSoup(r.text, "html.parser")
        except requests.RequestException as e:
            if attempt == n_tries - 1:
                print(f"  failed {url}: {e}")
                return None
            time.sleep(3)


def chapter_links_for_year(year):
    """Find every chapter URL on a single edition's landing page."""
    soup = fetch(f"{BASE_URL}/ed/{year}/", f"ed_{year}.html")
    if soup is None:
        return []
    paths = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0]
        if href.startswith(f"/ed/{year}/") and href != f"/ed/{year}/":
            paths.add(href)
    return sorted(paths)


def parse_chapter(url, cache_name):
    """Pull title, authors, affiliations, reading time and DOI from one page."""
    soup = fetch(url, cache_name)
    if soup is None:
        return None

    record = {"url": url}

    h1 = soup.find("h1")
    record["title"] = h1.get_text(strip=True) if h1 else ""

    # Pop the affiliation span out before reading the name so they don't merge.
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
    record["authors"] = "; ".join(authors)
    record["n_authors"] = len(authors)
    record["affiliations"] = " | ".join(affs)

    text = soup.get_text(" ", strip=True)
    m = re.search(r"(\d+)\s*min\.\s*read", text)
    record["reading_time_min"] = int(m.group(1)) if m else None

    m = re.search(r"10\.\d{4,9}/[^\s\"']+", text)
    record["doi"] = m.group(0).rstrip(".") if m else ""

    return record


all_records = []
for year in YEARS:
    print(f"[{year}] landing page")
    paths = chapter_links_for_year(year)
    print(f"[{year}] {len(paths)} chapters")
    for path in paths:
        slug = path.strip("/").replace("/", "_")
        rec = parse_chapter(BASE_URL + path, f"{slug}.html")
        if rec is None:
            continue
        rec["year"] = year
        all_records.append(rec)

print(f"\nTotal chapters: {len(all_records)}")

out_path = DAT + "whr_chapters.csv"
fields = ["year", "title", "authors", "n_authors", "affiliations",
          "reading_time_min", "doi", "url"]

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in all_records:
        writer.writerow({k: r.get(k, "") for k in fields})

print(f"wrote {out_path}")
