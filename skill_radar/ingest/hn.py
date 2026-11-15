"""Download every Hacker News "Ask HN: Who is hiring?" thread (monthly since 2011).

Source: public Algolia HN API (no key). One request per thread returns the whole comment tree;
raw responses are cached as gzip so reruns never download twice. Raw data is kept untouched;
all cleaning happens later in ``process/hn_postings.py`` (Bronze -> Silver).
"""

import argparse
import gzip
import json
import re
import time
from pathlib import Path

import requests

API = "https://hn.algolia.com/api/v1"
HEADERS = {"User-Agent": "academic-research-client/0.1"}
TITLE = re.compile(r"^ask hn: who is hiring\?", re.IGNORECASE)
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "hn"


def get(session, url, params=None, tries=5):
    for attempt in range(tries):
        try:
            response = session.get(url, params=params, headers=HEADERS, timeout=60)
            if response.status_code == 200:
                return response.json()
            if response.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
        except requests.RequestException:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"giving up on {url}")


def list_threads(session):
    """All "Who is hiring?" story ids with their creation time, oldest first."""
    stories, page = [], 0
    while True:
        data = get(session, f"{API}/search_by_date",
                   {"tags": "story,author_whoishiring", "hitsPerPage": 1000, "page": page})
        stories += data["hits"]
        page += 1
        if page >= data["nbPages"] or not data["hits"]:
            break
    threads = [{"id": int(s["objectID"]), "title": s["title"], "created_at_i": s["created_at_i"]}
               for s in stories if TITLE.match(s.get("title") or "")]
    return sorted(threads, key=lambda t: t["created_at_i"])


def run(raw_dir=RAW_DIR, pause=0.4):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    threads = list_threads(session)
    (raw_dir / "threads.json").write_text(json.dumps(threads, indent=1), encoding="utf-8")
    fetched = 0
    for i, thread in enumerate(threads, 1):
        target = raw_dir / f"{thread['id']}.json.gz"
        if target.exists():
            continue
        tree = get(session, f"{API}/items/{thread['id']}")
        with gzip.open(target, "wt", encoding="utf-8") as handle:
            json.dump(tree, handle)
        fetched += 1
        print(f"[{i}/{len(threads)}] {thread['title']}: {len(tree.get('children', []))} top-level comments", flush=True)
        time.sleep(pause)
    print(f"threads: {len(threads)}, downloaded now: {fetched}, cached: {len(threads) - fetched}")
    return threads


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    run()
