"""数据管理模块的数据处理服务。"""
from __future__ import annotations

import io
import json
import os
import re
import uuid
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import Request, UploadFile
from sqlalchemy.orm import Session

from config import MAX_UPLOAD_SIZE_MB, UPLOAD_DIR, SAMPLE_DATA, SESSION_DATA_DIR
from models.analysis_record import Dataset

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
SESSION_DATA_KEY = "df_store_id"
CSV_ENCODINGS = (
    "utf-8-sig",
    "utf-8",
    "gb18030",
    "gbk",
    "big5",
    "cp1252",
    "latin1",
)


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

    try:
        if ext == ".csv":
            return _read_csv_with_encoding_detection(file_bytes)
        elif ext in (".xlsx", ".xls"):
            return pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise ValueError("不支持的文件格式，请上传 CSV 或 Excel 文件")
    except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as e:
        raise ValueError(f"文件解析失败：{str(e)}。请检查文件格式是否正确。")
    except Exception as e:
        raise ValueError(f"文件读取失败：{str(e)}")


def _read_csv_with_encoding_detection(file_bytes: bytes) -> pd.DataFrame:
    """Try common CSV encodings used by exported spreadsheets."""
    candidates: list[tuple[int, int, pd.DataFrame]] = []
    last_error: Exception | None = None

    for index, encoding in enumerate(CSV_ENCODINGS):
        try:
            text = file_bytes.decode(encoding)
            df = pd.read_csv(io.StringIO(text))
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except pd.errors.ParserError as exc:
            last_error = exc
            continue

        candidates.append((_encoding_quality_score(text), index, df))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    raise ValueError("CSV 文件解析失败，请检查文件编码或分隔符") from last_error


def _encoding_quality_score(text: str) -> int:
    """Score common mojibake patterns lower is better."""
    sample = text[:20000]
    score = sample.count("\ufffd") * 100
    score += len(re.findall(r"[A-Za-z][\u4e00-\u9fff][A-Za-z]", sample)) * 50
    score += sum(1 for ch in sample if ord(ch) < 32 and ch not in "\r\n\t") * 20
    score += sum(sample.count(ch) for ch in ("Ã", "Â", "â€", "Ð", "Ñ")) * 5
    return score


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


def _session_data_path(store_id: str) -> str:
    """Return the on-disk path for a stored session dataframe."""
    uuid.UUID(store_id)
    return os.path.join(SESSION_DATA_DIR, f"{store_id}.json")


def _delete_stored_dataframe(store_id: str | None) -> None:
    if not store_id:
        return

    try:
        path = _session_data_path(store_id)
    except (TypeError, ValueError):
        return

    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def _dataframe_from_json(df_json: str) -> pd.DataFrame:
    """Restore dataframes saved by current and older session formats."""
    try:
        parsed = json.loads(df_json)
    except json.JSONDecodeError:
        df = pd.read_json(io.StringIO(df_json))
    else:
        if isinstance(parsed, dict) and {"columns", "data"}.issubset(parsed):
            df = pd.DataFrame(
                parsed["data"],
                columns=parsed["columns"],
                index=parsed.get("index"),
            )
        elif isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
            df = pd.DataFrame(parsed["data"])
        elif isinstance(parsed, list):
            df = pd.DataFrame(parsed)
        elif isinstance(parsed, dict):
            df = pd.DataFrame(parsed)
        else:
            raise ValueError("无法读取数据，请重新上传数据文件")

    # Restore NaN values lost in JSON serialization
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].where(df[col].notna(), np.nan)
    return df


def save_dataframe_to_session(
    request: Request, df: pd.DataFrame, filename: str
) -> None:
    """Save a DataFrame server-side and keep only a small key in the session."""
    old_store_id = request.session.get(SESSION_DATA_KEY)
    store_id = uuid.uuid4().hex
    path = _session_data_path(store_id)

    os.makedirs(SESSION_DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(df.to_json(orient="split", force_ascii=False))

    _delete_stored_dataframe(old_store_id)
    request.session[SESSION_DATA_KEY] = store_id
    request.session.pop("df_json", None)
    request.session["filename"] = filename


def load_dataframe_from_session(request: Request) -> Optional[pd.DataFrame]:
    """从 session 恢复 DataFrame。无数据时返回 None。"""
    store_id = request.session.get(SESSION_DATA_KEY)
    if store_id:
        try:
            path = _session_data_path(store_id)
        except (TypeError, ValueError):
            request.session.pop(SESSION_DATA_KEY, None)
            return None

        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return _dataframe_from_json(f.read())

        request.session.pop(SESSION_DATA_KEY, None)

    df_json = request.session.get("df_json")
    if not df_json:
        return None
    return _dataframe_from_json(df_json)


def clear_dataframe_from_session(request: Request) -> None:
    """Clear current dataframe data and remove its server-side cache file."""
    _delete_stored_dataframe(request.session.get(SESSION_DATA_KEY))
    for key in (SESSION_DATA_KEY, "df_json", "filename"):
        request.session.pop(key, None)


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
