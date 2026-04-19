import pandas as pd
import numpy as np
from xgboost import XGBRegressor
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


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
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
        ]
    feature_cols = [c for c in feature_cols if c in df.columns]

    X = df[feature_cols]
    y = df["actual_mid"]

    return X, y, df


from sklearn.inspection import permutation_importance
from scipy import stats


def calculate_significance(model: XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
    """
    1. Permutation importance — how much does each feature matter?
    2. Permutation test — is the model's overall performance better than chance?
    """
    # --- Feature significance via permutation importance ---
    perm = permutation_importance(model, X_test, y_test, n_repeats=30, random_state=42, n_jobs=-1)

    importance_df = pd.DataFrame({
        "feature": X_test.columns,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
        # z-score: how many std deviations above zero is the importance?
        "z_score": perm.importances_mean / (perm.importances_std + 1e-10),
        # one-tailed p-value from z-score
        "p_value": stats.norm.sf(perm.importances_mean / (perm.importances_std + 1e-10)),
        "significant": perm.importances_mean / (perm.importances_std + 1e-10) > 1.96,  # p < 0.05
    }).sort_values("importance_mean", ascending=False).round(4)

    print(f"\nPermutation feature importance:\n{importance_df.to_string()}")

    # --- Overall model significance via permutation test ---
    n_permutations = 1000
    baseline_mae = mean_absolute_error(y_test, model.predict(X_test))
    permuted_maes = []

    for _ in range(n_permutations):
        y_permuted = y_test.sample(frac=1, random_state=None).values
        permuted_maes.append(mean_absolute_error(y_permuted, model.predict(X_test)))

    permuted_maes = np.array(permuted_maes)
    # p-value: proportion of permutations where random MAE <= model MAE
    p_value_overall = (permuted_maes <= baseline_mae).mean()

    print(f"\nOverall model significance:")
    print(f"  Baseline MAE:      {baseline_mae:.4f}")
    print(f"  Permuted MAE mean: {permuted_maes.mean():.4f}")
    print(f"  p-value:           {p_value_overall:.4f}")
    print(f"  Significant:       {p_value_overall < 0.05}")

    return importance_df


from sklearn.model_selection import GridSearchCV, PredefinedSplit
import numpy as np


def train(X: pd.DataFrame, y: pd.Series, df: pd.DataFrame) -> XGBRegressor:
    train_mask = df["projection_year"] < 2023
    X_train, X_test = X[train_mask], X[~train_mask]
    y_train, y_test = y[train_mask], y[~train_mask]

    print(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")

    # Use a PredefinedSplit so grid search respects the temporal split
    # -1 = training fold, 0 = validation fold
    # Use the last 20% of training data as the validation fold
    n_val = int(len(X_train) * 0.2)
    split_index = [-1] * (len(X_train) - n_val) + [0] * n_val
    ps = PredefinedSplit(test_fold=split_index)

    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [3, 4, 6],
        "learning_rate": [0.01, 0.05, 0.1],
        "subsample": [0.7, 0.8, 1.0],
        "colsample_bytree": [0.7, 0.8, 1.0],
    }

    model = XGBRegressor(random_state=42, n_jobs=-1)

    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        scoring="neg_mean_absolute_error",
        cv=ps,
        verbose=2,
        n_jobs=-1,
    )

    print("\nRunning grid search...")
    grid_search.fit(X_train, y_train)

    print(f"\nBest parameters: {grid_search.best_params_}")
    print(f"Best CV MAE: {-grid_search.best_score_:.4f}")

    best_model = grid_search.best_estimator_

    # Evaluate on held-out test set
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"\nTest MAE:  {mae:.2f}")
    print(f"Test R2:   {r2:.4f}")

    # Save grid search results
    results_df = pd.DataFrame(grid_search.cv_results_)
    results_df.to_csv(os.path.join(DATA_DIR, "xgb_grid_search_results.csv"), index=False)
    print(f"\nGrid search results saved to {DATA_DIR}")

    importance_df = calculate_significance(best_model, X_test, y_test)
    importance_df.to_csv(os.path.join(DATA_DIR, "xgb_feature_significance.csv"), index=False)

    return best_model


if __name__ == "__main__":
    df = load_data()
    print(f"Loaded {len(df)} rows")

    X, y, df = prepare_features(df)
    print(f"Features: {X.columns.tolist()}")
    print(f"Target: pct_error - mean={y.mean():.2f}, std={y.std():.2f}")

    model = train(X, y, df)