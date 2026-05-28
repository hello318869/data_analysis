from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from models.user import Base, User                                              # noqa: F401
from models.analysis_record import Dataset, AnalysisRecord                      # noqa: F401


engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
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
