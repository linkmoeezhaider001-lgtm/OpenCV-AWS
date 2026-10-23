from unittest.mock import Mock

import pytest

from app.controller import decide_action
from app.main import decide
from app.models import PerceptionPayload


def make_payload(**overrides):
    payload = {
        "status": "SUCCESS",
        "frame_dimensions": [640, 480],
        "defect_detected": True,
        "confidence_score": 0.65,
        "total_defects": 1,
        "defects": [
            {
                "id": 1,
                "area": 450.0,
                "bounding_box": [310, 220, 45, 45],
                "centroid": [332, 242],
                "aspect_ratio": 1.0,
            }
        ],
        "active_config": {
            "blur_kernel": 5,
            "canny_threshold1": 50,
            "canny_threshold2": 150,
            "min_defect_area": 300.0,
            "roi_crop": None,
            "apply_clahe": False,
        },
    }
    payload.update(overrides)
    return PerceptionPayload.model_validate(payload)


def test_ambiguous_frame_requests_refined_configuration():
    action = decide_action(make_payload())

    assert action.action == "update_vision_config"
    assert action.parameters == {
        "roi_crop": [301, 211, 63, 63],
        "apply_clahe": True,
        "canny_threshold1": 25,
        "canny_threshold2": 100,
    }


def test_high_confidence_frame_flags_primary_defect():
    action = decide_action(make_payload(confidence_score=0.9))

    assert action.action == "flag_defect_alert"
    assert action.parameters["bounding_box"] == [310, 220, 45, 45]
    assert action.parameters["severity_score"] == 0.9


def test_clear_frame_passes_and_resets_active_roi():
    action = decide_action(
        make_payload(
            defect_detected=False,
            confidence_score=0.1,
            total_defects=0,
            defects=[],
            active_config={
                "blur_kernel": 5,
                "canny_threshold1": 50,
                "canny_threshold2": 150,
                "min_defect_area": 300.0,
                "roi_crop": [10, 10, 100, 100],
                "apply_clahe": True,
            },
        )
    )

    assert action.action == "pass_frame"
    assert action.parameters == {"roi_crop": None}


def test_high_confidence_without_candidate_is_rejected():
    with pytest.raises(ValueError, match="must include at least one defect"):
        decide_action(make_payload(confidence_score=0.9, defects=[]))


def test_decide_endpoint_logs_structured_decision_metadata(monkeypatch):
    logger = Mock()
    monkeypatch.setattr("app.main.logger", logger)

    action = decide(make_payload())

    assert action.action == "update_vision_config"
    logger.info.assert_called_once_with(
        "Vision decision completed",
        extra={
            "confidence_score": 0.65,
            "defect_detected": True,
            "total_defects": 1,
            "selected_action": "update_vision_config",
            "primary_bounding_box": [310, 220, 45, 45],
        },
    )
