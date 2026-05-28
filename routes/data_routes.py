"""数据管理路由：上传、预览、删除、加载示例数据。"""
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from models import get_db
from services.data_service import (
    validate_file,
    validate_file_size,
    read_file_to_dataframe,
    generate_unique_filename,
    save_uploaded_file,
    save_dataframe_to_session,
    load_dataframe_from_session,
    save_dataset_record,
    load_sample_data,
)

router = APIRouter()
templates: Jinja2Templates = None


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """展示文件上传页面。"""
    error = request.session.pop("flash_error", None)
    user = request.session.get("user")
    return templates.TemplateResponse(request, "upload.html", {
        "user": user,
        "error": error,
    })


@router.post("/upload")
async def handle_upload(request: Request, file: UploadFile = File(...)):
    """处理文件上传请求。"""
    try:
        validate_file(file)
        contents = await file.read()
        validate_file_size(len(contents))
        df = read_file_to_dataframe(contents, file.filename)

        unique_name = generate_unique_filename(file.filename)
        save_uploaded_file(contents, unique_name)
        save_dataframe_to_session(request, df, file.filename)

    except ValueError as exc:
        request.session["flash_error"] = str(exc)
        return RedirectResponse(url="/data/upload", status_code=303)
    except Exception:
        request.session["flash_error"] = "文件解析失败，请检查文件格式是否正确"
        return RedirectResponse(url="/data/upload", status_code=303)

    user = request.session.get("user")
    if user:
        try:
            with get_db() as db:
                dataset_id = save_dataset_record(db, user["id"], file.filename, df)
                request.session["current_dataset_id"] = dataset_id
        except Exception:
            pass

    return RedirectResponse(url="/data/preview", status_code=303)


@router.get("/preview", response_class=HTMLResponse)
async def preview_page(request: Request):
    """展示数据预览页面。"""
    df = load_dataframe_from_session(request)
    if df is None:
        request.session["flash_error"] = "请先上传数据文件"
        return RedirectResponse(url="/data/upload", status_code=303)

    user = request.session.get("user")
    preview_rows = df.head(10).fillna("").to_dict(orient="records")

    return templates.TemplateResponse(request, "preview.html", {
        "user": user,
        "filename": request.session.get("filename", "unknown"),
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "row_count": len(df),
        "col_count": len(df.columns),
        "preview_rows": preview_rows,
        "has_data": True,
    })


@router.post("/delete")
async def delete_data(request: Request):
    """清除当前 session 中的数据，返回首页。"""
    for key in ("df_json", "filename", "current_dataset_id", "last_analysis"):
        request.session.pop(key, None)

    return RedirectResponse(url="/", status_code=303)


@router.post("/load-sample")
async def load_sample(request: Request):
    """加载内置示例数据集。"""
    try:
        df = load_sample_data()
        save_dataframe_to_session(request, df, "sample_housing.csv")
    except Exception:
        request.session["flash_error"] = "示例数据加载失败"
        return RedirectResponse(url="/data/upload", status_code=303)

    user = request.session.get("user")
    if user:
        try:
            with get_db() as db:
                dataset_id = save_dataset_record(db, user["id"], "sample_housing.csv", df)
                request.session["current_dataset_id"] = dataset_id
        except Exception:
            pass

    return RedirectResponse(url="/data/preview", status_code=303)
