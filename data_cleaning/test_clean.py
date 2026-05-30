"""数据清洗模块 - 完整测试（pytest 格式）。

运行:
    pytest data_cleaning/test_clean.py -v
或:
    python -m pytest data_cleaning/test_clean.py -v
"""

from __future__ import annotations

import json
import os
from base64 import b64encode

import itsdangerous
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from data_cleaning.service import (
    analyze_missing,
    detect_outliers_iqr,
    execute_clean,
    auto_clean,
)
from data_cleaning.app import app, _df_to_json, SECRET_KEY
from data_cleaning.config import (
    ColumnRule,
    RuleSet,
    PRESETS,
    validate_ruleset,
    apply_ruleset,
    save_ruleset,
    load_ruleset,
    delete_ruleset,
    list_saved_rules,
)

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
    df = make_test_df()
    report = analyze_missing(df)

    assert isinstance(report, list), "return type is list"
    assert len(report) == 3, f"expected 3 cols with missing, got {len(report)}"

    cols = {r["column"] for r in report}
    assert cols == {COL_A, COL_B, COL_C}, "correct cols have missing"

    for r in report:
        assert r["missing_count"] >= 1, f"{r['column']} missing_count >= 1"
        assert isinstance(r["missing_pct"], (int, float)), f"{r['column']} missing_pct is numeric"
        assert isinstance(r["dtype"], str), f"{r['column']} dtype is str"

    df_full = pd.DataFrame({"a": [1, 2, 3]})
    assert len(analyze_missing(df_full)) == 0, "no missing returns empty"


def test_detect_outliers_iqr() -> None:
    df = make_test_df()
    report = detect_outliers_iqr(df)

    assert isinstance(report, list), "return type is list"
    outlier_cols = {r["column"] for r in report}
    assert outlier_cols == {COL_A, COL_B}, "outliers detected in num_a, num_b"

    for r in report:
        assert r["outlier_count"] >= 1, f"{r['column']} outlier_count >= 1"
        assert isinstance(r["outlier_indices"], list), f"{r['column']} outlier_indices is list"
        assert r["lower_bound"] < r["upper_bound"], f"{r['column']} lower < upper"

    df_normal = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
    assert len(detect_outliers_iqr(df_normal)) == 0, "no outliers returns empty"


def test_execute_clean_all_strategies() -> None:
    df = make_test_df()

    # mean
    r, c, msgs = execute_clean(df.copy(), "mean", [COL_A, COL_B])
    assert r[COL_A].isna().sum() == 0, "mean: num_a no missing"
    assert r[COL_B].isna().sum() == 0, "mean: num_b no missing"
    assert c >= 2, f"mean: at least 2 cells, got {c}"

    # median
    r, c, msgs = execute_clean(df.copy(), "median", [COL_A])
    assert r[COL_A].isna().sum() == 0, "median: num_a no missing"

    # mode
    r, c, msgs = execute_clean(df.copy(), "mode", [COL_C])
    assert r[COL_C].isna().sum() == 0, "mode: cat_c no missing"
    assert r.loc[2, COL_C] == "Y", "mode: filled with 'Y'"

    # drop
    r, c, msgs = execute_clean(df.copy(), "drop", [COL_A])
    assert len(r) == 6, f"drop: expected 6 rows, got {len(r)}"

    # custom
    r, c, msgs = execute_clean(df.copy(), "custom", [COL_A], fill_value=-999)
    assert r[COL_A].isna().sum() == 0, "custom: num_a no missing"
    assert r.loc[2, COL_A] == -999.0, "custom: filled with -999"

    # non-numeric with mean
    r, c, msgs = execute_clean(df.copy(), "mean", [COL_C])
    assert any("non-numeric" in m.lower() or "not numeric" in m.lower() or "\u975e\u6570\u503c" in m for m in msgs), \
        "non-numeric skips mean"
    assert r[COL_C].isna().sum() == 1, "cat_c not modified"

    # invalid column
    r, c, msgs = execute_clean(df.copy(), "mean", ["nonexistent", COL_A])
    assert any("\u4e0d\u5b58\u5728" in m for m in msgs), "invalid col reported"


def test_auto_clean() -> None:
    df = make_test_df()
    r, c, msgs = auto_clean(df)

    assert r.isna().sum().sum() == 0, "all missing handled"
    assert any("\u4e2d\u4f4d\u6570" in m for m in msgs), "numeric cols use median"
    assert any("\u4f17\u6570" in m for m in msgs), "categorical cols use mode"
    assert any("\u622a\u65ad" in m for m in msgs), "outliers clipped"
    assert r[COL_A].max() <= df[COL_A].max(), "num_a outlier clipped"
    assert r[COL_B].max() <= df[COL_B].max(), "num_b outlier clipped"


def test_edge_cases() -> None:
    df_empty = pd.DataFrame()
    assert len(analyze_missing(df_empty)) == 0, "empty df missing report empty"
    assert len(detect_outliers_iqr(df_empty)) == 0, "empty df outlier report empty"

    df_all_none = pd.DataFrame({"a": [None, None, None, None, None]})
    rpt = analyze_missing(df_all_none)
    assert len(rpt) == 1 and rpt[0]["missing_count"] == 5, "all-none col detected"

    r, c, msgs = execute_clean(df_all_none.copy(), "drop", ["a"])
    assert len(r) == 0, "drop all-none makes empty df"


# ============================================================
# API endpoint tests
# ============================================================

def test_get_clean_no_data() -> None:
    _clear_session_cookie()
    resp = client.get("/clean")
    assert resp.status_code == 400, f"expected 400, got {resp.status_code}"
    assert "detail" in resp.json(), "response has detail"


def test_get_clean_with_data() -> None:
    df = make_test_df()
    set_session_df(df)

    resp = client.get("/clean")
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"

    data = resp.json()
    for key in ("missing_report", "outlier_report", "columns", "rows", "row_count", "column_count"):
        assert key in data, f"response has {key}"

    assert len(data["missing_report"]) == 3, f"missing_report has 3 entries, got {len(data['missing_report'])}"
    assert len(data["outlier_report"]) == 2, f"outlier_report has 2 entries, got {len(data['outlier_report'])}"


def test_post_clean_execute() -> None:
    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/execute", json={
        "strategy": "mean",
        "columns": [COL_A, COL_B],
        "fill_value": None,
    })
    _update_session_cookie(resp)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"

    data = resp.json()
    assert "message" in data, "has message"
    assert "cleaned_count" in data, "has cleaned_count"
    assert data["cleaned_count"] >= 2, f"at least 2 cells cleaned, got {data['cleaned_count']}"

    # verify session updated via re-GET (cat_c still has 1 missing)
    resp2 = client.get("/clean")
    assert resp2.status_code == 200, "session updated: GET /clean ok"
    data2 = resp2.json()
    assert len(data2["missing_report"]) == 1, f"only cat_c missing remains, got {len(data2['missing_report'])}"


def test_post_clean_execute_custom_and_drop() -> None:
    # custom fill
    df = make_test_df()
    set_session_df(df)
    resp = client.post("/clean/execute", json={
        "strategy": "custom",
        "columns": [COL_A],
        "fill_value": -999,
    })
    _update_session_cookie(resp)
    assert resp.status_code == 200, "custom: 200"
    data = resp.json()
    assert data["cleaned_count"] == 1, f"custom: 1 cell, got {data['cleaned_count']}"

    # drop
    df = make_test_df()
    set_session_df(df)
    resp = client.post("/clean/execute", json={
        "strategy": "drop",
        "columns": [COL_A],
        "fill_value": None,
    })
    _update_session_cookie(resp)
    assert resp.status_code == 200, "drop: 200"
    data = resp.json()
    assert data["row_count"] < 7, f"drop: row count reduced to {data['row_count']}"


def test_post_clean_execute_validation() -> None:
    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/execute", json={
        "strategy": "mean",
        "columns": [],
        "fill_value": None,
    })
    assert resp.status_code == 400, "empty columns returns 400"

    resp = client.post("/clean/execute", json={
        "strategy": "invalid_strategy",
        "columns": [COL_A],
        "fill_value": None,
    })
    assert resp.status_code == 400, "invalid strategy returns 400"


def test_post_clean_auto() -> None:
    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/auto")
    _update_session_cookie(resp)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}"

    data = resp.json()
    assert "message" in data, "has message"
    assert "cleaned_count" in data, "has cleaned_count"
    assert len(data["missing_report"]) == 0, "auto clean: no missing left"
    assert data["cleaned_count"] == 3, f"auto clean: 3 cells, got {data['cleaned_count']}"

    # verify session updated
    resp2 = client.get("/clean")
    data2 = resp2.json()
    assert len(data2["missing_report"]) == 0, "session df has no missing"


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200, "health returns 200"
    assert resp.json() == {"status": "ok"}, "health returns ok"


# ============================================================
# API contract format validation
# ============================================================

def test_api_contract_formats() -> None:
    df = make_test_df()

    for item in analyze_missing(df):
        assert isinstance(item["column"], str), "missing_report: column is str"
        assert isinstance(item["missing_count"], int), "missing_report: missing_count is int"
        assert isinstance(item["missing_pct"], (int, float)), "missing_report: missing_pct is numeric"
        assert isinstance(item["dtype"], str), "missing_report: dtype is str"

    for item in detect_outliers_iqr(df):
        assert isinstance(item["column"], str), "outlier_report: column is str"
        assert isinstance(item["outlier_count"], int), "outlier_report: outlier_count is int"
        assert isinstance(item["outlier_indices"], list), "outlier_report: outlier_indices is list"
        assert isinstance(item["lower_bound"], (int, float)), "outlier_report: lower_bound is numeric"
        assert isinstance(item["upper_bound"], (int, float)), "outlier_report: upper_bound is numeric"


# ============================================================
# config.py tests
# ============================================================

def test_config_presets() -> None:
    assert "numeric" in PRESETS, "numeric preset exists"
    assert "categorical" in PRESETS, "categorical preset exists"
    assert "full" in PRESETS, "full preset exists"

    numeric = PRESETS["numeric"]
    assert numeric.name == "numeric_default", "numeric preset name"
    assert len(numeric.rules) == 1, "numeric preset has 1 rule"


def test_config_apply_ruleset() -> None:
    df = make_test_df()
    ruleset = PRESETS["numeric"]
    r, c, msgs = apply_ruleset(df, ruleset)

    assert r[COL_A].isna().sum() == 0, "ruleset: num_a no missing"
    assert r[COL_B].isna().sum() == 0, "ruleset: num_b no missing"
    assert any("\u4e2d\u4f4d\u6570" in m for m in msgs), "ruleset: median fill used"
    assert c >= 2, f"ruleset: at least 2 cells cleaned, got {c}"


def test_config_validate() -> None:
    valid = PRESETS["numeric"]
    errors = validate_ruleset(valid)
    assert len(errors) == 0, f"valid ruleset has no errors, got {errors}"

    bad = RuleSet(name="")
    errors = validate_ruleset(bad)
    assert len(errors) > 0, "empty name rejects"

    bad2 = RuleSet(name="bad", rules=[ColumnRule(column="a", missing_strategy="invalid")])
    errors = validate_ruleset(bad2)
    assert len(errors) > 0, "invalid strategy rejects"

    bad3 = RuleSet(name="bad", rules=[ColumnRule(column="a", missing_strategy="custom", fill_value=None)])
    errors = validate_ruleset(bad3)
    assert len(errors) > 0, "custom without fill_value rejects"


def test_config_persistence() -> None:
    ruleset = RuleSet(
        name="__test_temp__",
        description="temp",
        rules=[ColumnRule(column="test_col", missing_strategy="median")],
    )

    path = save_ruleset(ruleset)
    assert os.path.isfile(path), f"saved to {path}"
    assert "__test_temp__" in list_saved_rules(), "appears in saved list"

    loaded = load_ruleset("__test_temp__")
    assert loaded is not None, "load succeeds"
    if loaded:
        assert loaded.name == "__test_temp__", "loaded name matches"
        assert len(loaded.rules) == 1, "loaded rule count matches"

    assert delete_ruleset("__test_temp__"), "delete succeeds"
    assert "__test_temp__" not in list_saved_rules(), "removed from saved list"
    assert not delete_ruleset("__test_temp__"), "double delete returns False"
    assert load_ruleset("__nonexistent__") is None, "nonexistent returns None"


# ============================================================
# /clean/rules API endpoint tests
# ============================================================

def test_api_list_rules() -> None:
    resp = client.get("/clean/rules")
    assert resp.status_code == 200, "returns 200"
    data = resp.json()
    assert "presets" in data, "has presets"
    assert "saved" in data, "has saved"
    assert isinstance(data["presets"], list), "presets is list"
    assert isinstance(data["saved"], list), "saved is list"
    assert "numeric" in data["presets"], "numeric in presets"


def test_api_get_rule_detail() -> None:
    resp = client.get("/clean/rules/numeric")
    assert resp.status_code == 200, "returns 200"
    data = resp.json()
    assert data["name"] == "numeric_default", "correct preset detail"

    resp = client.get("/clean/rules/nonexistent")
    assert resp.status_code == 404, "nonexistent returns 404"


def test_api_apply_rule_by_name() -> None:
    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/rules/apply", json={"name": "numeric"})
    _update_session_cookie(resp)
    assert resp.status_code == 200, f"returns 200, got {resp.status_code}"

    data = resp.json()
    assert "message" in data, "has message"
    assert "cleaned_count" in data, "has cleaned_count"
    assert data["cleaned_count"] >= 2, f"at least 2 cells cleaned, got {data['cleaned_count']}"

    # verify session
    resp2 = client.get("/clean")
    missing = [m["column"] for m in resp2.json()["missing_report"]]
    assert COL_A not in missing, "num_a no longer missing"
    assert COL_B not in missing, "num_b no longer missing"


def test_api_apply_rule_inline() -> None:
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
    assert resp.status_code == 200, f"returns 200, got {resp.status_code}"
    data = resp.json()
    assert data["cleaned_count"] == 2, f"2 cells cleaned, got {data['cleaned_count']}"


def test_api_apply_rule_invalid() -> None:
    df = make_test_df()
    set_session_df(df)

    resp = client.post("/clean/rules/apply", json={})
    assert resp.status_code == 400, "empty body returns 400"

    resp = client.post("/clean/rules/apply", json={"name": "nonexistent"})
    assert resp.status_code == 404, "nonexistent name returns 404"


def test_api_save_and_delete_rule() -> None:
    resp = client.post("/clean/rules/save", json={
        "name": "__api_test_temp__",
        "description": "API test",
        "rules": [{"column": "x", "missing_strategy": "median"}],
    })
    assert resp.status_code == 200, f"save returns 200, got {resp.status_code}"
    assert "__api_test_temp__" in resp.json()["message"], "save message contains name"

    # check it appears in list
    resp2 = client.get("/clean/rules")
    assert "__api_test_temp__" in resp2.json()["saved"], "appears in saved list"

    # delete it
    resp3 = client.delete("/clean/rules/__api_test_temp__")
    assert resp.status_code == 200, f"delete returns 200, got {resp.status_code}"

    # verify deleted
    resp4 = client.get("/clean/rules")
    assert "__api_test_temp__" not in resp4.json()["saved"], "removed from saved list"


def test_api_cannot_delete_preset() -> None:
    resp = client.delete("/clean/rules/numeric")
    assert resp.status_code == 400, "cannot delete preset"
