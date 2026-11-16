"""Click-to-select on charts and cross-highlighting between pages (Power BI-style).

* ``clickable`` draws a chart whose points can be clicked; it returns the skill id of the clicked point.
  Streamlit keeps the selection, and Plotly dims the unselected points (cross-highlight inside the chart).
* The last clicked skill is stored as the *focus skill*: other charts emphasise it, the sidebar shows it and
  the profile page opens on it. ``clear_focus`` resets the focus and every chart selection.
"""

import streamlit as st

from skill_radar.ui import theme

FOCUS = "focus_skill"
NONCE = "chart_nonce"


def focus():
    return st.session_state.get(FOCUS)


def clear_focus():
    st.session_state.pop(FOCUS, None)
    st.session_state[NONCE] = st.session_state.get(NONCE, 0) + 1       # new chart keys -> selections are forgotten


def clickable(fig, key, ids):
    """Draw ``fig`` with click selection. ``ids`` maps curve number -> list of skill ids (by point index).

    Returns the selected skill id or None.
    """
    event = st.plotly_chart(theme.lock(fig), width="stretch", theme=None, config=theme.CONFIG, key=f"{key}_{st.session_state.get(NONCE, 0)}",
                            on_select="rerun", selection_mode="points")
    points = []
    try:
        points = list(event["selection"]["points"])
    except (KeyError, TypeError):
        pass
    for p in points:
        curve = p.get("curve_number", 0)
        index = p.get("point_index", p.get("point_number"))
        row = ids.get(curve)
        if row is not None and index is not None and 0 <= index < len(row):
            st.session_state[FOCUS] = row[index]
            return row[index]
    return None


def go_to_profile(skill):
    """Button callback: open the skill profile page on ``skill``."""
    st.session_state["pf_skill"] = skill
    st.session_state["page"] = "Hồ sơ kỹ năng"
