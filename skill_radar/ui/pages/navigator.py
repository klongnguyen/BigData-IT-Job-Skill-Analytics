"""Trang Skill Navigator: chọn kỹ năng đã biết, xem độ phủ thị trường và gợi ý kỹ năng nên học tiếp."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar import navigator as nav
from skill_radar.ui import data, theme
from skill_radar.ui.common import n_fmt, qdate

PRESETS = {
    "Tự chọn": [],
    "Web front-end": ["javascript", "react", "typescript"],
    "Back-end Python": ["python", "postgresql", "docker", "aws"],
    "Dữ liệu & ML": ["python", "sql", "ml", "pandas"],
    "Mobile iOS": ["ios", "swift"],
    "DevOps": ["linux", "docker", "kubernetes", "aws", "terraform"],
}
WINDOWS = {"8 quý gần nhất": 8, "16 quý gần nhất": 16, "Toàn bộ (từ 2015Q3)": None}


@st.cache_resource(show_spinner=False)
def _matrix(stamp):
    posting, posting_skill = data.postings()
    skills = sorted(posting_skill.skill.unique())
    matrix, keep = nav.dense_matrix(posting, posting_skill, skills)
    return matrix, posting.iloc[keep].reset_index(drop=True), skills


def _apply_preset():
    st.session_state["nav_skills"] = PRESETS[st.session_state["nav_preset"]]


def render(g):
    matrix_all, posting_all, skills = _matrix(data.db.GOLD.stat().st_mtime)
    index = {s: i for i, s in enumerate(skills)}
    st.markdown("Chọn những kỹ năng bạn đã có. Một tin **phù hợp** khi bạn biết ít nhất một tỷ lệ đặt trước trong số các kỹ năng được nêu trong tin.")
    if "nav_skills" not in st.session_state:
        st.session_state["nav_skills"] = PRESETS["Back-end Python"]
    c1, c2 = st.columns([1, 3])
    c1.selectbox("Hồ sơ mẫu", list(PRESETS), index=2, key="nav_preset", on_change=_apply_preset)
    known_ids = c2.multiselect("Kỹ năng của bạn", skills, format_func=g["label"].get, key="nav_skills")
    d1, d2, d3, d4 = st.columns([1.2, 1.4, 1, 1])
    window = d1.radio("Giai đoạn tin", list(WINDOWS), key="nav_window")
    threshold = d2.slider("Cần biết ít nhất … kỹ năng nêu trong tin", 20, 100, 50, step=10, format="%d%%", key="nav_threshold") / 100
    remote_only = d3.checkbox("Chỉ tin làm từ xa", key="nav_remote")
    salary_only = d4.checkbox("Chỉ tin nêu lương", key="nav_salary")

    mask = np.ones(len(posting_all), dtype=bool)
    n_q = WINDOWS[window]
    periods = sorted(posting_all.quarter.unique())
    if n_q:
        mask &= posting_all.quarter.isin(periods[-n_q:]).to_numpy()
    if remote_only:
        mask &= posting_all.is_remote.to_numpy().astype(bool)
    if salary_only:
        mask &= posting_all.has_salary.to_numpy().astype(bool)
    matrix = matrix_all[mask]
    if len(matrix) < 50:
        st.warning("Bộ lọc để lại quá ít tin (< 50). Hãy nới điều kiện.")
        return
    known = [index[s] for s in known_ids]
    cover = nav.coverage(matrix, known, threshold)
    fit = int(nav.fits(matrix, known, threshold).sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Độ phủ thị trường", theme.pct(cover), border=True, help="Tỷ lệ tin (có nêu ít nhất một kỹ năng) mà bạn đáp ứng đủ ngưỡng.")
    m2.metric("Số tin phù hợp", f"{n_fmt(fit)} / {n_fmt(len(matrix))}", border=True)
    m3.metric("Kỹ năng đã chọn", len(known), border=True)
    if not known:
        st.info("Chọn ít nhất một kỹ năng để xem kết quả.")
        return

    left, right = st.columns(2)
    with left:
        gain = nav.gains(matrix, known, threshold)
        top = np.argsort(gain)[::-1][:12]
        top = [j for j in top if gain[j] > 0][::-1]
        if top:
            fig = go.Figure(go.Bar(y=[g["label"][skills[j]] for j in top], x=[gain[j] / len(matrix) * 100 for j in top], orientation="h",
                                   marker={"color": [theme.category_color(g["category"][skills[j]]) for j in top]}, customdata=[int(gain[j]) for j in top],
                                   hovertemplate="<b>%{y}</b><br>+%{x:.1f} điểm % độ phủ<br>thêm %{customdata} tin phù hợp<extra></extra>"))
            theme.style(fig, height=430, legend=False, xtitle="Độ phủ tăng thêm (điểm %)")
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=False)
            theme.header("Nên học gì tiếp theo?", "Mỗi thanh: số tin mới trở nên phù hợp nếu bạn học thêm kỹ năng đó (chỉ tính một kỹ năng thêm).")
            theme.show(fig, "nav_gain")
        else:
            st.info("Không còn kỹ năng nào làm tăng độ phủ ở ngưỡng này.")
    with right:
        path = nav.plan(matrix, known, threshold, steps=6)
        if path:
            steps = ["Hiện tại", *[f"+ {g['label'][skills[p['skill']]]}" for p in path]]
            values = [cover * 100, *[p["coverage"] * 100 for p in path]]
            fig = go.Figure(go.Scatter(x=steps, y=values, mode="lines+markers+text", text=[f"{v:.0f}%" for v in values], textposition="top center",
                                       line={"color": theme.series_colors()[0], "width": 3, "shape": "hv"}, marker={"size": 9},
                                       hovertemplate="%{x}: %{y:.1f}%<extra></extra>"))
            theme.style(fig, height=430, legend=False, ytitle="Độ phủ (%)")
            fig.update_yaxes(range=[0, min(100, max(values) * 1.2 + 5)], ticksuffix="%")
            theme.header("Lộ trình học tham lam", "Mỗi bước chọn kỹ năng làm tăng độ phủ nhiều nhất, rồi lặp lại.")
            theme.show(fig, "nav_path")

    fits_all = nav.fits(matrix_all, known, threshold)
    by_quarter = pd.DataFrame({"quarter": posting_all.quarter, "fit": fits_all}).groupby("quarter").fit.mean() * 100
    fig = go.Figure(go.Scatter(x=qdate(by_quarter.index), y=by_quarter.rolling(4, min_periods=1).mean(), mode="lines",
                               line={"color": theme.series_colors()[1], "width": 2.5}, hovertemplate="%{y:.0f}%<extra>Trung bình 4 quý</extra>"))
    theme.style(fig, height=300, legend=False, hover="x unified", ytitle="% tin phù hợp")
    theme.time_range(fig)
    fig.update_yaxes(rangemode="tozero", ticksuffix="%")
    theme.header("Bộ kỹ năng này có “ăn khách” hơn theo thời gian?", "Độ phủ của đúng bộ kỹ năng đang chọn qua từng quý (trung bình 4 quý), trên toàn bộ tin, không phụ thuộc bộ lọc giai đoạn.")
    theme.show(fig, "nav_time")
    st.caption("Lưu ý: kết quả mô tả các tin trên Hacker News (thiên về startup, Mỹ, remote), kỹ năng nhận diện bằng từ khóa; không phải lời khuyên nghề nghiệp cho thị trường Việt Nam.")
