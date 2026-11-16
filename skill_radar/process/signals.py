"""Load the downloaded community-activity signals (CSV download caches) into the warehouse database.

    raw/npm/monthly_downloads.csv            -> signal_npm_month(package, month, downloads)
    raw/stackexchange/tag_counts_quarter.csv -> signal_se_quarter(tag, quarter, questions)

A table is created only when its download exists; the panel treats a missing table as "no signal".
"""

import pandas as pd

from skill_radar import db

NPM_CSV = db.DATA / "raw" / "npm" / "monthly_downloads.csv"
SE_CSV = db.DATA / "raw" / "stackexchange" / "tag_counts_quarter.csv"


def run(warehouse=db.WAREHOUSE, npm_csv=NPM_CSV, se_csv=SE_CSV):
    loaded = {}
    with db.session(warehouse) as conn:
        if npm_csv.is_file():
            loaded["signal_npm_month"] = db.write_table(conn, "signal_npm_month", pd.read_csv(npm_csv), indexes=["package"])
        if se_csv.is_file():
            loaded["signal_se_quarter"] = db.write_table(conn, "signal_se_quarter", pd.read_csv(se_csv), indexes=["tag"])
    return loaded


if __name__ == "__main__":
    print(run())
