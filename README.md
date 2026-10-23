# Agentic Vision Controller

This service evaluates OpenCV perception metadata and selects the next action in
the perception-decision-action loop:

- High-confidence defects (`confidence_score >= 0.85`) produce
  `flag_defect_alert`.
- Ambiguous detections produce `update_vision_config`, enabling CLAHE, lowering
  Canny thresholds, and creating a 20%-padded, frame-clamped ROI.
- Clear frames produce `pass_frame`; an active ROI is reset to `null`.

## Run

From the project root:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Send a payload to `http://127.0.0.1:8000/decide` using the shape in
[`sample_payload.json`](sample_payload.json).

## Test

```powershell
.\venv\Scripts\python.exe -m pytest
```
