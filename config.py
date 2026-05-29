import os
from typing import Final

BASE_DIR: Final[str] = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL: Final[str] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:QOPww848@127.0.0.1:3306/data_analysis_db",
)

UPLOAD_DIR: Final[str] = os.path.join(BASE_DIR, "static", "uploads")
OUTPUT_DIR: Final[str] = os.path.join(BASE_DIR, "outputs", "charts")
SESSION_DATA_DIR: Final[str] = os.path.join(BASE_DIR, "outputs", "session_data")
SAMPLE_DATA: Final[str] = os.path.join(BASE_DIR, "data", "sample_housing.csv")

SECRET_KEY: Final[str] = os.getenv("SECRET_KEY", "data-analysis-secret-key-2024")

MAX_UPLOAD_SIZE_MB: Final[int] = 10


def ensure_directories() -> None:
    """延迟创建必要的目录（在应用启动时调用）。"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(SESSION_DATA_DIR, exist_ok=True)
