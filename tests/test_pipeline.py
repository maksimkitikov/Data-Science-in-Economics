"""Sanity checks for the build pipeline.

We don't have a synthetic ground truth, so these are boundary checks:
they catch the sort of regression that would silently invalidate the
blog (Finland not on top, the OLS R^2 dropping, a figure missing, etc.).

Run with:  pytest tests/   (or  make test).
"""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
CLN = ROOT / "data" / "clean"
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"


# ---- analysis sample ------------------------------------------------------

@pytest.fixture(scope="module")
def df():
    return pd.read_csv(CLN / "analysis.csv")


def test_analysis_sample_size(df):
    # The sample is WHR 2023 intersected with World Bank 2022, intersected on ISO-3.
    # If the merge breaks (a name fails to map, the WB indicator changes,
    # etc.) the count will move; 130-140 is a safe band.
    assert 130 <= len(df) <= 140, f"unexpected sample size: {len(df)}"


def test_iso3_codes_unique(df):
    # one row per country
    assert df["country_code"].is_unique
    assert df["country_code"].str.len().eq(3).all()


def test_ladder_in_range(df):
    # Cantril Ladder is bounded in [0, 10] by construction.
    assert df["ladder"].between(0, 10).all()


def test_finland_on_top(df):
    # Finland has been #1 on the WHR Ladder since 2018; if it is not on top
    # something has shifted in the input data and the blog narrative
    # ("Finland's nearly six-point lead") no longer holds.
    top = df.sort_values("ladder", ascending=False).iloc[0]
    assert top["country_code"] == "FIN"


def test_no_negative_gdp(df):
    # NaNs are allowed (a couple of small economies are missing in the WB
    # cross-section); negatives are not.
    gdp = df["gdp_pc_ppp"].dropna()
    assert (gdp > 0).all()


# ---- regression outputs ---------------------------------------------------

def test_regression_summary_present():
    rs = pd.read_csv(TAB / "regression_summary.csv")
    # Six specifications, mostly multi-row.
    assert set(rs["model"].unique()) == {"m1", "m2", "m3", "m4", "m5", "m6"}
    # Headline finding: m4 should achieve R^2 above 0.8.
    m4_r2 = rs.loc[rs["model"] == "m4", "r2"].iloc[0]
    assert m4_r2 > 0.80


def test_log_gdp_coefficient_falls():
    # The blog claim "log-GDP coefficient halves and halves again" should
    # hold: the m1 coefficient should be larger than m4's.
    rs = pd.read_csv(TAB / "regression_summary.csv")
    m1 = rs.loc[(rs["model"] == "m1") & (rs["term"] == "log_gdp"), "coef"].iloc[0]
    m4 = rs.loc[(rs["model"] == "m4") & (rs["term"] == "log_gdp"), "coef"].iloc[0]
    assert m1 > m4 > 0


# ---- causal-forest outputs ------------------------------------------------

def test_cate_headline_within_bounds():
    with open(TAB / "cate_headline.json") as f:
        h = json.load(f)
    # Once moderators are controlled for, the ATE should be near zero.
    assert abs(h["ate"]) < 0.3
    # CATEs are bounded by Ladder span / 2 in either direction.
    assert -2.0 < h["cate_min"] < h["cate_max"] < 2.0


def test_cate_summary_byte_stable():
    # The rounding step in 06_causal_forest.py makes the CSV byte-stable
    # across rebuilds. We cannot verify byte-stability inside a single
    # test run, but we can verify the file exists and has 130 rows.
    cate = pd.read_csv(TAB / "cate_summary.csv")
    assert len(cate) == 130
    assert set(cate.columns) == {"country_code", "country_name", "ladder",
                                 "gdp_pc_ppp", "cate", "ci_lo", "ci_hi"}


# ---- figures --------------------------------------------------------------

EXPECTED_FIGURES = [
    "top_bottom_10.png", "gdp_vs_ladder.png", "decomposition.png",
    "cate_hist.png", "cate_by_gdp.png", "cf_importance.png",
    "chapters_trend.png", "ladder_timeseries.png",
]


@pytest.mark.parametrize("name", EXPECTED_FIGURES)
def test_figure_exists(name):
    p = FIG / name
    assert p.exists() and p.stat().st_size > 5_000, f"missing or empty: {name}"
