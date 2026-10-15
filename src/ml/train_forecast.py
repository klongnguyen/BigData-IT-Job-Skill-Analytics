"""Model training and forecasting pipeline for IT skill demand trends.

Supports training Random Forest / GBT models on 12-month historical series (2023),
evaluating with rolling-origin future backtest, and publishing prediction artifacts
to the Gold serving layer for Dashboard visualization.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from src.ml.feature_engineering import (
    FEATURE_COLUMNS,
    build_feature_dataset,
    split_train_test_inference,
)


def train_and_evaluate(
    skill_stats_df: pd.DataFrame,
    source: str = "kaggle_historical_archive",
    n_estimators: int = 100,
    max_depth: int = 6,
    random_state: int = 42,
):
    """Train ML model on feature dataset, evaluate on test set, and generate forecasts."""
    feature_df = build_feature_dataset(skill_stats_df, source=source)
    train_df, test_df, future_df = split_train_test_inference(feature_df)

    if train_df.empty or test_df.empty:
        raise ValueError("Insufficient feature rows for training/testing splits.")

    features = [
        "rate_t", "rate_t_1", "rate_t_2", "rate_t_3",
        "rolling_mean_3m", "rolling_slope_3m", "momentum", "acceleration",
        "log_occ_jobs", "log_skill_jobs"
    ]

    X_train, y_train = train_df[features], train_df["target_label"]
    X_test, y_test = test_df[features], test_df["target_label"]

    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    # Evaluate on test set
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)
    classes = list(clf.classes_)

    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()
    report = classification_report(y_test, y_pred, output_dict=True)

    feat_importances = {feat: float(imp) for feat, imp in zip(features, clf.feature_importances_)}

    # Construct test evaluation predictions dataframe
    test_results = test_df[[
        "market", "source", "occupation", "skill", "month", "demand_rate",
        "target_next_rate", "target_delta", "target_label"
    ]].copy()
    test_results.rename(columns={
        "month": "cutoff_month",
        "demand_rate": "rate_t",
        "target_label": "actual_label",
    }, inplace=True)

    # Target month is next month
    def next_month_str(m_str):
        y, m = map(int, m_str.split("-"))
        m_next = m + 1
        y_next = y
        if m_next > 12:
            m_next = 1
            y_next += 1
        return f"{y_next:04d}-{m_next:02d}"

    test_results["target_month"] = test_results["cutoff_month"].apply(next_month_str)
    test_results["predicted_label"] = y_pred
    test_results["confidence_score"] = np.max(y_prob, axis=1).round(4)
    test_results["is_future_forecast"] = False
    test_results["model_name"] = "RandomForest_TimeLag_v1"

    # Construct future inference predictions (from latest available month 2023-12 forecasting 2024-01)
    future_results = pd.DataFrame()
    if not future_df.empty:
        X_future = future_df[features]
        future_pred = clf.predict(X_future)
        future_prob = clf.predict_proba(X_future)

        future_results = future_df[[
            "market", "source", "occupation", "skill", "month", "demand_rate"
        ]].copy()
        future_results.rename(columns={
            "month": "cutoff_month",
            "demand_rate": "rate_t",
        }, inplace=True)
        future_results["target_next_rate"] = np.nan
        future_results["target_delta"] = np.nan
        future_results["actual_label"] = np.nan
        future_results["target_month"] = future_results["cutoff_month"].apply(next_month_str)
        future_results["predicted_label"] = future_pred
        future_results["confidence_score"] = np.max(future_prob, axis=1).round(4)
        future_results["is_future_forecast"] = True
        future_results["model_name"] = "RandomForest_TimeLag_v1"

    predictions_df = pd.concat([test_results, future_results], ignore_index=True)

    metrics = {
        "model_name": "RandomForest_TimeLag_v1",
        "framework": "PySpark MLlib / Scikit-Learn Hybrid",
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "future_samples": len(future_df),
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "classes": classes,
        "confusion_matrix": cm,
        "classification_report": report,
        "feature_importances": feat_importances,
    }

    return clf, predictions_df, metrics


def save_prediction_artifacts(predictions_df: pd.DataFrame, metrics: dict, output_dir: Path):
    """Save prediction parquet table and metrics json into target directory."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / "predictions.parquet"
    predictions_df.to_parquet(parquet_path, index=False)

    metrics_path = output_dir / "model_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return parquet_path, metrics_path
