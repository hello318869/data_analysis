from typing import Optional

from pydantic import BaseModel, Field


class AnalysisParams(BaseModel):
    """Parameters for running a machine-learning analysis on a dataset."""

    features: list[str] = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class VizParams(BaseModel):
    """Parameters for generating a visualization chart."""

    chart_type: str = Field(..., pattern=r"^(line|bar|scatter)$")
    x_col: str
    y_col: str
    title: Optional[str] = None
    color: Optional[str] = "blue"


class CleanParams(BaseModel):
    """Parameters for data-cleaning operations on a dataset."""

    strategy: str = Field(..., pattern=r"^(mean|median|mode|drop)$")
    columns: list[str] = Field(..., min_length=1)
    fill_value: Optional[float] = None
