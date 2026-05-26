"""
手动测试 services/ml_service.py。

运行方式：
    python tests/test_ml_service.py
"""
from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from services.ml_service import compare_regression_models, run_linear_regression


def main() -> None:
    csv_path = PROJECT_ROOT / "data" / "sample_housing.csv"
    df = pd.read_csv(csv_path)

    features = ["sqft", "bedrooms", "bathrooms", "age"]
    target = "price"
    model_columns = features + [target]
    df = df.dropna(subset=model_columns).copy()

    print(f"features: {features}")
    print(f"target: {target}")
    print(f"rows_after_dropna: {len(df)}")

    regression_result = run_linear_regression(df, features, target)
    print("\nLinear regression result:")
    print(f"R²: {regression_result['r2_score']}")
    print(f"MSE: {regression_result['mse']}")
    print(f"MAE: {regression_result['mae']}")
    print(f"coefficients: {regression_result['coefficients']}")
    print(f"intercept: {regression_result['intercept']}")
    print(
        "train_size/test_size: "
        f"{regression_result['train_size']}/{regression_result['test_size']}"
    )
    print(f"scatter_chart_path: {regression_result['scatter_chart_path']}")

    compare_result = compare_regression_models(df, features, target)
    print("\nModel comparison result:")
    print(f"comparison: {compare_result['comparison']}")
    print(f"best_algorithm: {compare_result['best_algorithm']}")

    assert "r2_score" in regression_result
    assert regression_result["mse"] >= 0
    assert regression_result["mae"] >= 0
    assert isinstance(regression_result["coefficients"], dict)
    assert regression_result["scatter_chart_path"].startswith("/outputs/charts/")
    assert len(compare_result["comparison"]) >= 3
    assert compare_result["best_algorithm"]

    print("\nAll ml_service checks passed.")


if __name__ == "__main__":
    main()
