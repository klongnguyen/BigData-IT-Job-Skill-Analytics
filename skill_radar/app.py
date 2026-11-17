"""Skill Radar dashboard.   python -m streamlit run skill_radar/app.py --server.port 8502"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from skill_radar.ui import data, interact, theme
from skill_radar.ui.pages import ecosystem, forecast, navigator, overview, profile, trends

PAGES = {
    "Tổng quan": (overview, "Bức tranh toàn thị trường"),
    "Xu hướng": (trends, "So sánh kỹ năng theo thời gian"),
    "Hồ sơ kỹ năng": (profile, "Mọi góc nhìn về một kỹ năng"),
    "Hệ sinh thái": (ecosystem, "Kỹ năng nào đi cùng nhau"),
    "Skill Navigator": (navigator, "Độ phủ kỹ năng của bạn"),
    "Dự báo & độ tin cậy": (forecast, "Dự báo và độ chính xác"),
}


def main():
    st.set_page_config(page_title="Skill Radar · Kỹ năng CNTT", page_icon="◈", layout="wide")
    st.markdown(theme.CSS, unsafe_allow_html=True)
    if not data.is_ready():
        st.markdown('<div class="hero">Skill Radar</div>', unsafe_allow_html=True)
        st.info("Chưa có dữ liệu. Chạy `python -m skill_radar.process.hn_postings` rồi `python -m skill_radar.pipeline`.")
        return
    g = data.load()
    with st.sidebar:
        st.markdown("### ◈ Skill Radar")
        names = list(PAGES)
        if "page" not in st.session_state and st.query_params.get("page") in names:
            st.session_state["page"] = st.query_params["page"]          # deep link: ?page=Xu hướng
        page = st.radio("Chuyên mục", names, key="page", label_visibility="collapsed", captions=[v[1] for v in PAGES.values()])
        st.query_params["page"] = page
        st.divider()
        f = g["facts"]
        st.caption(f"**Nguồn:** Hacker News, Ask HN: Who is hiring\n\n**Giai đoạn:** {f['first_quarter']} – {f['last_quarter']}\n\n"
                   f"**Tin phân tích:** {f['postings']:,}".replace(",", "."))
        st.caption("Dữ liệu lưu trong SQLite (`gold.db`).")
    st.markdown(f'<div class="hero">{page}</div><div class="subtitle">{PAGES[page][1]} · nhu cầu kỹ năng CNTT từ tin tuyển dụng, 2015–nay</div>', unsafe_allow_html=True)
    PAGES[page][0].render(g)
    if interact.focus():                      # drawn after the page so it shows the skill picked in this very run
        with st.sidebar:
            st.divider()
            st.caption(f"**Đang chọn:** {g['label'][interact.focus()]}")
            st.button("Bỏ chọn", on_click=interact.clear_focus, width="stretch")


if __name__ == "__main__":
    main()
