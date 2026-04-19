import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import os
import subprocess


def get_git_root() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


DATA_DIR = os.path.join(get_git_root(), "data")


def load_data() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "ipc_predicted_vs_actual.csv")
    df = pd.read_csv(path, parse_dates=["projection_start", "projection_end", "predicted_reporting_date"])
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()

    # Drop rows with missing target
    df = df.dropna(subset=["pct_error"])

    # Time features
    df["projection_year"] = df["projection_start"].dt.year
    df["projection_month"] = df["projection_start"].dt.month
    df["forecast_year"] = df["predicted_reporting_date"].dt.year
    df["forecast_month"] = df["predicted_reporting_date"].dt.month

    # Encode categoricals
    df["country_code_enc"] = pd.Categorical(df["country_code"]).codes
    df["admin_1_enc"] = pd.Categorical(df["admin_1"].fillna("country_level")).codes

    feature_cols = [
        "country_code_enc",
        "admin_1_enc",
        "projection_year",
        "projection_month",
        "forecast_year",
        "forecast_month",
        "predicted_mid",
        "actual_mid",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]

    X = df[feature_cols]
    y = df["pct_error"]

    return X, y


def train(X: pd.DataFrame, y: pd.Series) -> XGBRegressor:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=25,
    )

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"\nTest MAE:  {mae:.2f}")
    print(f"Test R²:   {r2:.4f}")

    # Feature importance
    importance = pd.Series(model.feature_importances_, index=X.columns)
    print(f"\nFeature importances:\n{importance.sort_values(ascending=False).round(4)}")

    return model


if __name__ == "__main__":
    df = load_data()
    print(f"Loaded {len(df)} rows")

    X, y = prepare_features(df)
    print(f"Features: {X.columns.tolist()}")
    print(f"Target: pct_error — mean={y.mean():.2f}, std={y.std():.2f}")

    model = train(X, y)