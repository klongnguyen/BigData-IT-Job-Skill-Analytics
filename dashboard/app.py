"""Run with: python -m streamlit run dashboard/app.py."""

from pathlib import Path
import os
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.data import GoldError, load_gold, select_scope, summarize_skills, trend_calendar


SOURCES = {
    "kaggle_historical_archive": "Archive · 2023",
    "arbeitnow": "Arbeitnow · snapshot 2026",
    "remotive": "Remotive · snapshot 2026",
}
ORIGINS = {"source_tags": "Nhãn kỹ năng từ nguồn", "extracted_from_jd": "Trích xuất từ mô tả công việc"}
PAGES = ["Tổng quan", "Nhóm nghề", "Kỹ năng & xu hướng", "So sánh nghề", "Dự báo & bằng chứng", "Dữ liệu 2026"]
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
    st.set_page_config(page_title="JobScope · IT Job Analytics", page_icon="◈", layout="wide")
    st.markdown("""<style>
    .block-container {padding-top:4rem; padding-bottom:3rem; max-width:1500px;}
    [data-testid="stMetric"] {background:white; border:1px solid #dce7e2;
       border-radius:12px; padding:18px 22px; min-height:116px;}
    [data-testid="stMetricValue"] {font-weight:650;}
    .eyebrow {font-size:12px; letter-spacing:2px; color:#13786d; font-weight:700;}
    .hero {font-size:38px; line-height:1.15; font-weight:750; letter-spacing:-1px; margin:8px 0;}
    .subtitle {color:#577069; font-size:16px; margin-bottom:24px;}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">JOBSCOPE / GLOBAL IT MARKET</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero">Thị trường IT, nhìn từ dữ liệu.</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Khám phá nhóm nghề, kỹ năng và xu hướng trong các nguồn tuyển dụng đã thu thập.</div>', unsafe_allow_html=True)
    try:
        backend = os.environ.get("JOB_GOLD_BACKEND", "parquet").lower()
        if backend == "mongo":
            from src.serving.mongo_gold import load_gold_mongo
            run = load_gold_mongo(audit_path=os.environ.get("JOB_ANALYTICS_AUDIT"),
                                  db_name=os.environ.get("JOB_MONGO_DB", "jobscope"))
        elif backend == "parquet":
            run = load_gold(audit_path=os.environ.get("JOB_ANALYTICS_AUDIT"))
        else:
            raise GoldError("JOB_GOLD_BACKEND must be parquet or mongo")
    except GoldError as exc:
        st.error("Không thể mở dữ liệu Gold đã xác minh.")
        st.code(str(exc), language=None)
        st.info("Khôi phục run Gold được tham chiếu trong docs/data/phase03_analytics_audit.json "
                "theo backend đã chọn. Xem docs/planning/dashboard_runbook.md.")
        st.stop()

    meta, tables = run.manifest, run.tables
    market = tables["market_stats"]
    with st.sidebar:
        st.markdown("## ◈ JobScope")
        st.caption("IT JOB & SKILL ANALYTICS")
        st.divider()
        st.markdown("#### Phạm vi phân tích")
        sources = sorted(market.source.unique(), key=lambda x: (x != "kaggle_historical_archive", x))
        source = st.selectbox("Nguồn dữ liệu", sources, format_func=lambda x: SOURCES.get(x, x), key="source")
        available_months = sorted(market.loc[market.source.eq(source), "month"].unique())
        months = st.multiselect("Tháng quan sát", available_months, default=available_months, key=f"months_{source}")
        available_occ = sorted(tables["occupation_stats"].loc[tables["occupation_stats"].source.eq(source), "occupation"].unique())
        occupations = st.multiselect("Nhóm nghề trong phạm vi", available_occ, default=available_occ, key=f"occupations_{source}")
        st.divider()
        st.caption("DỮ LIỆU ĐÃ XÁC MINH")
        st.write(f"{number(meta['input']['silver_rows'])} tin trong toàn bộ run")
        st.caption(f"Xử lý: {meta['completed_at']} · Taxonomy {meta['taxonomy_version']}")
        st.caption(f"Gold {backend.upper()} · chỉ đọc · SHA-256 đã đối chiếu")
        with st.expander("Run ID"):
            st.code(meta["run_id"], language=None)

    page = st.radio("Chuyên mục", PAGES, horizontal=True, label_visibility="collapsed", key="page")
    st.divider()
    st.caption(f"NGUỒN: {SOURCES.get(source, source)} · {len(months)} tháng được chọn · "
               f"{len(occupations)} nhóm nghề · Chỉ mô tả mẫu thu thập, không đại diện toàn thị trường.")
    if source != "kaggle_historical_archive" and page != PAGES[5]:
        st.warning("Snapshot API có phạm vi giới hạn (partial/scoped). Số mẫu nhỏ và coverage thay đổi; "
                   "không so sánh trực tiếp số tin với archive 2023.")
    occ = select_scope(tables["occupation_stats"], source, months, occupations)
    evidence = select_scope(tables["skill_evidence_stats"], source, months, occupations)
    skills = select_scope(tables["skill_stats"], source, months, occupations)
    n = int(occ.job_count.sum())
    if n == 0:
        st.info("Không có quan sát trong phạm vi này. Hãy chọn lại tháng hoặc nhóm nghề ở thanh bên.")
        if page not in PAGES[4:]:
            st.stop()

    if page == PAGES[5]:
        st.subheader("Dữ liệu mới năm 2026 · kiểm kê Bronze")
        audit = json.loads((ROOT / "docs/data/2026_ingestion_audit.json").read_text(encoding="utf-8"))
        rows = pd.DataFrame(audit["source_month_counts"])
        counts = rows.groupby(["market", "source"], as_index=False).jobs.sum()
        cols = st.columns(3)
        cols[0].metric("ID nguồn duy nhất", number(audit["unique_source_records"]))
        cols[1].metric("Run Bronze đã audit", str(len(audit["input_runs"])))
        cols[2].metric("Title chưa khớp 8 nhóm", number(audit["title_classification"]["unclassified_title_jobs"]))
        st.warning("Đây là bản ghi Bronze theo phạm vi từng nguồn. Chưa xác nhận toàn bộ là việc làm IT; "
                   "chưa đưa vào Silver/Gold hay cổng dự báo. US_FEDERAL là thị trường liên bang Mỹ riêng.")
        selected = st.selectbox("Nguồn Bronze", sorted(rows.source.unique()), key="bronze_source")
        scoped = rows.loc[rows.source.eq(selected)].sort_values("month")
        st.caption(f"{selected} · {scoped.market.iloc[0]} · các tháng không có trong bảng là chưa quan sát, không phải 0 tin.")
        chart(px.bar(scoped, x="month", y="jobs", color="market", color_discrete_sequence=PALETTE,
                     labels={"month": "Tháng đăng", "jobs": "Bản ghi nguồn"}))
        st.dataframe(counts, width="stretch", hide_index=True)
        st.caption("Arbeitnow/Remotive là snapshot; 10/2026 và dữ liệu đến 15/10 là kỳ chưa kết thúc. "
                   "91,7% tiêu đề của đợt mới chưa khớp taxonomy v0.1. Xem báo cáo 2026 để biết độ phủ và điều khoản nguồn.")
        st.stop()

    if page in PAGES[:2]:
        evidence_n = int(evidence.skill_evidence_jobs.sum())
        columns = st.columns(4)
        columns[0].metric("Tin tuyển dụng", number(n))
        columns[1].metric("Tin có kỹ năng", number(evidence_n))
        columns[2].metric("Coverage kỹ năng", f"{evidence_n/n:.1%}" if n else "—")
        columns[3].metric("Tháng có quan sát", str(occ.month.nunique()))
        st.caption(f"Coverage = {number(evidence_n)} / n={number(n)} tin trong phạm vi. "
                   "Độ phủ kỹ năng không phải độ chính xác trích xuất. Dedup: một bản ghi cho mỗi job_id.")
        occupation_totals = occ.groupby("occupation", as_index=False).job_count.sum().sort_values("job_count", ascending=False)
        occupation_totals["share_in_selected_scope"] = occupation_totals.job_count / n
        left, right = st.columns([1.25, 1])
        with left:
            st.subheader("Nhóm nghề được tuyển dụng")
            st.caption("Số tin trong nguồn và các tháng đã chọn")
            chart(px.bar(occupation_totals.sort_values("job_count"), x="job_count", y="occupation",
                         orientation="h", color_discrete_sequence=PALETTE,
                         labels={"occupation": "", "job_count": "Số tin"}))
        with right:
            st.subheader("Tuyển dụng theo tháng")
            st.caption("Tháng thiếu hoặc bỏ chọn giữ khoảng trống")
            monthly = occ.groupby("month", as_index=False).job_count.sum()
            calendar = pd.DataFrame({"month": pd.period_range(available_months[0], available_months[-1], freq="M").astype(str)})
            monthly = calendar.merge(monthly, on="month", how="left")
            fig = px.line(monthly, x="month", y="job_count", markers=True, color_discrete_sequence=PALETTE,
                          labels={"month": "Tháng", "job_count": "Số tin"})
            fig.update_traces(connectgaps=False, line_width=3)
            chart(fig)
        if page == PAGES[1]:
            st.subheader("Phân bố nghề trong phạm vi đã chọn")
            source_n = int(select_scope(market, source, months).job_count.sum())
            occupation_totals["source_jobs_in_selected_months"] = source_n
            occupation_totals["share_in_source"] = occupation_totals.job_count / source_n
            export_table(occupation_totals, "occupation_summary")
            st.caption("share_in_source dùng toàn bộ số tin của nguồn ở các tháng đã chọn làm mẫu số; "
                       "share_in_selected_scope chỉ dùng các nghề đã chọn.")
        else:
            st.info("Archive đo kỹ năng qua source tags; API đo qua mô tả công việc. "
                    "Mở Kỹ năng & xu hướng để xem từng nghề với mẫu số cụ thể.")
            with st.expander("Chất lượng và giới hạn dữ liệu"):
                st.write("Experience chưa đủ dữ liệu; chưa có phân bố quốc gia đã được kiểm định. "
                         "Không cộng số công ty duy nhất từng tháng để suy ra số công ty duy nhất cả kỳ.")
                export_table(select_scope(market, source, months), "source_month_quality")
                st.caption("Bảng này mô tả toàn nguồn theo tháng, không lọc theo nghề. "
                           "known_country_jobs chỉ là số tin có giá trị country, chưa xác minh độ đúng địa lý.")

    elif page in (PAGES[2], PAGES[3]):
        origins = sorted(skills.skills_origin.unique())
        if not origins:
            st.info("Phạm vi này có tin tuyển dụng nhưng chưa có quan sát kỹ năng chuẩn hóa.")
            st.stop()
        origin = st.selectbox("Chứng cứ kỹ năng", origins, format_func=lambda x: ORIGINS.get(x, x), key=f"origin_{source}")
        skills = skills.loc[skills.skills_origin.eq(origin)]
        summary = summarize_skills(skills, occ)
        st.caption(f"Chế độ đo: {origin} · taxonomy {meta['taxonomy_version']} · "
                   "Tỷ lệ = tổng tin có kỹ năng / tổng tin của nghề; gồm cả tin thiếu kỹ năng trong mẫu số.")
        if page == PAGES[3]:
            choices = sorted(summary.occupation.unique())
            compared = st.multiselect("Nghề muốn so sánh", choices, default=choices[:2], key=f"compare_{source}")
            compared_data = summary.loc[summary.occupation.isin(compared)].copy()
            if compared_data.empty:
                st.info("Chọn ít nhất một nghề có dữ liệu kỹ năng để so sánh.")
                st.stop()
            top = compared_data.groupby("skill").skill_job_count.sum().nlargest(10).index
            compared_data = compared_data.loc[compared_data.skill.isin(top)]
            st.subheader("Cùng nguồn, khác nhóm nghề")
            st.caption("Mỗi nghề có mẫu số riêng; ô không có chứng cứ giữ trống.")
            chart(px.bar(compared_data, x="skill", y="demand_rate", color="occupation", barmode="group",
                         color_discrete_sequence=PALETTE, hover_data=["skill_job_count", "denominator_jobs"],
                         labels={"demand_rate": "Tỷ lệ", "skill": "Kỹ năng", "occupation": "Nghề"}))
            export_table(compared_data, "occupation_skill_comparison")
        else:
            choices = sorted(summary.occupation.unique())
            occupation = st.selectbox("Nghề phân tích", choices, index=choices.index("Data Engineer") if "Data Engineer" in choices else 0,
                                      key=f"focus_{source}_{origin}")
            focus = summary.loc[summary.occupation.eq(occupation)]
            skill = st.selectbox("Kỹ năng", focus.skill.tolist(), key=f"skill_{source}_{origin}_{occupation}")
            selected = focus.loc[focus.skill.eq(skill)].iloc[0]
            cols = st.columns(3)
            cols[0].metric("Tỷ lệ tin có kỹ năng", f"{selected.demand_rate:.2%}")
            cols[1].metric("Tin có kỹ năng này", number(selected.skill_job_count))
            cols[2].metric("Mẫu số · tin của nghề", number(selected.denominator_jobs))
            st.caption(f"{source} · {occupation} · {skill} · tháng: {', '.join(months)}")
            left, right = st.columns([1, 1.25])
            with left:
                st.subheader("Kỹ năng nổi bật của nghề")
                chart(px.bar(focus.head(12).sort_values("demand_rate"), x="demand_rate", y="skill", orientation="h",
                             color_discrete_sequence=PALETTE, hover_data=["skill_job_count", "denominator_jobs"],
                             labels={"demand_rate": "Tỷ lệ", "skill": ""}))
            with right:
                st.subheader("Xu hướng đã quan sát")
                trend = select_scope(tables["skill_trends"], source, months, [occupation], origin)
                trend = trend.loc[trend.skill.eq(skill)]
                timeline = trend_calendar(trend, available_months[0], available_months[-1])
                fig = px.line(timeline, x="month", y="demand_rate", markers=True, color_discrete_sequence=PALETTE,
                              hover_data=["skill_job_count", "occupation_job_count"], labels={"month": "Tháng", "demand_rate": "Tỷ lệ"})
                fig.update_traces(connectgaps=False, line_width=3)
                fig.update_yaxes(tickformat=".0%")
                chart(fig)
            st.caption("Điểm 0 = có quan sát nhưng không thấy kỹ năng. Khoảng trống = không có quan sát hoặc tháng bị bỏ chọn. "
                       "observed_delta_pp chỉ có khi hai tháng quan sát liền nhau; có thể tham chiếu tháng trước ngoài bộ lọc.")
            export_table(timeline[["month", "skill_job_count", "occupation_job_count", "demand_rate", "observed_delta_pp"]], "observed_skill_trend")

    else:
        gate = meta["predictive_gate"]
        st.subheader("Dự báo: chưa đủ bằng chứng")
        st.warning(f"{gate['decision']} · {gate.get('predictive_claims', 'Insufficient evidence')}")
        st.write("Dashboard hiện chỉ phục vụ phân tích đã quan sát. Chưa có mô hình đã được đánh giá "
                 "hoặc kỳ dự báo được phát hành; không có nhãn Growing / Stable / Declining để công bố.")
        missing = gate.get("missing_months_between_first_and_last", [])
        cols = st.columns(3)
        cols[0].metric("Tháng thiếu trong toàn run", str(len(missing)))
        cols[1].metric("Tháng cuối của nguồn đang chọn", available_months[-1])
        cols[2].metric("Tin trong bộ lọc", number(n))
        st.caption("Quyết định gate dưới đây áp dụng toàn bộ run, không được xét lại khi thay bộ lọc.")
        st.dataframe(pd.DataFrame(gate.get("checks", [])), width="stretch", hide_index=True)
        with st.expander("Các tháng chưa có quan sát"):
            st.write(", ".join(missing) or "Không có tháng thiếu được khai báo.")
        st.markdown("#### Để đi tiếp")
        st.write("Bổ sung chuỗi dữ liệu thật liên tục và có thể so sánh; kiểm định taxonomy trên nhãn độc lập; "
                 "đánh giá rolling-origin trên dữ liệu tương lai trước khi xét lại cổng dự báo.")
        st.info("M2: cổng kỹ thuật HDFS → Spark đã đạt; ETL Silver từ HDFS và nghiệm thu toàn mốc còn mở. "
                "M8/M9: Parquet serving và demo local đã chạy; nghiệm thu tích hợp còn mở.")

    st.divider()
    st.caption(f"Gold run {meta['run_id']} · Hoàn tất {meta['completed_at']} · Taxonomy {meta['taxonomy_version']}")
    with st.expander("Nguồn gốc & kiểm chứng"):
        st.code(f"Manifest SHA-256: {run.manifest_sha256}", language=None)
        st.write("Đã kiểm tra manifest, checksum từng bảng và số dòng khi tải. Dedup: một bản ghi / job_id.")
        st.dataframe(pd.DataFrame([{"table": k, "rows": len(v)} for k, v in tables.items()]), hide_index=True)
        st.caption("Quyền sử dụng archive và đánh giá taxonomy còn cần hoàn thiện trước công bố. "
                   "Đây là bản demo local cho đồ án.")


if __name__ == "__main__":
    main()
