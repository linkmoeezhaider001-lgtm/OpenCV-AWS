"""Validated input models for perception metadata."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Defect(BaseModel):
    """A candidate defect reported by the perception engine."""

    id: int
    area: float = Field(ge=0)
    bounding_box: list[int] = Field(min_length=4, max_length=4)
    centroid: list[float] = Field(min_length=2, max_length=2)
    aspect_ratio: float = Field(gt=0)

    @field_validator("bounding_box")
    @classmethod
    def validate_bounding_box(cls, value: list[int]) -> list[int]:
        if value[2] <= 0 or value[3] <= 0:
            raise ValueError("bounding_box width and height must be positive")
        if value[0] < 0 or value[1] < 0:
            raise ValueError("bounding_box coordinates must be non-negative")
        return value


class VisionConfig(BaseModel):
    """OpenCV parameters currently used by the perception engine."""

    blur_kernel: int = Field(gt=0)
    canny_threshold1: int = Field(ge=0)
    canny_threshold2: int = Field(ge=0)
    min_defect_area: float = Field(ge=0)
    roi_crop: Optional[list[int]] = None
    apply_clahe: bool


class PerceptionPayload(BaseModel):
    """Frame metadata received from the OpenCV perception engine."""

    status: str
    frame_dimensions: list[int] = Field(min_length=2, max_length=2)
    defect_detected: bool
    confidence_score: float = Field(ge=0, le=1)
    total_defects: int = Field(ge=0)
    defects: list[Defect]
    active_config: VisionConfig

    @field_validator("frame_dimensions")
    @classmethod
    def validate_frame_dimensions(cls, value: list[int]) -> list[int]:
        if value[0] <= 0 or value[1] <= 0:
            raise ValueError("frame dimensions must be positive")
        return value


class ControllerAction(BaseModel):
    """Action command sent to the inspection system."""

    action: str
    reasoning: str
    parameters: dict

