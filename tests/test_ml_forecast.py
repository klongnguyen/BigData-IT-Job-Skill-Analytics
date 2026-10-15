"""Tests for ML feature engineering, model training, and forecast serving."""

import pandas as pd
import pytest

from dashboard.data import load_gold, load_predictions
from src.ml.feature_engineering import build_feature_dataset, split_train_test_inference
from src.ml.train_forecast import train_and_evaluate


def test_feature_engineering_lags_and_labels():
    # Synthetic skill stats across 6 months
    rows = []
    for i, month in enumerate(["2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06"]):
        rows.append({
            "market": "GLOBAL",
            "source": "test_src",
            "occupation": "Data Engineer",
            "skill": "Python",
            "month": month,
            "demand_rate": 0.10 + (i * 0.01),  # Growing by 0.01 each month
            "occupation_job_count": 100,
            "skill_job_count": 10 + i,
        })
    df = pd.DataFrame(rows)

    feat_df = build_feature_dataset(df, source="test_src")
    assert "rate_t_1" in feat_df.columns
    assert "rate_t_2" in feat_df.columns
    assert "rate_t_3" in feat_df.columns
    assert "target_label" in feat_df.columns

    # Check that lag 1 for month 2 matches rate of month 1
    m2 = feat_df[feat_df["month"] == "2023-02"].iloc[0]
    assert m2["rate_t_1"] == pytest.approx(0.10)

    # Check target label for month 1 (growing by 0.01 > 0.003)
    m1 = feat_df[feat_df["month"] == "2023-01"].iloc[0]
    assert m1["target_label"] == "Growing"


def test_train_and_evaluate_pipeline():
    run = load_gold(dataset="legacy_2023")
    skill_stats = run.tables["skill_stats"]
    clf, preds, metrics = train_and_evaluate(skill_stats, n_estimators=20, max_depth=4)

    assert not preds.empty
    assert "predicted_label" in preds.columns
    assert "confidence_score" in preds.columns
    assert "target_month" in preds.columns

    assert metrics["accuracy"] >= 0.50
    assert metrics["macro_f1"] >= 0.40
    assert set(metrics["classes"]) == {"Declining", "Growing", "Stable"}

    # Verify future predictions
    fut = preds[preds["is_future_forecast"] == True]
    assert not fut.empty
    assert (fut["target_month"] == "2024-01").all()


def test_load_predictions_from_gold():
    preds, metrics = load_predictions()
    assert preds is not None
    assert metrics is not None
    assert len(preds) > 0
    assert "accuracy" in metrics
    assert "macro_f1" in metrics


def test_multi_year_forecasting_pipeline():
    from dashboard.data import load_multi_year_forecast
    from src.ml.multi_year_forecast import build_unified_multi_year_dataset, train_and_forecast_next_3_years

    g23 = load_gold(dataset="legacy_2023")
    g26 = load_gold(dataset="scoped_2026")

    unified = build_unified_multi_year_dataset(g23.tables["skill_stats"], g26.tables["skill_stats"])
    assert not unified.empty
    assert "rate_2023" in unified.columns
    assert "rate_2026" in unified.columns

    model, forecast_df, metrics = train_and_forecast_next_3_years(unified, n_estimators=20)
    assert not forecast_df.empty
    assert "rate_2027_pred" in forecast_df.columns
    assert "rate_2028_pred" in forecast_df.columns
    assert "rate_2029_pred" in forecast_df.columns
    assert "trend_label" in forecast_df.columns

    assert metrics["directional_accuracy"] >= 0.55
    assert metrics["backtest_mae"] < 0.05

    # Check loaded predictions from gold artifacts
    preds, loaded_metrics = load_multi_year_forecast()
    assert preds is not None
    assert loaded_metrics is not None
    assert len(preds) == len(forecast_df)
    assert loaded_metrics["forecast_window"] == "2027 - 2029 (2 to 3 years from present)"
    assert loaded_metrics["data_sources"]["total_jobs"] >= 800000
