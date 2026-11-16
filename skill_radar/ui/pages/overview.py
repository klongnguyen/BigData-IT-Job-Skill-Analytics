"""Trang Tổng quan: bức tranh toàn thị trường trong một màn hình."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar import insights
from skill_radar.ui import interact, theme
from skill_radar.ui.pages import profile
from skill_radar.ui.common import n_fmt, qdate


MAX_RANK = 16
MIN_SHARE = 0.01


def _kpis(g):
    hist, radar, info = g["radar_history"], g["radar_series"], g["results"]["info"]
    last4, prev4 = insights.recent_periods(hist), insights.recent_periods(hist, 4, 4)
    now, before = insights.window_share(hist, last4), insights.window_share(hist, prev4)
    top = now.idxmax()
    change = ((now - before.reindex(now.index).fillna(0)) * 100)
    big = change[(now >= MIN_SHARE) | (before.reindex(now.index).fillna(0) >= MIN_SHARE)]      # ignore skills too rare to be meaningful
    up, down = big.idxmax(), big.idxmin()
    rising = radar[radar.direction == "Rising"].sort_values("delta_pp_4q", ascending=False)
    fading = radar[radar.direction == "Fading"].sort_values("delta_pp_4q")
    f1, f1_base = float(info["dv_macro_f1_model"]), float(info["dv_macro_f1_always_stable"])
    names = lambda frame: ", ".join(frame.label) or "không có"
    first = st.columns(3)                                                  # what the data covers
    first[0].metric("Tin đã phân tích", n_fmt(g["facts"]["postings"]), border=True,
                    help=f"Hacker News 'Ask HN: Who is hiring?', {g['facts']['first_quarter']} đến {g['facts']['last_quarter']}")
    first[1].metric("Kỹ năng theo dõi", len(g["skills"]), border=True, help="75 kỹ năng trong 8 nhóm, nhận diện bằng quy tắc từ khóa")
    first[2].metric("Phổ biến nhất", g["label"][top], delta=f"{theme.pct(now[top])} số tin", delta_color="off", border=True,
                    help="Kỹ năng được nhắc trong nhiều tin nhất ở 4 quý gần nhất.")
    second = st.columns(4)                                                 # where skills are heading, and how far to trust it
    second[0].metric("Tăng nhanh nhất", g["label"][up], delta=f"{big[up]:+.1f} điểm %".replace(".", ","), border=True,
                     help="Thay đổi tỷ lệ tin nhắc tới kỹ năng so với 4 quý trước đó. Chỉ xét kỹ năng có ít nhất 1% số tin ở một trong hai giai đoạn.")
    second[1].metric("Giảm mạnh nhất", g["label"][down], delta=f"{big[down]:+.1f} điểm %".replace(".", ","), border=True,
                     help="Thay đổi tỷ lệ tin nhắc tới kỹ năng so với 4 quý trước đó (cùng điều kiện như thẻ Tăng nhanh nhất).")
    second[2].metric("Dự báo sau 1 năm", f"{len(rising)} tăng, {len(fading)} giảm", delta=f"{int(info['skills_eligible'])} kỹ năng xét", delta_color="off", border=True,
                     help=f"Mô hình dự báo thay đổi tỷ lệ vượt ±1 điểm % sau 4 quý. Tăng: {names(rising)}. Giảm: {names(fading)}. Phần còn lại dự báo ổn định hoặc chưa đủ dữ liệu.")
    second[3].metric("Tin cậy dự báo", theme.vn(f1), delta=f"{f1 - f1_base:+.2f} hơn mốc cơ sở".replace(".", ","), border=True,
                     help=f"Điểm macro-F1 của nhãn Tăng/Ổn định/Giảm trên giai đoạn kiểm tra {info['holdout_targets']} (mô hình không được dùng các quý này để chọn). "
                          f"Mốc so sánh là đoán 'Ổn định' cho mọi kỹ năng, chỉ đạt {theme.vn(f1_base)}. 1,00 là hoàn hảo; mô hình mới ở mức trung bình, nên dùng để tham khảo.")
    st.caption("Tăng/giảm so sánh 4 quý gần nhất với 4 quý trước đó.")


def _insight_cards(g):
    cards = insights.make_insights(g["radar_history"], g["skill_year"], g["market_quarter"], g["label"])
    if not cards:
        return
    theme.header("Điểm nổi bật", "Tự sinh từ dữ liệu; thay đổi khi dữ liệu cập nhật.")
    for col, card in zip(st.columns(len(cards)), cards):
        with col, st.container(border=True, height=150):
            st.markdown(f'<div class="insight-title">{card["title"]}</div><div class="insight-body">{card["body"]}</div>', unsafe_allow_html=True)


def _treemap(g):
    hist = g["radar_history"]
    now = insights.window_share(hist, insights.recent_periods(hist))
    before = insights.window_share(hist, insights.recent_periods(hist, 4, 4))
    posts = insights.window_posts(hist, insights.recent_periods(hist))
    skills = [s for s in posts.index if posts[s] > 0]
    change = ((now - before) * 100).reindex(skills)
    limit = float(max(np.nanpercentile(np.abs(change), 90), 0.5))
    cats = sorted({g["category"][s] for s in skills}, key=theme.CATEGORY_ORDER.index)
    cat_values = [float(sum(posts[s] for s in skills if g["category"][s] == c)) for c in cats]
    ids = ["root"] + [f"c:{c}" for c in cats] + [f"s:{s}" for s in skills]
    labels = [" "] + [theme.CATEGORY_VI[c] for c in cats] + [g["label"][s] for s in skills]
    parents = [""] + ["root"] * len(cats) + [f"c:{g['category'][s]}" for s in skills]
    values = [float(sum(cat_values))] + cat_values + [float(posts[s]) for s in skills]
    colors = [0.0] * (len(cats) + 1) + [float(np.clip(change[s], -limit, limit)) for s in skills]
    custom = [["", "", ""]] * (len(cats) + 1) + [[theme.pct(now[s]), f"{change[s]:+.1f}".replace(".", ","), int(posts[s])] for s in skills]
    t = theme.tokens()
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total", customdata=custom,
        marker={"colors": colors, "colorscale": theme.diverging_scale(), "cmid": 0, "cmin": -limit, "cmax": limit,
                "line": {"width": 2, "color": t["surface"]},
                "colorbar": {"title": {"text": "Thay đổi<br>(điểm %)", "font": {"size": 11}}, "tickfont": {"size": 11}, "thickness": 10, "len": 0.6}},
        texttemplate="<b>%{label}</b><br>%{customdata[0]}", textfont={"size": 13}, pathbar={"visible": True, "thickness": 22}, root_color="rgba(0,0,0,0)",
        hovertemplate="<b>%{label}</b><br>%{customdata[2]} tin nhắc tới (%{customdata[0]} số tin)<br>Thay đổi so với 4 quý trước: %{customdata[1]} điểm %<extra></extra>"))
    fig.update_layout(height=470, margin={"l": 0, "r": 0, "t": 8, "b": 0}, paper_bgcolor="rgba(0,0,0,0)",
                      font={"color": t["text"], "size": 13})
    theme.header("Bản đồ kỹ năng năm qua", "Diện tích = số tin nhắc tới kỹ năng trong 4 quý gần nhất. Màu = thay đổi tỷ lệ so với 4 quý trước (xanh: tăng, đỏ: giảm). **Bấm vào một nhóm** để phóng to; bấm thanh đường dẫn phía trên để quay lại.")
    theme.show(fig, "ov_treemap")


def _composition(g):
    hist = g["radar_history"]
    mix = hist.groupby(["period", "category"]).posts.sum().reset_index()
    fig = go.Figure()
    for cat in theme.CATEGORY_ORDER:
        sub = mix[mix.category == cat]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(x=qdate(sub.period), y=sub.posts, name=theme.CATEGORY_VI[cat], mode="lines", stackgroup="one", groupnorm="percent",
                                 line={"width": 0.8, "color": theme.tokens()["surface"]}, fillcolor=theme.category_color(cat),
                                 hovertemplate="%{y:.1f}%<extra>" + theme.CATEGORY_VI[cat] + "</extra>"))
    theme.style(fig, height=380, hover="x unified", ytitle="% lượt nhắc kỹ năng")
    theme.time_range(fig)
    fig.update_yaxes(ticksuffix="%", range=[0, 100])
    theme.header("Cơ cấu lượt nhắc kỹ năng theo nhóm", "Mỗi tin có thể nhắc nhiều kỹ năng; biểu đồ chia 100% tổng lượt nhắc của từng quý.")
    theme.show(fig, "ov_composition")


def _bump(g):
    sy = g["skill_year"]
    annual = insights.annual_share(sy)
    years = [y for y in annual.index if y >= 2016]
    ranks = annual.loc[years].rank(axis=1, ascending=False, method="first")     # ties broken so labels never overlap
    last =ranks.loc[years[-1]].sort_values(kind="stable")
    total = len(last)
    theme.header("Cuộc đua xếp hạng kỹ năng", f"Hạng theo tỷ lệ tin nhắc tới trong từng năm; {years[-1]} tính đến quý gần nhất. Màu theo nhóm kỹ năng. "
                 f"Chọn khoảng hạng của năm {years[-1]} để xem; biểu đồ dài ra theo số hạng, cuộn trang xuống để xem hết. **Bấm vào một đường** để mở hồ sơ kỹ năng.")
    lo, hi = st.slider("Khoảng hạng hiển thị (theo năm gần nhất)", 1, total, (1, 12), key="ov_bump_range")
    top = list(last.index[lo - 1:hi])
    ymax = min(total, max(MAX_RANK, hi + 4)) if lo == 1 else min(total, hi + 4)
    ymin = max(1, lo - 4) if lo > 1 else 1
    fig = go.Figure()
    foc = interact.focus() if interact.focus() in top else None            # skill picked on another chart
    ids = {}
    for i, s in enumerate(top):
        color = theme.category_color(g["category"][s])
        r = ranks[s]
        ids[i] = [s] * len(years)
        fig.add_trace(go.Scatter(x=years, y=r, mode="lines+markers", name=g["label"][s], showlegend=False, opacity=0.3 if foc and s != foc else 1,
                                 line={"color": color, "width": 4.5 if s == foc else 2.2}, marker={"size": 8, "color": color, "line": {"width": 2, "color": theme.tokens()["surface"]}},
                                 hovertemplate="%{x}: hạng %{y:.0f}<extra>" + g["label"][s] + "</extra>"))
        if ymin - 0.5 <= r.iloc[-1] <= ymax + 0.5:
            fig.add_annotation(x=years[-1], y=r.iloc[-1], text=g["label"][s], showarrow=False, xanchor="left", xshift=10, font={"size": 12, "color": theme.tokens()["text"]})
        if ymin - 0.5 <= r.iloc[0] <= ymax + 0.5:
            fig.add_annotation(x=years[0], y=r.iloc[0], text=g["label"][s], showarrow=False, xanchor="right", xshift=-10, font={"size": 11, "color": theme.tokens()["text2"]})
    rows = ymax - ymin + 1
    theme.style(fig, height=int(min(2400, max(520, 30 * rows + 70))), legend=False, hover="closest")
    fig.update_yaxes(dtick=1, title="Hạng (1 = nhiều nhất)", range=[ymax + 0.5, ymin - 0.5])
    fig.update_xaxes(tickvals=years, range=[years[0] - 1.8, years[-1] + 1.8], tickformat="d")
    if ymax < max(ranks[top].max()):
        st.caption(f"Đường đi ra ngoài khung nghĩa là kỹ năng đó khi ấy xếp thấp hơn hạng {ymax} (hoặc cao hơn hạng {ymin}).")
    picked = interact.clickable(fig, "ov_bump", ids)
    if picked:
        profile.skill_panel(g, picked, "ov")


def render(g):
    _kpis(g)
    _insight_cards(g)
    left, right = st.columns([1.15, 1])
    with left:
        _treemap(g)
    with right:
        _composition(g)
    _bump(g)
