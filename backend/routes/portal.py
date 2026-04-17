from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from database import get_db, Case

router = APIRouter()

PORTAL_FILTER = Case.submitted_to_portal == 1


class ReviewUpdate(BaseModel):
    notes: str
    status: str = "reviewed"


def _get_case_or_404(case_id: int, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def _fmt_dt(dt):
    return dt.isoformat() if dt else None


def _serialize_case(c: Case, detail: bool = False) -> dict:
    base = {
        "id": c.id,
        "image_filename": c.image_filename,
        "condition_display": c.condition_display,
        "confidence": c.confidence,
        "risk_level": c.risk_level,
        "body_location": c.body_location,
        "recommendation": c.recommendation,
        "status": c.status,
        "professional_notes": c.professional_notes,
        "created_at": _fmt_dt(c.created_at),
        "reviewed_at": _fmt_dt(c.reviewed_at),
    }
    if detail:
        base["condition"] = c.condition
        base["symptoms_json"] = c.symptoms_json
    return base


@router.get("/cases")
def list_cases(
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Case).filter(PORTAL_FILTER)
    if status:
        query = query.filter(Case.status == status)
    if risk_level:
        query = query.filter(Case.risk_level == risk_level)
    return [_serialize_case(c) for c in query.order_by(Case.created_at.desc()).all()]


@router.get("/cases/{case_id}")
def get_portal_case(case_id: int, db: Session = Depends(get_db)):
    return _serialize_case(_get_case_or_404(case_id, db), detail=True)


@router.patch("/cases/{case_id}/review")
def review_case(case_id: int, update: ReviewUpdate, db: Session = Depends(get_db)):
    c = _get_case_or_404(case_id, db)
    c.professional_notes = update.notes
    c.status = update.status
    c.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Case updated successfully", "case_id": case_id}


@router.get("/stats")
def portal_stats(db: Session = Depends(get_db)):
    row = db.query(
        func.count().label("total"),
        func.sum(case((Case.status == "pending", 1), else_=0)).label("pending"),
        func.sum(case((Case.status == "reviewed", 1), else_=0)).label("reviewed"),
        func.sum(case((Case.risk_level == "HIGH", 1), else_=0)).label("high_risk"),
    ).filter(PORTAL_FILTER).one()
    return {
        "total": row.total or 0,
        "pending": row.pending or 0,
        "reviewed": row.reviewed or 0,
        "high_risk": row.high_risk or 0,
    }
