from fastapi.testclient import TestClient

from main import app


def test_upload_replaces_sample_without_oversized_session_cookie():
    client = TestClient(app)
    client.post("/data/load-sample", follow_redirects=False)

    rows = ["feature,target"]
    rows.extend(f"{i},{i * 2}" for i in range(600))
    csv_bytes = ("\n".join(rows) + "\n").encode("utf-8")

    response = client.post(
        "/data/upload",
        files={"file": ("uploaded.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/data/preview"
    assert len(response.headers["set-cookie"]) < 1000

    preview = client.get("/data/preview")

    assert preview.status_code == 200
    assert "uploaded.csv" in preview.text
    assert "sample_housing.csv" not in preview.text
    assert ">600<" in preview.text


def test_uploaded_data_is_available_to_clean_and_viz_pages():
    client = TestClient(app)
    csv_bytes = b"feature,target\n1,2\n3,4\n5,\n"

    upload = client.post(
        "/data/upload",
        files={"file": ("flow.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )
    assert upload.status_code == 303

    clean = client.get("/clean")
    assert clean.status_code == 200
    assert "flow.csv" in clean.text
    assert "feature" in clean.text
    assert "target" in clean.text

    viz = client.get("/viz")
    assert viz.status_code == 200
    assert "flow.csv" in viz.text
    assert "可视化分析" in viz.text


def test_upload_accepts_cp1252_csv_exports():
    client = TestClient(app)
    csv_bytes = "name,city\nAlice,Los\u00a0Angeles\n".encode("cp1252")

    response = client.post(
        "/data/upload",
        files={"file": ("cp1252.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 303

    preview = client.get("/data/preview")

    assert preview.status_code == 200
    assert "cp1252.csv" in preview.text
    assert "Los" in preview.text
    assert "Angeles" in preview.text


def test_upload_still_accepts_gbk_csv_exports():
    client = TestClient(app)
    csv_bytes = "姓名,城市\n张三,北京\n".encode("gbk")

    response = client.post(
        "/data/upload",
        files={"file": ("gbk.csv", csv_bytes, "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 303

    preview = client.get("/data/preview")

    assert preview.status_code == 200
    assert "gbk.csv" in preview.text
    assert "张三" in preview.text
    assert "北京" in preview.text


def test_export_requires_uploaded_data():
    client = TestClient(app)

    response = client.get("/data/export?format=csv", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/data/upload"


def test_export_current_data_as_csv_and_excel():
    client = TestClient(app)
    client.post("/data/load-sample", follow_redirects=False)

    csv_response = client.get("/data/export?format=csv")

    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "attachment" in csv_response.headers["content-disposition"]
    assert csv_response.content.startswith(b"\xef\xbb\xbf")
    assert "sqft" in csv_response.content.decode("utf-8-sig")

    excel_response = client.get("/data/export?format=xlsx")

    assert excel_response.status_code == 200
    assert excel_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment" in excel_response.headers["content-disposition"]
    assert excel_response.content.startswith(b"PK")
