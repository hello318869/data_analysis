from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship

from models.user import Base


class Dataset(Base):
    """Represents an uploaded dataset owned by a user."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String(255), nullable=False)
    columns_info = Column(JSON, nullable=True)
    row_count = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="datasets")
    analysis_records = relationship(
        "AnalysisRecord", back_populates="dataset", cascade="all, delete-orphan"
    )


class AnalysisRecord(Base):
    """Represents a single analysis run against a dataset."""

    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id = Column(
        Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    analysis_type = Column(String(50), nullable=True)
    parameters = Column(JSON, nullable=True)
    result_summary = Column(Text, nullable=True)
    chart_paths = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="analysis_records")
    dataset = relationship("Dataset", back_populates="analysis_records")
