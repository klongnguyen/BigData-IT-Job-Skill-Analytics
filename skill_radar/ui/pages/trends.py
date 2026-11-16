"""Trang Xu hướng: so sánh kỹ năng theo thời gian bằng bốn góc nhìn."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar import insights
from skill_radar.ui import interact, theme
from skill_radar.ui.pages import profile
from skill_radar.ui.common import add_events, qdate


def _heatmap(g):
    annual = insights.annual_share(g["skill_year"])
    annual = annual.loc[[y for y in annual.index if y >= 2016]]
    cols = st.columns([2, 1])
    with cols[0]:
        pick = st.multiselect("Nhóm kỹ năng", [c for c in theme.CATEGORY_ORDER if c in set(g["skills"].category)],
                              default=[c for c in theme.CATEGORY_ORDER if c in set(g["skills"].category)], format_func=theme.CATEGORY_VI.get, key="tr_hm_cats")
    with cols[1]:
        top_n = st.slider("Số kỹ năng hiển thị", 10, 40, 24, key="tr_hm_n")
    skills = [s for s in annual.columns if g["category"][s] in pick]
    order = annual.iloc[-1][skills].sort_values(ascending=False).head(top_n).index
    z = annual[order].T * 100
    t = theme.tokens()
    fig = go.Figure(go.Heatmap(
        z=z.to_numpy(), x=[str(y) for y in z.columns], y=[g["label"][s] for s in z.index], colorscale=theme.sequential_scale(),
        xgap=2, ygap=2, colorbar={"title": {"text": "% tin"}, "thickness": 10, "ticksuffix": "%"},
        hovertemplate="<b>%{y}</b> · %{x}<br>%{z:.1f}% số tin nhắc tới<extra></extra>"))
    if top_n <= 30:
        fig.update_traces(texttemplate="%{z:.0f}", textfont={"size": 11})
    theme.style(fig, height=max(360, 22 * len(order) + 90), legend=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False)
    theme.header("Bản đồ nhiệt: kỹ năng × năm", "Mỗi ô là % tin trong năm đó nhắc tới kỹ năng; xếp theo năm gần nhất. Năm đầu và năm cuối có thể chưa đủ 4 quý.")
    theme.show(fig, "tr_heatmap")


def _dumbbell(g):
    annual = insights.annual_share(g["skill_year"])
    years = [int(y) for y in annual.index if y >= 2016]
    c1, c2, c3 = st.columns(3)
    a = c1.selectbox("Năm so sánh (đầu)", years, index=years.index(2019) if 2019 in years else 0, key="tr_db_a")
    b = c2.selectbox("Năm so sánh (cuối)", years, index=len(years) - 1, key="tr_db_b")
    n = c3.slider("Số kỹ năng thay đổi nhiều nhất", 8, 30, 18, key="tr_db_n")
    if a == b:
        st.info("Chọn hai năm khác nhau.")
        return
    keep = annual.loc[[a, b]].max() >= 0.01
    delta = (annual.loc[b] - annual.loc[a])[keep]
    order = delta.abs().nlargest(n).sort_values().index
    t = theme.tokens()
    fig = go.Figure()
    for s in order:
        color = t["up"] if delta[s] > 0 else t["down"]
        fig.add_trace(go.Scatter(x=[annual.loc[a, s] * 100, annual.loc[b, s] * 100], y=[g["label"][s]] * 2, mode="lines", showlegend=False,
                                 line={"color": color, "width": 4}, hoverinfo="skip", opacity=0.75))
    fig.add_trace(go.Scatter(x=annual.loc[a, order] * 100, y=[g["label"][s] for s in order], mode="markers", name=str(a),
                             marker={"size": 11, "color": t["surface"], "line": {"width": 2, "color": t["flat"]}},
                             hovertemplate="%{y}<br>" + str(a) + ": %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=annual.loc[b, order] * 100, y=[g["label"][s] for s in order], mode="markers", name=str(b),
                             marker={"size": 11, "color": t["text"], "line": {"width": 2, "color": t["surface"]}},
                             customdata=[f"{delta[s] * 100:+.1f}".replace(".", ",") for s in order],
                             hovertemplate="%{y}<br>" + str(b) + ": %{x:.1f}%<br>Thay đổi: %{customdata} điểm %<extra></extra>"))
    theme.style(fig, height=max(380, 24 * len(order) + 80), hover="closest", xtitle="% số tin nhắc tới kỹ năng")
    fig.update_xaxes(ticksuffix="%", showgrid=True)
    fig.update_yaxes(showgrid=False)
    theme.header(f"Người thắng, người thua: {a} → {b}", "Vòng rỗng = năm đầu, chấm đặc = năm cuối; đường xanh: tăng, đỏ: giảm. Chỉ tính kỹ năng có tỷ lệ ≥ 1% ở ít nhất một trong hai năm.")
    theme.show(fig, "tr_dumbbell")


def _quadrant(g):
    hist = g["radar_history"]
    now = insights.window_share(hist, insights.recent_periods(hist))
    before = insights.window_share(hist, insights.recent_periods(hist, 4, 4))
    posts = insights.window_posts(hist, insights.recent_periods(hist))
    df = pd.DataFrame({"now": now, "delta": (now - before) * 100, "posts": posts}).dropna()
    df = df[df.posts >= 20].assign(label=lambda d: d.index.map(g["label"]), category=lambda d: d.index.map(g["category"]))
    xmid = float(df.now.median() * 100)
    t = theme.tokens()
    fig = go.Figure()
    ids = {}
    for i, cat in enumerate(theme.CATEGORY_ORDER):
        sub = df[df.category == cat]
        if sub.empty:
            continue
        ids[len(fig.data)] = list(sub.index)
        fig.add_trace(go.Scatter(
            x=sub.now * 100, y=sub.delta, mode="markers", name=theme.CATEGORY_VI[cat], customdata=np.column_stack([sub.label, sub.posts]),
            marker={"size": np.sqrt(sub.posts) * 0.9 + 6, "color": theme.category_color(cat), "symbol": theme.MARKERS[i], "opacity": 0.8,
                    "line": {"width": 1.5, "color": t["surface"]}},
            hovertemplate="<b>%{customdata[0]}</b><br>Tỷ lệ năm qua: %{x:.1f}%<br>Thay đổi: %{y:+.2f} điểm %<br>%{customdata[1]} tin<extra></extra>"))
    label_set = pd.concat([df.nlargest(6, "now"), df.nlargest(5, "delta"), df.nsmallest(5, "delta")]).index.unique()
    fig.add_trace(go.Scatter(x=df.loc[label_set].now * 100, y=df.loc[label_set].delta, mode="text", text=df.loc[label_set].label, textposition="top center",
                             textfont={"size": 11, "color": t["text"]}, showlegend=False, hoverinfo="skip"))
    fig.add_hline(y=0, line_color=t["axis"], line_width=1)
    fig.add_vline(x=xmid, line_color=t["axis"], line_width=1, line_dash="dot")
    ymax, ymin = df.delta.max(), df.delta.min()
    for text, x, y, ax, ay in (("Phổ biến & đang lên", 0.99, 0.98, "right", "top"), ("Ít phổ biến nhưng đang lên", 0.01, 0.98, "left", "top"),
                               ("Phổ biến nhưng chững lại", 0.99, 0.02, "right", "bottom"), ("Ít phổ biến & thu hẹp", 0.01, 0.02, "left", "bottom")):
        fig.add_annotation(xref="paper", yref="paper", x=x, y=y, text=text, showarrow=False, xanchor=ax, yanchor=ay, font={"size": 12, "color": t["muted"]})
    theme.style(fig, height=520, xtitle="Tỷ lệ tin nhắc tới trong 4 quý gần nhất (%, trục log)", ytitle="Thay đổi so với 4 quý trước (điểm %)")
    ticks = [v for v in (0.3, 0.5, 1, 2, 5, 10, 20, 30) if df.now.min() * 100 / 1.5 <= v <= df.now.max() * 100 * 1.5]
    fig.update_xaxes(type="log", tickvals=ticks, ticktext=[f"{v:g}%".replace(".", ",") for v in ticks])
    fig.update_layout(legend={"y": 1.1})
    theme.header("Vị thế và động lượng", "Kích thước = số tin; hình dạng + màu = nhóm. Đường chấm dọc là trung vị tỷ lệ (chia “phổ biến” và “ít phổ biến”). Đây là số liệu đã xảy ra, chưa phải dự báo. "
                 "**Bấm vào một bong bóng** để xem chi tiết kỹ năng bên dưới; bấm đúp vào biểu đồ để bỏ chọn.")
    picked = interact.clickable(fig, "tr_quadrant", ids)
    if picked:
        profile.skill_panel(g, picked, "tr")


def _compare(g):
    hist, events = g["radar_history"], g["event"]
    ids = list(g["skills"].sort_values("skill").skill)
    default = [s for s in ("react", "angular", "jquery", "typescript", "vue") if s in ids]
    c1, c2, c3 = st.columns([3, 1.2, 1])
    chosen = c1.multiselect("Kỹ năng", ids, default=default, format_func=g["label"].get, key="tr_cmp_skills", max_selections=8)
    mode = c2.radio("Thước đo", ["Tỷ lệ tin (%)", "Chỉ số (đỉnh = 100)"], key="tr_cmp_mode")
    smooth = c3.checkbox("Làm mượt 4 quý", value=True, key="tr_cmp_smooth")
    show_events = c3.checkbox("Hiện sự kiện", value=True, key="tr_cmp_events")
    if not chosen:
        st.info("Chọn ít nhất một kỹ năng.")
        return
    fig = go.Figure()
    colors = theme.series_colors()
    foc = interact.focus() if interact.focus() in chosen else None          # cross-highlight the skill picked elsewhere
    for i, s in enumerate(chosen):
        h = hist[hist.skill == s].sort_values("period")
        y = h.share * 100
        if smooth:
            y = y.rolling(4, min_periods=1).mean()
        if mode.startswith("Chỉ số"):
            y = y / y.max() * 100
        fig.add_trace(go.Scatter(x=qdate(h.period), y=y, mode="lines", name=g["label"][s], line={"color": colors[i % 8], "width": 4.5 if s == foc else 2.5},
                                 opacity=0.35 if foc and s != foc else 1,
                                 hovertemplate="%{y:.1f}" + ("" if mode.startswith("Chỉ số") else "%") + "<extra>" + g["label"][s] + "</extra>"))
    theme.style(fig, height=430, hover="x unified", ytitle="% tin nhắc tới" if not mode.startswith("Chỉ số") else "Chỉ số (đỉnh của từng kỹ năng = 100)")
    fig.update_yaxes(rangemode="tozero")
    theme.time_range(fig)
    if show_events:
        add_events(fig, events)
    theme.header("So sánh đường đi của các kỹ năng", "Chế độ chỉ số cho phép so sánh hình dạng tăng/giảm của kỹ năng lớn và nhỏ trên cùng một trục.")
    theme.show(fig, "tr_compare")


def render(g):
    tabs = st.tabs(["So sánh kỹ năng", "Bản đồ nhiệt", "Thắng – thua", "Vị thế & động lượng"])
    with tabs[0]:
        _compare(g)
    with tabs[1]:
        _heatmap(g)
    with tabs[2]:
        _dumbbell(g)
    with tabs[3]:
        _quadrant(g)
