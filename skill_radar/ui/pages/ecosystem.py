"""Trang Hệ sinh thái: kỹ năng nào hay đi cùng nhau và tạo thành "stack" nào."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar.ui import interact, theme
from skill_radar.ui.pages import profile


def _map(g):
    clusters = g["skill_cluster"]
    placed = clusters[clusters.cluster > 0].copy()
    pairs = g["skill_pair_window"]
    pos = placed.set_index("skill")[["x", "y"]]
    edges = pairs[pairs.a.isin(pos.index) & pairs.b.isin(pos.index) & (pairs.lift >= 2.0) & (pairs.n >= 25)].nlargest(120, "lift")
    t = theme.tokens()
    fig = go.Figure()
    xs, ys = [], []
    for e in edges.itertuples():
        xs += [pos.x[e.a], pos.x[e.b], None]
        ys += [pos.y[e.a], pos.y[e.b], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line={"color": t["muted"], "width": 0.8}, opacity=0.35, hoverinfo="skip", showlegend=False))
    ids = {}
    for c in sorted(placed.cluster.unique()):
        sub = placed[placed.cluster == c]
        ids[len(fig.data)] = list(sub.skill)
        fig.add_trace(go.Scatter(
            x=sub.x, y=sub.y, mode="markers+text", name=sub.cluster_name.iloc[0], text=[g["label"][s] for s in sub.skill], textposition="top center",
            textfont={"size": 11, "color": t["text"]}, customdata=np.column_stack([sub.mentions]),
            marker={"size": np.sqrt(sub.mentions) * 1.3 + 7, "color": theme.cluster_color(c), "symbol": theme.MARKERS[(int(c) - 1) % 8],
                    "line": {"width": 1.5, "color": t["surface"]}, "opacity": 0.92},
            hovertemplate="<b>%{text}</b><br>%{customdata[0]} tin nhắc tới (cửa sổ phân cụm)<extra>" + sub.cluster_name.iloc[0] + "</extra>"))
    theme.style(fig, height=640, hover="closest")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, gridcolor="rgba(0,0,0,0)")
    fig.update_layout(legend={"orientation": "h", "y": -0.02, "yanchor": "top"})
    f = g["facts"]
    theme.header("Bản đồ công nghệ: các “stack” hay đi cùng nhau",
                 f"Mỗi chấm là một kỹ năng; hai kỹ năng càng gần nhau càng hay xuất hiện cùng nhau trong một tin. Màu và hình = cụm ({int(f['cluster_k'])} cụm, "
                 f"{f['ecosystem_first_quarter']} đến nay, {int(f['cluster_window_postings']):,} tin). Đường nối: cặp có lift ≥ 2. "
                 "**Bấm vào một chấm** để xem chi tiết và các kỹ năng hay đi kèm.".replace(",", "."))
    picked = interact.clickable(fig, "eco_map", ids)
    if picked:
        profile.skill_panel(g, picked, "eco")
        profile._co_skills(g, picked, key="eco_map_co")
    if f["cluster_silhouette"] < 0.25:
        st.caption(f"Lưu ý: độ tách cụm khá yếu (silhouette {theme.vn(f['cluster_silhouette'])}). Các kỹ năng chồng lấn nhau nhiều, nên coi cụm là gợi ý chứ không phải ranh giới cứng.")
    summary = (placed.groupby(["cluster", "cluster_name"]).apply(
        lambda d: pd.Series({"Số kỹ năng": len(d), "Kỹ năng": ", ".join(g["label"][s] for s in d.sort_values("mentions", ascending=False).skill)}), include_groups=False)
               .reset_index().drop(columns="cluster").rename(columns={"cluster_name": "Cụm"}))
    with st.expander("Thành phần từng cụm"):
        st.dataframe(summary, hide_index=True, width="stretch")


def _lift_matrix(g):
    clusters = g["skill_cluster"]
    pairs = g["skill_pair_window"]
    n_show = st.slider("Số kỹ năng trong ma trận", 12, 40, 24, key="eco_n")
    order_ids = list(clusters[clusters.cluster > 0].sort_values(["cluster", "mentions"], ascending=[True, False]).skill)
    top = set(clusters[clusters.cluster > 0].nlargest(n_show, "mentions").skill)
    ids = [s for s in order_ids if s in top]
    z = pd.DataFrame(np.nan, index=ids, columns=ids)
    for r in pairs[pairs.a.isin(ids) & pairs.b.isin(ids)].itertuples():
        z.loc[r.a, r.b] = z.loc[r.b, r.a] = np.log2(r.lift)
    lim = float(np.nanpercentile(np.abs(z.to_numpy()), 95)) if z.notna().any().any() else 1.0
    fig = go.Figure(go.Heatmap(
        z=z.to_numpy(), x=[g["label"][s] for s in ids], y=[g["label"][s] for s in ids], colorscale=theme.diverging_scale(), zmid=0, zmin=-lim, zmax=lim,
        xgap=1, ygap=1, colorbar={"title": {"text": "log₂ lift"}, "thickness": 10},
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>log₂ lift %{z:.2f}<extra></extra>"))
    theme.style(fig, height=max(480, 22 * len(ids) + 120), legend=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, tickangle=-60)
    theme.header("Ma trận lift", "Xanh: hai kỹ năng đi cùng nhau nhiều hơn ngẫu nhiên; đỏ: ít hơn; xám nhạt/trống: không đủ dữ liệu. Xếp theo cụm.")
    theme.show(fig, "eco_lift")


def _explorer(g):
    from skill_radar.ui.pages.profile import co_skills
    ids = list(g["skill_cluster"].sort_values("mentions", ascending=False).skill)
    skill = st.selectbox("Chọn một kỹ năng để xem “bạn đồng hành”", ids, format_func=g["label"].get, key="eco_skill")
    co = co_skills(g["skill_pair_window"], skill, top=15)
    if co.empty:
        st.info("Chưa đủ dữ liệu đồng xuất hiện.")
        return
    co = co.iloc[::-1]
    fig = go.Figure(go.Bar(
        y=[g["label"][s] for s in co.other], x=co.p * 100, orientation="h", marker={"color": [theme.category_color(g["category"][s]) for s in co.other]},
        customdata=np.column_stack([co.lift.round(1), co.n]),
        hovertemplate="<b>%{y}</b><br>%{x:.0f}% tin nhắc " + g["label"][skill] + " cũng nhắc kỹ năng này<br>Lift %{customdata[0]}× · %{customdata[1]} tin<extra></extra>"))
    theme.style(fig, height=460, legend=False, xtitle=f"% tin nhắc {g['label'][skill]} cũng nhắc kỹ năng này")
    fig.update_xaxes(ticksuffix="%", showgrid=True)
    fig.update_yaxes(showgrid=False)
    theme.header(f"Kỹ năng đi cùng {g['label'][skill]}", "Màu theo nhóm kỹ năng (Ngôn ngữ, Front-end, …).")
    theme.show(fig, "eco_explorer")


def render(g):
    tabs = st.tabs(["Bản đồ công nghệ", "Bạn đồng hành của một kỹ năng", "Ma trận lift"])
    with tabs[0]:
        _map(g)
    with tabs[1]:
        _explorer(g)
    with tabs[2]:
        _lift_matrix(g)
