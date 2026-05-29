from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from models.user import Base, User                                              # noqa: F401
from models.analysis_record import Dataset, AnalysisRecord                      # noqa: F401


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,       # 每小时主动回收连接，防止 MySQL wait_timeout 后连接失效
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30,
        "charset": "utf8mb4",
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Session:
    """Context-manager for a database session, ensuring it is closed after use.

    Usage with `with` statement:
        with get_db() as db:
            user = db.query(User).first()

    Usage as FastAPI dependency:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
