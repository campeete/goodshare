import requests
import pandas as pd
import numpy as np

import requests

# Get an access token using a username and password
credentials = {"username": "alexander8", "password": "fewsnet1"}
response = requests.post("https://fdw.fews.net/api-token-auth/", data=credentials)
response.raise_for_status()
token = response.json()["token"]

# Set the authorization header to send with every request
HEADERS =  {"Authorization": "JWT " + token}

import requests
import pandas as pd
from urllib.parse import urlencode

BASE_URL = "https://fdw.fews.net/api"

COUNTRIES = ["HT", "SD", "ET", "ML", "NE", "SO"]

def get_paginated(endpoint: str, params: dict) -> list:
    results = []
    base_url = f"{BASE_URL}/{endpoint}/"
    query_string = urlencode(params, safe="+")
    url = f"{base_url}?{query_string}"

    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            results.extend(data)
            break
        else:
            results.extend(data.get("results", []))
            url = data.get("next")

    return results


def get_ipc_population_size(scenario: str, start_date: str, end_date: str) -> pd.DataFrame:
    all_results = []
    for country_code in COUNTRIES:
        for unit_type in [None, "admin1"]:
            params = {
                "country_code": country_code,
                "format": "json",
                "fields": "simple",
                "scenario": scenario,
                "start_date": start_date,
                "end_date": end_date,
            }
            if unit_type:
                params["unit_type"] = unit_type

            rows = get_paginated("ipcpopulationsize", params)
            label = unit_type or "country"
            print(f"  [{scenario}] {country_code} ({label}): {len(rows)} records")
            all_results.extend(rows)

    df = pd.DataFrame(all_results)

    # Drop duplicates in case country-level and admin1 pulls overlap
    if not df.empty:
        df = df.drop_duplicates(subset=["id"])

    return df

def build_comparison(start_date: str, end_date: str) -> pd.DataFrame:
    print("Fetching actual (CS)...")
    df_actual = get_ipc_population_size("CS", start_date, end_date)

    print("\nFetching predicted (ML)...")
    df_predicted = get_ipc_population_size("ML", start_date, end_date)

    for df in [df_actual, df_predicted]:
        for col in ["reporting_date", "projection_start", "projection_end"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

    actual_cols = [
        "country", "country_code", "fnid", "admin_0", "admin_1",
        "projection_start", "projection_end",
        "population_range", "reporting_date",
        "low_value", "high_value",
    ]
    predicted_cols = [
        "country", "country_code", "fnid", "admin_0", "admin_1",
        "projection_start", "projection_end",
        "population_range", "reporting_date",
        "low_value", "high_value",
    ]

    actual_cols = [c for c in actual_cols if c in df_actual.columns]
    predicted_cols = [c for c in predicted_cols if c in df_predicted.columns]

    df_actual = df_actual[actual_cols].copy().rename(columns={
        "low_value": "actual_low",
        "high_value": "actual_high",
        "population_range": "actual_range",
        "reporting_date": "actual_reporting_date",
    })
    df_predicted = df_predicted[predicted_cols].copy().rename(columns={
        "low_value": "predicted_low",
        "high_value": "predicted_high",
        "population_range": "predicted_range",
        "reporting_date": "predicted_reporting_date",
    })

    merge_keys = ["country_code", "fnid", "projection_start", "projection_end"]
    df = pd.merge(df_predicted, df_actual, on=merge_keys, suffixes=("_pred", "_act"))

    df["actual_mid"] = (df["actual_low"] + df["actual_high"]) / 2
    df["predicted_mid"] = (df["predicted_low"] + df["predicted_high"]) / 2

    df["difference"] = df["predicted_mid"] - df["actual_mid"]
    df["pct_error"] = (df["difference"] / df["actual_mid"]).round(4) * 100
    
    for col in ["country", "admin_0", "admin_1"]:
        pred_col, act_col = f"{col}_pred", f"{col}_act"
        if pred_col in df.columns:
            df[col] = df[pred_col]
            df = df.drop(columns=[c for c in [pred_col, act_col] if c in df.columns])

    front_cols = [
    "country", "country_code", "admin_0", "admin_1",
    "projection_start", "projection_end", "predicted_reporting_date",
    "predicted_low", "predicted_high", "predicted_mid", "predicted_range",
    "actual_low", "actual_high", "actual_mid", "actual_range",
    "difference", "pct_error",
]
    front_cols = [c for c in front_cols if c in df.columns]
    remaining = [c for c in df.columns if c not in front_cols]
    return df[front_cols + remaining].sort_values(["country_code", "projection_start"])


def summarize_by_country_and_time(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["year"] = df["projection_start"].dt.year

    return (
        df.groupby(["country", "year"])
        .agg(
            n_forecasts=("pct_error", "count"),
            mean_pct_error=("pct_error", "mean"),
            median_pct_error=("pct_error", "median"),
            iqr_pct_error=("pct_error", lambda x: round(x.quantile(0.75) - x.quantile(0.25), 2)),
            mae=("difference", lambda x: x.abs().mean()),
            bias=("difference", "mean"),
        )
        .round(2)
        .reset_index()
    )


def summarize_overall(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("country")
        .agg(
            n_forecasts=("pct_error", "count"),
            mean_pct_error=("pct_error", "mean"),
            median_pct_error=("pct_error", "median"),
            iqr_pct_error=("pct_error", lambda x: round(x.quantile(0.75) - x.quantile(0.25), 2)),
            mae=("difference", lambda x: x.abs().mean()),
            bias=("difference", "mean"),
        )
        .round(2)
        .reset_index()
    )

import os
import subprocess

def get_git_root() -> str:
    """Find the root of the git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


if __name__ == "__main__":
    from datetime import date

    end_date = date.today().isoformat()  # e.g
    
    df_comparison = build_comparison(start_date="2020-01-01", end_date=end_date)
    print(f"\nMatched rows: {len(df_comparison)}")

    df_summary = summarize_by_country_and_time(df_comparison)
    print(f"\nAccuracy by country and year:\n{df_summary.to_string()}")

    df_overall = summarize_overall(df_comparison)
    print(f"\nOverall accuracy by country:\n{df_overall.to_string()}")

    DATA_DIR = os.path.join(get_git_root(), "data")
    

    df_comparison.to_csv(os.path.join(DATA_DIR , "ipc_predicted_vs_actual.csv"), index=False)
    df_summary.to_csv(os.path.join(DATA_DIR, "ipc_accuracy_by_country_and_year.csv"), index=False)
    df_overall.to_csv(os.path.join(DATA_DIR, "ipc_accuracy_overall.csv"), index=False)
    print("\nSaved: ipc_predicted_vs_actual.csv, ipc_accuracy_by_country_and_year.csv, ipc_accuracy_overall.csv")
    print(f"\nSaved files to:{DATA_DIR}")
    
    