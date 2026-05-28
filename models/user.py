from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    """Represents a registered user of the data analysis system."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    datasets = relationship(
        "Dataset", back_populates="user", cascade="all, delete-orphan"
    )
    analysis_records = relationship(
        "AnalysisRecord", back_populates="user", cascade="all, delete-orphan"
    )
