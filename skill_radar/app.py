"""Skill Radar dashboard. Run:  python -m streamlit run skill_radar/app.py --server.port 8502"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar.models import LABELS as MODEL_LABELS

GOLD = Path(__file__).resolve().parent / "data" / "gold"
PAGES = ["Radar", "Lịch sử & dự báo", "Độ tin cậy"]
COLORS = {"Rising": "#13786D", "Stable": "#708CA4", "Fading": "#C0504D"}
DIRECTION_VI = {"Rising": "Đang lên", "Stable": "Ổn định", "Fading": "Suy giảm", "Insufficient evidence": "Chưa đủ bằng chứng"}
CATEGORY_VI = {"language": "Ngôn ngữ", "frontend": "Front-end", "backend": "Back-end", "data": "Dữ liệu", "ai": "AI/ML",
               "cloud": "Cloud/DevOps", "mobile": "Mobile", "other": "Khác"}
MIN_SIGNAL_SKILLS = 8
PALETTE = ["#13786D", "#BF8C42", "#708CA4", "#C0504D", "#46A69A", "#8E6BB5"]


def vn(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")


def pct(value, digits=1):
    return f"{value * 100:.{digits}f}%".replace(".", ",")


@st.cache_data
def load():
    if not (GOLD / "radar_manifest.json").is_file():
        return None
    return {"manifest": json.loads((GOLD / "radar_manifest.json").read_text(encoding="utf-8")),
            "series": pd.read_parquet(GOLD / "radar_series.parquet"),
            "paths": pd.read_parquet(GOLD / "radar_paths.parquet"),
            "history": pd.read_parquet(GOLD / "radar_history.parquet")}


def period_dates(periods):
    return pd.PeriodIndex(pd.Series(periods), freq="Q").to_timestamp()


def status(m):
    prod = m["production"]
    d = prod["direction_validation"]
    base = m["backtest"]["all_eligible"]["models"][prod["model"]].get("vs_best_baseline")
    if d["validated"]:
        st.success(f"**Đã kiểm chứng:** hướng thay đổi sau 1 năm (macro-F1 {vn(d['macro_f1_model'])} so với "
                   f"{vn(d['macro_f1_always_stable'])} khi luôn đoán 'Ổn định'), thử trên 2023–2026 chưa từng dùng để chọn mô hình.")
    else:
        st.warning("Hướng thay đổi chưa vượt baseline 'luôn Ổn định'.")
    if base and base["ci95"][1] >= 0:
        st.warning("**Chưa kiểm chứng:** giá trị tỷ lệ dự báo chưa vượt baseline 'giữ nguyên quý cuối', nên coi là kịch bản.")


def radar_page(data, m):
    series = data["series"]
    cats = sorted(series.category.unique())
    pick = st.multiselect("Nhóm kỹ năng", cats, default=cats, format_func=lambda c: CATEGORY_VI.get(c, c), key="radar_cats")
    frame = series[series.category.isin(pick) & series.eligible].copy()
    frame["direction_vi"] = frame.direction.map(DIRECTION_VI)
    counts = frame.direction.value_counts()
    cols = st.columns(3)
    for col, key in zip(cols, ["Rising", "Stable", "Fading"]):
        col.metric(DIRECTION_VI[key], int(counts.get(key, 0)))
    shown = frame.assign(a=frame.delta_pp_4q.abs()).nlargest(16, "a").sort_values("delta_pp_4q")
    fig = go.Figure(go.Bar(x=shown.delta_pp_4q, y=shown.label, orientation="h",
                           marker_color=[COLORS[d] for d in shown.direction],
                           hovertemplate="%{y}<br>Thay đổi dự báo: %{x:+.2f} điểm %<extra></extra>"))
    fig.add_vline(x=1.0, line_dash="dot", line_color="#98A9A3")
    fig.add_vline(x=-1.0, line_dash="dot", line_color="#98A9A3")
    fig.update_layout(height=450, margin={"l": 10, "r": 15, "t": 10, "b": 10}, yaxis_title="", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Thay đổi dự báo sau 4 quý so với trung bình năm vừa qua (điểm phần trăm)")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with st.expander("Xem bảng đầy đủ"):
        table = frame.sort_values("share_last_year", ascending=False)[
            ["label", "category", "share_last_year", "forecast_4q", "delta_pp_4q", "direction_vi", "peak_share", "peak_period"]]
        table = table.rename(columns={"label": "Kỹ năng", "category": "Nhóm", "share_last_year": "Tỷ lệ năm qua", "forecast_4q": "Dự báo 4 quý",
                                      "delta_pp_4q": "Thay đổi (điểm %)", "direction_vi": "Hướng", "peak_share": "Đỉnh lịch sử", "peak_period": "Quý đỉnh"})
        for col in ("Tỷ lệ năm qua", "Dự báo 4 quý", "Đỉnh lịch sử"):
            table[col] = (table[col] * 100).round(1)
        table["Thay đổi (điểm %)"] = table["Thay đổi (điểm %)"].round(2)
        st.dataframe(table, width="stretch", hide_index=True)
        st.download_button("Tải CSV", table.to_csv(index=False).encode("utf-8-sig"), file_name="skill_radar.csv", mime="text/csv", key="dl_radar")


def history_page(data):
    series, history, paths = data["series"], data["history"], data["paths"]
    labels = series.set_index("skill").label.to_dict()
    ids = list(series.sort_values("peak_share", ascending=False).skill)
    default = [s for s in ("react", "angular", "jquery", "typescript") if s in ids]
    chosen = st.multiselect("Kỹ năng", ids, default=default, format_func=lambda s: labels[s], key="hist_skills")
    if not chosen:
        st.info("Chọn ít nhất một kỹ năng.")
        return
    fig = go.Figure()
    for i, sid in enumerate(chosen):
        h = history[history.skill == sid]
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(x=period_dates(h.period), y=h.share, mode="lines", name=labels[sid], line={"color": color, "width": 2.5},
                                 hovertemplate="%{x|%Y} Q%{customdata}<br>%{y:.1%} tin nhắc tới<extra>" + labels[sid] + "</extra>",
                                 customdata=pd.PeriodIndex(h.period, freq="Q").quarter))
    if len(chosen) == 1:
        sid = chosen[0]
        h, p = history[history.skill == sid], paths[paths.skill == sid]
        fx = pd.concat([pd.Series([period_dates(h.period).max()]), pd.Series(period_dates(p.period))], ignore_index=True)
        fig.add_trace(go.Scatter(x=fx.iloc[1:], y=p.hi, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=fx.iloc[1:], y=p.lo, mode="lines", line={"width": 0}, fill="tonexty", fillcolor="rgba(19,120,109,0.16)",
                                 name="Khoảng 80%", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=fx, y=[h.share.iloc[-1], *p.forecast], mode="lines", name="Dự báo 4 quý tới",
                                 line={"color": PALETTE[0], "width": 2.5, "dash": "dash"}))
        row = series[series.skill == sid].iloc[0]
        cols = st.columns(4)
        cols[0].metric("Tỷ lệ năm qua", pct(row.share_last_year))
        cols[1].metric("Đỉnh lịch sử", pct(row.peak_share), help=f"Quý {row.peak_period}")
        cols[2].metric("Dự báo 4 quý tới", pct(row.forecast_4q))
        cols[3].metric("Hướng", DIRECTION_VI[row.direction], delta=f"{row.delta_pp_4q:+.2f} điểm %".replace(".", ","), delta_color="off")
    fig.update_yaxes(tickformat=".0%", rangemode="tozero", gridcolor="#E2EAE6")
    fig.update_xaxes(showgrid=False)
    fig.update_layout(hovermode="x unified", height=430, margin={"l": 10, "r": 15, "t": 10, "b": 10}, legend={"orientation": "h", "y": -0.15},
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Tỷ lệ = phần trăm tin 'Ask HN: Who is hiring?' trong quý nhắc tới kỹ năng.")


def reliability_page(m):
    bt = m["backtest"]["all_eligible"]
    prod = m["production"]
    rows = []
    for name, e in bt["models"].items():
        cmp = e.get("vs_best_baseline")
        rows.append({"Mô hình": MODEL_LABELS.get(name, name), "MAE (điểm %)": e["mae_pp"],
                     "Chênh so với baseline tốt nhất [KTC 95%]": "—" if cmp is None else f"{cmp['diff_pp']:+.3f} [{cmp['ci95'][0]:+.3f}; {cmp['ci95'][1]:+.3f}]"})
    proto = m["backtest"]["protocol"]
    st.caption(f"Chọn mô hình bằng dữ liệu tới {proto['selection_end']}; chấm một lần trên {proto['holdout_targets']} "
               f"({bt['skills']} kỹ năng có tỷ lệ trung bình ≥ 1%). Chênh âm nghĩa là tốt hơn baseline.")
    st.dataframe(pd.DataFrame(rows).sort_values("MAE (điểm %)"), width="stretch", hide_index=True)
    d = prod["direction_validation"]
    cols = st.columns(3)
    cols[0].metric("Macro-F1 hướng (mô hình)", vn(d["macro_f1_model"]))
    cols[1].metric("Macro-F1 'luôn Ổn định'", vn(d["macro_f1_always_stable"]))
    cols[2].metric("Khoảng 80% phủ thực tế", pct(prod["interval_coverage_80_holdout"], 0))

    st.subheader("Hoạt động cộng đồng có đi trước nhu cầu tuyển dụng không?")
    effect = bt["models"]["gbm+signals"]["signal_effect"]
    st.markdown(f"Thêm tín hiệu cộng đồng vào mô hình: chênh sai số **{effect['diff_pp']:+.3f}** điểm % "
                f"(KTC 95% [{effect['ci95'][0]:+.3f}; {effect['ci95'][1]:+.3f}]). "
                + ("Khoảng này chứa 0 nên **chưa thấy cải thiện**." if effect["ci95"][0] <= 0 <= effect["ci95"][1] else "Khoảng này không chứa 0."))
    for name, result in m["lead_lag"].items():
        label = {"npm_dl": "Lượt tải npm", "se_share": "Câu hỏi Stack Overflow", "gh_share": "Pull request GitHub"}.get(name, name)
        if not result or "lags" not in result or len(result["skills"]) < MIN_SIGNAL_SKILLS:
            n = len(result["skills"]) if result else 0
            st.caption(f"{label}: mới có {n} kỹ năng (cần ít nhất {MIN_SIGNAL_SKILLS}), chưa đủ để kết luận.")
            continue
        lags = result["lags"]
        ks = sorted(int(k) for k in lags)
        mean = [lags[str(k)]["mean_corr"] for k in ks]
        lo = [lags[str(k)]["ci95"][0] for k in ks]
        hi = [lags[str(k)]["ci95"][1] for k in ks]
        fig = go.Figure(go.Scatter(x=ks, y=mean, mode="lines+markers", line={"color": PALETTE[0]},
                                   error_y={"type": "data", "symmetric": False, "array": [h - a for h, a in zip(hi, mean)],
                                            "arrayminus": [a - l for a, l in zip(mean, lo)]}))
        fig.add_hline(y=0, line_color="#98A9A3")
        fig.update_layout(height=260, margin={"l": 10, "r": 15, "t": 30, "b": 10}, title=f"{label}: tương quan với thay đổi nhu cầu theo độ trễ (quý), {len(result['skills'])} kỹ năng",
                          xaxis_title="Độ trễ: tín hiệu đi trước k quý", yaxis_title="Tương quan TB", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with st.expander("Dữ liệu và giới hạn"):
        ev = m["evidence"]
        st.markdown(f"Nguồn: {ev['source']}, {ev['n_quarters']} quý ({ev['quarters'][0]} đến {ev['quarters'][1]}), "
                    f"**{ev['postings_total']:,}** tin, {ev['skills_total']} kỹ năng.".replace(",", "."))
        st.markdown("- Hacker News lệch về startup và công ty công nghệ, nhiều công ty ở Mỹ; không đại diện toàn thị trường.\n"
                    "- Kỹ năng được nhận diện bằng quy tắc từ khóa, đã kiểm tra mẫu các từ dễ nhầm (Go, Swift, ML, RAG).\n"
                    "- Một công ty có thể đăng lại hằng tháng.\n"
                    "- Tín hiệu cộng đồng: " + ", ".join(f"{k}: {v} kỹ năng" for k, v in ev["signals_available"].items()) + ".")


def main():
    st.set_page_config(page_title="Skill Radar · Kỹ năng CNTT", page_icon="◈", layout="wide")
    st.markdown("""<style>
    .block-container {padding-top:2.5rem; padding-bottom:2rem; max-width:1250px;}
    [data-testid="stMetric"] {background:white; border:1px solid #dce7e2; border-radius:12px; padding:16px 20px; min-height:100px;}
    .hero {font-size:32px; line-height:1.15; font-weight:750; letter-spacing:-0.5px; margin:0 0 4px 0;}
    .subtitle {color:#577069; font-size:14px; margin-bottom:14px;}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div class="hero">Skill Radar · Nhu cầu kỹ năng CNTT</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Xu hướng 15 năm từ tin tuyển dụng và dự báo có kiểm chứng.</div>', unsafe_allow_html=True)
    data = load()
    if data is None:
        st.info("Chưa có dữ liệu. Chạy `python -m skill_radar.pipeline`.")
        return
    page = st.radio("Chuyên mục", PAGES, horizontal=True, label_visibility="collapsed", key="page")
    m = data["manifest"]
    status(m)
    if page == PAGES[0]:
        radar_page(data, m)
    elif page == PAGES[1]:
        history_page(data)
    else:
        reliability_page(m)


if __name__ == "__main__":
    main()
