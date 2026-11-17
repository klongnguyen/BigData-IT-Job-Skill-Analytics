"""Forecast demand per skill CATEGORY (Language, Cloud, AI/ML, ...), not per skill.

Why: a category pools many skills, so its series is larger and smoother than any single skill.
Series: share of postings that mention at least one skill of the category (a posting counts once).
Same protocol as the skill-level backtest: parameters and models are chosen on data up to 2022Q4 only,
then scored once on 2023Q1 onward. With only 7 series, pooled ML would be meaningless, so the models are
the classical ones (naive, 4-quarter mean, exponential smoothing, damped trend).

The direction band is +-2.0 points: category shares are 10-60%, so the +-1.0 point band used for single
skills (shares of 1-25%) would be too tight. 1.0 and 3.0 are reported as sensitivity.

Reads gold.db only (posting, posting_skill, skills, radar_history) and writes the category_* tables.

    python -m skill_radar.category_forecast
"""

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from skill_radar import backtest as B
from skill_radar import db
from skill_radar import models as M
from skill_radar.panel import Panel

EXCLUDE = ("other",)          # a single skill, not a family
HORIZONS = (1, 2, 3, 4)
BAND_PP = 2.0
BANDS = (1.0, 2.0, 3.0)
INTERVAL = 0.80
BOOT = 2000


def category_series(gold):
    """Quarterly share of postings mentioning any skill of each category -> (share, posts, total) as DataFrames."""
    posting = db.read_sql(gold, "SELECT pid, quarter FROM posting")
    pairs = db.read_sql(gold, "SELECT pid, skill FROM posting_skill")
    skills = db.read_sql(gold, "SELECT skill, category FROM skills")
    total = db.read_sql(gold, "SELECT DISTINCT period, total FROM radar_history").set_index("period").total.sort_index()
    merged = pairs.merge(skills, on="skill").merge(posting, on="pid").drop_duplicates(["pid", "category"])
    posts = merged.groupby(["quarter", "category"]).size().unstack(fill_value=0).reindex(total.index, fill_value=0)
    posts = posts.drop(columns=[c for c in EXCLUDE if c in posts.columns])
    return posts.div(total, axis=0), posts, total


def to_panel(share, posts, total):
    return Panel(list(share.index), list(share.columns), np.zeros(share.shape[1], dtype=int), share.T.to_numpy(),
                 total.to_numpy(dtype=float), posts.T.to_numpy(dtype=float), {})


def _mae(table, name):
    t = table[table.model == name].dropna(subset=["pred"])
    return float((t.pred - t.actual).abs().mean() * 100)


def _f1(obs, pred):
    return f1_score(obs, pred, labels=B.LABELS, average="macro", zero_division=0)


def _label_frame(table, model, band):
    t = table[(table.model == model) & (table.h == 4)].dropna(subset=["pred"])
    return pd.DataFrame({"origin": t.origin.to_numpy(), "obs": B.label_of((t.actual - t.base4) * 100, band),
                         "pred": B.label_of((t.pred - t.base4) * 100, band)})


def direction_validation(table, model, band=BAND_PP):
    """Bootstrap over ORIGINS (the 7 categories of one origin move together) of macro-F1(model) - macro-F1(always Stable)."""
    frame = _label_frame(table, model, band)
    groups = {k: g for k, g in frame.groupby("origin")}
    keys = list(groups)
    rng = np.random.default_rng(B.SEED)

    def gain(sample):
        return _f1(sample.obs, sample.pred) - _f1(sample.obs, np.full(len(sample), "Stable"))

    diffs = [gain(pd.concat([groups[k] for k in rng.choice(keys, len(keys))])) for _ in range(BOOT)]
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return {"macro_f1_model": round(float(_f1(frame.obs, frame.pred)), 4),
            "macro_f1_always_stable": round(float(_f1(frame.obs, np.full(len(frame), "Stable"))), 4),
            "gain": round(float(gain(frame)), 4), "gain_lo": round(float(lo), 4), "gain_hi": round(float(hi), 4),
            "validated": int(lo > 0), "n": int(len(frame)), "origins": len(keys)}


def run(gold):
    share, posts, total = category_series(gold)
    panel = to_panel(share, posts, total)
    selection, holdout, sel_end = B.cells(panel)
    mask = np.ones(len(panel.skills), dtype=bool)
    alpha, _ = B.select_parameter(panel, "ses", M.ALPHA_GRID, selection, mask)
    phi, _ = B.select_parameter(panel, "damped", M.PHI_GRID, selection, mask)
    models = {"naive_last": M.naive_last, "mean4": M.mean4, "ses": M.make_ses(alpha), "damped": M.make_damped(phi)}

    sel_table = B.error_table(panel, models, selection)
    rate_model = min(models, key=lambda n: _mae(sel_table, n))
    dir_model = max(models, key=lambda n: (B.label_scores(sel_table, n, mask, BAND_PP) or {"macro_f1": -1})["macro_f1"])
    table = B.error_table(panel, models, holdout)

    # holdout scores
    score_rows = []
    for name in models:
        t = table[table.model == name].dropna(subset=["pred"])
        score_rows.append({"model": name, "h": 0, "mae_pp": _mae(table, name)})
        score_rows += [{"model": name, "h": int(h), "mae_pp": float((g.pred - g.actual).abs().mean() * 100)} for h, g in t.groupby("h")]
    label_rows = []
    for band in BANDS:
        stable = B.always_stable_f1(table, mask, band)
        label_rows.append({"band": band, "model": "always_stable", "macro_f1": stable["macro_f1"], "n": stable["n"]})
        for name in models:
            found = B.label_scores(table, name, mask, band)
            label_rows.append({"band": band, "model": name, "macro_f1": found["macro_f1"], "n": found["n"]})

    # production forecast, 80% interval from the holdout absolute errors of the production model
    t = table[table.model == rate_model].dropna(subset=["pred"])
    quantile = {int(h): float((g.pred - g.actual).abs().quantile(INTERVAL)) for h, g in t.groupby("h")}
    half = np.array([quantile[h] for h in HORIZONS])
    covered = float(np.mean([(r.actual >= r.pred - quantile[r.h]) and (r.actual <= r.pred + quantile[r.h]) for r in t.itertuples()]))
    view = M.view_of(panel, len(panel.periods))
    pred = np.clip(models[rate_model](view, list(HORIZONS)), 0, 1)
    dir_pred = np.clip(models[dir_model](view, [4]), 0, 1)[:, 0]
    base4 = view.share[:, -4:].mean(axis=1)
    future = pd.period_range(panel.periods[-1], periods=len(HORIZONS) + 1, freq="Q").astype(str)[1:]
    summary, paths = [], []
    for i, cat in enumerate(panel.skills):
        delta = (dir_pred[i] - base4[i]) * 100
        summary.append({"category": cat, "share_last_year": base4[i], "share_last_quarter": view.share[i, -1], "forecast_4q": pred[i, -1],
                        "delta_pp_4q": delta, "direction": str(B.label_of(np.array([delta]), BAND_PP)[0])})
        for j, h in enumerate(HORIZONS):
            paths.append({"category": cat, "period": future[j], "h": h, "forecast": pred[i, j],
                          "lo": max(0.0, pred[i, j] - half[j]), "hi": min(1.0, pred[i, j] + half[j])})
    history = pd.DataFrame([{"category": c, "period": p, "share": share.loc[p, c], "posts": int(posts.loc[p, c])}
                            for c in share.columns for p in share.index])
    info = {"rate_model": rate_model, "direction_model": dir_model, "band_pp": BAND_PP, "alpha_ses": alpha, "phi_damped": phi,
            "selection_end": B.SELECTION_END, "holdout_targets": f"{panel.periods[sel_end + 1]}..{panel.periods[-1]}",
            "n_categories": len(panel.skills), "interval_coverage_80": round(covered, 4),
            **{f"dv_{k}": v for k, v in direction_validation(table, dir_model).items()}}
    return {"history": history, "summary": pd.DataFrame(summary), "path": pd.DataFrame(paths),
            "score": pd.DataFrame(score_rows), "label": pd.DataFrame(label_rows), "info": info}


def write(gold, out):
    db.write_table(gold, "category_history", out["history"], indexes=["category"])
    db.write_table(gold, "category_forecast", out["summary"])
    db.write_table(gold, "category_path", out["path"], indexes=["category"])
    db.write_table(gold, "category_score", out["score"])
    db.write_table(gold, "category_label", out["label"])
    db.kv_write(gold, "category_info", out["info"])


if __name__ == "__main__":
    with db.session(db.GOLD) as conn:
        result = run(conn)
        write(conn, result)
    print(result["info"])
    print(result["summary"].round(3).to_string(index=False))
    print(result["score"][result["score"].h == 0].round(3).to_string(index=False))
