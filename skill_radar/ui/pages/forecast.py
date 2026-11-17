"""Trang Dự báo & độ tin cậy: radar 1 năm tới, độ chính xác của mô hình, tín hiệu cộng đồng."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from skill_radar.models import LABELS as MODEL_LABELS
from skill_radar.ui import interact, theme
from skill_radar.ui.pages import profile
from skill_radar.ui.common import qdate

LABEL_ORDER = ["Fading", "Stable", "Rising"]
MIN_SIGNAL_SKILLS = 8
SIGNAL_VI = {"npm_dl": "Lượt tải npm", "se_share": "Câu hỏi Stack Overflow", "gh_share": "Pull request GitHub"}
MAIN_MODELS = ["naive_last", "ses", "damped", "gbm", "gbm+signals"]


def label_of(delta_pp, band):
    return np.where(delta_pp > band, "Rising", np.where(delta_pp < -band, "Fading", "Stable"))


def confusion(cells, model, band):
    """Row-normalised confusion matrix of the 4-quarter direction label, plus counts."""
    t = cells[(cells.model == model) & (cells.h == 4)]
    obs = label_of((t.actual - t.base4) * 100, band)
    pred = label_of((t.pred - t.base4) * 100, band)
    counts = pd.crosstab(pd.Categorical(obs, LABEL_ORDER), pd.Categorical(pred, LABEL_ORDER), dropna=False)
    return counts


def _radar(g):
    series = g["radar_series"].assign(label_vi=lambda d: d.direction.map(theme.DIRECTION_VI), category_vi=lambda d: d.category.map(theme.CATEGORY_VI))
    cats = [c for c in theme.CATEGORY_ORDER if c in set(series.category)]
    pick = st.multiselect("Nhóm kỹ năng", cats, default=cats, format_func=theme.CATEGORY_VI.get, key="fc_cats")
    frame = series[series.category.isin(pick) & series.eligible]
    counts = frame.direction.value_counts()
    t = theme.tokens()
    color = {"Rising": t["up"], "Stable": t["flat"], "Fading": t["down"]}
    cols = st.columns(3)
    for col, key in zip(cols, ["Rising", "Stable", "Fading"]):
        col.metric(theme.DIRECTION_VI[key], int(counts.get(key, 0)), border=True)
    shown = frame.assign(a=frame.delta_pp_4q.abs()).nlargest(16, "a").sort_values("delta_pp_4q")
    fig = go.Figure(go.Bar(x=shown.delta_pp_4q, y=shown.label, orientation="h", marker_color=[color[d] for d in shown.direction],
                           hovertemplate="<b>%{y}</b><br>Thay đổi dự báo: %{x:+.2f} điểm %<extra></extra>"))
    fig.add_vline(x=1.0, line_dash="dot", line_color=t["muted"])
    fig.add_vline(x=-1.0, line_dash="dot", line_color=t["muted"])
    theme.style(fig, height=470, legend=False, xtitle="Thay đổi dự báo sau 4 quý so với trung bình năm vừa qua (điểm %)")
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=False)
    fig.update_traces(customdata=shown.skill, selected={"marker": {"opacity": 1}}, unselected={"marker": {"opacity": 0.35}})
    theme.header("Radar 1 năm tới", "16 kỹ năng thay đổi nhiều nhất. Đường chấm là mốc ±1 điểm %. **Bấm vào một cột** để xem chi tiết.")
    picked = interact.clickable(fig, "fc_radar", {0: list(shown.skill)})
    if picked:
        profile.skill_panel(g, picked, "fc")
    with st.expander("Bảng đầy đủ"):
        table = frame.sort_values("share_last_year", ascending=False)[["label", "category_vi", "share_last_year", "forecast_4q", "delta_pp_4q", "label_vi", "peak_share", "peak_period"]]
        table = table.rename(columns={"label": "Kỹ năng", "category_vi": "Nhóm", "share_last_year": "Tỷ lệ năm qua", "forecast_4q": "Dự báo 4 quý",
                                      "delta_pp_4q": "Thay đổi (điểm %)", "label_vi": "Hướng", "peak_share": "Đỉnh lịch sử", "peak_period": "Quý đỉnh"})
        for c in ("Tỷ lệ năm qua", "Dự báo 4 quý", "Đỉnh lịch sử"):
            table[c] = (table[c] * 100).round(1)
        table["Thay đổi (điểm %)"] = table["Thay đổi (điểm %)"].round(2)
        st.dataframe(table, width="stretch", hide_index=True)
        st.download_button("Tải CSV", table.to_csv(index=False).encode("utf-8-sig"), file_name="skill_radar.csv", mime="text/csv", key="dl_radar")


def _direction(g):
    info = g["results"]["info"]
    cells = g["backtest_cell"]
    model = info["direction_model"]
    counts = confusion(cells, model, info["band_pp"])
    pct_row = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0).fillna(0) * 100
    names = [theme.DIRECTION_VI[l] for l in LABEL_ORDER]
    text = [[f"{pct_row.iloc[i, j]:.0f}%<br>({counts.iloc[i, j]})" for j in range(3)] for i in range(3)]
    fig = go.Figure(go.Heatmap(z=pct_row.to_numpy(), x=names, y=names, colorscale=theme.sequential_scale(), zmin=0, zmax=100, xgap=3, ygap=3,
                               text=text, texttemplate="%{text}", textfont={"size": 14}, showscale=False,
                               hovertemplate="Thực tế: %{y}<br>Dự đoán: %{x}<br>%{z:.0f}% các trường hợp thực tế<extra></extra>"))
    theme.style(fig, height=380, legend=False, xtitle="Mô hình dự đoán", ytitle="Thực tế")
    fig.update_xaxes(showgrid=False, side="top")
    fig.update_yaxes(showgrid=False, autorange="reversed")
    left, right = st.columns([1, 1.3])
    with left:
        theme.header("Ma trận nhầm lẫn của nhãn hướng", f"Mỗi hàng là hướng thực tế, chia 100% theo hướng mô hình đoán. Dự báo 4 quý, giai đoạn {info['holdout_targets']}.")
        theme.show(fig, "fc_confusion")
    with right:
        labels = g["results"]["label_score"]
        band = labels[labels.band == info["band_pp"]]
        mods = band[band.model != "always_stable"].sort_values("macro_f1")
        stable = float(band[band.model == "always_stable"].macro_f1.iloc[0])
        t = theme.tokens()
        fig = go.Figure(go.Bar(y=[MODEL_LABELS.get(m, m) for m in mods.model], x=mods.macro_f1, orientation="h",
                               marker={"color": [t["up"] if m == model else t["flat"] for m in mods.model]},
                               hovertemplate="<b>%{y}</b><br>macro-F1 %{x:.3f}<extra></extra>"))
        fig.add_vline(x=stable, line_dash="dot", line_color=t["down"], annotation_text=f"Luôn đoán Ổn định: {theme.vn(stable)}", annotation_position="top left")
        theme.style(fig, height=380, legend=False, xtitle="macro-F1 của nhãn hướng (cao hơn là tốt hơn)")
        fig.update_xaxes(showgrid=True, range=[0, max(mods.macro_f1.max(), stable) * 1.15])
        fig.update_yaxes(showgrid=False)
        theme.header("Mô hình nào đoán đúng hướng?", "Cột xanh là mô hình đang dùng. Cột càng dài càng tốt.")
        theme.show(fig, "fc_f1")
    gain_lo, gain_hi = info["dv_gain_lo"], info["dv_gain_hi"]
    st.markdown(f"So với việc luôn đoán Ổn định, macro-F1 hơn **{theme.pp(info['dv_gain'], 3)}** (khoảng tin cậy 95%: {theme.vn(gain_lo, 3)} đến {theme.vn(gain_hi, 3)}). "
                + ("Khoảng này không chứa 0 nên mô hình đoán hướng tốt hơn đoán bừa." if gain_lo > 0 else "Khoảng này chứa 0 nên chưa kết luận được."))


def _values(g):
    info, res = g["results"]["info"], g["results"]
    scores = res["model_score"]
    scores = scores[scores.scope == "all_eligible"]
    base = scores[scores.diff_pp.isna()].iloc[0]
    cmp = scores[scores.diff_pp.notna()].sort_values("diff_pp")
    t = theme.tokens()

    def verdict(r):
        if r.ci_hi < 0:
            return t["up"]
        if r.ci_lo > 0:
            return t["down"]
        return t["flat"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cmp.diff_pp, y=[MODEL_LABELS.get(m, m) for m in cmp.model], mode="markers", marker={"size": 11, "color": [verdict(r) for r in cmp.itertuples()]},
                             error_x={"type": "data", "symmetric": False, "array": cmp.ci_hi - cmp.diff_pp, "arrayminus": cmp.diff_pp - cmp.ci_lo, "color": t["muted"], "thickness": 2},
                             hovertemplate="<b>%{y}</b><br>Chênh %{x:+.3f} điểm % so với baseline<extra></extra>"))
    fig.add_vline(x=0, line_color=t["text2"], line_width=1)
    theme.style(fig, height=380, legend=False, xtitle="Chênh sai số so với baseline (điểm %, âm là tốt hơn)")
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=False, autorange="reversed")
    left, right = st.columns(2)
    with left:
        theme.header(f"Có mô hình nào hơn {MODEL_LABELS.get(base.model, base.model)}?", "Chấm là chênh lệch sai số, thanh ngang là khoảng tin cậy 95%. Xanh: tốt hơn. Đỏ: tệ hơn. Xám: chưa phân biệt được.")
        theme.show(fig, "fc_compare")
    with right:
        hz = res["model_horizon_error"]
        hz = hz[(hz.scope == "all_eligible") & hz.model.isin(MAIN_MODELS)]
        fig = go.Figure()
        for i, m in enumerate(MAIN_MODELS):
            sub = hz[hz.model == m].sort_values("h")
            fig.add_trace(go.Scatter(x=[f"{h} quý" for h in sub.h], y=sub.mae_pp, mode="lines+markers", name=MODEL_LABELS.get(m, m),
                                     line={"color": theme.series_colors()[i], "width": 2.5}, marker={"size": 7}, hovertemplate="%{y:.3f}<extra>" + MODEL_LABELS.get(m, m) + "</extra>"))
        theme.style(fig, height=380, hover="x unified", ytitle="Sai số tuyệt đối TB (điểm %)", xtitle="Dự báo trước")
        fig.update_yaxes(rangemode="tozero")
        theme.header("Sai số tăng theo thời gian dự báo", "Dự báo càng xa càng khó nên sai số tăng ở mọi mô hình.")
        theme.show(fig, "fc_horizon")

    cells = g["backtest_cell"]
    c1, c2 = st.columns([1, 3])
    model = c1.selectbox("Mô hình", [m for m in MAIN_MODELS if m in set(cells.model)], index=2 if "damped" in set(cells.model) else 0,
                         format_func=lambda m: MODEL_LABELS.get(m, m), key="fc_scatter_model")
    h = c1.selectbox("Dự báo trước", [1, 2, 3, 4], index=3, format_func=lambda x: f"{x} quý", key="fc_scatter_h")
    sub = cells[(cells.model == model) & (cells.h == h)]
    lim = float(max(sub.pred.max(), sub.actual.max()) * 100 * 1.05)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, lim], y=[0, lim], mode="lines", line={"color": t["muted"], "dash": "dot", "width": 1.5}, hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=sub.pred * 100, y=sub.actual * 100, mode="markers", marker={"size": 7, "color": theme.series_colors()[0], "opacity": 0.55, "line": {"width": 0}},
                             customdata=np.column_stack([sub.skill.map(g["label"]), sub.target_period]),
                             hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>Dự đoán %{x:.1f}% · Thực tế %{y:.1f}%<extra></extra>", showlegend=False))
    theme.style(fig, height=430, legend=False, xtitle="Dự đoán (% tin)", ytitle="Thực tế (% tin)")
    fig.update_xaxes(range=[0, lim], showgrid=True)
    fig.update_yaxes(range=[0, lim])
    mae = float((sub.pred - sub.actual).abs().mean() * 100)
    with c2:
        theme.header("Dự đoán so với thực tế (giai đoạn kiểm tra)", f"Mỗi chấm là một kỹ năng trong một quý. Càng gần đường chéo càng đúng. Sai số trung bình {theme.vn(mae, 2)} điểm %.")
        theme.show(fig, "fc_scatter")
    st.markdown(f"Khoảng dự báo 80% chứa đúng giá trị thực **{theme.pct(info['interval_coverage_80'], 1)}** số lần, nên độ rộng khoảng là hợp lý.")


def _signals(g):
    res, info = g["results"], g["results"]["info"]
    eff = res["model_score"]
    eff = eff[(eff.scope == "all_eligible") & (eff.model == "gbm+signals")].iloc[0]
    st.markdown(f"Thêm tín hiệu cộng đồng vào mô hình làm sai số đổi **{theme.pp(eff.signal_diff_pp, 3)}** điểm % (khoảng tin cậy 95%: {theme.vn(eff.signal_ci_lo, 3)} đến {theme.vn(eff.signal_ci_hi, 3)}). "
                + ("Khoảng này chứa 0 nên **chưa thấy cải thiện**." if eff.signal_ci_lo <= 0 <= eff.signal_ci_hi else "Khoảng này không chứa 0."))
    lead, lags = res["leadlag_signal"], res["leadlag"]
    for r in lead.itertuples():
        name = SIGNAL_VI.get(r.signal, r.signal)
        if not r.has_lags or r.n_skills < MIN_SIGNAL_SKILLS:
            st.caption(f"{name}: mới có {r.n_skills} kỹ năng, cần ít nhất {MIN_SIGNAL_SKILLS} mới kết luận được.")
            continue
        sub = lags[lags.signal == r.signal].sort_values("lag")
        fig = go.Figure(go.Scatter(x=sub.lag, y=sub.mean_corr, mode="lines+markers", line={"color": theme.series_colors()[0], "width": 2.5}, marker={"size": 8},
                                   error_y={"type": "data", "symmetric": False, "array": sub.ci_hi - sub.mean_corr, "arrayminus": sub.mean_corr - sub.ci_lo, "color": theme.tokens()["muted"]},
                                   hovertemplate="Tín hiệu đi trước %{x} quý<br>Tương quan TB %{y:.3f}<extra></extra>"))
        fig.add_hline(y=0, line_color=theme.tokens()["text2"], line_width=1)
        theme.style(fig, height=300, legend=False, xtitle="Độ trễ: tín hiệu đi trước k quý", ytitle="Tương quan TB")
        fig.update_xaxes(dtick=1)
        left, right = st.columns(2)
        with left:
            theme.header(f"{name}: có đi trước nhu cầu không?", f"Tương quan trung bình của {r.n_skills} kỹ năng. Nếu thanh sai số chứa 0 thì chưa có bằng chứng.")
            theme.show(fig, f"fc_lag_{r.signal}")
        with right:
            per = res["leadlag_skill"]
            per = per[per.signal == r.signal].pivot(index="skill", columns="lag", values="corr")
            fig = go.Figure(go.Heatmap(z=per.to_numpy(), x=[str(c) for c in per.columns], y=[g["label"][s] for s in per.index], colorscale=theme.diverging_scale(), zmid=0, zmin=-1, zmax=1,
                                       xgap=2, ygap=2, colorbar={"title": {"text": "r"}, "thickness": 10}, hovertemplate="<b>%{y}</b> · độ trễ %{x}<br>r = %{z:.2f}<extra></extra>"))
            theme.style(fig, height=300, legend=False, xtitle="Độ trễ (quý)")
            fig.update_yaxes(autorange="reversed", showgrid=False)
            fig.update_xaxes(showgrid=False)
            theme.header("Từng kỹ năng", "Xanh: cùng chiều. Đỏ: ngược chiều. Rõ nhất là cùng thời điểm, chưa thấy đi trước.")
            theme.show(fig, f"fc_lagskill_{r.signal}")
    sig = g["signal_quarter"]
    with_npm = sorted(sig.dropna(subset=["npm_dl"]).skill.unique()) if "npm_dl" in sig else []
    if with_npm:
        skill = st.selectbox("Đối chiếu nhu cầu tuyển dụng với lượt tải npm", with_npm, format_func=g["label"].get, key="fc_overlay")
        s = sig[sig.skill == skill].dropna(subset=["npm_dl"]).sort_values("period")
        h = g["radar_history"]
        h = h[(h.skill == skill) & h.period.isin(s.period)].sort_values("period")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=qdate(h.period), y=h.share / h.share.max() * 100, mode="lines", name="Nhu cầu tuyển dụng (HN)", line={"color": theme.series_colors()[0], "width": 2.5}))
        fig.add_trace(go.Scatter(x=qdate(s.period), y=s.npm_dl / s.npm_dl.max() * 100, mode="lines", name="Lượt tải npm", line={"color": theme.series_colors()[1], "width": 2.5}))
        theme.style(fig, height=340, hover="x unified", ytitle="Chỉ số (đỉnh = 100)")
        theme.time_range(fig)
        theme.header(f"{g['label'][skill]}: tuyển dụng và lượt tải npm", "Cả hai quy về đỉnh = 100 để so cùng một trục.")
        theme.show(fig, "fc_overlay_chart")
    st.caption(f"Hiện chưa có bằng chứng cộng đồng đi trước tuyển dụng. Stack Overflow mới có {info.get('signal_skills_se_share', 0)} kỹ năng và GitHub chưa thu thập, nên chưa thể kết luận chắc chắn.")


def _categories(g):
    from plotly.subplots import make_subplots
    info, hist, path, summary = g["category_info"], g["category_history"], g["category_path"], g["category_forecast"]
    cats = [c for c in theme.CATEGORY_ORDER if c in set(summary.category)]
    t = theme.tokens()
    cols = 4
    rows = -(-len(cats) // cols)
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[theme.CATEGORY_VI[c] for c in cats], horizontal_spacing=0.06, vertical_spacing=0.16)
    for i, cat in enumerate(cats):
        r, c = i // cols + 1, i % cols + 1
        h = hist[hist.category == cat].sort_values("period").tail(16)
        p = path[path.category == cat].sort_values("h")
        color = theme.category_color(cat)
        fx = qdate(p.period)
        fig.add_trace(go.Scatter(x=fx, y=p.hi * 100, mode="lines", line={"width": 0}, hoverinfo="skip", showlegend=False), row=r, col=c)
        fig.add_trace(go.Scatter(x=fx, y=p.lo * 100, mode="lines", line={"width": 0}, fill="tonexty", fillcolor="rgba(128,128,128,0.22)", hoverinfo="skip", showlegend=False), row=r, col=c)
        fig.add_trace(go.Scatter(x=qdate(h.period), y=h.share * 100, mode="lines", line={"color": color, "width": 2.5}, showlegend=False,
                                 hovertemplate="%{x|%Y}: %{y:.1f}%<extra></extra>"), row=r, col=c)
        fig.add_trace(go.Scatter(x=[qdate([h.period.iloc[-1]])[0], *fx], y=[h.share.iloc[-1] * 100, *p.forecast * 100], mode="lines", showlegend=False,
                                 line={"color": t["text"], "width": 2, "dash": "dash"}, hovertemplate="Dự báo %{y:.1f}%<extra></extra>"), row=r, col=c)
    theme.style(fig, height=250 * rows + 40, legend=False, hover="x")
    fig.update_layout(margin={"l": 8, "r": 16, "t": 40, "b": 8})
    fig.update_yaxes(ticksuffix="%", showgrid=True)
    fig.update_xaxes(showgrid=False, tickformat="%Y", nticks=4)
    fig.update_annotations(font={"size": 13, "color": t["text"]})
    theme.header("Dự báo theo nhóm kỹ năng", "Đường liền là 4 năm gần nhất, nét đứt là dự báo 4 quý tới, vùng xám là khoảng 80%. Nhóm gộp nhiều kỹ năng nên ổn định hơn từng kỹ năng riêng lẻ.")
    theme.show(fig, "fc_cat_paths")

    table = summary.assign(Nhóm=summary.category.map(theme.CATEGORY_VI), Hướng=summary.direction.map(theme.DIRECTION_VI))
    table = table.sort_values("delta_pp_4q", ascending=False)
    table = table.assign(**{"Tỷ lệ năm qua": (table.share_last_year * 100).round(1), "Dự báo 4 quý": (table.forecast_4q * 100).round(1),
                            "Thay đổi (điểm %)": table.delta_pp_4q.round(2)})[["Nhóm", "Tỷ lệ năm qua", "Dự báo 4 quý", "Thay đổi (điểm %)", "Hướng"]]
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption(f"Tỷ lệ là % tin có nhắc ít nhất một kỹ năng của nhóm. Hướng dùng ngưỡng ±{theme.vn(info['band_pp'], 1)} điểm %. Con số dự báo chỉ là kịch bản.")


def render(g):
    tabs = st.tabs(["Radar 1 năm tới", "Theo nhóm kỹ năng", "Độ chính xác của hướng", "Độ chính xác của số liệu", "Tín hiệu cộng đồng"])
    with tabs[0]:
        _radar(g)
    with tabs[1]:
        _categories(g)
    with tabs[2]:
        _direction(g)
    with tabs[3]:
        _values(g)
    with tabs[4]:
        _signals(g)
    with st.expander("Dữ liệu và giới hạn"):
        f, info = g["facts"], g["results"]["info"]
        st.markdown(f"Nguồn: {info['evidence_source']}, {info['n_quarters']} quý ({info['first_quarter']} đến {info['last_quarter']}), "
                    f"**{f['postings']:,}** tin, {info['skills_total']} kỹ năng.".replace(",", "."))
        st.markdown("- Hacker News thiên về startup và công ty công nghệ ở Mỹ, không đại diện cho cả thị trường, nhất là Việt Nam.\n"
                    "- Kỹ năng nhận diện bằng từ khóa, nên được nhắc tới chưa chắc là đang tuyển.\n"
                    "- Một công ty có thể đăng lại mỗi tháng.\n"
                    "- Số liệu remote, lương, cấp bậc lấy bằng regex, chưa đối chiếu thủ công.\n"
                    f"- Mô hình chọn bằng dữ liệu đến {info['selection_end']}, rồi chấm một lần trên {info['holdout_targets']}.")
