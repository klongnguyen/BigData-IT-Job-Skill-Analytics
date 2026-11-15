"""Forecast models for quarterly skill-demand share (HN job postings).

Every model has the same contract::

    predict(view, horizons) -> ndarray (n_skills, len(horizons))

``view`` holds ONLY the quarters visible at the forecast origin (the caller slices it), so a model
cannot read the future. ``horizons`` are quarters ahead (1 = next quarter). A model that cannot
produce a horizon returns NaN there.

Baselines   naive_last, mean4 (mean of the last four quarters = a year, which also removes seasonality)
Smoothing   ses
Trend       damped (OLS trend over the last 8 quarters, momentum fades with factor phi)
Pooled ML   ridge / gbm over all skills, WITHOUT or WITH leading-indicator signals
"""

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from skill_radar.panel import CATEGORIES

MIN_CUTOFF = 7                 # pooled features need 8 visible quarters
MAX_POOLED_H = 4
SIGNALS = ("se_share", "npm_dl", "gh_share")
EPS = {"se_share": 1e-4, "gh_share": 1e-4, "npm_dl": 1.0}
SEED = 42


@dataclass
class View:
    share: np.ndarray
    total: np.ndarray
    category: np.ndarray
    signals: dict

    @property
    def T(self):
        return self.share.shape[1]


def view_of(panel, T):
    return View(panel.share[:, :T], panel.total[:T], panel.category,
                {k: v[:, :T] for k, v in panel.signals.items()})


# ---------------------------------------------------------------- baselines
def naive_last(view, horizons):
    return np.repeat(view.share[:, -1:], len(horizons), axis=1)


def mean4(view, horizons):
    return np.repeat(view.share[:, -4:].mean(axis=1, keepdims=True), len(horizons), axis=1)


def make_ses(alpha):
    def ses(view, horizons):
        level = view.share[:, 0].copy()
        for t in range(1, view.T):
            level = alpha * view.share[:, t] + (1 - alpha) * level
        return np.repeat(level[:, None], len(horizons), axis=1)
    ses.param = alpha
    return ses


def _ols(window):
    n = window.shape[1]
    t = np.arange(n, dtype=float)
    tc = t - t.mean()
    slope = (window * tc).sum(axis=1) / (tc ** 2).sum()
    fitted_last = window.mean(axis=1) + slope * (n - 1 - t.mean())
    return slope, fitted_last


def make_damped(phi, window=8):
    def damped(view, horizons):
        slope, level = _ols(view.share[:, -window:])
        h = np.asarray(horizons, dtype=float)
        cum = h if abs(phi - 1) < 1e-12 else phi * (1 - phi ** h) / (1 - phi)
        return level[:, None] + slope[:, None] * cum[None, :]
    damped.param = phi
    return damped


# ------------------------------------------------------------------- pooled
def _growth(series, c, name):
    recent = np.nanmean(series[:, c - 3:c + 1], axis=1)
    prior = np.nanmean(series[:, c - 7:c - 3], axis=1)
    have = ~(np.isnan(recent) | np.isnan(prior))
    growth = np.zeros(series.shape[0])
    eps = EPS[name]
    growth[have] = np.clip(np.log((recent[have] + eps) / (prior[have] + eps)), -3, 3)
    return growth, have.astype(float)


def features(view, c, use_signals):
    s = view.share
    base = s[:, c - 3:c + 1].mean(axis=1)
    slope8, _ = _ols(s[:, c - 7:c + 1])
    cols = [s[:, c] - base, s[:, c - 1] - base, s[:, c - 2] - base, slope8, base,
            np.full(s.shape[0], np.log(view.total[c]))]
    cols += list(np.eye(len(CATEGORIES))[view.category].T)
    if use_signals:
        for name in SIGNALS:
            if name in view.signals:
                growth, have = _growth(view.signals[name], c, name)
                cols += [growth, have]
    return np.column_stack(cols), base


def _ridge():
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0))


def _gbm():
    return GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, max_depth=2,
                                     subsample=0.8, random_state=SEED)


def make_pooled(kind, use_signals):
    factory = {"ridge": _ridge, "gbm": _gbm}[kind]

    def pooled(view, horizons):
        out = np.full((view.share.shape[0], len(horizons)), np.nan)
        T = view.T
        if T - 1 < MIN_CUTOFF:
            return out
        x_now, base_now = features(view, T - 1, use_signals)
        for j, h in enumerate(horizons):
            if h > MAX_POOLED_H:
                continue
            cutoffs = [c for c in range(MIN_CUTOFF, T) if c + h <= T - 1]    # target already observed
            if not cutoffs:
                continue
            xs, ys = [], []
            for c in cutoffs:
                x, base = features(view, c, use_signals)
                xs.append(x)
                ys.append(view.share[:, c + h] - base)
            model = factory()
            model.fit(np.vstack(xs), np.concatenate(ys))
            out[:, j] = base_now + model.predict(x_now)
        return out

    pooled.param = f"{kind}+signals" if use_signals else kind
    return pooled


PHI_GRID = (0.25, 0.5, 0.75, 0.9)
ALPHA_GRID = (0.2, 0.4, 0.6, 0.8)

LABELS = {
    "naive_last": "Giữ nguyên quý cuối",
    "mean4": "Trung bình 4 quý",
    "ses": "Làm mượt mũ (SES)",
    "damped": "Xu hướng giảm dần",
    "ridge": "Ridge (chỉ lịch sử tuyển dụng)",
    "gbm": "Gradient Boosting (chỉ lịch sử)",
    "ridge+signals": "Ridge + tín hiệu cộng đồng",
    "gbm+signals": "Gradient Boosting + tín hiệu cộng đồng",
}
