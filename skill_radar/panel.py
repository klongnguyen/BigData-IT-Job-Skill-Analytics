"""Quarterly panel: job-posting demand (target) joined with community-activity signals (leading indicators).

All series are quarterly. A quarter is *complete* for demand when at least MIN_MONTHS of its three
monthly "Who is hiring?" threads exist, and the newest month is excluded while it is still filling.

Signals (each optional per skill; missing stays NaN, never filled):
  se_share  Stack Overflow questions with the skill's tag / all questions that quarter
  npm_dl    npm downloads in the quarter (JavaScript-ecosystem skills)
  gh_share  share of GitHub pull requests in the skill's language (sampled hours)
"""

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd

from skill_radar import db
from skill_radar.taxonomy import SKILLS

MIN_MONTHS = 2
MODEL_START = "2015Q3"          # first quarter after HN's missing 2015 months; gap-free from here
CATEGORIES = sorted({s["category"] for s in SKILLS})


def last_complete_month(today=None):
    today = today or dt.date.today()
    return (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")


def hn_demand(conn, today=None):
    postings = db.read_sql(conn, "SELECT comment_id, month, quarter FROM postings")
    postings = postings[postings.month <= last_complete_month(today)]
    skills = db.read_sql(conn, "SELECT comment_id, skill FROM posting_skills")
    totals = postings.groupby("quarter").agg(hn_total=("comment_id", "size"), n_months=("month", "nunique"))
    merged = skills.merge(postings[["comment_id", "quarter"]], on="comment_id")
    counts = merged.groupby(["quarter", "skill"]).size().rename("hn_posts")
    grid = pd.MultiIndex.from_product([totals.index, [s["id"] for s in SKILLS]], names=["period", "skill"])
    frame = (counts.rename_axis(["period", "skill"]).reindex(grid, fill_value=0).reset_index()
             .merge(totals.rename_axis("period").reset_index(), on="period"))
    frame = frame[frame.n_months >= MIN_MONTHS]
    frame["hn_share"] = frame.hn_posts / frame.hn_total
    return frame


def _empty(column):
    return pd.DataFrame(columns=["period", "skill", column])


def se_signal(conn):
    if not db.has_table(conn, "signal_se_quarter"):
        return _empty("se_share")
    raw = db.read_sql(conn, "SELECT tag, quarter, questions FROM signal_se_quarter")
    total = raw[raw.tag == "__all__"].set_index("quarter").questions
    tags = raw[raw.tag != "__all__"].copy()
    tags["se_share"] = tags.questions / tags.quarter.map(total)
    rows = []
    for s in SKILLS:
        if s.get("se_tag"):
            sub = tags[tags.tag == s["se_tag"]]
            rows.append(pd.DataFrame({"period": sub.quarter, "skill": s["id"], "se_share": sub.se_share}))
    return pd.concat(rows, ignore_index=True) if rows else _empty("se_share")


def npm_quarterly(conn):
    """Complete-quarter npm downloads per package: columns package, period, npm_dl."""
    if not db.has_table(conn, "signal_npm_month"):
        return pd.DataFrame(columns=["package", "period", "npm_dl"])
    raw = db.read_sql(conn, "SELECT package, month, downloads FROM signal_npm_month")
    raw["period"] = pd.PeriodIndex(raw.month, freq="M").asfreq("Q").astype(str)
    months = raw.groupby(["package", "period"]).month.nunique()
    quarterly = raw.groupby(["package", "period"]).downloads.sum().to_frame("npm_dl")
    return quarterly[months.reindex(quarterly.index) == 3].reset_index()      # complete quarters only


def npm_signal(conn):
    quarterly = npm_quarterly(conn)
    rows = []
    for s in SKILLS:
        if s.get("npm"):
            sub = quarterly[quarterly.package == s["npm"]]
            rows.append(pd.DataFrame({"period": sub.period, "skill": s["id"], "npm_dl": sub.npm_dl}))
    return pd.concat(rows, ignore_index=True) if rows else _empty("npm_dl")


def gh_signal(conn):
    """GitHub Archive has not been collected; the signal stays empty and is reported as unavailable."""
    if not db.has_table(conn, "signal_gh_month"):
        return _empty("gh_share")
    raw = db.read_sql(conn, "SELECT month, language, prs, total_prs FROM signal_gh_month")
    raw["period"] = pd.PeriodIndex(raw.month, freq="M").asfreq("Q").astype(str)
    quarterly = raw.groupby(["period", "language"]).agg(prs=("prs", "sum"), total=("total_prs", "sum")).reset_index()
    quarterly["gh_share"] = quarterly.prs / quarterly.total
    rows = []
    for s in SKILLS:
        if s.get("gh"):
            sub = quarterly[quarterly.language == s["gh"]]
            rows.append(pd.DataFrame({"period": sub.period, "skill": s["id"], "gh_share": sub.gh_share}))
    return pd.concat(rows, ignore_index=True) if rows else _empty("gh_share")


def build_long(conn, today=None):
    frame = hn_demand(conn, today)
    for signal in (se_signal(conn), npm_signal(conn), gh_signal(conn)):
        frame = frame.merge(signal, on=["period", "skill"], how="left")
    frame["category"] = frame.skill.map({s["id"]: s["category"] for s in SKILLS})
    return frame.sort_values(["skill", "period"]).reset_index(drop=True)


@dataclass
class Panel:
    periods: list
    skills: list                  # skill ids (rows)
    category: np.ndarray          # int code per skill
    share: np.ndarray             # S x T   HN demand share (target)
    total: np.ndarray             # T       postings per quarter
    posts: np.ndarray             # S x T   postings mentioning the skill
    signals: dict                 # name -> S x T (NaN where unavailable)


def to_panel(long, start=MODEL_START):
    long = long[long.period >= start]
    periods = sorted(long.period.unique())
    expected = pd.period_range(periods[0], periods[-1], freq="Q").astype(str).tolist()
    if periods != expected:
        raise ValueError(f"gaps in quarterly demand: have {len(periods)} of {len(expected)} quarters")
    skills = [s["id"] for s in SKILLS]

    def wide(column):
        table = long.pivot(index="skill", columns="period", values=column)
        return table.reindex(index=skills, columns=periods).to_numpy(dtype=float)

    cat_code = {c: i for i, c in enumerate(CATEGORIES)}
    category = np.array([cat_code[s["category"]] for s in SKILLS])
    total = long.drop_duplicates("period").set_index("period").hn_total.reindex(periods).to_numpy(dtype=float)
    signals = {name: wide(name) for name in ("se_share", "npm_dl", "gh_share") if name in long}
    return Panel(periods, skills, category, wide("hn_share"), total, wide("hn_posts"), signals)
