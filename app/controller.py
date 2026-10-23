"""Decision-making controller for the visual inspection loop."""

from app.models import ControllerAction, Defect, PerceptionPayload


def _primary_defect(payload: PerceptionPayload) -> Defect | None:
    if not payload.defects:
        return None
    return max(payload.defects, key=lambda defect: defect.area)


def _padded_roi(
    bounding_box: list[int], frame_dimensions: list[int], padding_ratio: float = 0.2
) -> list[int]:
    """Return a padded, frame-clamped ROI around a suspicious bounding box."""
    x, y, width, height = bounding_box
    padding_x = round(width * padding_ratio)
    padding_y = round(height * padding_ratio)
    frame_width, frame_height = frame_dimensions

    left = max(0, x - padding_x)
    top = max(0, y - padding_y)
    right = min(frame_width, x + width + padding_x)
    bottom = min(frame_height, y + height + padding_y)
    return [left, top, right - left, bottom - top]


def _refined_config(payload: PerceptionPayload, defect: Defect) -> dict:
    config = payload.active_config
    return {
        "roi_crop": _padded_roi(defect.bounding_box, payload.frame_dimensions),
        "apply_clahe": True,
        "canny_threshold1": max(0, config.canny_threshold1 // 2),
        "canny_threshold2": max(0, round(config.canny_threshold2 * 2 / 3)),
    }


def decide_action(payload: PerceptionPayload) -> ControllerAction:
    """Apply the decision matrix and return the next system action."""
    defect = _primary_defect(payload)
    confidence = payload.confidence_score

    if payload.defect_detected and confidence >= 0.85:
        if defect is None:
            raise ValueError(
                "A high-confidence defect frame must include at least one defect"
            )
        return ControllerAction(
            action="flag_defect_alert",
            reasoning=(
                f"Confirmed defect with confidence_score={confidence:.2f}; "
                f"primary bounding_box={defect.bounding_box}."
            ),
            parameters={
                "bounding_box": defect.bounding_box,
                "severity_score": confidence,
            },
        )

    if payload.defect_detected or confidence >= 0.30:
        if defect is None:
            raise ValueError(
                "An ambiguous frame must include a defect candidate to refine the ROI"
            )
        return ControllerAction(
            action="update_vision_config",
            reasoning=(
                f"Ambiguous result with confidence_score={confidence:.2f}; "
                f"refining bounding_box={defect.bounding_box}."
            ),
            parameters=_refined_config(payload, defect),
        )

    return ControllerAction(
        action="pass_frame",
        reasoning=f"Clear frame with confidence_score={confidence:.2f}.",
        parameters={"roi_crop": None}
        if payload.active_config.roi_crop is not None
        else {},
    )
