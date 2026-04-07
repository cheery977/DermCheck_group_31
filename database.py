from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./dermcheck.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    image_filename = Column(String)
    condition = Column(String)
    condition_display = Column(String)
    confidence = Column(Float)
    risk_level = Column(String)   # LOW, MEDIUM, HIGH
    body_location = Column(String, nullable=True)
    symptoms_json = Column(Text, nullable=True)  # JSON string of symptom form answers
    recommendation = Column(Text)
    status = Column(String, default="pending")   # pending, reviewed
    professional_notes = Column(Text, nullable=True)
    submitted_to_portal = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
