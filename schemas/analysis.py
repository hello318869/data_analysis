from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AnalysisParams(BaseModel):
    """Parameters for running a machine-learning analysis on a dataset."""

    features: list[str] = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class VizParams(BaseModel):
    """Parameters for generating a visualization chart."""

    chart_type: str = Field(..., pattern=r"^(line|bar|scatter)$")
    x_col: str = Field(..., min_length=1)
    y_col: str = Field(..., min_length=1)
    title: Optional[str] = None
    color: Optional[str] = "blue"


class CleanParams(BaseModel):
    """Parameters for data-cleaning operations on a dataset."""

    strategy: str = Field(..., pattern=r"^(mean|median|mode|drop)$")
    columns: list[str] = Field(..., min_length=1)
    fill_value: Optional[float] = None

    @field_validator("fill_value")
    @classmethod
    def validate_fill_value(cls, v, info):
        """fill_value 仅在自定义填充策略时有效（当前支持 mean/median/mode/drop）。"""
        if v is not None:
            raise ValueError("当前清洗策略不支持自定义填充值，请使用 mean/median/mode/drop")
        return v
