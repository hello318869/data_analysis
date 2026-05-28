"""数据清洗模块 - 完整测试。

直接运行:
    python -m data_cleaning.test_clean
或从项目根目录:
    python data_cleaning/test_clean.py
"""

from __future__ import annotations

import json
import os
import sys
from base64 import b64encode

import itsdangerous
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from data_cleaning.service import (
    analyze_missing,
    detect_outliers_iqr,
    execute_clean,
    auto_clean,
)
from data_cleaning.app import app, _df_to_json, SECRET_KEY

client = TestClient(app)
_SIGNER = itsdangerous.TimestampSigner(SECRET_KEY)


def _set_session_cookie(data: dict) -> None:
    encoded = b64encode(json.dumps(data).encode()).decode()
    signed = _SIGNER.sign(encoded)
    client.cookies.clear()
    client.cookies["session"] = signed.decode() if isinstance(signed, bytes) else signed


def _update_session_cookie(resp) -> None:
    """Extract Set-Cookie from response and update client cookies."""
    for cookie in resp.headers.get_list("set-cookie"):
        if cookie.startswith("session="):
            val = cookie.split(";")[0].split("=", 1)[1]
            client.cookies.clear()
            client.cookies["session"] = val
            return


def _clear_session_cookie() -> None:
    client.cookies.clear()


def set_session_df(df: pd.DataFrame, filename: str = "test.csv") -> None:
    _set_session_cookie({
        "df_json": _df_to_json(df),
        "filename": filename,
    })


PASS = 0
FAIL = 0


def check(condition: bool, label: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}")


# ============================================================
# Test data
# ============================================================

COL_A = "num_a"
COL_B = "num_b"
COL_C = "cat_c"
COL_D = "full_d"


def make_test_df() -> pd.DataFrame:
    data = {
        COL_A: [1.0, 2.0, None, 4.0, 100.0, 5.0, 6.0],
        COL_B: [10.0, 20.0, 30.0, None, 1000.0, 40.0, 50.0],
        COL_C: ["X", "Y", None, "Y", "Z", "X", "Y"],
        COL_D: [1, 2, 3, 4, 5, 6, 7],
    }
    return pd.DataFrame(data)


# ============================================================
# service.py unit tests
# ============================================================

def test_analyze_missing() -> None:
    print("\n" + "=" * 60)
    print("Test analyze_missing")
    print("=" * 60)

    df = make_test_df()
    report = analyze_missing(df)

    check(isinstance(report, list), "return type is list")
    check(len(report) == 3, f"expected 3 cols with missing, got {len(report)}")

    cols = {r["column"] for r in report}
    check(cols == {COL_A, COL_B, COL_C}, "correct cols have missing")

    for r in report:
        check(r["missing_count"] >= 1, f"{r['column']} missing_count >= 1")
        check(isinstance(r["missing_pct"], (int, float)), f"{r['column']} missing_pct is numeric")
        check(isinstance(r["dtype"], str), f"{r['column']} dtype is str")

    df_full = pd.DataFrame({"a": [1, 2, 3]})
    check(len(analyze_missing(df_full)) == 0, "no missing returns empty")


def test_detect_outliers_iqr() -> None:
    print("\n" + "=" * 60)
    print("Test detect_outliers_iqr")
    print("=" * 60)

    df = make_test_df()
    report = detect_outliers_iqr(df)

    check(isinstance(report, list), "return type is list")
    outlier_cols = {r["column"] for r in report}
    check(outlier_cols == {COL_A, COL_B}, "outliers detected in num_a, num_b")

    for r in report:
        check(r["outlier_count"] >= 1, f"{r['column']} outlier_count >= 1")
        check(isinstance(r["outlier_indices"], list), f"{r['column']} outlier_indices is list")
        check(r["lower_bound"] < r["upper_bound"], f"{r['column']} lower < upper")

    df_normal = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
    check(len(detect_outliers_iqr(df_normal)) == 0, "no outliers returns empty")


def test_execute_clean_all_strategies() -> None:
    print("\n" + "=" * 60)
    print("Test execute_clean - all strategies")
    print("=" * 60)

    df = make_test_df()

    # mean
    r, c, msgs = execute_clean(df.copy(), "mean", [COL_A, COL_B])
    check(r[COL_A].isna().sum() == 0, "mean: num_a no missing")
    check(r[COL_B].isna().sum() == 0, "mean: num_b no missing")
    check(c >= 2, f"mean: at least 2 cells, got {c}")

    # median
    r, c, msgs = execute_clean(df.copy(), "median", [COL_A])
    check(r[COL_A].isna().sum() == 0, "median: num_a no missing")

    # mode
    r, c, msgs = execute_clean(df.copy(), "mode", [COL_C])
    check(r[COL_C].isna().sum() == 0, "mode: cat_c no missing")
    check(r.loc[2, COL_C] == "Y", "mode: filled with 'Y'")

    # drop
    r, c, msgs = execute_clean(df.copy(), "drop", [COL_A])
    check(len(r) == 6, f"drop: expected 6 rows, got {len(r)}")

    # custom
    r, c, msgs = execute_clean(df.copy(), "custom", [COL_A], fill_value=-999)
    check(r[COL_A].isna().sum() == 0, "custom: num_a no missing")
    check(r.loc[2, COL_A] == -999.0, "custom: filled with -999")

    # non-numeric with mean
    r, c, msgs = execute_clean(df.copy(), "mean", [COL_C])
    check(any("non-numeric" in m.lower() or "not numeric" in m.lower() or "\u975e\u6570\u503c" in m for m in msgs),
          "non-numeric skips mean")
    check(r[COL_C].isna().sum() == 1, "cat_c not modified")

    # invalid column
    r, c, msgs = execute_clean(df.copy(), "mean", ["nonexistent", COL_A])
    check(any("\u4e0d\u5b58\u5728" in m for m in msgs), "invalid col reported")


def test_auto_clean() -> None:
    print("\n" + "=" * 60)
    print("Test auto_clean")
    print("=" * 60)

    df = make_test_df()
    r, c, msgs = auto_clean(df)

    check(r.isna().sum().sum() == 0, "all missing handled")
    check(any("\u4e2d\u4f4d\u6570" in m for m in msgs), "numeric cols use median")
    check(any("\u4f17\u6570" in m for m in msgs), "categorical cols use mode")
    check(any("\u622a\u65ad" in m for m in msgs), "outliers clipped")
    check(r[COL_A].max() <= df[COL_A].max(), "num_a outlier clipped")
    check(r[COL_B].max() <= df[COL_B].max(), "num_b outlier clipped")


def test_edge_cases() -> None:
    print("\n" + "=" * 60)
    print("Test edge cases")
    print("=" * 60)

    df_empty = pd.DataFrame()
    check(len(analyze_missing(df_empty)) == 0, "empty df missing report empty")
    check(len(detect_outliers_iqr(df_empty)) == 0, "empty df outlier report empty")

    df_all_none = pd.DataFrame({"a": [None, None, None, None, None]})
    rpt = analyze_missing(df_all_none)
    check(len(rpt) == 1 and rpt[0]["missing_count"] == 5, "all-none col detected")

    r, c, msgs = execute_clean(df_all_none.copy(), "drop", ["a"])
    check(len(r) == 0, "drop all-none makes empty df")


# ============================================================
# API endpoint tests
# ============================================================

def test_get_clean_no_data() -> None:
    print("\n" + "=" * 60)
    print("Test GET /clean - no data")
    print("=" * 60)

    _clear_session_cookie()
    resp = client.get("/clean")
    check(resp.status_code == 400, f"expected 400, got {resp.status_code}")
    check("detail" in resp.json(), "response has detail")


def test_get_clean_with_data() -> None:
    print("\n" + "=" * 60)
    print("Test GET /clean - with data")
    print("=" * 60)

    df = make_test_df()
    set_session_df(df)

    resp = client.get("/clean")
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")

    data = resp.json()
    for key in ("missing_report", "outlier_report", "columns", "rows", "row_count", "column_count"):
        check(key in data, f"response has {key}")

    check(len(data["missing_report"]) == 3, f"missing_report has 3 entries, got {len(data['missing_report'])}")
    check(len(data["outlier_report"]) == 2, f"outlier_report has 2 entries, got {len(data['outlier_report'])}")


def test_post_clean_execute() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/execute - mean fill")
    print("=" * 60)

    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/execute", json={
        "strategy": "mean",
        "columns": [COL_A, COL_B],
        "fill_value": None,
    })
    _update_session_cookie(resp)
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")

    data = resp.json()
    check("message" in data, "has message")
    check("cleaned_count" in data, "has cleaned_count")
    check(data["cleaned_count"] >= 2, f"at least 2 cells cleaned, got {data['cleaned_count']}")

    # verify session updated via re-GET (cat_c still has 1 missing)
    resp2 = client.get("/clean")
    check(resp2.status_code == 200, "session updated: GET /clean ok")
    data2 = resp2.json()
    check(len(data2["missing_report"]) == 1, f"only cat_c missing remains, got {len(data2['missing_report'])}")


def test_post_clean_execute_custom_and_drop() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/execute - custom & drop")
    print("=" * 60)

    # custom fill
    df = make_test_df()
    set_session_df(df)
    resp = client.post("/clean/execute", json={
        "strategy": "custom",
        "columns": [COL_A],
        "fill_value": -999,
    })
    _update_session_cookie(resp)
    check(resp.status_code == 200, "custom: 200")
    data = resp.json()
    check(data["cleaned_count"] == 1, f"custom: 1 cell, got {data['cleaned_count']}")

    # drop
    df = make_test_df()
    set_session_df(df)
    resp = client.post("/clean/execute", json={
        "strategy": "drop",
        "columns": [COL_A],
        "fill_value": None,
    })
    _update_session_cookie(resp)
    check(resp.status_code == 200, "drop: 200")
    data = resp.json()
    check(data["row_count"] < 7, f"drop: row count reduced to {data['row_count']}")


def test_post_clean_execute_validation() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/execute - validation")
    print("=" * 60)

    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/execute", json={
        "strategy": "mean",
        "columns": [],
        "fill_value": None,
    })
    check(resp.status_code == 400, "empty columns returns 400")

    resp = client.post("/clean/execute", json={
        "strategy": "invalid_strategy",
        "columns": [COL_A],
        "fill_value": None,
    })
    check(resp.status_code == 400, "invalid strategy returns 400")


def test_post_clean_auto() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/auto")
    print("=" * 60)

    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/auto")
    _update_session_cookie(resp)
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")

    data = resp.json()
    check("message" in data, "has message")
    check("cleaned_count" in data, "has cleaned_count")
    check(len(data["missing_report"]) == 0, "auto clean: no missing left")
    check(data["cleaned_count"] == 3, f"auto clean: 3 cells, got {data['cleaned_count']}")

    # verify session updated
    resp2 = client.get("/clean")
    data2 = resp2.json()
    check(len(data2["missing_report"]) == 0, "session df has no missing")


def test_health() -> None:
    print("\n" + "=" * 60)
    print("Test GET /health")
    print("=" * 60)

    resp = client.get("/health")
    check(resp.status_code == 200, "health returns 200")
    check(resp.json() == {"status": "ok"}, "health returns ok")


# ============================================================
# API contract format validation
# ============================================================

def test_api_contract_formats() -> None:
    print("\n" + "=" * 60)
    print("Test API contract data formats")
    print("=" * 60)

    df = make_test_df()

    for item in analyze_missing(df):
        check(isinstance(item["column"], str), "missing_report: column is str")
        check(isinstance(item["missing_count"], int), "missing_report: missing_count is int")
        check(isinstance(item["missing_pct"], (int, float)), "missing_report: missing_pct is numeric")
        check(isinstance(item["dtype"], str), "missing_report: dtype is str")

    for item in detect_outliers_iqr(df):
        check(isinstance(item["column"], str), "outlier_report: column is str")
        check(isinstance(item["outlier_count"], int), "outlier_report: outlier_count is int")
        check(isinstance(item["outlier_indices"], list), "outlier_report: outlier_indices is list")
        check(isinstance(item["lower_bound"], (int, float)), "outlier_report: lower_bound is numeric")
        check(isinstance(item["upper_bound"], (int, float)), "outlier_report: upper_bound is numeric")


# ============================================================
# config.py tests
# ============================================================

from data_cleaning.config import (
    ColumnRule, RuleSet, PRESETS,
    validate_ruleset, apply_ruleset,
    save_ruleset, load_ruleset, delete_ruleset, list_saved_rules,
)


def test_config_presets() -> None:
    print("\n" + "=" * 60)
    print("Test config presets")
    print("=" * 60)

    check("numeric" in PRESETS, "numeric preset exists")
    check("categorical" in PRESETS, "categorical preset exists")
    check("full" in PRESETS, "full preset exists")

    numeric = PRESETS["numeric"]
    check(numeric.name == "numeric_default", "numeric preset name")
    check(len(numeric.rules) == 1, "numeric preset has 1 rule")


def test_config_apply_ruleset() -> None:
    print("\n" + "=" * 60)
    print("Test config apply_ruleset")
    print("=" * 60)

    df = make_test_df()
    ruleset = PRESETS["numeric"]
    r, c, msgs = apply_ruleset(df, ruleset)

    check(r[COL_A].isna().sum() == 0, "ruleset: num_a no missing")
    check(r[COL_B].isna().sum() == 0, "ruleset: num_b no missing")
    check(any("\u4e2d\u4f4d\u6570" in m for m in msgs), "ruleset: median fill used")
    check(c >= 2, f"ruleset: at least 2 cells cleaned, got {c}")


def test_config_validate() -> None:
    print("\n" + "=" * 60)
    print("Test config validate_ruleset")
    print("=" * 60)

    valid = PRESETS["numeric"]
    errors = validate_ruleset(valid)
    check(len(errors) == 0, f"valid ruleset has no errors, got {errors}")

    bad = RuleSet(name="")
    errors = validate_ruleset(bad)
    check(len(errors) > 0, "empty name rejects")

    bad2 = RuleSet(name="bad", rules=[ColumnRule(column="a", missing_strategy="invalid")])
    errors = validate_ruleset(bad2)
    check(len(errors) > 0, "invalid strategy rejects")

    bad3 = RuleSet(name="bad", rules=[ColumnRule(column="a", missing_strategy="custom", fill_value=None)])
    errors = validate_ruleset(bad3)
    check(len(errors) > 0, "custom without fill_value rejects")


def test_config_persistence() -> None:
    print("\n" + "=" * 60)
    print("Test config save/load/delete")
    print("=" * 60)

    ruleset = RuleSet(
        name="__test_temp__",
        description="temp",
        rules=[ColumnRule(column="test_col", missing_strategy="median")],
    )

    path = save_ruleset(ruleset)
    check(os.path.isfile(path), f"saved to {path}")
    check("__test_temp__" in list_saved_rules(), "appears in saved list")

    loaded = load_ruleset("__test_temp__")
    check(loaded is not None, "load succeeds")
    if loaded:
        check(loaded.name == "__test_temp__", "loaded name matches")
        check(len(loaded.rules) == 1, "loaded rule count matches")

    check(delete_ruleset("__test_temp__"), "delete succeeds")
    check("__test_temp__" not in list_saved_rules(), "removed from saved list")
    check(not delete_ruleset("__test_temp__"), "double delete returns False")
    check(load_ruleset("__nonexistent__") is None, "nonexistent returns None")


# ============================================================
# /clean/rules API endpoint tests
# ============================================================

def test_api_list_rules() -> None:
    print("\n" + "=" * 60)
    print("Test GET /clean/rules")
    print("=" * 60)

    resp = client.get("/clean/rules")
    check(resp.status_code == 200, "returns 200")
    data = resp.json()
    check("presets" in data, "has presets")
    check("saved" in data, "has saved")
    check(isinstance(data["presets"], list), "presets is list")
    check(isinstance(data["saved"], list), "saved is list")
    check("numeric" in data["presets"], "numeric in presets")


def test_api_get_rule_detail() -> None:
    print("\n" + "=" * 60)
    print("Test GET /clean/rules/{name}")
    print("=" * 60)

    resp = client.get("/clean/rules/numeric")
    check(resp.status_code == 200, "returns 200")
    data = resp.json()
    check(data["name"] == "numeric_default", "correct preset detail")

    resp = client.get("/clean/rules/nonexistent")
    check(resp.status_code == 404, "nonexistent returns 404")


def test_api_apply_rule_by_name() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/rules/apply - by name")
    print("=" * 60)

    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/rules/apply", json={"name": "numeric"})
    _update_session_cookie(resp)
    check(resp.status_code == 200, f"returns 200, got {resp.status_code}")

    data = resp.json()
    check("message" in data, "has message")
    check("cleaned_count" in data, "has cleaned_count")
    check(data["cleaned_count"] >= 2, f"at least 2 cells cleaned, got {data['cleaned_count']}")

    # verify session
    resp2 = client.get("/clean")
    missing = [m["column"] for m in resp2.json()["missing_report"]]
    check(COL_A not in missing, "num_a no longer missing")
    check(COL_B not in missing, "num_b no longer missing")


def test_api_apply_rule_inline() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/rules/apply - inline")
    print("=" * 60)

    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/rules/apply", json={
        "ruleset": {
            "name": "temp_inline",
            "description": "temp",
            "rules": [
                {"column": COL_A, "missing_strategy": "mean", "outlier_method": "none"},
                {"column": COL_C, "missing_strategy": "mode", "outlier_method": "none"},
            ],
        },
    })
    _update_session_cookie(resp)
    check(resp.status_code == 200, f"returns 200, got {resp.status_code}")
    data = resp.json()
    check(data["cleaned_count"] == 2, f"2 cells cleaned, got {data['cleaned_count']}")


def test_api_apply_rule_invalid() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/rules/apply - invalid")
    print("=" * 60)

    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/rules/apply", json={})
    check(resp.status_code == 400, "empty body returns 400")

    resp = client.post("/clean/rules/apply", json={"name": "nonexistent"})
    check(resp.status_code == 404, "nonexistent name returns 404")


def test_api_save_and_delete_rule() -> None:
    print("\n" + "=" * 60)
    print("Test POST /clean/rules/save + DELETE")
    print("=" * 60)

    resp = client.post("/clean/rules/save", json={
        "name": "__api_test_temp__",
        "description": "API test",
        "rules": [{"column": "x", "missing_strategy": "median"}],
    })
    check(resp.status_code == 200, f"save returns 200, got {resp.status_code}")
    check("__api_test_temp__" in resp.json()["message"], "save message contains name")

    # check it appears in list
    resp2 = client.get("/clean/rules")
    check("__api_test_temp__" in resp2.json()["saved"], "appears in saved list")

    # delete it
    resp3 = client.delete("/clean/rules/__api_test_temp__")
    check(resp.status_code == 200, f"delete returns 200, got {resp.status_code}")

    # verify deleted
    resp4 = client.get("/clean/rules")
    check("__api_test_temp__" not in resp4.json()["saved"], "removed from saved list")


def test_api_cannot_delete_preset() -> None:
    print("\n" + "=" * 60)
    print("Test DELETE /clean/rules/{name} - preset protection")
    print("=" * 60)

    resp = client.delete("/clean/rules/numeric")
    check(resp.status_code == 400, "cannot delete preset")


# ============================================================
# main
# ============================================================

def main() -> int:
    global PASS, FAIL

    print("=" * 60)
    print("Data Cleaning Module - Full Test")
    print("=" * 60)

    test_analyze_missing()
    test_detect_outliers_iqr()
    test_execute_clean_all_strategies()
    test_auto_clean()
    test_edge_cases()

    test_get_clean_no_data()
    test_get_clean_with_data()
    test_post_clean_execute()
    test_post_clean_execute_custom_and_drop()
    test_post_clean_execute_validation()
    test_post_clean_auto()
    test_health()

    test_api_contract_formats()

    # config / rules engine
    test_config_presets()
    test_config_apply_ruleset()
    test_config_validate()
    test_config_persistence()

    # /clean/rules API
    test_api_list_rules()
    test_api_get_rule_detail()
    test_api_apply_rule_by_name()
    test_api_apply_rule_inline()
    test_api_apply_rule_invalid()
    test_api_save_and_delete_rule()
    test_api_cannot_delete_preset()

    total = PASS + FAIL
    print("\n" + "=" * 60)
    print(f"Result: {PASS}/{total} passed", end="")
    if FAIL > 0:
        print(f"  -  {FAIL} failed")
    else:
        print("  -  ALL PASSED!")

    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
