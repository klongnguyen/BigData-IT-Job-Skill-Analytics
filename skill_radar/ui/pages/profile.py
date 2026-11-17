"""Trang Hồ sơ kỹ năng: mọi góc nhìn về một kỹ năng."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar import insights
from skill_radar.ui import interact, theme
from skill_radar.ui.pages import why
from skill_radar.ui.common import add_events, n_fmt, qdate

SHOW_WHY = False        # the "why did this skill rise/fall" section is switched off for now; set True to bring it back

ATTRS = [("remote", "Làm từ xa"), ("hybrid", "Hybrid"), ("salary", "Nêu mức lương"), ("equity", "Có equity / cổ phần"),
         ("senior", "Vị trí senior trở lên"), ("junior", "Junior / thực tập"), ("visa", "Hỗ trợ visa")]
MIN_SALARY_N = 20


def co_skills(pairs, skill, top=12):
    """Skills mentioned together with ``skill``: probability P(other | skill) and lift, from the ecosystem window."""
    left = pairs[pairs.a == skill].rename(columns={"b": "other", "n_a": "n_self", "n_b": "n_other"})
    right = pairs[pairs.b == skill].rename(columns={"a": "other", "n_b": "n_self", "n_a": "n_other"})
    both = pd.concat([left, right], ignore_index=True)
    both["p"] = both.n / both.n_self
    return both.sort_values("p", ascending=False).head(top)


def attribute_comparison(attr_year, market, skill, years):
    mine = attr_year[(attr_year.skill == skill) & attr_year.year.isin(years)]
    base = market[market.period.str[:4].astype(int).isin(years)]
    rows = []
    for key, label in ATTRS:
        if mine.posts.sum() == 0:
            continue
        rows.append({"key": key, "label": label, "skill": mine[key].sum() / mine.posts.sum(), "market": base[key].sum() / base.n_posts.sum(),
                     "n": int(mine.posts.sum())})
    return pd.DataFrame(rows)


def _fan(g, skill, key="pf_fan"):
    hist = g["radar_history"]
    h = hist[hist.skill == skill].sort_values("period")
    row = g["radar_series"][g["radar_series"].skill == skill].iloc[0]
    t = theme.tokens()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=qdate(h.period), y=h.share * 100, name="Từng quý", marker={"color": theme.category_color(g["category"][skill]), "opacity": 0.35},
                         hovertemplate="%{y:.1f}% (%{customdata} tin)<extra>Từng quý</extra>", customdata=h.posts.astype(int)))
    fig.add_trace(go.Scatter(x=qdate(h.period), y=h.share.rolling(4, min_periods=1).mean() * 100, mode="lines", name="Trung bình 4 quý",
                             line={"color": theme.category_color(g["category"][skill]), "width": 3}, hovertemplate="%{y:.1f}%<extra>Trung bình 4 quý</extra>"))
    if bool(row.eligible):
        p = g["radar_paths"][g["radar_paths"].skill == skill].sort_values("h")
        fx = qdate(list(p.period))
        fig.add_trace(go.Scatter(x=fx, y=p.hi * 100, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=fx, y=p.lo * 100, mode="lines", line={"width": 0}, fill="tonexty", fillcolor="rgba(128,128,128,0.22)",
                                 name="Khoảng 80%", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[qdate([h.period.iloc[-1]])[0], *fx], y=[h.share.iloc[-1] * 100, *p.forecast * 100], mode="lines", name="Kịch bản 4 quý tới",
                                 line={"color": t["text"], "width": 2.5, "dash": "dash"}, hovertemplate="%{y:.1f}%<extra>Kịch bản</extra>"))
    theme.style(fig, height=400, hover="x unified", ytitle="% tin nhắc tới")
    fig.update_yaxes(rangemode="tozero", ticksuffix="%")
    add_events(fig, g["event"])
    theme.header("Lịch sử và kịch bản 4 quý tới", "Cột là từng quý, đường là trung bình 4 quý. Nét đứt chỉ là kịch bản, chưa chắc chính xác." if bool(row.eligible)
                 else "Kỹ năng này quá ít tin nên không dự báo, chỉ hiển thị lịch sử.")
    theme.time_range(fig)
    theme.show(fig, key)


def _attributes(g, skill, key="pf_attrs"):
    years = sorted(g["skill_attr_year"].year.unique())[-2:]
    data = attribute_comparison(g["skill_attr_year"], g["market_quarter"], skill, years)
    if data.empty:
        return
    t = theme.tokens()
    data = data.iloc[::-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=data.label, x=data.market * 100, orientation="h", name="Toàn bộ tin", marker={"color": t["flat"], "opacity": 0.6},
                         hovertemplate="%{x:.1f}%<extra>Toàn bộ tin</extra>"))
    fig.add_trace(go.Bar(y=data.label, x=data.skill * 100, orientation="h", name=g["label"][skill], marker={"color": theme.category_color(g["category"][skill])},
                         hovertemplate="%{x:.1f}%<extra>" + g["label"][skill] + "</extra>"))
    theme.style(fig, height=380, xtitle="% số tin", hover="y unified")
    fig.update_layout(barmode="group", bargap=0.35)
    fig.update_xaxes(ticksuffix="%", showgrid=True)
    fig.update_yaxes(showgrid=False)
    theme.header(f"Chân dung tin tuyển {g['label'][skill]} so với thị trường", f"Năm {years[0]} đến {years[1]}, dựa trên {n_fmt(data.n.iloc[0])} tin nhắc tới {g['label'][skill]}.")
    theme.show(fig, key)


def _co_skills(g, skill, key="pf_co"):
    co = co_skills(g["skill_pair_window"], skill)
    if co.empty:
        st.caption("Chưa đủ dữ liệu đồng xuất hiện cho kỹ năng này.")
        return
    co = co.iloc[::-1]
    fig = go.Figure(go.Bar(
        y=[g["label"][s] for s in co.other], x=co.p * 100, orientation="h", marker={"color": [theme.category_color(g["category"][s]) for s in co.other]},
        customdata=np.column_stack([co.lift.round(1), co.n]),
        hovertemplate="<b>%{y}</b><br>%{x:.0f}% tin nhắc " + g["label"][skill] + " cũng nhắc kỹ năng này<br>Lift %{customdata[0]}× · %{customdata[1]} tin<extra></extra>"))
    theme.style(fig, height=380, legend=False, xtitle=f"% tin nhắc {g['label'][skill]} cũng nhắc kỹ năng này")
    fig.update_xaxes(ticksuffix="%", showgrid=True)
    fig.update_yaxes(showgrid=False)
    theme.header("Hay đi kèm với", f"Từ {g['facts']['ecosystem_first_quarter']} đến nay. Lift lớn hơn 1 nghĩa là đi cùng nhau nhiều hơn ngẫu nhiên.")
    theme.show(fig, key)


def _kpis(g, skill):
    row = g["radar_series"][g["radar_series"].skill == skill].iloc[0]
    hist = g["radar_history"]
    now = insights.window_share(hist, insights.recent_periods(hist))
    rank = int(now.rank(ascending=False, method="min")[skill])
    sal = g["skill_salary"]
    mine = sal[(sal.scope == "recent") & (sal.skill == skill)]
    overall = sal[(sal.scope == "recent") & (sal.skill == "__all__")]
    cols = st.columns(5)
    cols[0].metric("Tỷ lệ 4 quý gần nhất", theme.pct(row.share_last_year), border=True)
    cols[1].metric("Hạng trong 75 kỹ năng", f"#{rank}", border=True)
    cols[2].metric("Đỉnh lịch sử", theme.pct(row.peak_share), delta=f"quý {row.peak_period}", delta_color="off", border=True)
    cols[3].metric("Hướng 1 năm tới", theme.DIRECTION_VI[row.direction] if bool(row.eligible) else "—",
                   delta=f"{theme.pp(row.delta_pp_4q)} điểm %" if bool(row.eligible) else None, delta_color="off", border=True,
                   help="Nhãn do mô hình GBM đoán."
                   if bool(row.eligible) else "Kỹ năng này quá ít tin nên không dự báo hướng.")
    if len(mine) and int(mine.n.iloc[0]) >= MIN_SALARY_N:
        cols[4].metric("Lương trung vị", f"{mine['median'].iloc[0]:.0f}k USD", border=True,
                       delta=f"{mine['median'].iloc[0] - overall['median'].iloc[0]:+.0f}k so với chung".replace(".", ","), delta_color="off",
                       help=f"Dựa trên {int(mine.n.iloc[0])} tin nêu lương USD trong 8 quý gần nhất")
    else:
        cols[4].metric("Lương trung vị", "—", border=True, help=f"Chưa đủ {MIN_SALARY_N} tin nêu lương cho kỹ năng này")


def skill_panel(g, skill, prefix):
    """Detail card shown under a chart after a click: KPIs, history + scenario and a shortcut to the full profile."""
    with st.container(border=True):
        left, right = st.columns([5, 1.4])
        left.markdown(f"#### Chi tiết: {g['label'][skill]}")
        right.button("Mở hồ sơ đầy đủ →", key=f"{prefix}_go", on_click=interact.go_to_profile, args=(skill,), width="stretch")
        _kpis(g, skill)
        _fan(g, skill, key=f"{prefix}_fan")


def render(g):
    ids = list(g["radar_series"].sort_values("share_last_year", ascending=False).skill)
    if "pf_skill" not in st.session_state:
        st.session_state["pf_skill"] = interact.focus() if interact.focus() in ids else ("python" if "python" in ids else ids[0])
    skill = st.selectbox("Chọn kỹ năng", ids, format_func=g["label"].get, key="pf_skill")
    st.session_state[interact.FOCUS] = skill
    cluster = g["skill_cluster"][g["skill_cluster"].skill == skill].iloc[0]
    _kpis(g, skill)
    if cluster.cluster > 0:
        st.caption(f"Thuộc cụm công nghệ: **{cluster.cluster_name}** (xem trang Hệ sinh thái).")
    _fan(g, skill)
    left, right = st.columns(2)
    with left:
        _attributes(g, skill)
    with right:
        _co_skills(g, skill)
    if SHOW_WHY:
        why.render(g, skill)
