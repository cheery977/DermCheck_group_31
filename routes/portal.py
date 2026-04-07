from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db, Case

router = APIRouter()


class ReviewUpdate(BaseModel):
    notes: str
    status: str = "reviewed"


@router.get("/cases")
def list_cases(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Case).filter(Case.submitted_to_portal == 1)

    if status:
        query = query.filter(Case.status == status)
    if risk_level:
        query = query.filter(Case.risk_level == risk_level)

    cases = query.order_by(Case.created_at.desc()).all()

    return [
        {
            "id": c.id,
            "image_filename": c.image_filename,
            "condition_display": c.condition_display,
            "confidence": round(c.confidence * 100, 1),
            "risk_level": c.risk_level,
            "body_location": c.body_location,
            "recommendation": c.recommendation,
            "status": c.status,
            "professional_notes": c.professional_notes,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
        }
        for c in cases
    ]


@router.get("/cases/{case_id}")
def get_portal_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "id": case.id,
        "image_filename": case.image_filename,
        "condition": case.condition,
        "condition_display": case.condition_display,
        "confidence": round(case.confidence * 100, 1),
        "risk_level": case.risk_level,
        "body_location": case.body_location,
        "symptoms_json": case.symptoms_json,
        "recommendation": case.recommendation,
        "status": case.status,
        "professional_notes": case.professional_notes,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "reviewed_at": case.reviewed_at.isoformat() if case.reviewed_at else None,
    }


@router.patch("/cases/{case_id}/review")
def review_case(case_id: int, update: ReviewUpdate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.professional_notes = update.notes
    case.status = update.status
    case.reviewed_at = datetime.utcnow()
    db.commit()

    return {"message": "Case updated successfully", "case_id": case_id}


@router.get("/stats")
def portal_stats(db: Session = Depends(get_db)):
    total = db.query(Case).filter(Case.submitted_to_portal == 1).count()
    pending = db.query(Case).filter(Case.submitted_to_portal == 1, Case.status == "pending").count()
    reviewed = db.query(Case).filter(Case.submitted_to_portal == 1, Case.status == "reviewed").count()
    high_risk = db.query(Case).filter(Case.submitted_to_portal == 1, Case.risk_level == "HIGH").count()

    return {
        "total": total,
        "pending": pending,
        "reviewed": reviewed,
        "high_risk": high_risk,
    }
