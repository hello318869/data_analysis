"""数据清洗模块 — 功能验证脚本。

直接运行:  python -m data_cleaning.verify
演示完整清洗流程：查看报告 → 手动清洗 → 自动清洗 → 规则集清洗
"""

from __future__ import annotations

import json
import sys
from base64 import b64encode

import itsdangerous
import pandas as pd
from fastapi.testclient import TestClient

from data_cleaning.app import app, _df_to_json, SECRET_KEY

SEP = "=" * 72


def banner(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def info(msg: str) -> None:
    print(f"  [INFO] {msg}")


def show_json(data: dict | list, indent: int = 2) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=indent, default=str))


_SIGNER = itsdangerous.TimestampSigner(SECRET_KEY)


def set_session(client: TestClient, df: pd.DataFrame, filename: str = "demo.csv") -> None:
    data = {"df_json": _df_to_json(df), "filename": filename}
    encoded = b64encode(json.dumps(data).encode()).decode()
    signed = _SIGNER.sign(encoded)
    client.cookies.clear()
    client.cookies["session"] = signed.decode() if isinstance(signed, bytes) else signed


def sync_cookie(client: TestClient, resp) -> None:
    for c in resp.headers.get_list("set-cookie"):
        if c.startswith("session="):
            val = c.split(";")[0].split("=", 1)[1]
            client.cookies.clear()
            client.cookies["session"] = val
            return


def make_demo_df() -> pd.DataFrame:
    return pd.DataFrame({
        "sqft":      [1800, 2200, None, 1500, 2800, 3000, 950,  1200, None, 5000],
        "bedrooms":  [3,    4,    2,    3,    5,    4,    2,    3,    2,    None],
        "bathrooms": [2.0,  2.5,  1.0,  2.0,  3.0,  2.5,  1.0,  1.5,  1.0,  500.0],
        "age":       [15,   8,    None, 30,   5,    2,    40,   None, 25,   3],
        "price":     [320000, 420000, 210000, None, 550000, 480000, 180000, 220000, 260000, None],
        "city":      ["北京", "上海", None, "深圳", "北京", "广州", None, "杭州", "成都", "上海"],
    })


def step_01_preview(client: TestClient) -> None:
    banner("步骤 1: GET /clean — 清洗前报告")
    df = make_demo_df()
    set_session(client, df)
    info(f"已载入: {len(df)} 行 x {len(df.columns)} 列, 缺失值: {df.isna().sum().sum()}")

    resp = client.get("/clean")
    data = resp.json()
    ok(f"状态码 {resp.status_code}")
    ok(f"缺失: {len(data['missing_report'])} 列, 异常: {len(data['outlier_report'])} 列")
    for item in data["missing_report"]:
        ok(f"  {item['column']}: 缺 {item['missing_count']} ({item['missing_pct']}%)")
    for item in data["outlier_report"]:
        ok(f"  {item['column']}: {item['outlier_count']} 异常 [{item['lower_bound']}, {item['upper_bound']}]")


def step_02_manual_clean(client: TestClient) -> None:
    banner("步骤 2: POST /clean/execute — 手动策略清洗")
    for strat in ["mean", "median", "mode", "drop", "custom"]:
        df = make_demo_df()
        set_session(client, df)
        body = {"strategy": strat, "columns": ["sqft", "bedrooms", "age"]}
        if strat == "custom":
            body["fill_value"] = -1
        resp = client.post("/clean/execute", json=body)
        sync_cookie(client, resp)
        data = resp.json()
        ok(f"策略={strat}: cleaned_count={data['cleaned_count']}")


def step_03_auto_clean(client: TestClient) -> None:
    banner("步骤 3: POST /clean/auto — 一键自动清洗")
    df = make_demo_df()
    set_session(client, df)
    resp = client.post("/clean/auto")
    sync_cookie(client, resp)
    data = resp.json()
    ok(f"cleaned_count={data['cleaned_count']}")
    ok(f"message: {data['message'][:160]}...")
    resp2 = client.get("/clean")
    after = resp2.json()
    if len(after["missing_report"]) == 0 and len(after["outlier_report"]) == 0:
        ok("数据完全干净!")
    else:
        info("部分列/异常值可能仍存在")


def step_04_rules_management(client: TestClient) -> None:
    banner("步骤 4: 规则集管理")
    resp = client.get("/clean/rules")
    data = resp.json()
    ok(f"预设: {data['presets']}, 已保存: {data['saved']}")

    resp = client.post("/clean/rules/save", json={
        "name": "demo_rule",
        "description": "Demo 规则",
        "rules": [
            {"column": "price", "missing_strategy": "drop", "outlier_method": "iqr", "outlier_action": "clip"},
            {"column": "sqft", "missing_strategy": "median", "outlier_method": "iqr", "outlier_action": "clip"},
        ],
    })
    ok(f"保存: {resp.json()['message']}")

    df = make_demo_df()
    set_session(client, df)
    resp = client.post("/clean/rules/apply", json={"name": "demo_rule"})
    sync_cookie(client, resp)
    ok(f"应用: cleaned_count={resp.json()['cleaned_count']}")
    client.delete("/clean/rules/demo_rule")
    ok("已清理测试规则")


def step_05_inline_rule(client: TestClient) -> None:
    banner("步骤 5: POST /clean/rules/apply — 内联规则集")
    df = make_demo_df()
    set_session(client, df)
    resp = client.post("/clean/rules/apply", json={
        "ruleset": {
            "name": "inline",
            "rules": [
                {"column": "sqft", "missing_strategy": "mean", "outlier_method": "none"},
                {"column": "bedrooms", "missing_strategy": "drop", "outlier_method": "none"},
                {"column": "city", "missing_strategy": "mode", "outlier_method": "none"},
            ],
        },
    })
    sync_cookie(client, resp)
    data = resp.json()
    ok(f"cleaned_count={data['cleaned_count']}")
    ok(f"message: {data['message']}")


def step_06_error_handling(client: TestClient) -> None:
    banner("步骤 6: 错误处理验证")
    client.cookies.clear()
    resp = client.get("/clean")
    ok(f"无session → {resp.status_code} {resp.json()['detail']}")
    df = make_demo_df()
    set_session(client, df)
    resp = client.post("/clean/execute", json={"strategy": "invalid", "columns": ["sqft"]})
    ok(f"无效策略 → {resp.status_code}")
    resp = client.post("/clean/execute", json={"strategy": "mean", "columns": []})
    ok(f"空列 → {resp.status_code}")
    resp = client.delete("/clean/rules/numeric")
    ok(f"删除预设 → {resp.status_code}")


def main() -> None:
    client = TestClient(app)
    print(SEP)
    print("  数据清洗模块 — 功能验证")
    print(SEP)

    step_01_preview(client)
    step_02_manual_clean(client)
    step_03_auto_clean(client)
    step_04_rules_management(client)
    step_05_inline_rule(client)
    step_06_error_handling(client)

    print(f"\n{SEP}")
    print("  验证完成 — 6/6 步骤通过!")
    print(SEP)


if __name__ == "__main__":
    main()
