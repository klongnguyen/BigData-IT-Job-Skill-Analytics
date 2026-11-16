"""Model results as relational tables in gold.db (replaces the old radar_manifest.json).

    run_info             key/value facts about the run (dates, protocol, production choices, direction validation)
    selection_score      parameter / model choice scores on the selection window only
    model_score          holdout error per model, with the paired-bootstrap comparison to the best baseline
    model_horizon_error  holdout error per model and forecast horizon
    label_score          direction-label macro-F1 per model and band (plus the 'always Stable' reference)
    interval_quantile    scaled error quantile that sets the 80% forecast interval, per horizon
    leadlag_signal, leadlag, leadlag_skill   does community activity move before hiring demand?
"""

import pandas as pd

from skill_radar import db

CI = ("ci_lo", "ci_hi")


def _flatten(manifest):
    ev, bt, prod = manifest["evidence"], manifest["backtest"], manifest["production"]
    proto, sel, dv = bt["protocol"], bt["selection"], prod["direction_validation"]
    info = {
        "schema_version": manifest["schema_version"], "created_at_utc": manifest["created_at_utc"],
        "evidence_source": ev["source"], "first_quarter": ev["quarters"][0], "last_quarter": ev["quarters"][1],
        "n_quarters": ev["n_quarters"], "postings_total": ev["postings_total"], "skills_total": ev["skills_total"],
        "skills_eligible": ev["skills_eligible"],
        "horizons": ",".join(str(h) for h in proto["horizons"]), "selection_end": proto["selection_end"],
        "holdout_targets": proto["holdout_targets"], "min_share": proto["min_share"], "band_pp": proto["band_pp"],
        "alpha_ses": sel["alpha_ses"], "phi_damped": sel["phi_damped"],
        "eligible_skills": bt["eligible_skills"], "with_signal_skills": bt["with_signal_skills"],
        "rate_model": prod["model"], "direction_model": prod["direction_model"],
        "dv_macro_f1_model": dv["macro_f1_model"], "dv_macro_f1_always_stable": dv["macro_f1_always_stable"],
        "dv_gain": dv["gain"], "dv_gain_lo": dv["gain_ci95"][0], "dv_gain_hi": dv["gain_ci95"][1], "dv_validated": int(dv["validated"]),
        "interval_coverage_80": prod["interval_coverage_80_holdout"],
    }
    info.update({f"signal_skills_{k}": v for k, v in ev["signals_available"].items()})
    return info


def _selection_rows(manifest):
    sel, prod = manifest["backtest"]["selection"], manifest["production"]
    rows = [("alpha_ses_mae", k, v) for k, v in sel["alpha_scores_mae_pp"].items()]
    rows += [("phi_damped_mae", k, v) for k, v in sel["phi_scores_mae_pp"].items()]
    rows += [("rate_model_mae", k, v) for k, v in prod["selection_mae_pp"].items()]
    rows += [("direction_model_f1", k, v) for k, v in prod["selection_direction_f1"].items()]
    return pd.DataFrame(rows, columns=["kind", "key", "value"]).astype({"key": str})


def _model_rows(manifest):
    scores, horizons = [], []
    for scope in ("all_eligible", "signal_covered"):
        block = manifest["backtest"].get(scope)
        if not block:
            continue
        for model, e in block["models"].items():
            cmp, eff = e.get("vs_best_baseline"), e.get("signal_effect")
            scores.append({"scope": scope, "model": model, "mae_pp": e["mae_pp"], "skills": block["skills"],
                           "baseline": cmp["baseline"] if cmp else None, "diff_pp": cmp["diff_pp"] if cmp else None,
                           "ci_lo": cmp["ci95"][0] if cmp else None, "ci_hi": cmp["ci95"][1] if cmp else None,
                           "signal_vs": eff["vs"] if eff else None, "signal_diff_pp": eff["diff_pp"] if eff else None,
                           "signal_ci_lo": eff["ci95"][0] if eff else None, "signal_ci_hi": eff["ci95"][1] if eff else None})
            for h, v in e["mae_pp_by_horizon"].items():
                horizons.append({"scope": scope, "model": model, "h": int(h), "mae_pp": v})
    return pd.DataFrame(scores), pd.DataFrame(horizons)


def _label_rows(manifest):
    rows = []
    for band, block in manifest["backtest"]["labels"].items():
        for model, e in block.items():
            support = e.get("support", {})
            rows.append({"band": float(band), "model": model, "macro_f1": e["macro_f1"] if e else None, "n": e["n"] if e else None,
                         "support_fading": support.get("Fading"), "support_stable": support.get("Stable"),
                         "support_rising": support.get("Rising")})
    return pd.DataFrame(rows)


def _leadlag_rows(manifest):
    signals, lags, per_skill = [], [], []
    for name, res in manifest["lead_lag"].items():
        res = res or {}
        signals.append({"signal": name, "n_skills": len(res.get("skills", [])), "note": res.get("note"),
                        "has_lags": int("lags" in res)})
        for k, v in res.get("lags", {}).items():
            lags.append({"signal": name, "lag": int(k), "mean_corr": v["mean_corr"], "ci_lo": v["ci95"][0], "ci_hi": v["ci95"][1],
                         "placebo_p": v["placebo_p"], "share_positive": v["share_positive"], "n_skills": v["skills"]})
            per_skill += [{"signal": name, "lag": int(k), "skill": s, "corr": c} for s, c in v["per_skill"].items()]
    return pd.DataFrame(signals), pd.DataFrame(lags), pd.DataFrame(per_skill)


def save_results(conn, manifest):
    db.kv_write(conn, "run_info", _flatten(manifest))
    db.write_table(conn, "selection_score", _selection_rows(manifest))
    scores, horizons = _model_rows(manifest)
    db.write_table(conn, "model_score", scores)
    db.write_table(conn, "model_horizon_error", horizons)
    db.write_table(conn, "label_score", _label_rows(manifest))
    q = manifest["production"]["interval_quantiles"]
    db.write_table(conn, "interval_quantile", pd.DataFrame({"h": [int(k) for k in q], "q": list(q.values())}))
    signals, lags, per_skill = _leadlag_rows(manifest)
    db.write_table(conn, "leadlag_signal", signals)
    db.write_table(conn, "leadlag", lags, indexes=["signal"])
    db.write_table(conn, "leadlag_skill", per_skill, indexes=["signal"])


def typed_info(raw):
    """run_info values are stored as text; convert the numeric ones."""
    out = {}
    for k, v in raw.items():
        try:
            out[k] = int(v) if v.lstrip("-").isdigit() else float(v)
        except (ValueError, AttributeError):
            out[k] = v
    return out


def load_results(conn):
    names = ("selection_score", "model_score", "model_horizon_error", "label_score", "interval_quantile",
             "leadlag_signal", "leadlag", "leadlag_skill")
    out = {n: db.read_sql(conn, f"SELECT * FROM {n}") for n in names}
    out["info"] = typed_info(db.kv_read(conn, "run_info"))
    return out
