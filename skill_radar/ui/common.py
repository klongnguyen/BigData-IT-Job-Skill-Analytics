"""Small helpers shared by the dashboard pages."""

import pandas as pd

from skill_radar.ui import theme


def qdate(periods):
    """'2024Q3' strings -> timestamp at the middle of the quarter (for time axes)."""
    return pd.PeriodIndex(list(periods), freq="Q").to_timestamp() + pd.Timedelta(days=45)


def quarter_label(period):
    return f"Q{period[-1]}/{period[:4]}"


def add_events(fig, events, first_period=None):
    """Dotted vertical lines with a short label for dated events (paper-relative, works on date axes)."""
    t = theme.tokens()
    for i, row in enumerate(events.sort_values("period").itertuples()):
        if first_period and row.period < first_period:
            continue
        x = qdate([row.period])[0]
        fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, xref="x", yref="paper", line={"color": t["muted"], "width": 1, "dash": "dot"})
        fig.add_annotation(x=x, y=1.0, yref="paper", text=row.label, showarrow=False, xanchor="left", yanchor="top", xshift=4, yshift=-16 * (i % 2),
                           font={"size": 11, "color": t["text2"]}, bgcolor="rgba(0,0,0,0)")


def n_fmt(value):
    return f"{int(value):,}".replace(",", ".")
