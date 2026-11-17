"""Why did a skill's share of postings rise or fall? Descriptive drivers, not causes.

The data (job postings that mention words) cannot prove causation. What it can do is separate
explanations that are checkable from the postings themselves:

* ``hinge_break``   when did the trend bend, and by how much?
* ``shift_share``   how much of the change happened *inside* comparable postings (the skill itself was
                    asked for more often) and how much came from the *mix* of postings changing
                    (for example more remote postings, and remote postings mention the skill more).
* ``breadth``       is the change spread over many employers or driven by a few that post every month?
* ``comovement``    which skills rose or fell together with it (possible complements or substitutes)?
* ``model_inputs``  what the forecasting model actually looks at (recent momentum), so the forecast is not
                    mistaken for an explanation.
"""

import numpy as np
import pandas as pd

MIN_SEG = 6                 # quarters on each side of a trend break
MIN_BREAK_GAIN = 0.20       # a bend must remove at least 20% of the straight-line fit error to be reported
MIN_SLOPE_CHANGE_PP = 0.3   # ... and change the slope by at least 0.3 percentage points per year
MIN_COMOVE_SHARE = 0.005    # skills below 0.5% average share are too noisy to compare
MIN_COMOVE_POINTS = 12


# ------------------------------------------------------------------- trend break
def hinge_break(share, min_seg=MIN_SEG):
    """Best single bend of a continuous two-slope line fitted to a quarterly share series.

    Returns a dict with ``knot`` (index), slopes before/after in percentage points per YEAR, ``gain`` (share of the
    straight-line error removed by allowing a bend) and ``significant`` (bend is large enough to report).
    """
    y = np.asarray(share, dtype=float)
    n = len(y)
    t = np.arange(n, dtype=float)
    line = np.column_stack([np.ones(n), t])
    sse_line = float(((y - line @ np.linalg.lstsq(line, y, rcond=None)[0]) ** 2).sum())
    best = None
    for k in range(min_seg, n - min_seg):
        x = np.column_stack([np.ones(n), t, np.maximum(t - k, 0.0)])
        beta = np.linalg.lstsq(x, y, rcond=None)[0]
        sse = float(((y - x @ beta) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, k, beta, x @ beta)
    if best is None or sse_line <= 0:
        return {"significant": False, "gain": 0.0}
    sse, k, beta, fitted = best
    before, after = beta[1] * 400, (beta[1] + beta[2]) * 400
    gain = 1 - sse / sse_line
    return {"knot": int(k), "slope_before_pp_year": float(before), "slope_after_pp_year": float(after), "gain": float(gain),
            "fitted": fitted, "significant": bool(gain >= MIN_BREAK_GAIN and abs(after - before) >= MIN_SLOPE_CHANGE_PP)}


def nearby_events(period, events, within=2):
    """Events (a DataFrame with ``period``, ``label``) at most ``within`` quarters from ``period``."""
    base = pd.Period(period, freq="Q")
    keep = [e for e in events.itertuples() if abs((pd.Period(e.period, freq="Q") - base).n) <= within]
    return [e.label for e in keep]


# --------------------------------------------------------------------- shift-share
def shift_share(posting, posting_skill, skill, periods_a, periods_b, column):
    """Split the change in a skill's share between two windows into a *within* and a *mix* part.

    share = sum_s w_s * p_s  (w = share of postings of segment s, p = share of those postings that mention the skill).
    change = sum_s mean(w) * (p_b - p_a)   <- within: the skill is mentioned more often in comparable postings
           + sum_s (w_b - w_a) * mean(p)   <- mix: the kind of postings changed
    The two parts add up exactly to the change in share.
    """
    mentions = set(posting_skill.pid[posting_skill.skill == skill])
    rows = []
    frames = {}
    for tag, periods in (("a", periods_a), ("b", periods_b)):
        sub = posting[posting.quarter.isin(periods)]
        sub = sub.assign(has=sub.pid.isin(mentions))
        grouped = sub.groupby(column).agg(n=("pid", "size"), k=("has", "sum"))
        grouped["w"] = grouped.n / grouped.n.sum()
        grouped["p"] = grouped.k / grouped.n
        frames[tag] = grouped
    a, b = frames["a"], frames["b"]
    for cat in sorted(set(a.index) | set(b.index), key=str):
        wa, wb = (a.w.get(cat, 0.0), b.w.get(cat, 0.0))
        pa, pb = (a.p.get(cat, 0.0), b.p.get(cat, 0.0))
        if cat not in a.index:
            pa = pb                      # a segment absent in one window cannot show a within-change
        if cat not in b.index:
            pb = pa
        rows.append({"category": cat, "w_a": wa, "w_b": wb, "p_a": pa, "p_b": pb,
                     "within": (wa + wb) / 2 * (pb - pa), "mix": (wb - wa) * (pa + pb) / 2})
    table = pd.DataFrame(rows)
    share_a = float((a.w * a.p).sum())
    share_b = float((b.w * b.p).sum())
    return {"table": table, "share_a": share_a, "share_b": share_b, "within": float(table.within.sum()), "mix": float(table["mix"].sum())}


# ------------------------------------------------------------------------ breadth
def breadth(posting, posting_skill, skill, periods):
    """How many different employers mention the skill, and how concentrated they are (author ids, never names)."""
    pids = set(posting_skill.pid[posting_skill.skill == skill])
    sub = posting[posting.quarter.isin(periods) & posting.pid.isin(pids)]
    n = len(sub)
    if n == 0:
        return {"posts": 0, "authors": 0, "posts_per_author": 0.0, "top5_share": 0.0}
    counts = sub.author_id.value_counts()
    return {"posts": int(n), "authors": int(len(counts)), "posts_per_author": float(n / len(counts)), "top5_share": float(counts.head(5).sum() / n)}


# --------------------------------------------------------------------- co-movement
def comovement(history, skill, top=5):
    """Skills whose year-on-year change moves with / against this skill's (correlation of 4-quarter changes).

    Returns (together, against): DataFrames with columns skill, corr. Descriptive only: two skills can move together
    because of a third factor, and changes that overlap in time are strongly autocorrelated.
    """
    wide = history.pivot(index="period", columns="skill", values="share").sort_index()
    change = wide.diff(4).dropna(how="all")
    if skill not in change or change[skill].notna().sum() < MIN_COMOVE_POINTS:
        return pd.DataFrame(columns=["skill", "corr"]), pd.DataFrame(columns=["skill", "corr"])
    keep = [c for c in wide if c != skill and wide[c].mean() >= MIN_COMOVE_SHARE]
    corr = change[keep].corrwith(change[skill]).dropna()
    frame = corr.rename("corr").rename_axis("skill").reset_index()
    return frame.nlargest(top, "corr").reset_index(drop=True), frame.nsmallest(top, "corr").reset_index(drop=True)


# ---------------------------------------------------------------- forecast inputs
def model_inputs(share):
    """The quantities the direction model reads for one skill (shares in 0-1, results in percentage points)."""
    s = np.asarray(share, dtype=float)
    base = s[-4:].mean()
    n = 8
    t = np.arange(n, dtype=float)
    tc = t - t.mean()
    slope = float((s[-n:] * tc).sum() / (tc ** 2).sum())
    return {"base_pp": base * 100, "slope_pp_per_quarter": slope * 100,
            "last_vs_base_pp": [float((s[-i] - base) * 100) for i in (1, 2, 3)]}


# ------------------------------------------------------------------ plain-language summary
def _pct(x, digits=1):
    return f"{x * 100:.{digits}f}%".replace(".", ",")


def _pp(x, digits=1):
    return f"{x * 100:+.{digits}f}".replace(".", ",")


def summarize(label, periods_a, periods_b, shifts, breadth_a, breadth_b, brk, break_period, events, together, against, labels, inputs):
    """Bullet sentences (Vietnamese) that put the driver analysis together. ``shifts`` is a list of shift_share results."""
    first = shifts[0]
    total = first["share_b"] - first["share_a"]
    out = [f"**{label}:** đổi từ {_pct(first['share_a'])} tin (quý {periods_a[0]} đến {periods_a[-1]}) thành {_pct(first['share_b'])} (quý {periods_b[0]} đến {periods_b[-1]}), "
           f"thay đổi {_pp(total)} điểm %."]
    if abs(total) >= 0.003:
        ratios = [s["within"] / total for s in shifts]
        within = float(np.mean(ratios))
        if within >= 0.7:
            out.append("**Do chính kỹ năng:** kỹ năng được nhắc nhiều hơn hoặc ít hơn ngay trong các tin cùng loại.")
        elif within <= 0.3:
            out.append("**Do cơ cấu tin:** loại tin tuyển dụng thay đổi, ví dụ nhiều tin remote hơn.")
        else:
            out.append("**Một phần do cơ cấu tin:** vừa do kỹ năng được nhắc khác đi, vừa do loại tin thay đổi.")
    if breadth_b["posts"] < 30 or breadth_a["posts"] < 30:
        out.append(f"**Số tin ít:** chỉ {breadth_a['posts']} và {breadth_b['posts']} tin nhắc kỹ năng, nên kết luận dễ sai.")
    else:
        out.append(f"**Độ rộng:** số nhà tuyển dụng nhắc kỹ năng đổi từ {breadth_a['authors']} thành {breadth_b['authors']}, 5 nhà đăng nhiều nhất chiếm "
                   f"{_pct(breadth_a['top5_share'], 0)} rồi {_pct(breadth_b['top5_share'], 0)} số tin.")
    if brk.get("significant"):
        before = f"{brk['slope_before_pp_year'] + 0.0:+.1f}".replace("-0,0", "0,0").replace("-0.0", "0.0").replace(".", ",")
        after = f"{brk['slope_after_pp_year'] + 0.0:+.1f}".replace(".", ",")
        text = f"**Bước ngoặt:** xu hướng đổi hướng quanh {break_period}, trước đó {before} điểm %/năm, sau đó {after} điểm %/năm."
        if events:
            text += f" Gần với sự kiện: {', '.join(events)}."
        out.append(text)
    else:
        out.append("**Bước ngoặt:** chưa thấy điểm đổi hướng rõ, xu hướng khá đều.")
    if len(together) or len(against):
        names = lambda ids: ", ".join(labels[s] for s in ids)
        parts = []
        if len(together):
            parts.append(f"cùng chiều với {names(list(together)[:3])}")
        if len(against):
            parts.append(f"ngược chiều với {names(list(against)[:3])}")
        out.append("**Biến động:** " + ", ".join(parts) + " (chỉ là tương quan).")
    slope = f"{inputs['slope_pp_per_quarter']:+.2f}".replace(".", ",")
    base = f"{inputs['base_pp']:.1f}".replace(".", ",")
    out.append(f"**Dự báo dựa vào gì:** chỉ dựa vào đà gần đây (độ dốc 8 quý {slope} điểm %/quý, mức nền {base}%).")
    return out
