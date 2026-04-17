# DermCheck — AI Skin Condition Analysis

CM3202 Emerging Technologies Group Project — Theme 2: Digital Health and Wellbeing

## Overview

DermCheck is a web application that lets users upload a photo of a skin concern and receive an AI-powered analysis in seconds. The backend runs an EfficientNet-B0 convolutional neural network trained on the HAM10000 dermoscopic image dataset. High-risk findings are automatically forwarded to a professional review portal where clinicians can view cases, add notes, and mark them as reviewed.

### Key features

| Feature | Technology |
|---|---|
| CNN skin lesion classifier | PyTorch · EfficientNet-B0 · Transfer learning |
| Grad-CAM explainability heatmap | Custom gradient hook implementation |
| Symptom-based NLP risk adjustment | Rule-based scoring on structured input |
| Interactive body map | SVG click interface |
| Professional review portal | FastAPI · SQLite · React |
| REST API | FastAPI with auto-generated docs at `/docs` |

---

## Project structure

```
.
├── backend/
│   ├── main.py               # FastAPI application entry point
│   ├── database.py           # SQLAlchemy models and DB setup
│   ├── requirements.txt
│   ├── routes/
│   │   ├── diagnosis.py      # /api/diagnosis endpoints
│   │   └── portal.py         # /api/portal endpoints
│   └── ml/
│       ├── model.py          # EfficientNet-B0 architecture + class definitions
│       ├── train.py          # Training script for HAM10000
│       └── predict.py        # Inference + Grad-CAM generation
└── frontend/
    ├── src/
    │   ├── pages/            # Home, Upload, Results, Portal
    │   └── components/       # Navbar, BodyMap, SymptomForm, RiskBadge, Disclaimer
    ├── package.json
    └── vite.config.js        # Proxies /api and /uploads to backend
```

---

## Setup

### Prerequisites

- Python 3.11+ (install from **python.org**, not the Microsoft Store)
- Node.js 18+
- Nvidia GPU recommended for training (CPU works but is very slow)

### 1 — Install backend dependencies

**With Nvidia GPU (recommended):**
```bash
cd backend
pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cu126
```

**CPU only (no GPU):**
```bash
cd backend
pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu
```

### 2 — Train the model (or skip to demo mode)

**Download the HAM10000 dataset** from Kaggle:
https://www.kaggle.com/datasets/kmader/skin-lesion-analysis-toward-melanoma-detection

Unzip so you have:
```
backend/
  data/
    HAM10000_images_part_1/
    HAM10000_images_part_2/
    HAM10000_metadata.csv
```

Then run:
```bash
cd backend
python ml/train.py --data_dir ./data --epochs 30 --batch_size 32
```

Training takes roughly 2–3 hours on a mid-range GPU. The best checkpoint is saved to `backend/ml/checkpoints/best_model.pth`.

> **Demo mode:** If no checkpoint exists, the app still runs using ImageNet-pretrained weights as a stand-in. Predictions will not be clinically meaningful but the full UI and workflow can be demonstrated.

### 3 — Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4 — Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## ML model details

**Architecture:** EfficientNet-B0, fine-tuned from ImageNet weights

**Dataset:** HAM10000 — 10,015 dermoscopic images across 7 classes

| Class | Condition | Risk level |
|---|---|---|
| mel | Melanoma | HIGH |
| bcc | Basal Cell Carcinoma | HIGH |
| akiec | Actinic Keratosis | HIGH |
| vasc | Vascular Lesion | MEDIUM |
| bkl | Benign Keratosis | MEDIUM |
| nv | Melanocytic Nevus | LOW |
| df | Dermatofibroma | LOW |

**Class imbalance:** HAM10000 is heavily skewed (~67% nevi). We address this with weighted random sampling during training and class-weighted cross-entropy loss.

**Explainability:** Grad-CAM hooks into the final convolutional block to produce a spatial heatmap, giving users and clinicians a visual explanation of the prediction.

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/diagnosis/analyse` | Upload image, receive diagnosis |
| GET | `/api/diagnosis/case/{id}` | Retrieve a specific case |
| GET | `/api/portal/cases` | List all portal cases (filterable) |
| GET | `/api/portal/cases/{id}` | Get full case detail |
| PATCH | `/api/portal/cases/{id}/review` | Add clinician notes and mark reviewed |
| GET | `/api/portal/stats` | Summary statistics |

---

## Disclaimer

DermCheck is a proof-of-concept academic project. It is not a certified medical device and should not be used to make clinical decisions. Always consult a qualified healthcare professional for any skin concern.
