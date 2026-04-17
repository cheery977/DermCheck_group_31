import os
import uuid
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import init_db, get_db
from routes import diagnosis, portal

# Create upload folder if it doesn't exist
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="DermCheck API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["Diagnosis"])
app.include_router(portal.router, prefix="/api/portal", tags=["Professional Portal"])

# Serve uploaded images statically
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "DermCheck API"}
