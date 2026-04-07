import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from PIL import Image

from database import get_db, Case

def run_prediction(image_path):
    # Lazy import so the server starts even if PyTorch DLLs aren't loaded yet
    from ml.predict import run_prediction as _run
    return _run(image_path)

router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/analyse")
async def analyse_image(
    file: UploadFile = File(...),
    body_location: str = Form(default=""),
    symptoms: str = Form(default="{}"),
    session_id: str = Form(default=""),
    db: Session = Depends(get_db)
):
    # Basic file validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WebP images are accepted.")

    # Save the uploaded file
    if not session_id:
        session_id = str(uuid.uuid4())

    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # Run the model
    try:
        result = run_prediction(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")

    # Parse symptom data
    try:
        symptoms_data = json.loads(symptoms) if symptoms else {}
    except json.JSONDecodeError:
        symptoms_data = {}

    # Adjust risk based on symptom responses (simple rule-based NLP supplement)
    adjusted_risk = adjust_risk_with_symptoms(result["risk_level"], symptoms_data)

    # Build recommendation text
    recommendation = build_recommendation(result["condition"], adjusted_risk, result["confidence"])

    # Save to DB
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


def adjust_risk_with_symptoms(model_risk: str, symptoms: dict) -> str:
    """
    Simple rule-based adjustment of ML risk level using symptom answers.
    Upgrades risk if red-flag symptoms are present.
    """
    red_flags = 0

    if symptoms.get("bleeding") == "yes":
        red_flags += 2
    if symptoms.get("growing") == "yes":
        red_flags += 1
    if symptoms.get("duration_weeks", 0) and int(symptoms.get("duration_weeks", 0)) > 8:
        red_flags += 1
    if symptoms.get("family_history") == "yes":
        red_flags += 1
    if symptoms.get("irregular_border") == "yes":
        red_flags += 1

    risk_order = ["LOW", "MEDIUM", "HIGH"]
    current_index = risk_order.index(model_risk) if model_risk in risk_order else 0

    if red_flags >= 3:
        current_index = min(current_index + 2, 2)
    elif red_flags >= 1:
        current_index = min(current_index + 1, 2)

    return risk_order[current_index]


def build_recommendation(condition: str, risk_level: str, confidence: float) -> str:
    recommendations = {
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
    return recommendations.get(risk_level, recommendations["MEDIUM"])
