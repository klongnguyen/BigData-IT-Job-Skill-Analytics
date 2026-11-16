"""Trang Thị trường: bối cảnh của tin tuyển dụng ngoài danh sách kỹ năng."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar.ui import interact, theme
from skill_radar.ui.pages import profile
from skill_radar.ui.common import add_events, n_fmt, qdate

MIN_SKILL_POSTS = 100
MIN_SALARY_N = 20
MIN_QUARTER_SALARY_N = 15


def _lines(df, columns, names, g, key, height=360, events=True, ytitle="% số tin"):
    colors = theme.series_colors()
    fig = go.Figure()
    for i, (col, name) in enumerate(zip(columns, names)):
        fig.add_trace(go.Scatter(x=qdate(df.period), y=df[col] / df.n_posts * 100, mode="lines", name=name, line={"color": colors[i], "width": 2.5},
                                 hovertemplate="%{y:.1f}%<extra>" + name + "</extra>"))
    theme.style(fig, height=height, hover="x unified", ytitle=ytitle)
    fig.update_yaxes(rangemode="tozero", ticksuffix="%")
    theme.time_range(fig)
    if events:
        add_events(fig, g["event"])
    theme.show(fig, key)


def _remote(g):
    m = g["market_quarter"]
    theme.header("Remote, onsite, hybrid theo quý", "Tỷ lệ tin có nhắc từ khóa; một tin có thể nhắc nhiều hình thức. Nhãn ONSITE/REMOTE chỉ thành quy ước đăng bài của HN từ khoảng 2015.")
    _lines(m, ["remote", "onsite", "hybrid"], ["Làm từ xa", "Tại văn phòng", "Hybrid"], g, "mk_remote")
    attr = g["skill_attr_year"]
    years = sorted(attr.year.unique())[-2:]
    sub = attr[attr.year.isin(years)].groupby("skill")[["posts", "remote"]].sum()
    sub = sub[sub.posts >= MIN_SKILL_POSTS].assign(share=lambda d: d.remote / d.posts)
    base = m[m.period.str[:4].astype(int).isin(years)]
    base_share = base.remote.sum() / base.n_posts.sum()
    show = pd.concat([sub.nlargest(10, "share"), sub.nsmallest(10, "share")]).drop_duplicates().sort_values("share")
    t = theme.tokens()
    fig = go.Figure(go.Bar(y=[g["label"][s] for s in show.index], x=show.share * 100, orientation="h",
                           marker={"color": [theme.category_color(g["category"][s]) for s in show.index]}, customdata=show.posts.astype(int),
                           hovertemplate="<b>%{y}</b><br>%{x:.0f}% tin nhắc làm từ xa<br>%{customdata} tin<extra></extra>"))
    fig.add_vline(x=base_share * 100, line_dash="dot", line_color=t["text2"], annotation_text=f"Chung {theme.pct(base_share, 0)}", annotation_position="top")
    theme.style(fig, height=520, legend=False, xtitle="% tin của kỹ năng nhắc làm từ xa")
    fig.update_xaxes(ticksuffix="%", showgrid=True)
    fig.update_yaxes(showgrid=False)
    theme.header("Kỹ năng nào “remote” nhất?", f"10 kỹ năng cao nhất và thấp nhất, năm {years[0]}–{years[1]}, kỹ năng có ≥ {MIN_SKILL_POSTS} tin. Màu theo nhóm kỹ năng. **Bấm vào một cột** để xem chi tiết kỹ năng.")
    picked = interact.clickable(fig, "mk_remote_skills", {0: list(show.index)})
    if picked:
        profile.skill_panel(g, picked, "mk")


def _pay(g):
    m = g["market_quarter"]
    left, right = st.columns(2)
    with left:
        theme.header("Minh bạch lương và quyền lợi", "% tin nêu mức lương, nhắc equity/cổ phần, nhắc visa.")
        _lines(m, ["salary", "equity", "visa"], ["Nêu mức lương", "Equity / cổ phần", "Visa / bảo lãnh"], g, "mk_pay_share", height=340)
    with right:
        trend = m[m.usd_salary >= MIN_QUARTER_SALARY_N]
        fig = go.Figure(go.Scatter(x=qdate(trend.period), y=trend.salary_median_k, mode="lines+markers", line={"color": theme.series_colors()[0], "width": 2.5},
                                   marker={"size": 7}, customdata=trend.usd_salary, hovertemplate="%{y:.0f}k USD (n = %{customdata})<extra>Trung vị</extra>"))
        theme.style(fig, height=340, legend=False, hover="x unified", ytitle="nghìn USD / năm")
        fig.update_yaxes(rangemode="tozero")
        theme.time_range(fig)
        theme.header("Lương công bố (trung vị)", f"Chỉ tính tin nêu mức lương USD/năm; quý có ít hơn {MIN_QUARTER_SALARY_N} tin bị bỏ. Cơ cấu tin nêu lương thay đổi nên xu hướng chỉ mang tính tham khảo.")
        theme.show(fig, "mk_pay_trend")
    sal = g["skill_salary"]
    scope = st.radio("Giai đoạn", ["8 quý gần nhất", "Toàn bộ"], horizontal=True, key="mk_sal_scope")
    key = "recent" if scope.startswith("8") else "all"
    s = sal[(sal.scope == key) & (sal.skill != "__all__") & (sal.n >= MIN_SALARY_N)].sort_values("median")
    if s.empty:
        st.info("Chưa đủ tin nêu lương.")
        return
    overall = sal[(sal.scope == key) & (sal.skill == "__all__")].iloc[0]
    t = theme.tokens()
    labels = [g["label"][x] for x in s.skill]
    colors = [theme.category_color(g["category"][x]) for x in s.skill]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=s.q3 - s.q1, base=s.q1, orientation="h", marker={"color": colors, "opacity": 0.35}, width=0.55, name="Khoảng tứ phân vị (25%–75%)",
                         customdata=np.column_stack([s.q1, s.q3, s.n]), hovertemplate="<b>%{y}</b><br>25%–75%: %{customdata[0]:.0f}k – %{customdata[1]:.0f}k<br>%{customdata[2]} tin<extra></extra>"))
    fig.add_trace(go.Scatter(y=labels, x=s["median"], mode="markers", name="Trung vị", marker={"size": 10, "color": colors, "line": {"width": 2, "color": t["surface"]}},
                             hovertemplate="<b>%{y}</b><br>Trung vị: %{x:.0f}k USD<extra></extra>"))
    fig.add_vline(x=overall["median"], line_dash="dot", line_color=t["text2"], annotation_text=f"Chung {overall['median']:.0f}k", annotation_position="top")
    theme.style(fig, height=max(420, 24 * len(s) + 100), xtitle="nghìn USD / năm", hover="closest", legend=False)
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=False)
    theme.header("Lương công bố theo kỹ năng", f"Thanh: khoảng 25%–75%; chấm: trung vị; màu theo nhóm kỹ năng. Kỹ năng có ≥ {MIN_SALARY_N} tin nêu lương USD (tổng {n_fmt(overall.n)} tin). "
                 "Chỉ phản ánh tin có công bố lương, thiên về công ty Mỹ; nhóm tin nêu lương đổi theo thời gian nên đây không phải mức lương thị trường.")
    theme.show(fig, "mk_pay_skills")


def _level(g):
    m = g["market_quarter"]
    left, right = st.columns(2)
    with left:
        theme.header("Cấp bậc được nhắc tới", "Senior = senior/staff/principal/lead/head of…; Junior = junior/entry-level/new grad; Thực tập.")
        _lines(m, ["senior", "junior", "intern"], ["Senior trở lên", "Junior / mới ra trường", "Thực tập"], g, "mk_level", height=360)
    with right:
        theme.header("Hình thức hợp đồng", "Từ khóa full-time, part-time, contract/freelance (không tính 'smart contract').")
        _lines(m, ["fulltime", "parttime", "contract"], ["Toàn thời gian", "Bán thời gian", "Hợp đồng / freelance"], g, "mk_contract", height=360)


def render(g):
    tabs = st.tabs(["Làm từ xa", "Lương & quyền lợi", "Cấp bậc & hợp đồng"])
    for tab, fn in zip(tabs, (_remote, _pay, _level)):
        with tab:
            fn(g)
