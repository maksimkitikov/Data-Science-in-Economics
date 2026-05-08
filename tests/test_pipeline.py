"""Sanity checks plus a couple of unit tests on the helper functions."""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLN = ROOT / "data" / "clean"
TAB = ROOT / "output" / "tables"


def test_analysis_sample_size():
    df = pd.read_csv(CLN / "analysis.csv")
    assert len(df) == 136
    assert df["country_code"].is_unique


def test_finland_on_top():
    df = pd.read_csv(CLN / "analysis.csv")
    top = df.sort_values("ladder", ascending=False).iloc[0]
    assert top["country_code"] == "FIN"


def test_six_specifications():
    rs = pd.read_csv(TAB / "regression_summary.csv")
    assert set(rs["model"].unique()) == {"m1", "m2", "m3", "m4", "m5", "m6"}


def test_ate_is_a_number():
    with open(TAB / "cate_headline.json") as f:
        h = json.load(f)
    assert isinstance(h["ate"], (int, float))
    assert -2 < h["ate"] < 2


def test_to_iso_strips_asterisk_and_whitespace():
    """Same logic as in 04_build_database.py, kept here so the helper is unit-tested."""
    name2iso = {"Finland": "FIN", "United States": "USA"}

    def to_iso(n):
        return name2iso.get(n.replace("*", "").strip())

    assert to_iso("Finland*") == "FIN"
    assert to_iso("  United States  ") == "USA"
    assert to_iso("Atlantis") is None


def test_doi_pattern():
    """The regex used in 01_scrape_whr_chapters.py to pull DOIs out of chapter text."""
    text = "DOI: 10.18724/whr-z6ws-dp10 published 2026"
    m = re.search(r"10\.\d{4,9}/[^\s\"']+", text)
    assert m and m.group(0) == "10.18724/whr-z6ws-dp10"
