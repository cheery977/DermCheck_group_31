import os
import uuid
import json

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, Case
from ml.predict import run_prediction

router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

RISK_ORDER = ["LOW", "MEDIUM", "HIGH"]

RECOMMENDATIONS = {
    "HIGH": (
        "Our analysis has flagged this as potentially requiring urgent attention. "
        "We strongly recommend you consult a dermatologist or your GP as soon as possible. "
        "Your image and this report have been forwarded to the professional portal for review. "
        "Please do not delay seeking medical advice."
    ),
    "MEDIUM": (
        "Our analysis suggests this may benefit from a professional opinion. "
        "We recommend booking an appointment with your GP within the next few weeks. "
        "Monitor the area for any changes in size, colour, or texture in the meantime."
    ),
    "LOW": (
        "Our analysis suggests this is likely a benign condition. "
        "Keep an eye on the area and consult a pharmacist for over-the-counter treatment options. "
        "If you notice any changes or the condition worsens, please see your GP."
    ),
}


@router.post("/analyse")
async def analyse_image(
    file: UploadFile = File(...),
    body_location: str = Form(default=""),
    symptoms: str = Form(default="{}"),
    session_id: str = Form(default=""),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WebP images are accepted.")

    if not session_id:
        session_id = str(uuid.uuid4())

    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    try:
        result = run_prediction(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")

    try:
        symptoms_data = json.loads(symptoms) if symptoms else {}
    except json.JSONDecodeError:
        symptoms_data = {}

    adjusted_risk = _adjust_risk(result["risk_level"], symptoms_data)
    recommendation = RECOMMENDATIONS.get(adjusted_risk, RECOMMENDATIONS["MEDIUM"])

    case = Case(
        session_id=session_id,
        image_filename=filename,
        condition=result["condition"],
        condition_display=result["condition_display"],
        confidence=result["confidence"],
        risk_level=adjusted_risk,
        body_location=body_location,
        symptoms_json=json.dumps(symptoms_data),
        recommendation=recommendation,
        submitted_to_portal=1 if adjusted_risk == "HIGH" else 0,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "case_id": case.id,
        "session_id": session_id,
        "condition": result["condition"],
        "condition_display": result["condition_display"],
        "confidence": result["confidence"],
        "risk_level": adjusted_risk,
        "top_predictions": result["top_predictions"],
        "recommendation": recommendation,
        "gradcam_filename": result.get("gradcam_filename"),
        "submitted_to_portal": bool(case.submitted_to_portal),
        "image_filename": filename,
    }


@router.get("/case/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _adjust_risk(model_risk: str, symptoms: dict) -> str:
    red_flags = 0
    if symptoms.get("bleeding") == "yes":
        red_flags += 2
    if symptoms.get("growing") == "yes":
        red_flags += 1
    if symptoms.get("irregular_border") == "yes":
        red_flags += 1
    if symptoms.get("family_history") == "yes":
        red_flags += 1

    try:
        weeks = int(symptoms.get("duration_weeks") or 0)
        if weeks > 8:
            red_flags += 1
    except (ValueError, TypeError):
        pass

    idx = RISK_ORDER.index(model_risk) if model_risk in RISK_ORDER else 0
    if red_flags >= 3:
        idx = min(idx + 2, 2)
    elif red_flags >= 1:
        idx = min(idx + 1, 2)
    return RISK_ORDER[idx]
