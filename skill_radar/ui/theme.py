"""Visual system for the dashboard: validated categorical palette, light tokens (white background), Plotly styling.

Colours follow the data-viz method (reference palette, fixed hue order, never cycled):
  * categorical  one hue per skill category, assigned by entity so a filter never repaints a category;
  * sequential   one hue (blue) for magnitude;
  * diverging    blue <-> red around a neutral gray for change (blue = up, red = down).
"""

import streamlit as st

CATEGORY_ORDER = ["language", "frontend", "backend", "data", "ai", "cloud", "mobile", "other"]
CATEGORY_VI = {"language": "Ngôn ngữ", "frontend": "Front-end", "backend": "Back-end", "data": "Dữ liệu", "ai": "AI/ML",
               "cloud": "Cloud/DevOps", "mobile": "Mobile", "other": "Khác"}
DIRECTION_VI = {"Rising": "Đang lên", "Stable": "Ổn định", "Fading": "Suy giảm", "Insufficient evidence": "Chưa đủ bằng chứng"}
REGION_VI = {"NA": "Bắc Mỹ", "EU": "Châu Âu", "APAC": "Châu Á – Thái Bình Dương", "UNKNOWN": "Không nêu địa điểm"}

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
T = {"surface": "#ffffff", "text": "#111827", "text2": "#4b5563", "muted": "#8a8985", "grid": "rgba(17,24,39,0.08)",
     "axis": "rgba(17,24,39,0.28)", "up": "#2a78d6", "down": "#e34948", "flat": "#9b9a96", "mid": "#f0efec",
     "sequential": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
     "diverging": ["#e34948", "#f0aaa9", "#f0efec", "#a9cbf4", "#2a78d6"]}
MARKERS = ["circle", "square", "diamond", "triangle-up", "cross", "x", "star", "hexagon"]


def tokens():
    return T


def series_colors():
    return SERIES


def category_color(category):
    """Fixed colour per skill category; 'other' (a single skill) takes the neutral gray."""
    if category == "other":
        return tokens()["flat"]
    return series_colors()[CATEGORY_ORDER.index(category)]


def cluster_color(cluster_id):
    return SERIES[(int(cluster_id) - 1) % len(SERIES)] if int(cluster_id) > 0 else T["flat"]


def diverging_scale():
    return [[i / 4, c] for i, c in enumerate(tokens()["diverging"])]


def sequential_scale():
    seq = tokens()["sequential"]
    return [[i / (len(seq) - 1), c] for i, c in enumerate(seq)]


def vn(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")


def pct(value, digits=1):
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def pp(value, digits=2):
    return f"{value:+.{digits}f}".replace(".", ",")


def style(fig, height=420, legend=True, xtitle=None, ytitle=None, hover="closest", ytickformat=None, xgrid=False):
    t = tokens()
    fig.update_layout(
        height=height, margin={"l": 8, "r": 16, "t": 34 if legend else 10, "b": 8}, showlegend=legend, hovermode=hover,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, 'Segoe UI', system-ui, sans-serif", "size": 13, "color": t["text2"]},
        hoverlabel={"bgcolor": t["surface"], "font": {"color": t["text"], "size": 13}, "bordercolor": t["axis"]},
        legend={"orientation": "h", "y": 1.0, "x": 0, "yanchor": "bottom", "font": {"size": 12}, "title": {"text": ""}})
    fig.update_xaxes(showgrid=xgrid, gridcolor=t["grid"], linecolor=t["axis"], zeroline=False, title=xtitle, ticks="outside", tickcolor=t["axis"], automargin=True)
    fig.update_yaxes(gridcolor=t["grid"], zeroline=False, title=ytitle, tickformat=ytickformat, automargin=True)
    return fig


CONFIG = {"displayModeBar": False, "displaylogo": False, "doubleClick": "reset", "scrollZoom": False}


def time_range(fig):
    """Range buttons on a date axis. The Plotly toolbar is hidden on purpose; double-click still resets a zoom."""
    buttons = [{"count": 3, "label": "3 năm", "step": "year", "stepmode": "backward"},
               {"count": 5, "label": "5 năm", "step": "year", "stepmode": "backward"}, {"step": "all", "label": "Tất cả"}]
    fig.update_xaxes(rangeselector={"buttons": buttons, "x": 1, "xanchor": "right", "y": 1.02, "yanchor": "bottom", "bgcolor": "#f3f4f6",
                                    "activecolor": "#cde2fb", "font": {"size": 11}})
    return fig


def lock(fig):
    """No drag-zoom, pan or axis dragging: a zoomed chart had no way back (the toolbar is hidden). Hover, click and
    the range buttons still work."""
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def show(fig, key):
    st.plotly_chart(lock(fig), width="stretch", theme=None, config=CONFIG, key=key)


def header(title, subtitle=None):
    st.markdown(f"##### {title}")
    if subtitle:
        st.caption(subtitle)


CSS = """<style>
.block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px;}
.hero {font-size: 30px; line-height: 1.15; font-weight: 750; letter-spacing: -0.4px; margin: 0;}
.subtitle {opacity: .72; font-size: 14px; margin: 2px 0 14px 0;}
h5 {margin-top: 1.1rem !important; margin-bottom: .1rem !important;}
button[data-baseweb="tab"] {font-size: 15px;}
[data-testid="stElementToolbar"] {display: none;}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] *, [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *,
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {white-space: normal !important; overflow: visible !important; text-overflow: clip !important;}
[data-testid="stMetricValue"] {font-size: 1.35rem; line-height: 1.2;}
[data-testid="stMetric"] {min-height: 7.4rem;}
[data-testid="stMetricDelta"] {font-size: .85rem; line-height: 1.25;}
.insight-title {font-weight: 650; font-size: 15px; margin-bottom: 2px;}
.insight-body {opacity: .8; font-size: 13.5px; line-height: 1.4;}
</style>"""
