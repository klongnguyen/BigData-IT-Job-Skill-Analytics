"""Monthly npm download counts for the JavaScript-ecosystem skills (a leading indicator).

The npm API allows at most ~18 months per range request, so the history is fetched in windows.
Only complete calendar months are kept; the first partial month and the current month are dropped.
"""

import datetime as dt
import time
from pathlib import Path

import pandas as pd
import requests

from skill_radar.taxonomy import SKILLS

API = "https://api.npmjs.org/downloads/range"
HEADERS = {"User-Agent": "academic-research-client/0.1"}
START = dt.date(2015, 1, 10)       # npm statistics begin here
WINDOW_DAYS = 500                  # < 18 months
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "npm" / "monthly_downloads.csv"


def windows(start, end):
    cursor = start
    while cursor <= end:
        stop = min(cursor + dt.timedelta(days=WINDOW_DAYS), end)
        yield cursor, stop
        cursor = stop + dt.timedelta(days=1)


def fetch_package(session, package, end):
    daily = []
    for a, b in windows(START, end):
        for attempt in range(8):
            try:
                r = session.get(f"{API}/{a}:{b}/{package}", headers=HEADERS, timeout=60)
                if r.status_code == 200:
                    daily += r.json().get("downloads", [])
                    break
            except requests.RequestException:
                pass
            time.sleep(min(2 ** attempt, 60))          # back off on 429 / transient errors
        else:
            raise RuntimeError(f"npm failed for {package} {a}:{b}")
        time.sleep(0.3)
    frame = pd.DataFrame(daily)
    if frame.empty:
        return frame
    frame["day"] = pd.to_datetime(frame["day"])
    frame["month"] = frame.day.dt.strftime("%Y-%m")
    days = frame.groupby("month").day.nunique()
    monthly = frame.groupby("month").downloads.sum()
    full = [m for m in monthly.index if days[m] >= pd.Period(m).days_in_month]   # complete months only
    return monthly.loc[full].rename("downloads").reset_index().assign(package=package)


def run(out=OUT):
    packages = sorted({s["npm"] for s in SKILLS if s.get("npm")})
    end = dt.date.today() - dt.timedelta(days=1)
    session = requests.Session()
    parts = Path(out).parent / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    frames = []
    for package in packages:
        part = parts / (package.replace("/", "__").replace("@", "") + ".csv")
        if part.exists():                              # resume: skip packages already fetched
            frames.append(pd.read_csv(part))
            continue
        frame = fetch_package(session, package, end)
        frame.to_csv(part, index=False)
        print(f"{package}: {len(frame)} months", flush=True)
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    return result


if __name__ == "__main__":
    run()
