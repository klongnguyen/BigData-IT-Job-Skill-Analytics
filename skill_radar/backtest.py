"""Rolling-origin backtest: does community activity help forecast job-posting demand?

Protocol (fixed before any model is scored)
-------------------------------------------
* Target: quarterly share of "Who is hiring?" postings mentioning a skill (one source, 2015Q3 on).
* Horizons: 1-4 quarters ahead.
* Selection window: origins whose targets are all <= 2022Q4. Damping / smoothing parameters are
  chosen here, and only here.
* Holdout: origins from the end of 2022 onward, targets 2023Q1-latest. Scored once.
* Eligible skills: mean demand share >= 1% over the selection window (decided without the holdout).
* Main question: for the SAME model class, does adding community signals (Stack Overflow, npm,
  GitHub) lower the holdout error versus history alone? Paired bootstrap over skills.
* Direction labels: Rising / Stable / Fading from the 4-quarter-ahead change vs the last-year mean,
  +-1.0 percentage-point band set in advance (0.5 and 2.0 reported as sensitivity).
"""

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from skill_radar import models as M

HORIZONS = (1, 2, 3, 4)
SELECTION_END = "2022Q4"
FIRST_ORIGIN = 12              # visible quarters at the earliest origin
MIN_SHARE = 0.01
BAND_PP = 1.0
BAND_SENSITIVITY = (0.5, 1.0, 2.0)
BOOT = 2000
SEED = 42
LABELS = ["Fading", "Stable", "Rising"]


def label_of(delta_pp, band):
    return np.where(delta_pp > band, "Rising", np.where(delta_pp < -band, "Fading", "Stable"))


def cells(panel):
    n = len(panel.periods)
    sel_end = panel.periods.index(SELECTION_END)
    selection = [(T, [h for h in HORIZONS if T + h - 1 <= sel_end]) for T in range(FIRST_ORIGIN, sel_end + 1)]
    holdout = [(T, [h for h in HORIZONS if T + h - 1 <= n - 1]) for T in range(sel_end + 1, n)]
    return [c for c in selection if c[1]], [c for c in holdout if c[1]], sel_end


def eligible_mask(panel, sel_end):
    return panel.share[:, :sel_end + 1].mean(axis=1) >= MIN_SHARE


def error_table(panel, models, cell_list):
    frames = []
    for name, fn in models.items():
        for T, hs in cell_list:
            view = M.view_of(panel, T)
            pred = fn(view, hs)
            base = view.share[:, -4:].mean(axis=1)
            for j, h in enumerate(hs):
                frames.append(pd.DataFrame({
                    "model": name, "origin": T, "h": h, "skill": np.arange(len(base)),
                    "pred": pred[:, j], "actual": panel.share[:, T + h - 1], "base4": base}))
    return pd.concat(frames, ignore_index=True)


def mae_pp(table, mask):
    t = table[table.skill.isin(np.flatnonzero(mask))].dropna(subset=["pred"])
    return float((t.pred - t.actual).abs().mean() * 100) if len(t) else float("nan")


def select_parameter(panel, family, grid, selection, mask):
    maker = {"ses": M.make_ses, "damped": M.make_damped}[family]
    scores = {p: mae_pp(error_table(panel, {family: maker(p)}, selection), mask) for p in grid}
    return min(scores, key=scores.get), scores


def per_skill_error(table, model, mask, cells_keys=None):
    t = table[(table.model == model) & table.skill.isin(np.flatnonzero(mask))]
    if cells_keys is not None:
        t = t.merge(cells_keys, on=["origin", "h"])
    t = t.dropna(subset=["pred"])
    return (t.pred - t.actual).abs().groupby(t.skill).mean() * 100


def paired_bootstrap(a, b, seed=SEED):
    """mean(a-b) over skills with a 95% interval; negative means model a is better."""
    common = a.index.intersection(b.index)
    d = (a.loc[common] - b.loc[common]).to_numpy()
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, len(d), (BOOT, len(d)))].mean(axis=1)
    return float(d.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975)), int(len(d))


def label_scores(table, model, mask, band):
    """Macro-F1 of the 4-quarter-ahead direction label, pooled over holdout origins."""
    t = table[(table.model == model) & (table.h == 4) & table.skill.isin(np.flatnonzero(mask))].dropna(subset=["pred"])
    if t.empty:
        return None
    obs = label_of((t.actual - t.base4) * 100, band)
    pred = label_of((t.pred - t.base4) * 100, band)
    return {"macro_f1": round(float(f1_score(obs, pred, labels=LABELS, average="macro", zero_division=0)), 4),
            "n": int(len(t))}


def always_stable_f1(table, mask, band):
    t = table[(table.model == table.model.iloc[0]) & (table.h == 4) & table.skill.isin(np.flatnonzero(mask))]
    obs = label_of((t.actual - t.base4) * 100, band)
    return {"macro_f1": round(float(f1_score(obs, np.full(len(obs), "Stable"), labels=LABELS, average="macro", zero_division=0)), 4),
            "n": int(len(t)), "support": {l: int((obs == l).sum()) for l in LABELS}}


def run(panel):
    selection, holdout, sel_end = cells(panel)
    mask = eligible_mask(panel, sel_end)
    alpha, a_scores = select_parameter(panel, "ses", M.ALPHA_GRID, selection, mask)
    phi, p_scores = select_parameter(panel, "damped", M.PHI_GRID, selection, mask)
    models = {"naive_last": M.naive_last, "mean4": M.mean4, "ses": M.make_ses(alpha), "damped": M.make_damped(phi),
              "ridge": M.make_pooled("ridge", False), "gbm": M.make_pooled("gbm", False),
              "ridge+signals": M.make_pooled("ridge", True), "gbm+signals": M.make_pooled("gbm", True)}
    table = error_table(panel, models, holdout)
    has_signal = np.zeros(len(panel.skills), dtype=bool)
    for arr in panel.signals.values():
        has_signal |= ~np.isnan(arr[:, :sel_end + 1]).all(axis=1)

    def summarize(sub_mask):
        # only (origin, h) cells that every model can produce, so models are compared like for like
        ok = table.dropna(subset=["pred"]).groupby(["origin", "h"]).model.nunique()
        keys = ok[ok == len(models)].reset_index()[["origin", "h"]]
        out = {}
        for name in models:
            sub = table[(table.model == name)].merge(keys, on=["origin", "h"])
            by_h = {int(h): round(mae_pp(g, sub_mask), 4) for h, g in sub.groupby("h")}
            out[name] = {"mae_pp": round(mae_pp(sub, sub_mask), 4), "mae_pp_by_horizon": by_h}
        best_base = min(("naive_last", "mean4"), key=lambda m: out[m]["mae_pp"])
        errs = {n: per_skill_error(table, n, sub_mask, keys) for n in models}
        for name in models:
            if name != best_base:
                d, lo, hi, n = paired_bootstrap(errs[name], errs[best_base])
                out[name]["vs_best_baseline"] = {"baseline": best_base, "diff_pp": round(d, 4), "ci95": [round(lo, 4), round(hi, 4)], "skills": n}
        for with_sig, without in (("ridge+signals", "ridge"), ("gbm+signals", "gbm")):
            d, lo, hi, n = paired_bootstrap(errs[with_sig], errs[without])
            out[with_sig]["signal_effect"] = {"vs": without, "diff_pp": round(d, 4), "ci95": [round(lo, 4), round(hi, 4)], "skills": n}
        return {"best_baseline": best_base, "models": out, "cells": int(len(keys)),
                "skills": int(sub_mask.sum())}

    result = {
        "protocol": {"horizons": list(HORIZONS), "selection_end": SELECTION_END, "holdout_targets": f"{panel.periods[sel_end + 1]}..{panel.periods[-1]}",
                     "min_share": MIN_SHARE, "band_pp": BAND_PP, "quarters": len(panel.periods), "first": panel.periods[0], "last": panel.periods[-1]},
        "selection": {"alpha_ses": alpha, "alpha_scores_mae_pp": {str(k): round(v, 4) for k, v in a_scores.items()},
                      "phi_damped": phi, "phi_scores_mae_pp": {str(k): round(v, 4) for k, v in p_scores.items()}},
        "eligible_skills": int(mask.sum()), "with_signal_skills": int((mask & has_signal).sum()),
        "all_eligible": summarize(mask),
        "signal_covered": summarize(mask & has_signal) if (mask & has_signal).sum() >= 5 else None,
        "labels": {},
    }
    for band in BAND_SENSITIVITY:
        result["labels"][str(band)] = {
            "always_stable": always_stable_f1(table, mask, band),
            **{n: label_scores(table, n, mask, band) for n in models}}
    return result, table
