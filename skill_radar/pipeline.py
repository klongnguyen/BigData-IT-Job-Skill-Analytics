"""End-to-end Skill Radar run: panel -> backtest -> lead-lag -> production forecast -> artifacts.

Two production choices, each made on the SELECTION window only and among models that need no
community signals: the RATE model (lowest error) and the DIRECTION model (highest macro-F1 of the
Rising/Stable/Fading label). Their holdout skill is then reported as measured, never assumed.

    python -m skill_radar.pipeline
"""

import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from skill_radar import analytics
from skill_radar import category_forecast as C
from skill_radar import backtest as B
from skill_radar import db
from skill_radar import leadlag as L
from skill_radar import models as M
from skill_radar import panel as P
from skill_radar import store
from skill_radar.taxonomy import BY_ID

FORECAST_Q = 4
INTERVAL = 0.80
CELL_MODELS = ("naive_last", "ses", "damped", "gbm")      # models whose holdout predictions are kept for the dashboard
NO_SIGNAL_MODELS = ("naive_last", "mean4", "ses", "damped", "ridge", "gbm")


def build_models(alpha, phi):
    return {"naive_last": M.naive_last, "mean4": M.mean4, "ses": M.make_ses(alpha), "damped": M.make_damped(phi),
            "ridge": M.make_pooled("ridge", False), "gbm": M.make_pooled("gbm", False),
            "ridge+signals": M.make_pooled("ridge", True), "gbm+signals": M.make_pooled("gbm", True)}


def pick_production(panel, models, selection, mask):
    scores = {}
    for name in NO_SIGNAL_MODELS:
        table = B.error_table(panel, {name: models[name]}, selection).dropna(subset=["pred"])
        scores[name] = B.mae_pp(table, mask)
    return min(scores, key=scores.get), scores


def pick_direction(panel, models, selection, mask):
    scores = {}
    for name in NO_SIGNAL_MODELS:
        table = B.error_table(panel, {name: models[name]}, selection)
        found = B.label_scores(table, name, mask, B.BAND_PP)
        scores[name] = found["macro_f1"] if found else -1.0
    return max(scores, key=scores.get), scores


def direction_validation(table, model, mask, band=B.BAND_PP):
    """Cluster bootstrap over skills of macro-F1(model) - macro-F1(always Stable), 4-quarter label."""
    t = table[(table.model == model) & (table.h == 4) & table.skill.isin(np.flatnonzero(mask))].dropna(subset=["pred"])
    obs = B.label_of((t.actual - t.base4) * 100, band)
    pred = B.label_of((t.pred - t.base4) * 100, band)
    frame = pd.DataFrame({"skill": t.skill.to_numpy(), "obs": obs, "pred": pred})
    groups = {k: g for k, g in frame.groupby("skill")}
    keys = list(groups)
    rng = np.random.default_rng(B.SEED)

    def f1(o, p):
        return f1_score(o, p, labels=B.LABELS, average="macro", zero_division=0)

    diffs = []
    for _ in range(1000):
        sample = pd.concat([groups[k] for k in rng.choice(keys, len(keys))])
        diffs.append(f1(sample.obs, sample.pred) - f1(sample.obs, np.full(len(sample), "Stable")))
    point = f1(frame.obs, frame.pred) - f1(frame.obs, np.full(len(frame), "Stable"))
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return {"macro_f1_model": round(float(f1(frame.obs, frame.pred)), 4),
            "macro_f1_always_stable": round(float(f1(frame.obs, np.full(len(frame), "Stable"))), 4),
            "gain": round(float(point), 4), "gain_ci95": [round(float(lo), 4), round(float(hi), 4)],
            "validated": bool(lo > 0)}


def interval_quantiles(table, model, mask):
    t = table[(table.model == model) & table.skill.isin(np.flatnonzero(mask))].dropna(subset=["pred"])
    scale = np.sqrt(np.clip(t.base4, 0.01, 0.99) * (1 - np.clip(t.base4, 0.01, 0.99)))
    z = (t.pred - t.actual).abs() / scale
    return {int(h): float(g.quantile(INTERVAL)) for h, g in z.groupby(t.h)}


def coverage(table, model, mask, quantiles):
    t = table[(table.model == model) & table.skill.isin(np.flatnonzero(mask))].dropna(subset=["pred"])
    half = t.h.map(quantiles) * np.sqrt(np.clip(t.base4, 0.01, 0.99) * (1 - np.clip(t.base4, 0.01, 0.99)))
    return float(((t.actual >= t.pred - half) & (t.actual <= t.pred + half)).mean())


def production_forecast(panel, fn, dir_fn, quantiles, mask, evidence):
    horizons = list(range(1, FORECAST_Q + 1))
    view = M.view_of(panel, len(panel.periods))
    pred = np.clip(fn(view, horizons), 0, 1)
    dir_pred = np.clip(dir_fn(view, [FORECAST_Q]), 0, 1)[:, 0]
    base4 = view.share[:, -4:].mean(axis=1)
    future = pd.period_range(panel.periods[-1], periods=FORECAST_Q + 1, freq="Q").astype(str)[1:]
    rows, paths = [], []
    for i, sid in enumerate(panel.skills):
        s = BY_ID[sid]
        half = np.array([quantiles[h] for h in horizons]) * np.sqrt(np.clip(base4[i], 0.01, 0.99) * (1 - np.clip(base4[i], 0.01, 0.99)))
        delta = (dir_pred[i] - base4[i]) * 100
        rows.append({"skill": sid, "label": s["label"], "category": s["category"], "eligible": bool(mask[i]),
                     "share_last_year": base4[i], "share_last_quarter": view.share[i, -1],
                     "forecast_4q": pred[i, -1], "delta_pp_4q": delta,
                     "direction": str(B.label_of(np.array([delta]), B.BAND_PP)[0]) if mask[i] else "Insufficient evidence",
                     "evidence": evidence if mask[i] else "insufficient",
                     "peak_share": float(view.share[i].max()), "peak_period": panel.periods[int(view.share[i].argmax())],
                     "posts_last_year": float(panel.posts[i, -4:].sum())})
        for j, h in enumerate(horizons):
            paths.append({"skill": sid, "period": future[j], "h": h, "forecast": pred[i, j],
                          "lo": max(0.0, pred[i, j] - half[j]), "hi": min(1.0, pred[i, j] + half[j])})
    return pd.DataFrame(rows), pd.DataFrame(paths)


def history_frame(panel):
    rows = []
    for i, sid in enumerate(panel.skills):
        rows.append(pd.DataFrame({"skill": sid, "period": panel.periods, "share": panel.share[i],
                                  "posts": panel.posts[i], "total": panel.total}))
    return pd.concat(rows, ignore_index=True)


def backtest_cells(table, panel, mask):
    """Holdout predictions of the main models, with skill ids and quarter labels, for the reliability charts."""
    t = table[table.model.isin(CELL_MODELS) & table.skill.isin(np.flatnonzero(mask))].dropna(subset=["pred"]).copy()
    t["skill"] = [panel.skills[i] for i in t.skill]
    t["origin_period"] = [panel.periods[T - 1] for T in t.origin]
    t["target_period"] = [panel.periods[T + h - 1] for T, h in zip(t.origin, t.h)]
    return t[["model", "skill", "origin_period", "target_period", "h", "pred", "actual", "base4"]].reset_index(drop=True)


def signal_frame(long):
    cols = [c for c in ("se_share", "npm_dl", "gh_share") if c in long]
    out = long[["period", "skill", *cols]].dropna(subset=cols, how="all")
    return out.reset_index(drop=True)


def run(warehouse=db.WAREHOUSE, gold=db.GOLD, today=None):
    warnings.filterwarnings("ignore")
    wh = db.connect(warehouse, readonly=True)
    try:
        long = P.build_long(wh, today)
        panel = P.to_panel(long)
        result, table = B.run(panel)
        selection, holdout, sel_end = B.cells(panel)
        mask = B.eligible_mask(panel, sel_end)
        models = build_models(result["selection"]["alpha_ses"], result["selection"]["phi_damped"])
        production, sel_scores = pick_production(panel, models, selection, mask)
        dir_model, dir_scores = pick_direction(panel, models, selection, mask)
        direction = direction_validation(table, dir_model, mask)
        quantiles = interval_quantiles(table, production, mask)
        series, paths = production_forecast(panel, models[production], models[dir_model], quantiles, mask,
                                            "validated" if direction["validated"] else "scenario_only")
        lead = {name: L.analyse(panel, name) for name in panel.signals}
        manifest = {
            "schema_version": 2, "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "evidence": {"source": "Hacker News 'Ask HN: Who is hiring?' monthly threads", "quarters": [panel.periods[0], panel.periods[-1]],
                         "n_quarters": len(panel.periods), "postings_total": int(panel.total.sum()), "skills_total": len(panel.skills),
                         "skills_eligible": int(mask.sum()), "signals_available": {k: int((~np.isnan(v).all(axis=1)).sum()) for k, v in panel.signals.items()}},
            "backtest": result,
            "production": {"model": production, "selection_mae_pp": {k: round(v, 4) for k, v in sel_scores.items()},
                           "direction_model": dir_model, "selection_direction_f1": {k: round(v, 4) for k, v in dir_scores.items()},
                           "direction_validation": direction, "interval_quantiles": {str(k): round(v, 4) for k, v in quantiles.items()},
                           "interval_coverage_80_holdout": round(coverage(table, production, mask, quantiles), 4)},
            "lead_lag": lead,
        }
        with db.session(gold) as g:
            db.write_table(g, "radar_series", series, indexes=["skill"])
            db.write_table(g, "radar_paths", paths, indexes=["skill"])
            db.write_table(g, "radar_history", history_frame(panel), indexes=[("skill", "period")])
            db.write_table(g, "backtest_cell", backtest_cells(table, panel, mask), indexes=["model", "skill"])
            db.write_table(g, "signal_quarter", signal_frame(long), indexes=["skill"])
            store.save_results(g, manifest)
            facts = analytics.build(wh, g, panel.periods, P.last_complete_month(today))
            C.write(g, C.run(g))                      # category-level forecast, reads the gold posting tables just written
        manifest["gold_facts"] = facts
    finally:
        wh.close()
    vacuum = db.connect(gold)
    vacuum.execute("VACUUM")
    vacuum.close()
    return manifest, series, paths


if __name__ == "__main__":
    manifest, series, _ = run()
    print("rate model:", manifest["production"]["model"], "| direction model:", manifest["production"]["direction_model"])
    print("direction validation:", manifest["production"]["direction_validation"])
    print(series[series.eligible].direction.value_counts().to_dict())
    print("gold facts:", manifest["gold_facts"])
