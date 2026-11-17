"""Mục "Vì sao kỹ năng này tăng/giảm?" của trang Hồ sơ kỹ năng (phân tích mô tả, không phải nhân quả)."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar import drivers, insights
from skill_radar.ui import data, theme
from skill_radar.ui.common import add_events, n_fmt, qdate

OFFSETS = {"1 năm trước": 4, "3 năm trước": 12, "5 năm trước": 20}
SEGMENTS = {
    "Hình thức làm việc": ("is_remote", {1: "Tin nhắc làm từ xa", 0: "Tin không nhắc remote"}),
    "Cấp bậc": ("is_senior", {1: "Tin vị trí senior trở lên", 0: "Tin khác"}),
    "Khu vực": ("region", theme.REGION_VI),
}


def _waterfall(result, label):
    t = theme.tokens()
    steps = [("Kỳ trước", result["share_a"] * 100, "absolute"), ("Kỹ năng được nhắc\nkhác đi (trong tin tương đương)", result["within"] * 100, "relative"),
             ("Loại tin thay đổi\n(cơ cấu)", result["mix"] * 100, "relative"), ("Kỳ này", result["share_b"] * 100, "total")]
    fig = go.Figure(go.Waterfall(
        x=[s[0] for s in steps], y=[s[1] for s in steps], measure=[s[2] for s in steps], connector={"line": {"color": t["axis"], "width": 1}},
        increasing={"marker": {"color": t["up"]}}, decreasing={"marker": {"color": t["down"]}}, totals={"marker": {"color": t["flat"]}},
        text=[(f"{v:.1f}%" if m != "relative" else f"{v:+.2f}").replace(".", ",") for _, v, m in steps], textposition="outside",
        hovertemplate="%{x}<br>%{y:.2f} điểm %<extra></extra>"))
    theme.style(fig, height=380, legend=False, ytitle="% tin nhắc " + label)
    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(showgrid=False)
    return fig


def render(g, skill):
    label = g["label"][skill]
    hist = g["radar_history"]
    st.markdown("### Vì sao kỹ năng này tăng/giảm?")
    st.caption("Chỉ cho thấy thay đổi **đến từ đâu**, không chứng minh được nguyên nhân.")
    choice = st.radio("So sánh 4 quý gần nhất với", list(OFFSETS), index=1, horizontal=True, key="why_offset")
    periods_b = insights.recent_periods(hist, 4)
    periods_a = insights.recent_periods(hist, 4, OFFSETS[choice])
    posting, posting_skill = data.postings()

    shifts = {name: drivers.shift_share(posting, posting_skill, skill, periods_a, periods_b, col) for name, (col, _) in SEGMENTS.items()}
    breadth_a = drivers.breadth(posting, posting_skill, skill, periods_a)
    breadth_b = drivers.breadth(posting, posting_skill, skill, periods_b)
    series = hist[hist.skill == skill].sort_values("period")
    brk = drivers.hinge_break(series.share.to_numpy())
    break_period = series.period.iloc[brk["knot"]] if "knot" in brk else None
    events = drivers.nearby_events(break_period, g["event"]) if brk.get("significant") else []
    together, against = drivers.comovement(hist, skill)
    inputs = drivers.model_inputs(series.share.to_numpy())

    with st.container(border=True):
        st.markdown("**Tóm tắt**")
        for line in drivers.summarize(label, periods_a, periods_b, list(shifts.values()), breadth_a, breadth_b, brk, break_period, events,
                                      together.skill, against.skill, g["label"], inputs):
            st.markdown(f"- {line}")

    tabs = st.tabs(["Bước ngoặt", "Cơ cấu tin hay chính kỹ năng?", "Độ rộng nhà tuyển dụng", "Đồng biến / ngược chiều", "Mô hình dự báo dựa vào gì?"])
    with tabs[0]:
        _break_tab(g, series, brk, break_period, events, label)
    with tabs[1]:
        _mix_tab(shifts, label, periods_a, periods_b)
    with tabs[2]:
        _breadth_tab(breadth_a, breadth_b, periods_a, periods_b)
    with tabs[3]:
        _comove_tab(g, skill, together, against, label)
    with tabs[4]:
        _model_tab(inputs, label)


def _break_tab(g, series, brk, break_period, events, label):
    t = theme.tokens()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=qdate(series.period), y=series.share * 100, name="Từng quý", marker={"color": theme.category_color(g["category"][series.skill.iloc[0]]), "opacity": 0.3},
                         hovertemplate="%{y:.1f}%<extra>Từng quý</extra>"))
    if "fitted" in brk:
        fig.add_trace(go.Scatter(x=qdate(series.period), y=brk["fitted"] * 100, mode="lines", name="Đường xu hướng hai đoạn",
                                 line={"color": t["text"], "width": 3}, hovertemplate="%{y:.1f}%<extra>Xu hướng hai đoạn</extra>"))
    if brk.get("significant"):
        x = qdate([break_period])[0]
        fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper", line={"color": t["down"], "width": 2, "dash": "dash"})
        fig.add_annotation(x=x, y=0.04, yref="paper", text=f"Bước ngoặt {break_period}", showarrow=False, xanchor="left", yanchor="bottom", xshift=6, font={"size": 12, "color": t["down"]})
    theme.style(fig, height=380, hover="x unified", ytitle="% tin nhắc tới")
    fig.update_yaxes(rangemode="tozero", ticksuffix="%")
    add_events(fig, g["event"])
    theme.time_range(fig)
    theme.header("Xu hướng đổi hướng khi nào?", "Đường đen gồm hai đoạn thẳng khớp nhất với dữ liệu, chỗ gấp là bước ngoặt. Vạch xám là các sự kiện để tham khảo.")
    theme.show(fig, "why_break")
    if brk.get("significant"):
        before = f"{brk['slope_before_pp_year'] + 0.0:+.1f}".replace("-0.0", "0.0")
        st.markdown(f"Độ dốc trước bước ngoặt: **{before}** điểm %/năm; sau: **{brk['slope_after_pp_year']:+.1f}** điểm %/năm "
                    f"(giải thích thêm {brk['gain'] * 100:.0f}% sai số so với một đường thẳng).".replace(".", ","))


def _mix_tab(shifts, label, periods_a, periods_b):
    name = st.radio("Chia tin theo", list(SEGMENTS), horizontal=True, key="why_segment")
    col, names = SEGMENTS[name]
    result = shifts[name]
    theme.header(f"Thay đổi của {label} đến từ chính kỹ năng hay từ cơ cấu tin?",
                 f"Thay đổi từ quý {periods_a[0]} đến {periods_a[-1]} sang quý {periods_b[0]} đến {periods_b[-1]}, chia thành hai phần. Một là kỹ năng được nhắc nhiều hay ít hơn **trong tin cùng loại**. Hai là **loại tin thay đổi**, ví dụ tin remote nhiều lên.")
    theme.show(_waterfall(result, label), "why_waterfall")
    table = result["table"].assign(Nhóm=lambda d: d.category.map(lambda c: names.get(c, str(c))))
    table = table[["Nhóm", "w_a", "w_b", "p_a", "p_b", "within", "mix"]].rename(columns={
        "w_a": "Tỷ trọng tin (trước)", "w_b": "Tỷ trọng tin (nay)", "p_a": "Tỷ lệ nhắc kỹ năng (trước)", "p_b": "Tỷ lệ nhắc kỹ năng (nay)",
        "within": "Đóng góp: kỹ năng đổi (điểm %)", "mix": "Đóng góp: cơ cấu đổi (điểm %)"})
    for c in table.columns[1:]:
        table[c] = (table[c] * 100).round(2)
    with st.expander("Chi tiết từng nhóm tin"):
        st.dataframe(table, hide_index=True, width="stretch")
        st.caption("Phần kỹ năng đổi = tỷ trọng trung bình × thay đổi tỷ lệ nhắc. Phần cơ cấu đổi = thay đổi tỷ trọng × tỷ lệ nhắc trung bình.")


def _breadth_tab(a, b, periods_a, periods_b):
    theme.header("Tăng trưởng có rộng không?", "Nếu số nhà tuyển dụng tăng cùng nhịp với số tin thì tăng trưởng rộng. Nếu vài người đăng liên tục chiếm phần lớn thì tăng trưởng yếu hơn.")
    rows = [("Số tin nhắc kỹ năng", a["posts"], b["posts"], n_fmt), ("Số nhà tuyển dụng khác nhau", a["authors"], b["authors"], n_fmt),
            ("Tin / nhà tuyển dụng", a["posts_per_author"], b["posts_per_author"], lambda v: f"{v:.2f}".replace(".", ",")),
            ("5 nhà đăng nhiều nhất chiếm", a["top5_share"], b["top5_share"], lambda v: theme.pct(v, 0))]
    cols = st.columns(len(rows))
    for col, (name, va, vb, fmt) in zip(cols, rows):
        delta = f"trước: {fmt(va)}"
        col.metric(name, fmt(vb), delta=delta, delta_color="off", border=True)
    st.caption(f"Số lớn là quý {periods_b[0]} đến {periods_b[-1]}, số nhỏ bên dưới là quý {periods_a[0]} đến {periods_a[-1]}.")


def _comove_tab(g, skill, together, against, label):
    pairs = g["skill_pair_window"]

    def lift(other):
        row = pairs[((pairs.a == other) & (pairs.b == skill)) | ((pairs.a == skill) & (pairs.b == other))]
        return float(row.lift.iloc[0]) if len(row) else float("nan")

    frame = pd.concat([together.assign(kind="Cùng chiều"), against.assign(kind="Ngược chiều")], ignore_index=True)
    if frame.empty:
        st.info("Chưa đủ dữ liệu để so sánh.")
        return
    frame = frame.sort_values("corr")
    t = theme.tokens()
    fig = go.Figure(go.Bar(y=[g["label"][s] for s in frame.skill], x=frame["corr"], orientation="h",
                           marker={"color": [t["up"] if c > 0 else t["down"] for c in frame["corr"]]},
                           customdata=[lift(s) for s in frame.skill],
                           hovertemplate="<b>%{y}</b><br>Tương quan thay đổi theo năm: %{x:.2f}<br>Lift cùng tin: %{customdata:.1f}<extra></extra>"))
    fig.add_vline(x=0, line_color=t["axis"], line_width=1)
    theme.style(fig, height=420, legend=False, xtitle="Tương quan của thay đổi theo năm (−1 đến +1)")
    fig.update_xaxes(range=[-1, 1], showgrid=True)
    fig.update_yaxes(showgrid=False)
    theme.header(f"Kỹ năng nào biến động cùng hay ngược chiều với {label}?", "Xanh là cùng tăng giảm, đỏ là ngược nhau. Đây chỉ là tương quan, không chứng minh nguyên nhân.")
    theme.show(fig, "why_comove")


def _model_tab(inputs, label):
    st.markdown(f"Mô hình đoán hướng (Gradient Boosting) **không biết nguyên nhân**. Nó chỉ đọc vài con số về đà gần đây của {label} và nhóm kỹ năng:")
    base, slope = inputs["base_pp"], inputs["slope_pp_per_quarter"]
    last = inputs["last_vs_base_pp"]
    table = pd.DataFrame({"Đầu vào": ["Mức nền (trung bình 4 quý gần nhất)", "Độ dốc 8 quý gần nhất", "Quý gần nhất so với mức nền", "Quý trước đó so với mức nền", "Quý thứ ba tính ngược so với mức nền"],
                          "Giá trị": [f"{base:.1f}%", f"{slope:+.2f} điểm %/quý", f"{last[0]:+.2f} điểm %", f"{last[1]:+.2f} điểm %", f"{last[2]:+.2f} điểm %"]})
    table["Giá trị"] = table["Giá trị"].str.replace(".", ",", regex=False)
    st.dataframe(table, hide_index=True, width="stretch")
    st.markdown("Mô hình còn dùng tổng số tin của quý và nhóm kỹ năng. Vì vậy dự báo chủ yếu là quán tính: đang lên thì tiếp tục lên chậm dần, đang giảm thì giảm chậm dần. "
                "Nó **không** biết các nguyên nhân như công nghệ mới hay sa thải, nên chỉ đoán khá được **hướng**, không đoán chính xác con số.")
