"""Tests for the Skill Radar pipeline: taxonomy, HN processing, panel, models, backtest protocol."""

import numpy as np
import pandas as pd
import pytest

from skill_radar import backtest as B
from skill_radar import models as M
from skill_radar.panel import Panel, to_panel
from skill_radar.process import hn_postings as P
from skill_radar.taxonomy import BY_ID, SKILLS, clean_html, extract_skills


def skills(text):
    return extract_skills(clean_html(text))


# --------------------------------------------------------------- taxonomy
@pytest.mark.parametrize("text, expected", [
    ("We use Swift.", {"swift"}),
    ("Built with Go.", {"go"}),
    ("Go to market, go-to-market strategy", set()),
    ("Node.js and jQuery.js", {"node", "jquery"}),                 # ".js" must not mean javascript
    ("Java. Not javascript", {"java", "javascript"}),
    ("PostgreSQL and MySQL, not NoSQL", {"postgresql", "mysql"}),  # "sql" must not fire inside names
    ("React Native app; React.js too", {"reactnative", "react"}),
    ("C++ and C# developers", {"cpp", "csharp"}),
    ("Spark SQL, pyspark", {"spark", "sql"}),
    ("our RAG pipeline.", {"rag"}),
    ("Kubernetes (k8s) on AWS", {"kubernetes", "aws"}),
    ("We are a great team", set()),
])
def test_extraction_rules(text, expected):
    assert set(skills(text)) == expected


def test_html_is_stripped_before_entities_are_decoded():
    raw = 'Acme | Remote<p>Python &#x2F; Django &amp; Postgres &lt;3 <a href="x">link</a>'
    cleaned = clean_html(raw)
    assert "<" not in cleaned.replace("<3", "") and "Python / Django & Postgres <3" in cleaned


def test_taxonomy_is_well_formed():
    assert len({s["id"] for s in SKILLS}) == len(SKILLS)
    assert all(s["aliases"] and s["category"] for s in SKILLS)
    assert BY_ID["python"]["se_tag"] == "python" and BY_ID["react"]["npm"] == "react"


# ------------------------------------------------------------ processing
def test_thread_month_uses_title_not_creation_date():
    thread = {"title": "Ask HN: Who is hiring? (April 2011)", "created_at_i": 1301529600}   # created 2011-03-31
    assert P.thread_month(thread) == "2011-04"
    assert P.thread_month({"title": "Ask HN: Who is hiring?", "created_at_i": 1301529600}) == "2011-03"
    assert P.quarter_of("2024-11") == "2024Q4" and P.quarter_of("2024-01") == "2024Q1"


def test_demand_panel_shares_use_all_postings_as_denominator():
    postings = pd.DataFrame({"comment_id": [1, 2, 3, 4], "month": ["2024-01"] * 4, "quarter": ["2024Q1"] * 4})
    post_skills = pd.DataFrame({"comment_id": [1, 2, 3], "skill": ["python", "python", "go"]})
    panel = P.demand_panel(postings, post_skills, "quarter").set_index("skill")
    assert panel.loc["python", "posts_with_skill"] == 2 and panel.loc["python", "share"] == 0.5
    assert panel.loc["go", "share"] == 0.25 and panel.loc["rust", "share"] == 0
    assert (panel.total_posts == 4).all()


# ------------------------------------------------------------------ panel
def synthetic_panel(n_quarters=36, n_skills=12, seed=0, signal=True):
    rng = np.random.default_rng(seed)
    periods = pd.period_range("2015Q3", periods=n_quarters, freq="Q").astype(str).tolist()
    trend = rng.normal(0, 0.002, (n_skills, 1))
    share = np.clip(0.05 + np.cumsum(rng.normal(0, 0.004, (n_skills, n_quarters)), axis=1) + trend * np.arange(n_quarters), 0.01, 0.9)
    category = np.arange(n_skills) % 3
    signals = {"se_share": share * 0.1 * (1 + rng.normal(0, 0.05, share.shape))} if signal else {}
    return Panel(periods, [f"s{i}" for i in range(n_skills)], category, share, np.full(n_quarters, 1500.0),
                 share * 1500, signals)


def test_to_panel_rejects_gaps():
    periods = ["2016Q1", "2016Q2", "2016Q4"]
    long = pd.DataFrame([{"period": p, "skill": s["id"], "hn_share": 0.1, "hn_posts": 10, "hn_total": 100}
                         for p in periods for s in SKILLS])
    with pytest.raises(ValueError, match="gaps"):
        to_panel(long, start="2016Q1")


# ----------------------------------------------------------------- models
@pytest.mark.parametrize("name", ["naive_last", "mean4", "ses", "damped", "ridge", "gbm", "ridge+signals", "gbm+signals"])
def test_no_model_sees_quarters_after_the_origin(name):
    panel = synthetic_panel()
    fns = {"naive_last": M.naive_last, "mean4": M.mean4, "ses": M.make_ses(0.4), "damped": M.make_damped(0.5),
           "ridge": M.make_pooled("ridge", False), "gbm": M.make_pooled("gbm", False),
           "ridge+signals": M.make_pooled("ridge", True), "gbm+signals": M.make_pooled("gbm", True)}
    T = 24
    before = fns[name](M.view_of(panel, T), [1, 2, 3, 4])
    panel.share[:, T:] = 0.999                                  # corrupt every future quarter
    panel.total[T:] = 1.0
    for arr in panel.signals.values():
        arr[:, T:] = 123.0
    after = fns[name](M.view_of(panel, T), [1, 2, 3, 4])
    assert np.allclose(before, after, equal_nan=True)


def test_pooled_models_return_nan_when_history_is_too_short():
    panel = synthetic_panel()
    assert np.isnan(M.make_pooled("ridge", False)(M.view_of(panel, 6), [1])).all()


def test_damped_matches_a_known_line():
    t = np.arange(8)
    share = np.vstack([0.10 + 0.01 * t, 0.30 - 0.005 * t])
    view = M.View(share, np.full(8, 1500.0), np.zeros(2, dtype=int), {})
    got = M.make_damped(1.0)(view, [1, 2])                     # phi=1 -> plain line
    assert np.allclose(got, [[0.18, 0.19], [0.26, 0.255]])


# -------------------------------------------------------------- protocol
def test_cells_never_let_selection_touch_the_holdout():
    panel = synthetic_panel(n_quarters=45)
    panel.periods = pd.period_range("2015Q3", periods=45, freq="Q").astype(str).tolist()
    selection, holdout, sel_end = B.cells(panel)
    assert panel.periods[sel_end] == "2022Q4"
    assert all(T + max(hs) - 1 <= sel_end for T, hs in selection)
    assert min(T for T, _ in holdout) == sel_end + 1
    assert all(T + max(hs) - 1 <= len(panel.periods) - 1 for T, hs in holdout)


def test_eligibility_ignores_the_holdout():
    panel = synthetic_panel(n_quarters=45)
    panel.periods = pd.period_range("2015Q3", periods=45, freq="Q").astype(str).tolist()
    _, _, sel_end = B.cells(panel)
    before = B.eligible_mask(panel, sel_end).copy()
    panel.share[:, sel_end + 1:] = 0.0
    assert (B.eligible_mask(panel, sel_end) == before).all()


def test_label_boundaries():
    assert B.label_of(np.array([1.01, 1.0, 0.0, -1.0, -1.01]), 1.0).tolist() == ["Rising", "Stable", "Stable", "Stable", "Fading"]


def test_backtest_runs_end_to_end_and_is_deterministic():
    panel = synthetic_panel(n_quarters=45, n_skills=14, seed=1)
    panel.periods = pd.period_range("2015Q3", periods=45, freq="Q").astype(str).tolist()
    a, _ = B.run(panel)
    b, _ = B.run(panel)
    assert a == b
    assert a["all_eligible"]["models"]["ridge+signals"]["signal_effect"]["vs"] == "ridge"
    assert set(a["labels"]) == {"0.5", "1.0", "2.0"}
