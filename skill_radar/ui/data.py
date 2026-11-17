"""Cached readers for gold.db: the dashboard never touches the warehouse or any JSON file."""

import pandas as pd
import streamlit as st

from skill_radar import db, store

TABLES = ["skills", "radar_series", "radar_paths", "radar_history", "market_quarter", "skill_year",
          "skill_pair_year", "skill_pair_window", "skill_attr_year", "skill_salary", "skill_cluster", "event",
          "signal_quarter", "backtest_cell", "category_history", "category_forecast", "category_path", "category_score", "category_label"]


def is_ready():
    return db.GOLD.is_file() and db.GOLD.stat().st_size > 0


@st.cache_data(show_spinner="Đang đọc cơ sở dữ liệu…")
def _load(stamp):
    with db.session(db.GOLD, readonly=True) as conn:
        data = {name: db.read_sql(conn, f"SELECT * FROM {name}") for name in TABLES}
        data["facts"] = store.typed_info(db.kv_read(conn, "gold_fact"))
        data["results"] = store.load_results(conn)
        data["category_info"] = store.typed_info(db.kv_read(conn, "category_info"))
    skills = data["skills"]
    data["label"] = skills.set_index("skill").label.to_dict()
    data["category"] = skills.set_index("skill").category.to_dict()
    for name in ("radar_history", "skill_year"):
        data[name] = data[name].assign(label=data[name].skill.map(data["label"]), category=data[name].skill.map(data["category"]))
    return data


def load():
    return _load(db.GOLD.stat().st_mtime)


@st.cache_data(show_spinner=False)
def _postings(stamp):
    with db.session(db.GOLD, readonly=True) as conn:
        posting = db.read_sql(conn, "SELECT pid, quarter, year, is_remote, has_salary, is_senior, is_onsite, region, author_id FROM posting ORDER BY pid")
        skills = db.read_sql(conn, "SELECT pid, skill FROM posting_skill")
    return posting, skills


def postings():
    """Postings and their skills (used by the Skill Navigator only)."""
    return _postings(db.GOLD.stat().st_mtime)
