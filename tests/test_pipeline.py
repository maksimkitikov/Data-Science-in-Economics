"""A handful of sanity checks on the analysis sample. Run: pytest tests/."""
import json
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


def test_regressions_have_six_specs():
    rs = pd.read_csv(TAB / "regression_summary.csv")
    assert set(rs["model"].unique()) == {"m1", "m2", "m3", "m4", "m5", "m6"}


def test_ate_is_a_number():
    with open(TAB / "cate_headline.json") as f:
        h = json.load(f)
    assert isinstance(h["ate"], (int, float))
    assert -2 < h["ate"] < 2
