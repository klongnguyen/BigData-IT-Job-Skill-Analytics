"""Bronze -> Silver -> Gold for the Hacker News "Who is hiring?" series.

Bronze  raw comment trees (data/raw/hn/*.json.gz), never modified.
Silver  one row per job posting (top-level comment) + one row per (posting, skill).
Gold    demand share per skill and period:  postings mentioning the skill / all postings.

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

from skill_radar.taxonomy import SKILLS, clean_html, extract_skills

DATA = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA / "raw" / "hn"
OUT_DIR = DATA / "processed"
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


def build_postings(raw_dir=RAW_DIR):
    raw_dir = Path(raw_dir)
    threads = json.loads((raw_dir / "threads.json").read_text(encoding="utf-8"))
    rows, dropped = [], {"deleted_or_empty": 0, "too_short": 0, "duplicate_id": 0}
    seen = set()
    for thread in threads:
        path = raw_dir / f"{thread['id']}.json.gz"
        if not path.exists():
            continue
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            tree = json.load(handle)
        month = thread_month(thread)
        for child in tree.get("children", []):
            text = clean_html(child.get("text"))
            if not text:
                dropped["deleted_or_empty"] += 1
            elif len(text) < MIN_CHARS:
                dropped["too_short"] += 1
            elif child["id"] in seen:
                dropped["duplicate_id"] += 1
            else:
                seen.add(child["id"])
                rows.append({"thread_id": thread["id"], "month": month, "quarter": quarter_of(month),
                             "comment_id": child["id"], "author": child.get("author"),
                             "created_at": child.get("created_at"), "text": text})
    return pd.DataFrame(rows), dropped, len(threads)


def attach_skills(postings):
    pairs = []
    for comment_id, text in zip(postings.comment_id, postings.text):
        pairs += [(comment_id, sid) for sid in extract_skills(text)]
    return pd.DataFrame(pairs, columns=["comment_id", "skill"])


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


def run(raw_dir=RAW_DIR, out_dir=OUT_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    postings, dropped, n_threads = build_postings(raw_dir)
    post_skills = attach_skills(postings)
    postings.to_parquet(out_dir / "hn_postings.parquet", index=False)
    post_skills.to_parquet(out_dir / "hn_posting_skills.parquet", index=False)
    monthly = demand_panel(postings, post_skills, "month")
    quarterly = demand_panel(postings, post_skills, "quarter")
    monthly.to_parquet(out_dir / "hn_demand_month.parquet", index=False)
    quarterly.to_parquet(out_dir / "hn_demand_quarter.parquet", index=False)
    report = {"threads": n_threads, "postings": int(len(postings)), "months": int(postings.month.nunique()),
              "quarters": int(postings.quarter.nunique()), "dropped": dropped,
              "postings_with_any_skill": int(post_skills.comment_id.nunique()),
              "first_month": postings.month.min(), "last_month": postings.month.max()}
    (out_dir / "hn_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
