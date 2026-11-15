"""Quarterly Stack Overflow question counts per tag (a leading indicator of developer interest).

The public API returns an exact ``total`` for any (tag, date range). Without an API key the quota
is 300 requests/day, so the fetch is resumable: results are appended to a CSV and the next run
continues where the last stopped. With a free key (env ``SE_API_KEY``) the quota is 10,000/day.
The key is read from the environment and is never written to disk.
"""

import csv
import datetime as dt
import os
import sys
import time
from pathlib import Path

import requests

from skill_radar.taxonomy import SKILLS

API = "https://api.stackexchange.com/2.3/questions"
HEADERS = {"User-Agent": "academic-research-client/0.1"}
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "stackexchange" / "tag_counts_quarter.csv"
FIRST_QUARTER = (2011, 1)
ALL_QUESTIONS = "__all__"


def quarters(today=None):
    today = today or dt.date.today()
    y, q = FIRST_QUARTER
    while (y, q) < (today.year, (today.month - 1) // 3 + 1):     # complete quarters only
        yield y, q
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)


def bounds(y, q):
    start = dt.datetime(y, 3 * q - 2, 1, tzinfo=dt.timezone.utc)
    end = dt.datetime(y + (q == 4), 1 if q == 4 else 3 * q + 1, 1, tzinfo=dt.timezone.utc)
    return int(start.timestamp()), int(end.timestamp())


def load_done(path):
    if not Path(path).exists():
        return set()
    with open(path, newline="", encoding="utf-8") as handle:
        return {(r["tag"], r["quarter"]) for r in csv.DictReader(handle)}


def run(out=OUT, budget=None):
    key = os.environ.get("SE_API_KEY")
    budget = budget if budget is not None else (9000 if key else 280)
    ordered = []
    for s in SKILLS:                       # taxonomy order, de-duplicated
        if s.get("se_tag") and s["se_tag"] not in ordered:
            ordered.append(s["se_tag"])
    tags = [ALL_QUESTIONS] + ordered
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(out)
    # tag-major: finish one tag's whole history before starting the next, so each is usable at once
    todo = [(t, y, q) for t in tags for (y, q) in quarters() if (t, f"{y}Q{q}") not in done]
    print(f"keyed={bool(key)} budget={budget} remaining={len(todo)} done={len(done)}", flush=True)
    new_file = not out.exists()
    session = requests.Session()
    calls = 0
    with open(out, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["tag", "quarter", "questions"])
        for tag, y, q in todo:
            if calls >= budget:
                break
            frm, to = bounds(y, q)
            params = {"fromdate": frm, "todate": to - 1, "site": "stackoverflow", "filter": "total"}
            if tag != ALL_QUESTIONS:
                params["tagged"] = tag
            if key:
                params["key"] = key
            response = session.get(API, params=params, headers=HEADERS, timeout=60)
            calls += 1
            data = response.json()
            if "error_id" in data:
                print("API stopped:", data.get("error_message"), file=sys.stderr)
                break
            writer.writerow([tag, f"{y}Q{q}", data["total"]])
            handle.flush()
            time.sleep(max(data.get("backoff", 0), 0.15))
    print(f"calls this run: {calls}")


if __name__ == "__main__":
    run()
