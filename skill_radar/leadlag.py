"""Lead-lag analysis: does community activity move before job-posting demand?

For each skill with a signal series:
    x_t = change in the signal over a year   (log ratio of the signal now vs 4 quarters ago)
    y_t = change in HN demand share over a year (share_t - share_{t-4})
and the correlation corr(x_{t-k}, y_t) for k = 0..K quarters. k > 0 means the signal LEADS demand.

Inference is across skills, not across time (yearly changes overlap, so time points are not
independent): the mean correlation per lag gets a bootstrap interval over skills, and a PLACEBO
pairs each skill's demand with a different skill's signal to show what chance alone produces.
"""

import numpy as np

from skill_radar.models import EPS

DIFF = 4
MAX_LAG = 6
MIN_POINTS = 16
BOOT = 2000
SEED = 42


def growth(series, name, diff=DIFF):
    eps = EPS[name]
    out = np.full(series.shape, np.nan)
    out[:, diff:] = np.log((series[:, diff:] + eps) / (series[:, :-diff] + eps))
    return out


def lagged_corr(x, y, k):
    """corr(x[t-k], y[t]) over time points where both exist; NaN if too few."""
    a = x[:, :x.shape[1] - k] if k else x
    b = y[:, k:]
    out = np.full(x.shape[0], np.nan)
    for i in range(x.shape[0]):
        ok = ~(np.isnan(a[i]) | np.isnan(b[i]))
        if ok.sum() >= MIN_POINTS and a[i][ok].std() > 0 and b[i][ok].std() > 0:
            out[i] = np.corrcoef(a[i][ok], b[i][ok])[0, 1]
    return out


def analyse(panel, name, max_lag=MAX_LAG, seed=SEED):
    if name not in panel.signals:
        return None
    sig = panel.signals[name]
    usable = (~np.isnan(sig)).sum(axis=1) >= MIN_POINTS + DIFF + max_lag
    idx = np.flatnonzero(usable)
    if len(idx) < 3:
        return {"signal": name, "skills": [panel.skills[i] for i in idx], "note": "too few skills with this signal"}
    x = growth(sig[idx], name)
    y = np.full((len(idx), sig.shape[1]), np.nan)
    y[:, DIFF:] = panel.share[idx][:, DIFF:] - panel.share[idx][:, :-DIFF]
    rng = np.random.default_rng(seed)
    result = {"signal": name, "skills": [panel.skills[i] for i in idx], "lags": {}}
    for k in range(max_lag + 1):
        r = lagged_corr(x, y, k)
        good = r[~np.isnan(r)]
        boots = good[rng.integers(0, len(good), (BOOT, len(good)))].mean(axis=1)
        placebo = []
        for _ in range(500):
            perm = rng.permutation(len(idx))
            if len(idx) > 1 and (perm == np.arange(len(idx))).all():
                continue
            p = lagged_corr(x[perm], y, k)
            placebo.append(np.nanmean(p))
        placebo = np.array(placebo)
        result["lags"][k] = {
            "mean_corr": round(float(good.mean()), 4),
            "ci95": [round(float(np.quantile(boots, .025)), 4), round(float(np.quantile(boots, .975)), 4)],
            "placebo_p": round(float((np.abs(placebo) >= abs(good.mean())).mean()), 4),
            "share_positive": round(float((good > 0).mean()), 3), "skills": int(len(good)),
            "per_skill": {panel.skills[idx[i]]: (None if np.isnan(r[i]) else round(float(r[i]), 3)) for i in range(len(idx))},
        }
    return result
