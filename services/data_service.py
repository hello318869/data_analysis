"""数据管理模块的数据处理服务。"""
from __future__ import annotations

import io
import os
import uuid
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import Request, UploadFile
from sqlalchemy.orm import Session

from config import MAX_UPLOAD_SIZE_MB, UPLOAD_DIR, SAMPLE_DATA
from models.analysis_record import Dataset

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_file(file: UploadFile) -> str:
    """校验上传文件，返回小写扩展名。校验不通过抛出 ValueError。"""
    if not file or not file.filename:
        raise ValueError("请选择要上传的文件")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("仅支持 CSV、XLSX、XLS 格式文件")

    return ext


def validate_file_size(size: int) -> None:
    """校验文件大小是否在限制内。"""
    if size > MAX_SIZE_BYTES:
        raise ValueError(f"文件大小不能超过 {MAX_UPLOAD_SIZE_MB}MB")


def read_file_to_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """根据文件扩展名选择读取方式，返回 DataFrame。"""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        return _read_csv_with_encoding_detection(file_bytes)
    elif ext in (".xlsx", ".xls"):
        try:
            return pd.read_excel(io.BytesIO(file_bytes))
        except Exception:
            raise ValueError("Excel 文件格式错误或已损坏")
    else:
        raise ValueError("仅支持 CSV、XLSX、XLS 格式文件")


def _read_csv_with_encoding_detection(file_bytes: bytes) -> pd.DataFrame:
    """UTF-8 → GBK 两级回退读取 CSV。"""
    try:
        return pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
    except UnicodeDecodeError:
        pass

    try:
        return pd.read_csv(io.BytesIO(file_bytes), encoding="gbk")
    except UnicodeDecodeError:
        pass

    raise ValueError("无法识别文件编码，请尝试将文件转换为 UTF-8 格式后重新上传")


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名：时间戳_UUID_原始扩展名。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(original_filename)[1]
    return f"{timestamp}_{unique_id}{ext}"


def save_uploaded_file(file_bytes: bytes, filename: str) -> str:
    """保存文件到 UPLOAD_DIR，返回完整文件路径。"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path


def save_dataframe_to_session(
    request: Request, df: pd.DataFrame, filename: str
) -> None:
    """将 DataFrame 以 orient="split" 格式存入 session。"""
    request.session["df_json"] = df.to_json(orient="split")
    request.session["filename"] = filename


def load_dataframe_from_session(request: Request) -> Optional[pd.DataFrame]:
    """从 session 恢复 DataFrame。无数据时返回 None。"""
    df_json = request.session.get("df_json")
    if not df_json:
        return None
    return pd.read_json(io.StringIO(df_json), orient="split")


def save_dataset_record(
    db: Session, user_id: int, filename: str, df: pd.DataFrame
) -> int:
    """保存数据集元数据到 datasets 表，返回 dataset_id。"""
    dataset = Dataset(
        user_id=user_id,
        filename=filename,
        columns_info=df.dtypes.astype(str).to_dict(),
        row_count=len(df),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset.id


def load_sample_data() -> pd.DataFrame:
    """加载内置示例数据集。"""
    return pd.read_csv(SAMPLE_DATA)
