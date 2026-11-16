"""Gold analytic tables for the dashboard, built from the warehouse (Silver) database.

Everything is computed for the same window as the forecasting panel (quarters 2015Q3 on, complete
quarters only), so every page of the dashboard describes the same postings.

    skills               taxonomy (label, category, signal mappings)
    posting              one row per posting, no text: month, flags, pay, city, region, number of skills
    posting_skill        (pid, skill) pairs -- the Skill Navigator reads this
    market_quarter       counts of postings with each flag per quarter, plus pay medians
    location_year       postings per (year, region, city)
    skill_year           postings mentioning each skill per year
    skill_pair_year      postings mentioning both skills of a pair per year
    skill_pair_window    pairs in the ecosystem window (last 12 quarters) with counts and lift
    skill_attr_year      per (year, skill): how many of its postings are remote / show pay / mention equity / senior ...
    skill_salary         advertised USD salary quartiles per skill ('all' years and 'recent' 8 quarters)
    employer             most active employers (first field of 'Company | Location | ...' postings)
    skill_cluster        technology stacks (see ecosystem.py)
    event                dated events annotated on charts
    signal_npm_month, signal_se_quarter   community-activity signals
    gold_fact            small run facts
"""

import numpy as np
import pandas as pd
from scipy import sparse

from skill_radar import db, ecosystem
from skill_radar.taxonomy import SKILLS

FLAGS = {"remote": "is_remote", "onsite": "is_onsite", "hybrid": "is_hybrid", "salary": "has_salary", "usd_salary": "salary_usd_k",
         "equity": "has_equity", "visa": "has_visa", "senior": "is_senior", "junior": "is_junior", "intern": "is_intern",
         "fulltime": "is_fulltime", "parttime": "is_parttime", "contract": "is_contract"}
RECENT_QUARTERS = 8          # window for "recent" salary and for the ecosystem map
ECOSYSTEM_QUARTERS = 12
EMPLOYER_MIN_POSTS = 8
EVENTS = [("2020Q1", "COVID-19"), ("2022Q4", "ChatGPT ra mắt"), ("2023Q1", "Sa thải hàng loạt ngành tech")]


def load_postings(wh, periods, last_month):
    sql = f"""
        SELECT p.comment_id AS pid, p.month, p.quarter, CAST(substr(p.month, 1, 4) AS INTEGER) AS year, p.author,
               f.is_remote, f.is_onsite, f.is_hybrid, f.has_salary, f.salary_usd_k, f.has_equity, f.has_visa,
               f.is_senior, f.is_junior, f.is_intern, f.is_fulltime, f.is_parttime, f.is_contract, f.city, f.region, f.company,
               (SELECT COUNT(*) FROM posting_skills s WHERE s.comment_id = p.comment_id) AS n_skills
        FROM postings p JOIN posting_features f USING (comment_id)
        WHERE p.quarter IN ({",".join("?" * len(periods))}) AND p.month <= ?"""
    frame = db.read_sql(wh, sql, [*periods, last_month])
    for col in [c for c in frame.columns if c.startswith(("is_", "has_"))]:
        frame[col] = frame[col].astype(bool)
    return frame


def market_quarter(posting):
    grouped = posting.groupby("quarter")
    out = pd.DataFrame({"n_posts": grouped.size()})
    for name, col in FLAGS.items():
        out[name] = grouped[col].apply(lambda s: int(s.notna().sum()) if name == "usd_salary" else int(s.sum()))
    out["salary_median_k"] = grouped.salary_usd_k.median()
    return out.rename_axis("period").reset_index()


def location_year(posting):
    sub = posting.assign(city=posting.city.fillna(""))
    return sub.groupby(["year", "region", "city"]).size().rename("posts").reset_index()


def skill_matrix(posting, posting_skill, skills):
    index = pd.Series(np.arange(len(posting)), index=posting.pid)
    col = {s: i for i, s in enumerate(skills)}
    rows = index.reindex(posting_skill.pid).to_numpy()
    cols = posting_skill.skill.map(col).to_numpy()
    return sparse.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(len(posting), len(skills)))


def skill_year_tables(posting, matrix, skills):
    """skill_year and skill_pair_year from per-year slices of the sparse posting x skill matrix."""
    years, pairs = [], []
    totals = posting.groupby("year").size()
    for year, idx in posting.groupby("year").indices.items():
        sub = matrix[idx]
        counts = np.asarray(sub.sum(axis=0)).ravel().astype(int)
        years.append(pd.DataFrame({"year": year, "skill": skills, "posts": counts, "total": int(totals[year])}))
        co = np.triu(np.asarray((sub.T @ sub).todense()), k=1)
        a, b = np.nonzero(co)
        pairs.append(pd.DataFrame({"year": year, "a": [skills[i] for i in a], "b": [skills[j] for j in b], "n": co[a, b].astype(int)}))
    return pd.concat(years, ignore_index=True), pd.concat(pairs, ignore_index=True)


def skill_attr_year(posting, posting_skill):
    merged = posting_skill.merge(posting[["pid", "year", "is_remote", "has_salary", "salary_usd_k", "has_equity", "is_senior",
                                          "is_junior", "has_visa", "is_hybrid"]], on="pid")
    merged["usd_salary"] = merged.salary_usd_k.notna()
    agg = merged.groupby(["year", "skill"]).agg(
        posts=("pid", "size"), remote=("is_remote", "sum"), hybrid=("is_hybrid", "sum"), salary=("has_salary", "sum"),
        usd_salary=("usd_salary", "sum"), equity=("has_equity", "sum"), senior=("is_senior", "sum"),
        junior=("is_junior", "sum"), visa=("has_visa", "sum"))
    return agg.astype(int).reset_index()


def skill_salary(posting, posting_skill, periods):
    paid = posting[posting.salary_usd_k.notna()][["pid", "quarter", "salary_usd_k"]]
    merged = posting_skill.merge(paid, on="pid")
    rows = []
    for scope, frame, all_frame in (("all", merged, paid), ("recent", merged[merged.quarter.isin(periods[-RECENT_QUARTERS:])],
                                                       paid[paid.quarter.isin(periods[-RECENT_QUARTERS:])])):
        for skill, g in frame.groupby("skill"):
            q1, med, q3 = g.salary_usd_k.quantile([0.25, 0.5, 0.75])
            rows.append({"scope": scope, "skill": skill, "n": len(g), "q1": q1, "median": med, "q3": q3})
        if len(all_frame):
            q1, med, q3 = all_frame.salary_usd_k.quantile([0.25, 0.5, 0.75])
            rows.append({"scope": scope, "skill": "__all__", "n": len(all_frame), "q1": q1, "median": med, "q3": q3})
    return pd.DataFrame(rows)


def employers(posting):
    sub = posting[posting.company.notna()].assign(key=lambda d: d.company.str.lower())
    agg = sub.groupby("key").agg(company=("company", lambda s: s.value_counts().index[0]), posts=("pid", "size"),
                                 active_months=("month", "nunique"), first_month=("month", "min"), last_month=("month", "max"))
    return agg[agg.posts >= EMPLOYER_MIN_POSTS].sort_values("posts", ascending=False).reset_index(drop=True)


def build(wh, gold, periods, last_month):
    """Build every analytic gold table; ``wh`` and ``gold`` are open connections. Returns a facts dict."""
    ids = [s["id"] for s in SKILLS]
    label = {s["id"]: s["label"] for s in SKILLS}
    posting = load_postings(wh, periods, last_month)
    pids = set(posting.pid)
    posting_skill = db.read_sql(wh, "SELECT comment_id AS pid, skill FROM posting_skills")
    posting_skill = posting_skill[posting_skill.pid.isin(pids)].reset_index(drop=True)

    matrix = skill_matrix(posting, posting_skill, ids)
    skill_year, pair_year = skill_year_tables(posting, matrix, ids)
    window = posting.quarter.isin(periods[-ECOSYSTEM_QUARTERS:]).to_numpy()
    window_matrix = matrix[np.flatnonzero(window)]
    clusters, cluster_info = ecosystem.build_clusters(window_matrix, ids, label)
    window_pairs = ecosystem.pair_table(ecosystem.cooccurrence(window_matrix), ids, window_matrix.shape[0])

    db.write_table(gold, "skills", pd.DataFrame([{"skill": s["id"], "label": s["label"], "category": s["category"],
                                                   "npm_package": s.get("npm"), "se_tag": s.get("se_tag")} for s in SKILLS]))
    # employer identity is kept only as an anonymous integer (enough to count distinct employers, not to name them)
    gold_posting = posting.assign(author_id=pd.factorize(posting.author)[0]).drop(columns=["author", "company"])
    db.write_table(gold, "posting", gold_posting, indexes=["pid", "quarter"])
    db.write_table(gold, "posting_skill", posting_skill, indexes=["pid"])
    db.write_table(gold, "market_quarter", market_quarter(posting))
    db.write_table(gold, "location_year", location_year(posting), indexes=["year"])
    db.write_table(gold, "skill_year", skill_year, indexes=[("skill", "year")])
    db.write_table(gold, "skill_pair_year", pair_year, indexes=[("a", "b")])
    db.write_table(gold, "skill_attr_year", skill_attr_year(posting, posting_skill), indexes=[("skill", "year")])
    db.write_table(gold, "skill_salary", skill_salary(posting, posting_skill, periods))
    db.write_table(gold, "employer", employers(posting))
    db.write_table(gold, "skill_cluster", clusters, indexes=["skill"])
    db.write_table(gold, "skill_pair_window", window_pairs)
    db.write_table(gold, "event", pd.DataFrame(EVENTS, columns=["period", "label"]))

    author_counts = posting.author.value_counts()
    facts = {"postings": len(posting), "postings_with_skill": int(posting_skill.pid.nunique()), "authors": int(len(author_counts)),
             "repeat_author_share": round(float(posting.author.map(author_counts).ge(5).mean()), 4),
             "company_parsed_share": round(float(posting.company.notna().mean()), 4),
             "first_quarter": periods[0], "last_quarter": periods[-1], "recent_first_quarter": periods[-RECENT_QUARTERS],
             "ecosystem_first_quarter": periods[-ECOSYSTEM_QUARTERS], **{f"cluster_{k}": v for k, v in cluster_info.items()}}
    db.kv_write(gold, "gold_fact", facts)
    return facts
