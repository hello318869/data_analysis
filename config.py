import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:QOPww848@127.0.0.1:3306/data_analysis_db",
)

UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "charts")
SESSION_DATA_DIR = os.path.join(BASE_DIR, "outputs", "session_data")
SAMPLE_DATA = os.path.join(BASE_DIR, "data", "sample_housing.csv")

SECRET_KEY = os.getenv("SECRET_KEY", "data-analysis-secret-key-2024")

MAX_UPLOAD_SIZE_MB = 10

# Ensure directories exist on import
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SESSION_DATA_DIR, exist_ok=True)
