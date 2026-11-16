"""Pure-pandas summaries that the dashboard turns into charts and headline sentences."""

import pandas as pd


def annual_share(skill_year):
    """Wide table year x skill: share of that year's postings mentioning the skill."""
    table = skill_year.assign(share=skill_year.posts / skill_year.total)
    return table.pivot(index="year", columns="skill", values="share").sort_index()


def full_years(history):
    """Years for which the quarterly history holds all four quarters."""
    years = pd.Series([int(p[:4]) for p in history.period.unique()]).value_counts()
    return sorted(int(y) for y, n in years.items() if n == 4)


def window_share(history, periods):
    """Share of postings mentioning each skill over a set of quarters (pooled counts, not an average of ratios)."""
    sub = history[history.period.isin(periods)]
    total = sub.drop_duplicates("period").total.sum()
    return (sub.groupby("skill").posts.sum() / total).rename("share")


def window_posts(history, periods):
    return history[history.period.isin(periods)].groupby("skill").posts.sum().rename("posts")


def recent_periods(history, n=4, offset=0):
    periods = sorted(history.period.unique())
    end = len(periods) - offset
    return periods[max(end - n, 0):end]


def rank_table(annual):
    """Rank (1 = most mentioned) of every skill in every year."""
    return annual.rank(axis=1, ascending=False, method="min")


def _pct(x, digits=1):
    return f"{x * 100:.{digits}f}%".replace(".", ",")


def _pp(x, digits=1):
    return f"{x * 100:+.{digits}f}".replace(".", ",")


def make_insights(history, skill_year, market, labels):
    """A handful of data-driven headline sentences: list of dicts with 'title' and 'body'."""
    out = []
    annual = annual_share(skill_year)
    years = [y for y in full_years(history) if y in annual.index]
    if len(years) >= 2:
        base = 2019 if 2019 in years else years[0]
        last = years[-1]
        diff = (annual.loc[last] - annual.loc[base])[(annual.loc[[base, last]].max() >= 0.01)]
        up, down = diff.idxmax(), diff.idxmin()
        out.append({"title": f"{labels[up]} tăng nhiều nhất",
                    "body": f"Từ {_pct(annual.loc[base, up])} tin năm {base} lên {_pct(annual.loc[last, up])} năm {last} ({_pp(diff[up])} điểm %)."})
        out.append({"title": f"{labels[down]} giảm nhiều nhất",
                    "body": f"Từ {_pct(annual.loc[base, down])} năm {base} xuống {_pct(annual.loc[last, down])} năm {last} ({_pp(diff[down])} điểm %)."})
        if 2022 in annual.index:
            now = window_share(history, recent_periods(history))
            posts = window_posts(history, recent_periods(history))
            base22 = annual.loc[2022]
            eligible = [s for s in now.index if posts[s] >= 50 and base22[s] > 0]
            if eligible:
                ratio = (now[eligible] / base22[eligible]).sort_values(ascending=False)
                s = ratio.index[0]
                times = f"{ratio[s]:.1f}".replace(".", ",")
                out.append({"title": f"{labels[s]} bứt phá nhanh nhất",
                            "body": f"Tỷ lệ tin nhắc tới tăng gấp {times} lần so với năm 2022 ({_pct(base22[s])} → {_pct(now[s])})."})
    if len(market):
        m = market.assign(remote_share=market.remote / market.n_posts, salary_share=market.salary / market.n_posts)
        peak = m.loc[m.remote_share.idxmax()]
        recent = m.tail(4)
        out.append({"title": "Làm việc từ xa đã qua đỉnh",
                    "body": f"Đỉnh {_pct(peak.remote_share, 0)} tin nhắc remote ở {peak.period}; 4 quý gần nhất còn {_pct(recent.remote.sum() / recent.n_posts.sum(), 0)}."})
        old = m[m.period.str.startswith("2019")]
        if len(old):
            out.append({"title": "Công khai mức lương ngày càng phổ biến",
                        "body": f"{_pct(old.salary.sum() / old.n_posts.sum(), 0)} tin năm 2019 nêu lương; 4 quý gần nhất là {_pct(recent.salary.sum() / recent.n_posts.sum(), 0)}."})
    return out
