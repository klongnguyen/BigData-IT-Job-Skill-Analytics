"""Feature engineering module for skill demand trend forecasting.

Constructs rolling lag features and trend target labels for (occupation, skill)
time-series pairs from audited Gold layer tables.
"""

from pathlib import Path
import numpy as np
import pandas as pd


THRESHOLD_EPSILON = 0.003  # 0.3 percentage points shift defines Growing vs Declining
FEATURE_COLUMNS = [
    "rate_t", "rate_t_1", "rate_t_2", "rate_t_3",
    "rolling_mean_3m", "rolling_slope_3m", "momentum", "acceleration",
    "log_occ_jobs", "log_skill_jobs"
]


def build_feature_dataset(skill_stats_df: pd.DataFrame, source: str = "kaggle_historical_archive") -> pd.DataFrame:
    """Extract and build time-series features and future target labels.

    Features generated per (market, source, occupation, skill, month=t):
      - rate_t: demand rate at month t
      - rate_t_1: demand rate at t - 1 month
      - rate_t_2: demand rate at t - 2 months
      - rate_t_3: demand rate at t - 3 months
      - rolling_mean_3m: mean of rates across t, t-1, t-2
      - rolling_slope_3m: linear slope across 3 months
      - momentum: rate_t - rate_t_1
      - acceleration: (rate_t - rate_t_1) - (rate_t_1 - rate_t_2)
      - occupation_job_count: total jobs for occupation at month t
      - skill_job_count: jobs requiring skill at month t
      - target_next_rate: demand rate at t + 1 month (if available)
      - target_delta: target_next_rate - rate_t
      - target_label: 'Growing', 'Stable', 'Declining'
    """
    df = skill_stats_df.copy()
    if source:
        df = df[df["source"] == source]

    # Ensure required columns
    required = ["market", "source", "occupation", "skill", "month", "demand_rate", "occupation_job_count", "skill_job_count"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column in skill_stats: {col}")

    # Sort strictly by series and chronological calendar month
    df = df.sort_values(["market", "source", "occupation", "skill", "month"]).reset_index(drop=True)

    series_group = df.groupby(["market", "source", "occupation", "skill"])

    # Compute historical lags
    df["rate_t"] = df["demand_rate"].astype(float)
    df["rate_t_1"] = series_group["demand_rate"].shift(1)
    df["rate_t_2"] = series_group["demand_rate"].shift(2)
    df["rate_t_3"] = series_group["demand_rate"].shift(3)

    # Rolling statistics
    df["rolling_mean_3m"] = (df["rate_t"] + df["rate_t_1"] + df["rate_t_2"]) / 3.0
    df["rolling_slope_3m"] = (df["rate_t"] - df["rate_t_2"]) / 2.0
    df["momentum"] = df["rate_t"] - df["rate_t_1"]
    df["acceleration"] = df["momentum"] - (df["rate_t_1"] - df["rate_t_2"])
    df["log_occ_jobs"] = np.log1p(df["occupation_job_count"].clip(lower=0))
    df["log_skill_jobs"] = np.log1p(df["skill_job_count"].clip(lower=0))

    # Target: month t + 1
    df["target_next_rate"] = series_group["demand_rate"].shift(-1)
    df["target_delta"] = df["target_next_rate"] - df["rate_t"]

    def assign_label(val):
        if pd.isna(val):
            return np.nan
        if val > THRESHOLD_EPSILON:
            return "Growing"
        elif val < -THRESHOLD_EPSILON:
            return "Declining"
        return "Stable"

    df["target_label"] = df["target_delta"].apply(assign_label)

    return df


def split_train_test_inference(feature_df: pd.DataFrame, train_cutoffs=None, test_cutoffs=None):
    """Split feature dataframe into train, test, and future inference sets.

    - Train set: records having complete lags and target, within train_cutoffs
    - Test set: records having complete lags and target, within test_cutoffs
    - Future inference set: latest available month records (complete lags, predict next unobserved month)
    """
    valid_lags = feature_df.dropna(subset=["rate_t_3"]).copy()

    if train_cutoffs is None:
        train_cutoffs = ["2023-04", "2023-05", "2023-06", "2023-07", "2023-08"]
    if test_cutoffs is None:
        test_cutoffs = ["2023-09", "2023-10", "2023-11"]

    train_df = valid_lags[valid_lags["month"].isin(train_cutoffs) & valid_lags["target_label"].notna()].copy()
    test_df = valid_lags[valid_lags["month"].isin(test_cutoffs) & valid_lags["target_label"].notna()].copy()

    # The latest month in series (e.g. 2023-12) used to forecast the future month (e.g. 2024-01)
    max_month = valid_lags["month"].max()
    future_df = valid_lags[valid_lags["month"] == max_month].copy()

    return train_df, test_df, future_df
