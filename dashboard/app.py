"""Run with: python -m streamlit run dashboard/app.py."""

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.data import (
    GoldError, load_catalog, load_gold, load_multi_year_forecast,
    select_scope, summarize_skills, trend_calendar
)


SOURCES = {
    "kaggle_historical_archive": "Archive 2023",
    "arbeitnow": "Arbeitnow 2026",
    "remotive": "Remotive 2026",
    "usajobs_historic": "USAJOBS 2210 · US Federal",
}
ORIGINS = {"source_tags": "Nhãn kỹ năng từ nguồn", "extracted_from_jd": "Trích xuất từ mô tả công việc"}
PAGES = ["Tổng quan", "Thống kê kỹ năng", "So sánh nghề", "Dự báo kỹ năng ML"]
PALETTE = ["#13786D", "#46A69A", "#88BEB4", "#BF8C42", "#708CA4"]


def number(value):
    return f"{int(value):,}".replace(",", ".")


def chart(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": "#193630", "size": 13},
        margin={"l": 10, "r": 15, "t": 18, "b": 10}, height=350,
        legend_title_text="", hoverlabel={"bgcolor": "white"},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E2EAE6", zeroline=False)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def export_table(frame, name):
    st.dataframe(frame, width="stretch", hide_index=True)
    st.download_button("Tải bảng CSV", frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{name}.csv", mime="text/csv", key=f"download_{name}")


def main():
    st.set_page_config(page_title="JobScope · Phân tích & Dự báo Kỹ năng IT", page_icon="◈", layout="wide")
    st.markdown("""<style>
    .block-container {padding-top:3rem; padding-bottom:3rem; max-width:1450px;}
    [data-testid="stMetric"] {background:white; border:1px solid #dce7e2;
       border-radius:12px; padding:18px 22px; min-height:110px;}
    [data-testid="stMetricValue"] {font-weight:650;}
    .eyebrow {font-size:12px; letter-spacing:2px; color:#13786d; font-weight:700;}
    .hero {font-size:36px; line-height:1.15; font-weight:750; letter-spacing:-0.5px; margin:6px 0;}
    .subtitle {color:#577069; font-size:15px; margin-bottom:20px;}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">JOBSCOPE · BIG DATA & MACHINE LEARNING ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero">Thị trường IT: Phân tích & Dự báo Kỹ năng</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Thống kê nhu cầu kỹ năng thực tế và dự phóng xu hướng công nghệ 2–3 năm tới bằng Machine Learning.</div>', unsafe_allow_html=True)

    try:
        catalog = load_catalog()
        with st.sidebar:
            st.markdown("## ◈ JobScope")
            st.caption("IT JOB & SKILL ANALYTICS")
            st.divider()
            dataset = st.selectbox("Bộ dữ liệu (Dataset)", list(catalog),
                                   format_func=lambda x: catalog[x]["label"], key="dataset")
        backend = os.environ.get("JOB_GOLD_BACKEND", "parquet").lower()
        if backend == "mongo" and dataset == "legacy_2023":
            from src.serving.mongo_gold import load_gold_mongo
            run = load_gold_mongo(audit_path=os.environ.get("JOB_ANALYTICS_AUDIT"),
                                  db_name=os.environ.get("JOB_MONGO_DB", "jobscope"))
        elif backend in {"parquet", "mongo"}:
            backend = "parquet"
            run = load_gold(dataset=dataset)
        else:
            raise GoldError("JOB_GOLD_BACKEND must be parquet or mongo")
    except GoldError as exc:
        st.error("Không thể mở dữ liệu Gold đã xác minh.")
        st.code(str(exc), language=None)
        st.stop()

    meta = run.manifest
    tables = {name: frame if "market" in frame else frame.assign(market="GLOBAL")
              for name, frame in run.tables.items()}
    market = tables["market_stats"]

    with st.sidebar:
        st.markdown("#### Bộ lọc phạm vi")
        markets = sorted(market.market.unique(), key=lambda x: (x != "GLOBAL", x))
        selected_market = st.selectbox("Thị trường", markets, key="market")
        sources = sorted(market.loc[market.market.eq(selected_market), "source"].unique(),
                         key=lambda x: (x != "kaggle_historical_archive", x))
        source = st.selectbox("Nguồn tuyển dụng", sources, format_func=lambda x: SOURCES.get(x, x), key="source")
        available_months = sorted(market.loc[market.market.eq(selected_market) &
                                             market.source.eq(source), "month"].unique())
        month_key = f"months_{source}" if dataset == "legacy_2023" else f"months_{dataset}_{selected_market}_{source}"
        months = st.multiselect("Tháng quan sát", available_months, default=available_months, key=month_key)
        occ_table = tables["occupation_stats"]
        available_occ = sorted(occ_table.loc[occ_table.market.eq(selected_market) &
                                             occ_table.source.eq(source) &
                                             occ_table.month.isin(months), "occupation"].unique())
        occupations = st.multiselect("Nhóm nghề", available_occ, default=available_occ,
                                     key=f"occupations_{dataset}_{selected_market}_{source}")
        st.divider()
        st.metric("Tổng tin tuyển dụng", number(meta['input']['silver_rows']))

    page = st.radio("Chuyên mục", PAGES, horizontal=True, label_visibility="collapsed", key="page")
    st.divider()

    occ = select_scope(tables["occupation_stats"], source, months, occupations, market=selected_market)
    evidence = select_scope(tables["skill_evidence_stats"], source, months, occupations, market=selected_market)
    skills = select_scope(tables["skill_stats"], source, months, occupations, market=selected_market)
    n = int(occ.job_count.sum())

    if n == 0:
        st.info("Không có quan sát trong phạm vi này. Hãy chọn lại tháng hoặc nhóm nghề ở thanh bên.")
        if page != PAGES[3]:
            st.stop()

    if page == PAGES[0]:
        # TRANG 1: TỔNG QUAN
        evidence_n = int(evidence.skill_evidence_jobs.sum())
        columns = st.columns(4)
        columns[0].metric("Tin tuyển dụng", number(n))
        columns[1].metric("Tin có kỹ năng", number(evidence_n))
        columns[2].metric("Tỷ lệ có kỹ năng", f"{evidence_n/n:.1%}" if n else "—")
        columns[3].metric("Tháng quan sát", str(occ.month.nunique()))

        occupation_totals = occ.groupby("occupation", as_index=False).job_count.sum().sort_values("job_count", ascending=False)
        occupation_totals["share_in_selected_scope"] = occupation_totals.job_count / n

        left, right = st.columns([1.2, 1])
        with left:
            st.subheader("Phân bố tuyển dụng theo nhóm nghề")
            chart(px.bar(occupation_totals.sort_values("job_count"), x="job_count", y="occupation",
                         orientation="h", color_discrete_sequence=PALETTE,
                         labels={"occupation": "", "job_count": "Số tin"}))
        with right:
            st.subheader("Xu hướng tuyển dụng theo thời gian")
            monthly = occ.groupby("month", as_index=False).job_count.sum()
            calendar = pd.DataFrame({"month": pd.period_range(available_months[0], available_months[-1], freq="M").astype(str)})
            monthly = calendar.merge(monthly, on="month", how="left")
            fig = px.line(monthly, x="month", y="job_count", markers=True, color_discrete_sequence=PALETTE,
                          labels={"month": "Tháng", "job_count": "Số tin"})
            fig.update_traces(connectgaps=False, line_width=3)
            chart(fig)

        st.subheader("Bảng phân bố chi tiết các nhóm nghề")
        export_table(occupation_totals, "occupation_summary")

    elif page == PAGES[1]:
        # TRANG 2: THỐNG KÊ KỸ NĂNG TRONG NĂM
        origins = sorted(skills.skills_origin.unique())
        if not origins:
            st.info("Phạm vi này có tin tuyển dụng nhưng chưa có dữ liệu kỹ năng.")
            st.stop()

        if len(origins) > 1:
            origin = st.selectbox("Chứng cứ kỹ năng", origins, format_func=lambda x: ORIGINS.get(x, x), key=f"origin_{source}")
        else:
            origin = origins[0]

        filtered_skills = skills.loc[skills.skills_origin.eq(origin)]
        summary = summarize_skills(filtered_skills, occ)

        choices = sorted(summary.occupation.unique())
        default_idx = choices.index("Data Engineer") if "Data Engineer" in choices else 0
        occupation = st.selectbox("Nhóm nghề phân tích", choices, index=default_idx, key=f"focus_{source}_{origin}")
        focus = summary.loc[summary.occupation.eq(occupation)]

        skill = st.selectbox("Kỹ năng", focus.skill.tolist(), key=f"skill_{source}_{origin}_{occupation}")
        selected = focus.loc[focus.skill.eq(skill)].iloc[0]

        cols = st.columns(3)
        cols[0].metric("Tỷ lệ tin yêu cầu kỹ năng", f"{selected.demand_rate:.2%}")
        cols[1].metric("Số tin yêu cầu kỹ năng này", number(selected.skill_job_count))
        cols[2].metric("Tổng số tin của nhóm nghề", number(selected.denominator_jobs))

        left, right = st.columns([1, 1.25])
        with left:
            st.subheader(f"Top kỹ năng phổ biến nhất · {occupation}")
            chart(px.bar(focus.head(12).sort_values("demand_rate"), x="demand_rate", y="skill", orientation="h",
                         color_discrete_sequence=PALETTE, hover_data=["skill_job_count", "denominator_jobs"],
                         labels={"demand_rate": "Tỷ lệ", "skill": ""}))
        with right:
            st.subheader(f"Xu hướng xuất hiện qua các tháng · {skill}")
            trend = select_scope(tables["skill_trends"], source, months, [occupation], origin,
                                 market=selected_market)
            trend = trend.loc[trend.skill.eq(skill)]
            timeline = trend_calendar(trend, available_months[0], available_months[-1])
            fig = px.line(timeline, x="month", y="demand_rate", markers=True, color_discrete_sequence=PALETTE,
                          hover_data=["skill_job_count", "occupation_job_count"], labels={"month": "Tháng", "demand_rate": "Tỷ lệ"})
            fig.update_traces(connectgaps=False, line_width=3)
            fig.update_yaxes(tickformat=".0%")
            chart(fig)

        st.subheader("Bảng dữ liệu kỹ năng theo tháng")
        export_table(timeline[["month", "skill_job_count", "occupation_job_count", "demand_rate", "observed_delta_pp"]], "skill_monthly_trend")

    elif page == PAGES[2]:
        # TRANG 3: SO SÁNH NGHỀ
        origins = sorted(skills.skills_origin.unique())
        if not origins:
            st.info("Phạm vi này chưa có dữ liệu kỹ năng.")
            st.stop()
        origin = origins[0] if len(origins) == 1 else st.selectbox("Chứng cứ kỹ năng", origins, format_func=lambda x: ORIGINS.get(x, x), key=f"origin_comp_{source}")
        filtered_skills = skills.loc[skills.skills_origin.eq(origin)]
        summary = summarize_skills(filtered_skills, occ)

        choices = sorted(summary.occupation.unique())
        compared = st.multiselect("Chọn các nhóm nghề muốn so sánh", choices, default=choices[:2], key=f"compare_{source}")
        compared_data = summary.loc[summary.occupation.isin(compared)].copy()

        if compared_data.empty:
            st.info("Hãy chọn ít nhất một nhóm nghề có dữ liệu kỹ năng.")
            st.stop()

        top = compared_data.groupby("skill").skill_job_count.sum().nlargest(10).index
        compared_data = compared_data.loc[compared_data.skill.isin(top)]

        st.subheader("So sánh tỷ lệ yêu cầu kỹ năng giữa các nhóm nghề")
        chart(px.bar(compared_data, x="skill", y="demand_rate", color="occupation", barmode="group",
                     color_discrete_sequence=PALETTE, hover_data=["skill_job_count", "denominator_jobs"],
                     labels={"demand_rate": "Tỷ lệ yêu cầu", "skill": "Kỹ năng", "occupation": "Nhóm nghề"}))
        export_table(compared_data, "occupation_skill_comparison")

    else:
        # TRANG 4: DỰ BÁO KỸ NĂNG BẰNG MACHINE LEARNING (2026 ➔ 2029)
        my_preds, my_metrics = load_multi_year_forecast()

        if my_preds is not None and my_metrics is not None:
            st.subheader("Dự báo Xu hướng Nhu cầu Kỹ năng CNTT trong 2–3 Năm Tới (2026 ➔ 2029)")
            st.caption(
                "Mô hình **Gradient Boosting Time-Series Forecaster** được huấn luyện trên **tập dữ liệu gộp chung qua các năm (2023 đến 2026)** "
                "với gần 800.000 tin tuyển dụng thực tế, nhằm dự phóng xu hướng dịch chuyển kỹ năng công nghệ trong 2 đến 3 năm tới tính từ hiện tại."
            )

            cols = st.columns(4)
            cols[0].metric("Giai đoạn dự báo", "2027 – 2029 (2–3 năm tới)")
            cols[1].metric("Độ chính xác xu hướng", f"{my_metrics['directional_accuracy']:.1%}")
            cols[2].metric("Sai số tuyệt đối (MAE)", f"{my_metrics['backtest_mae']:.2%}")
            cols[3].metric("Hệ số xác định (R²)", f"{my_metrics['backtest_r2']:.4f}")

            dist = my_metrics.get("trend_distribution", {})
            st.info(
                f"📊 **Tổng quan xu hướng 3 năm tới:** Có **{dist.get('Growing', 0)} kỹ năng Tăng trưởng mạnh (Growing 🚀)**, "
                f"**{dist.get('Stable', 0)} kỹ năng Ổn định (Stable ⚖️)**, và "
                f"**{dist.get('Declining', 0)} kỹ năng Giảm nhu cầu (Declining 📉)**."
            )

            st.divider()
            st.markdown("#### 🎯 Tra cứu Dự báo Xu hướng theo Nghề & Kỹ năng (2026 ➔ 2029)")
            c1, c2 = st.columns(2)
            occ_choices = sorted(my_preds["occupation"].unique())
            pred_occ = c1.selectbox("Nhóm nghề CNTT", occ_choices, key="multi_pred_occ")
            occ_slice = my_preds[my_preds["occupation"] == pred_occ]
            skill_choices = sorted(occ_slice["skill"].unique())
            pred_skill = c2.selectbox("Kỹ năng", skill_choices, key="multi_pred_skill")

            sel_row = occ_slice[occ_slice["skill"] == pred_skill]
            if not sel_row.empty:
                s = sel_row.iloc[0]
                trend_lbl = s["trend_label"]
                delta_3y = s["delta_3y"]
                conf = s["confidence_score"]

                lbl_color = "#13786D" if trend_lbl == "Growing" else ("#BF8C42" if trend_lbl == "Stable" else "#D9534F")
                badge_icon = "🚀" if trend_lbl == "Growing" else ("⚖️" if trend_lbl == "Stable" else "📉")

                kpi_cols = st.columns(5)
                kpi_cols[0].metric("Hiện tại (2026)", f"{s['rate_2026']:.1%}")
                kpi_cols[1].metric("Dự báo 2027 (+1 năm)", f"{s['rate_2027_pred']:.1%}")
                kpi_cols[2].metric("Dự báo 2028 (+2 năm)", f"{s['rate_2028_pred']:.1%}")
                kpi_cols[3].metric("Dự báo 2029 (+3 năm)", f"{s['rate_2029_pred']:.1%}")
                kpi_cols[4].metric("Xu hướng 3 năm", f"{badge_icon} {trend_lbl}", f"{delta_3y:+.1%}")

                st.subheader("Biểu đồ Chuỗi Thời gian: Thực tế Quan sát & Đường Phóng Dự báo (2023 ➔ 2029)")
                timeline_df = pd.DataFrame([
                    {"Năm": "2023", "Tỷ lệ nhu cầu": s["rate_2023"], "Giai đoạn": "Thực tế lịch sử"},
                    {"Năm": "2024", "Tỷ lệ nhu cầu": s["rate_2024"], "Giai đoạn": "Thực tế lịch sử"},
                    {"Năm": "2025", "Tỷ lệ nhu cầu": s["rate_2025"], "Giai đoạn": "Thực tế lịch sử"},
                    {"Năm": "2026", "Tỷ lệ nhu cầu": s["rate_2026"], "Giai đoạn": "Hiện tại (Baseline)"},
                    {"Năm": "2027", "Tỷ lệ nhu cầu": s["rate_2027_pred"], "Giai đoạn": f"Dự báo ({trend_lbl})"},
                    {"Năm": "2028", "Tỷ lệ nhu cầu": s["rate_2028_pred"], "Giai đoạn": f"Dự báo ({trend_lbl})"},
                    {"Năm": "2029", "Tỷ lệ nhu cầu": s["rate_2029_pred"], "Giai đoạn": f"Dự báo ({trend_lbl})"},
                ])

                fig_multi = px.line(
                    timeline_df, x="Năm", y="Tỷ lệ nhu cầu", color="Giai đoạn", markers=True,
                    color_discrete_map={
                        "Thực tế lịch sử": "#46A69A",
                        "Hiện tại (Baseline)": "#13786D",
                        f"Dự báo ({trend_lbl})": lbl_color,
                    },
                    labels={"Tỷ lệ nhu cầu": "Tỷ lệ việc làm yêu cầu", "Năm": "Năm quan sát / Dự báo"}
                )
                fig_multi.update_traces(line_width=3.5, marker=dict(size=8))
                fig_multi.update_yaxes(tickformat=".1%")
                chart(fig_multi)

            st.subheader(f"Top Kỹ năng Bứt phá Mạnh nhất 2026 ➔ 2029 · {pred_occ}")
            top_grow = occ_slice.sort_values("delta_3y", ascending=False).head(10).copy()
            fig_bar = px.bar(
                top_grow.sort_values("delta_3y"),
                x="delta_3y", y="skill", orientation="h",
                color="delta_3y", color_continuous_scale="Teal",
                labels={"delta_3y": "Tăng trưởng dự kiến sau 3 năm (điểm %)", "skill": "Kỹ năng"},
                hover_data=["rate_2026", "rate_2029_pred"]
            )
            fig_bar.update_xaxes(tickformat="+.1%")
            chart(fig_bar)

            st.subheader("Bảng Dự báo Chi tiết Tất cả Kỹ năng (2023 ➔ 2029)")
            display_cols = ["occupation", "skill", "rate_2023", "rate_2026", "rate_2027_pred", "rate_2028_pred", "rate_2029_pred", "delta_3y", "trend_label", "confidence_score"]
            st.dataframe(occ_slice[display_cols], width="stretch", hide_index=True)
            export_table(my_preds[display_cols], "it_skill_trend_forecast_2026_2029")
        else:
            st.info("Chưa tìm thấy tệp kết quả dự báo đa năm. Chạy python -m src.ml.multi_year_forecast để tạo artifacts.")

    st.divider()
    st.caption("JobScope · Hệ thống Phân tích & Dự báo Xu hướng Kỹ năng CNTT | Big Data & Machine Learning")


if __name__ == "__main__":
    main()
