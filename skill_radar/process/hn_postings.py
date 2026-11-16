"""Bronze -> Silver for the Hacker News "Who is hiring?" series, stored in SQLite (data/warehouse.db).

Bronze  bronze_thread, bronze_comment   raw top-level comments exactly as downloaded (HTML), never modified.
Silver  postings                        one clean row per job posting
        posting_skills                  one row per (posting, skill)
        posting_features                one row per posting: work mode, pay, seniority, location, employer
        demand_month, demand_quarter    postings mentioning a skill / all postings
        etl_report                      row counts and every drop, so nothing disappears silently

Rules that matter for the statistics:
* only top-level comments are postings (replies are discussion);
* the period is the month printed in the thread title (threads are created a day or two early);
* a month with two threads is merged and de-duplicated by comment id;
* postings shorter than MIN_CHARS are dropped; every drop is counted and reported.
"""

import calendar
import gzip
import json
import re
from pathlib import Path

import pandas as pd

from skill_radar import db
from skill_radar.process.features import extract_features
from skill_radar.taxonomy import SKILLS, clean_html, extract_skills

RAW_DIR = db.DATA / "raw" / "hn"
MIN_CHARS = 50
MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
TITLE_MONTH = re.compile(r"\(([A-Za-z]+)\s+(\d{4})\)")


def thread_month(thread):
    match = TITLE_MONTH.search(thread["title"])
    if match and match.group(1).lower() in MONTHS:
        return f"{int(match.group(2)):04d}-{MONTHS[match.group(1).lower()]:02d}"
    ts = pd.Timestamp(thread["created_at_i"], unit="s", tz="UTC")
    return f"{ts.year:04d}-{ts.month:02d}"


def quarter_of(month):
    year, m = month.split("-")
    return f"{year}Q{(int(m) - 1) // 3 + 1}"


# ------------------------------------------------------------------- bronze
def read_bronze(raw_dir=RAW_DIR):
    """Load downloaded threads into (threads, comments) frames. Comments keep their raw HTML (None if deleted)."""
    raw_dir = Path(raw_dir)
    threads = json.loads((raw_dir / "threads.json").read_text(encoding="utf-8"))
    thread_rows, comment_rows = [], []
    for thread in threads:
        path = raw_dir / f"{thread['id']}.json.gz"
        if not path.exists():
            continue
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            tree = json.load(handle)
        thread_rows.append({"thread_id": thread["id"], "title": thread["title"], "month": thread_month(thread),
                            "created_at_i": thread.get("created_at_i")})
        for child in tree.get("children", []):
            comment_rows.append({"thread_id": thread["id"], "comment_id": child["id"], "author": child.get("author"),
                                 "created_at": child.get("created_at"), "html": child.get("text")})
    return pd.DataFrame(thread_rows), pd.DataFrame(comment_rows)


# ------------------------------------------------------------------- silver
def build_postings(threads, comments):
    """Clean bronze comments into postings; returns (postings, dropped counts)."""
    month_of = threads.set_index("thread_id").month
    dropped = {"deleted_or_empty": 0, "too_short": 0, "duplicate_id": 0}
    seen, rows = set(), []
    for c in comments.itertuples(index=False):
        text = clean_html(c.html if isinstance(c.html, str) else None)    # deleted comments arrive as None/NaN
        if not text:
            dropped["deleted_or_empty"] += 1
        elif len(text) < MIN_CHARS:
            dropped["too_short"] += 1
        elif c.comment_id in seen:
            dropped["duplicate_id"] += 1
        else:
            seen.add(c.comment_id)
            month = month_of[c.thread_id]
            rows.append({"thread_id": c.thread_id, "month": month, "quarter": quarter_of(month), "comment_id": c.comment_id,
                         "author": c.author, "created_at": c.created_at, "text": text})
    return pd.DataFrame(rows), dropped


def attach_skills(postings):
    pairs = []
    for comment_id, text in zip(postings.comment_id, postings.text):
        pairs += [(comment_id, sid) for sid in extract_skills(text)]
    return pd.DataFrame(pairs, columns=["comment_id", "skill"])


def attach_features(postings):
    rows = [extract_features(text) for text in postings.text]
    frame = pd.DataFrame(rows)
    frame.insert(0, "comment_id", postings.comment_id.to_numpy())
    return frame


def demand_panel(postings, post_skills, period):
    totals = postings.groupby(period).size().rename("total_posts")
    n_months = postings.groupby(period).month.nunique().rename("n_months")
    merged = post_skills.merge(postings[["comment_id", period]], on="comment_id")
    counts = merged.groupby([period, "skill"]).size().rename("posts_with_skill").reset_index()
    grid = pd.MultiIndex.from_product([totals.index, [s["id"] for s in SKILLS]], names=[period, "skill"])
    panel = (counts.set_index([period, "skill"]).reindex(grid, fill_value=0).reset_index()
             .merge(totals.reset_index(), on=period).merge(n_months.reset_index(), on=period))
    panel["share"] = panel.posts_with_skill / panel.total_posts
    return panel.rename(columns={period: "period"})


def run(raw_dir=RAW_DIR, warehouse=db.WAREHOUSE):
    threads, comments = read_bronze(raw_dir)
    postings, dropped = build_postings(threads, comments)
    post_skills = attach_skills(postings)
    features = attach_features(postings)
    report = {"threads": len(threads), "postings": int(len(postings)), "months": int(postings.month.nunique()),
              "quarters": int(postings.quarter.nunique()), "bronze_comments": int(len(comments)),
              **{f"dropped_{k}": v for k, v in dropped.items()},
              "postings_with_any_skill": int(post_skills.comment_id.nunique()),
              "first_month": postings.month.min(), "last_month": postings.month.max()}
    with db.session(warehouse) as conn:
        db.write_table(conn, "bronze_thread", threads, indexes=["thread_id"])
        db.write_table(conn, "bronze_comment", comments, indexes=["comment_id", "thread_id"])
        db.write_table(conn, "postings", postings, indexes=["comment_id", "month", "quarter", "author"])
        db.write_table(conn, "posting_skills", post_skills, indexes=["comment_id", "skill"])
        db.write_table(conn, "posting_features", features, indexes=["comment_id"])
        db.write_table(conn, "demand_month", demand_panel(postings, post_skills, "month"), indexes=[("period", "skill")])
        db.write_table(conn, "demand_quarter", demand_panel(postings, post_skills, "quarter"), indexes=[("period", "skill")])
        db.kv_write(conn, "etl_report", report)
    return report


def rebuild_features(warehouse=db.WAREHOUSE):
    """Recompute posting_features from the stored postings (use after editing the rules in features.py)."""
    with db.session(warehouse) as conn:
        postings = db.read_sql(conn, "SELECT comment_id, text FROM postings ORDER BY comment_id")
        features = attach_features(postings)
        return db.write_table(conn, "posting_features", features, indexes=["comment_id"])


if __name__ == "__main__":
    import sys
    print(rebuild_features() if "--features-only" in sys.argv else json.dumps(run(), indent=2))
