"""Tests for posting features, the SQLite layer, result storage, the ecosystem and the Skill Navigator."""

import numpy as np
import pandas as pd
import pytest

from skill_radar import db, ecosystem, insights, navigator, store
from skill_radar.process import features as F
from skill_radar.process import hn_postings as P


# ------------------------------------------------------------- features
@pytest.mark.parametrize("text, expected", [
    ("Acme | Remote (US) | Python", True),
    ("We are fully REMOTE", True),
    ("Onsite only, no remote", False),
    ("Remote: No", False),
    ("Remote work is not possible", False),
    ("Come to the office", False),
])
def test_remote_flag(text, expected):
    assert F.extract_features(text)["is_remote"] is expected


@pytest.mark.parametrize("text, expected", [
    ("$120k-$160k plus equity", 140.0),
    ("Salary: $95K", 95.0),
    ("$120,000 - $160,000", 140.0),
    ("$100-150k", 125.0),
    ("raised $20,000,000 in funding", None),        # funding, not pay
    ("We raised $5M", None),
    ("$10k stipend", None),                         # below the plausible annual range
    ("$900k", None),                                # above the plausible annual range
    ("no figures here", None),
])
def test_salary_usd_k(text, expected):
    assert F.salary_usd_k(text) == expected


def test_salary_flag_includes_other_currencies_but_usd_value_does_not():
    f = F.extract_features("London | £60k-£80k")
    assert f["has_salary"] is True and f["salary_usd_k"] is None


def test_seniority_and_contract_flags():
    f = F.extract_features("Senior Backend Engineer, contract, intern welcome")
    assert f["is_senior"] and f["is_contract"] and f["is_intern"] and not f["is_junior"]
    assert not F.extract_features("We build smart contract tooling")["is_contract"]
    assert not F.extract_features("Our staff is friendly")["is_senior"]


def test_location_prefers_the_earliest_city_in_the_header():
    assert F.locate("Foo | San Francisco or New York") == ("San Francisco", "NA")
    assert F.locate("Foo | NYC | Remote") == ("New York", "NA")
    assert F.locate("Foo | Europe | Python") == (None, "EU")
    assert F.locate("Foo | Remote | Python") == (None, "UNKNOWN")
    assert F.locate("x" * 300 + " London") == (None, "UNKNOWN")        # only the header counts


def test_company_is_the_first_field_of_pipe_postings_only():
    assert F.company_of("Acme (YC S12) | London | Python") == "Acme"
    assert F.company_of("Senior Software Engineer | London | Python") is None   # job title, not a company
    assert F.company_of("We are hiring Python developers in London") is None     # not pipe-formatted


# -------------------------------------------------------------- database
def test_write_read_roundtrip_and_indexes(tmp_path):
    frame = pd.DataFrame({"a": [1, 2], "flag": [True, False], "name": ["x", None]})
    with db.session(tmp_path / "t.db") as conn:
        assert db.write_table(conn, "t", frame, indexes=["a"]) == 2
        db.kv_write(conn, "info", {"k": 1.5, "s": "text"})
    with db.session(tmp_path / "t.db", readonly=True) as conn:
        back = db.read_sql(conn, "SELECT * FROM t ORDER BY a")
        assert back.flag.tolist() == [1, 0] and back.name.isna().tolist() == [False, True]
        assert db.kv_read(conn, "info") == {"k": "1.5", "s": "text"}
        assert db.has_table(conn, "t") and not db.has_table(conn, "missing")
        with pytest.raises(Exception):
            conn.execute("DROP TABLE t")                                 # read-only connection must refuse writes


def test_readonly_requires_an_existing_database(tmp_path):
    with pytest.raises(FileNotFoundError):
        db.connect(tmp_path / "nope.db", readonly=True)


def test_bronze_to_silver_in_a_temporary_warehouse(tmp_path):
    threads = pd.DataFrame({"thread_id": [1], "title": ["Ask HN: Who is hiring? (January 2024)"], "month": ["2024-01"], "created_at_i": [0]})
    comments = pd.DataFrame({"thread_id": [1, 1, 1, 1], "comment_id": [10, 11, 12, 13], "author": list("abcd"),
                             "created_at": [""] * 4,
                             "html": ["Acme | Remote | Python and Django developers needed for our team of engineers",
                                      None, "too short", "Beta | NYC | ONSITE | Go and Rust; $150k-$180k + equity for senior engineers"]})
    postings, dropped = P.build_postings(threads, comments)
    assert dropped == {"deleted_or_empty": 1, "too_short": 1, "duplicate_id": 0} and len(postings) == 2
    skills = P.attach_skills(postings)
    assert set(skills[skills.comment_id == 10].skill) == {"python", "django"}
    feats = P.attach_features(postings).set_index("comment_id")
    assert feats.loc[10, "is_remote"] and feats.loc[13, "is_onsite"] and feats.loc[13, "salary_usd_k"] == 165.0


# --------------------------------------------------------------- results
def mini_manifest():
    models = {"naive_last": {"mae_pp": 1.0, "mae_pp_by_horizon": {"1": 0.9, "4": 1.1}},
              "gbm": {"mae_pp": 0.9, "mae_pp_by_horizon": {"1": 0.8, "4": 1.0},
                      "vs_best_baseline": {"baseline": "naive_last", "diff_pp": -0.1, "ci95": [-0.2, 0.0], "skills": 5}},
              "gbm+signals": {"mae_pp": 0.89, "mae_pp_by_horizon": {"1": 0.8, "4": 1.0},
                              "vs_best_baseline": {"baseline": "naive_last", "diff_pp": -0.11, "ci95": [-0.2, 0.0], "skills": 5},
                              "signal_effect": {"vs": "gbm", "diff_pp": -0.01, "ci95": [-0.02, 0.0], "skills": 5}}}
    return {"schema_version": 2, "created_at_utc": "2026-01-01T00:00:00+00:00",
            "evidence": {"source": "HN", "quarters": ["2015Q3", "2026Q3"], "n_quarters": 45, "postings_total": 10, "skills_total": 3,
                         "skills_eligible": 2, "signals_available": {"npm_dl": 2, "se_share": 0}},
            "backtest": {"protocol": {"horizons": [1, 4], "selection_end": "2022Q4", "holdout_targets": "2023Q1..2026Q3", "min_share": 0.01, "band_pp": 1.0},
                         "selection": {"alpha_ses": 0.8, "alpha_scores_mae_pp": {"0.2": 1.0}, "phi_damped": 0.25, "phi_scores_mae_pp": {"0.25": 0.7}},
                         "eligible_skills": 2, "with_signal_skills": 1,
                         "all_eligible": {"best_baseline": "naive_last", "models": models, "cells": 4, "skills": 5},
                         "signal_covered": None,
                         "labels": {"1.0": {"always_stable": {"macro_f1": 0.26, "n": 9, "support": {"Fading": 1, "Stable": 7, "Rising": 1}},
                                            "gbm": {"macro_f1": 0.47, "n": 9}}}},
            "production": {"model": "gbm", "selection_mae_pp": {"gbm": 0.7}, "direction_model": "gbm", "selection_direction_f1": {"gbm": 0.6},
                           "direction_validation": {"macro_f1_model": 0.47, "macro_f1_always_stable": 0.26, "gain": 0.2, "gain_ci95": [0.1, 0.3], "validated": True},
                           "interval_quantiles": {"1": 0.05, "4": 0.07}, "interval_coverage_80_holdout": 0.8},
            "lead_lag": {"npm_dl": {"signal": "npm_dl", "skills": ["react", "vue"],
                                    "lags": {"0": {"mean_corr": 0.1, "ci95": [-0.1, 0.3], "placebo_p": 0.4, "share_positive": 0.5, "skills": 2,
                                                   "per_skill": {"react": 0.5, "vue": None}}}},
                         "gh_share": {"signal": "gh_share", "skills": [], "note": "too few skills with this signal"}}}


def test_results_roundtrip_through_tables(tmp_path):
    with db.session(tmp_path / "g.db") as conn:
        store.save_results(conn, mini_manifest())
    with db.session(tmp_path / "g.db", readonly=True) as conn:
        r = store.load_results(conn)
    info = r["info"]
    assert info["rate_model"] == "gbm" and info["dv_validated"] == 1 and info["dv_gain_lo"] == 0.1 and info["n_quarters"] == 45
    ms = r["model_score"].set_index("model")
    assert ms.loc["gbm", "ci_hi"] == 0.0 and ms.loc["gbm+signals", "signal_diff_pp"] == -0.01 and pd.isna(ms.loc["naive_last", "diff_pp"])
    assert set(r["model_horizon_error"].h) == {1, 4}
    labels = r["label_score"].set_index("model")
    assert labels.loc["always_stable", "support_stable"] == 7
    assert r["leadlag_signal"].set_index("signal").loc["gh_share", "has_lags"] == 0
    assert r["leadlag"].shape[0] == 1 and r["leadlag_skill"]["corr"].isna().sum() == 1


# ------------------------------------------------------------ ecosystem
def block_matrix(n_per_block=8, blocks=5, n_postings=1500, seed=0):
    """Postings that draw their skills from one block of skills: the clusters are the blocks."""
    rng = np.random.default_rng(seed)
    n_skills = n_per_block * blocks
    matrix = np.zeros((n_postings, n_skills), dtype=bool)
    for i in range(n_postings):
        block = rng.integers(blocks)
        picks = rng.choice(n_per_block, size=4, replace=False) + block * n_per_block
        matrix[i, picks] = True
    return matrix


def test_clusters_recover_planted_blocks_and_respect_minimum_size():
    matrix = block_matrix()
    skills = [f"s{i}" for i in range(matrix.shape[1])]
    frame, info = ecosystem.build_clusters(matrix, skills, {s: s for s in skills})
    assert info["k"] == 5 and info["silhouette"] > 0.3
    block_of = frame.set_index("skill").cluster
    for b in range(5):
        assert block_of[[f"s{i}" for i in range(b * 8, b * 8 + 8)]].nunique() == 1
    assert frame.groupby("cluster").size().min() >= ecosystem.MIN_CLUSTER
    again, _ = ecosystem.build_clusters(matrix, skills, {s: s for s in skills})
    assert np.allclose(frame.x, again.x)                                  # layout is reproducible


def test_pair_table_lift_matches_hand_calculation():
    matrix = np.array([[1, 1, 0]] * 4 + [[1, 0, 0]] * 4 + [[0, 0, 1]] * 2, dtype=bool)
    pairs = ecosystem.pair_table(ecosystem.cooccurrence(matrix), ["a", "b", "c"], len(matrix), min_pair=2)
    row = pairs.iloc[0]
    assert (row.a, row.b, row.n) == ("a", "b", 4)
    assert row.lift == pytest.approx((4 / 10) / ((8 / 10) * (4 / 10)))


# ------------------------------------------------------------- navigator
def toy_matrix():
    return np.array([[1, 0, 0], [1, 1, 0], [1, 1, 0], [0, 1, 1], [0, 0, 1], [0, 0, 1]], dtype=bool)


def test_fits_uses_the_share_of_a_postings_skills():
    m = toy_matrix()
    assert navigator.fits(m, [0], 1.0).tolist() == [True, False, False, False, False, False]
    assert navigator.fits(m, [0], 0.5).tolist() == [True, True, True, False, False, False]
    assert navigator.coverage(m, [0, 1], 1.0) == pytest.approx(3 / 6)


def test_gains_and_greedy_plan_reach_full_coverage():
    m = toy_matrix()
    gains = navigator.gains(m, [0], 1.0)
    assert gains.tolist() == [0, 2, 2]                    # skill b completes two postings, skill c completes two
    path = navigator.plan(m, [0], 1.0, steps=5)
    assert path[-1]["coverage"] == pytest.approx(1.0)
    assert all(a["coverage"] < b["coverage"] for a, b in zip(path, path[1:]))
    assert navigator.plan(m, [0, 1, 2], 1.0) == []         # nothing left to learn


def test_dense_matrix_drops_postings_without_skills():
    posting = pd.DataFrame({"pid": [1, 2, 3]})
    ps = pd.DataFrame({"pid": [1, 1, 3], "skill": ["a", "b", "a"]})
    matrix, keep = navigator.dense_matrix(posting, ps, ["a", "b"])
    assert matrix.tolist() == [[True, True], [True, False]] and keep.tolist() == [0, 2]


# -------------------------------------------------------------- insights
def test_annual_share_and_ranks():
    sy = pd.DataFrame({"year": [2019, 2019, 2020, 2020], "skill": ["a", "b", "a", "b"], "posts": [30, 10, 10, 30], "total": [100, 100, 100, 100]})
    annual = insights.annual_share(sy)
    assert annual.loc[2019, "a"] == 0.3
    ranks = insights.rank_table(annual)
    assert ranks.loc[2019, "a"] == 1 and ranks.loc[2020, "a"] == 2


def test_window_share_pools_counts_not_ratios():
    hist = pd.DataFrame({"skill": ["a", "a"], "period": ["2024Q1", "2024Q2"], "posts": [10, 90], "total": [100, 900]})
    assert insights.window_share(hist, ["2024Q1", "2024Q2"])["a"] == pytest.approx(0.1)
    assert insights.recent_periods(hist, 1) == ["2024Q2"] and insights.recent_periods(hist, 1, 1) == ["2024Q1"]


# --------------------------------------------------------------- drivers
from skill_radar import drivers  # noqa: E402


def test_hinge_break_finds_a_planted_bend_and_ignores_a_straight_line():
    t = np.arange(40, dtype=float)
    bent = np.where(t < 25, 0.05, 0.05 + 0.01 * (t - 25))
    found = drivers.hinge_break(bent)
    assert found["significant"] and abs(found["knot"] - 25) <= 2
    assert found["slope_before_pp_year"] == pytest.approx(0, abs=0.2) and found["slope_after_pp_year"] == pytest.approx(4.0, abs=0.5)
    straight = drivers.hinge_break(0.05 + 0.002 * t)
    assert not straight["significant"]


def make_postings():
    """Remote postings mention the skill 50% of the time, others 10%; the remote share grows from 20% to 60%."""
    rows, mentions = [], []
    pid = 0
    for quarter, remote_share in (("2024Q1", 0.2), ("2025Q1", 0.6)):
        for i in range(100):
            remote = i < remote_share * 100
            rows.append({"pid": pid, "quarter": quarter, "is_remote": int(remote), "author_id": pid % 40})
            if (remote and i % 2 == 0) or (not remote and i % 10 == 0):
                mentions.append({"pid": pid, "skill": "x"})
            pid += 1
    return pd.DataFrame(rows), pd.DataFrame(mentions)


def test_shift_share_parts_add_up_and_attribute_the_change_to_the_mix():
    posting, ps = make_postings()
    r = drivers.shift_share(posting, ps, "x", ["2024Q1"], ["2025Q1"], "is_remote")
    assert r["share_a"] == pytest.approx(0.2 * 0.5 + 0.8 * 0.1) and r["share_b"] == pytest.approx(0.6 * 0.5 + 0.4 * 0.1)
    assert r["within"] + r["mix"] == pytest.approx(r["share_b"] - r["share_a"])
    assert r["within"] == pytest.approx(0, abs=1e-9) and r["mix"] > 0.15          # per-type rates are constant: only the mix moved


def test_breadth_counts_distinct_authors_and_concentration():
    posting, ps = make_postings()
    b = drivers.breadth(posting, ps, "x", ["2025Q1"])
    assert b["posts"] == len(set(ps.pid) & set(posting.pid[posting.quarter == "2025Q1"]))
    assert 1 <= b["authors"] <= 40 and 0 < b["top5_share"] <= 1
    assert drivers.breadth(posting, ps, "x", ["2030Q1"])["posts"] == 0


def test_comovement_separates_followers_from_opposites():
    periods = pd.period_range("2015Q3", periods=30, freq="Q").astype(str)
    rng = np.random.default_rng(0)
    base = np.cumsum(rng.normal(0, 0.01, 30)) + 0.2
    frame = []
    for name, series in (("a", base), ("same", base * 0.9 + 0.01), ("opp", 0.5 - base)):
        frame.append(pd.DataFrame({"skill": name, "period": periods, "share": series}))
    hist = pd.concat(frame)
    together, against = drivers.comovement(hist, "a", top=1)
    assert together.skill.iloc[0] == "same" and against.skill.iloc[0] == "opp"


def test_model_inputs_match_a_hand_calculation():
    s = np.array([0.10, 0.10, 0.10, 0.10, 0.10, 0.11, 0.12, 0.13])
    out = drivers.model_inputs(s)
    assert out["base_pp"] == pytest.approx(11.5) and out["last_vs_base_pp"][0] == pytest.approx(1.5)
    assert out["slope_pp_per_quarter"] > 0


def test_nearby_events_uses_a_two_quarter_window():
    events = pd.DataFrame({"period": ["2020Q1", "2022Q4"], "label": ["COVID-19", "ChatGPT"]})
    assert drivers.nearby_events("2022Q2", events) == ["ChatGPT"] and drivers.nearby_events("2018Q1", events) == []


# ------------------------------------------------------------------- ui
@pytest.mark.parametrize("module", ["overview", "trends", "profile", "why", "ecosystem", "navigator", "forecast"])
def test_every_dashboard_page_imports(module):
    """A syntax or import error in a page would stop the whole dashboard from starting."""
    import importlib
    importlib.import_module(f"skill_radar.ui.pages.{module}")


# ------------------------------------------------------------- category forecast
from skill_radar import category_forecast as CF  # noqa: E402


def _toy_gold(tmp_path):
    """45 quarters, 60 postings each. Category 'a' appears in 50% of postings, 'b' in 20% (the share of b falls every quarter)."""
    periods = pd.period_range("2015Q3", periods=45, freq="Q").astype(str)
    postings, pairs, pid = [], [], 0
    for q, period in enumerate(periods):
        for i in range(60):
            postings.append({"pid": pid, "quarter": period})
            if i < 30:
                pairs.append({"pid": pid, "skill": "x1" if i % 2 else "x2"})      # two skills of category a: counted once per posting
            if i >= 60 - max(2, 12 - q // 4):
                pairs.append({"pid": pid, "skill": "y1"})
            pid += 1
    conn = db.connect(tmp_path / "toy_gold.db")
    db.write_table(conn, "posting", pd.DataFrame(postings))
    db.write_table(conn, "posting_skill", pd.DataFrame(pairs))
    db.write_table(conn, "skills", pd.DataFrame({"skill": ["x1", "x2", "y1", "z1"], "category": ["a", "a", "b", "other"]}))
    db.write_table(conn, "radar_history", pd.DataFrame({"skill": "x1", "period": periods, "total": 60}))
    return conn


def test_category_series_counts_a_posting_once_per_category(tmp_path):
    conn = _toy_gold(tmp_path)
    share, posts, total = CF.category_series(conn)
    assert list(share.columns) == ["a", "b"]                   # 'other' is dropped
    assert share["a"].eq(0.5).all()                            # 30 of 60, although x1 and x2 are both in category a
    assert share["b"].is_monotonic_decreasing
    conn.close()


def test_category_forecast_run_shapes_and_no_future_leak(tmp_path):
    conn = _toy_gold(tmp_path)
    out = CF.run(conn)
    assert set(out["summary"].category) == {"a", "b"}
    assert len(out["path"]) == 2 * len(CF.HORIZONS)
    assert (out["path"].lo <= out["path"].forecast).all() and (out["path"].forecast <= out["path"].hi).all()
    assert out["info"]["rate_model"] in {"naive_last", "mean4", "ses", "damped"}
    assert out["info"]["selection_end"] == "2022Q4"
    assert out["summary"].set_index("category").loc["a", "direction"] == "Stable"     # flat series must not be called Rising/Fading
    again = CF.run(conn)
    assert again["info"] == out["info"]                         # reproducible
    conn.close()
