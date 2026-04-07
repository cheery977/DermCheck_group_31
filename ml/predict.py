"""
Inference module for the DermCheck classifier.

Handles:
  - Image preprocessing
  - Model loading (with demo-mode fallback if PyTorch isn't available)
  - Grad-CAM heatmap generation
  - Returning a structured prediction dict
"""

import os
import uuid
import random
from pathlib import Path

from ml.constants import CLASS_NAMES, CLASS_DISPLAY_NAMES, RISK_LEVELS

CHECKPOINT_PATH = Path(__file__).parent / "checkpoints" / "best_model.pth"
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

# Try importing PyTorch — fall back to demo mode if DLLs aren't available
try:
    import torch
    import torch.nn.functional as F
    from torchvision import transforms
    from PIL import Image
    import numpy as np
    TORCH_AVAILABLE = True
except OSError:
    TORCH_AVAILABLE = False
    print("[WARN] PyTorch could not be loaded (missing DLLs). Running in DEMO mode.")
    print("[WARN] Install Visual C++ Redistributable 2022 x64 from Microsoft to fix this.")
    from PIL import Image
    import numpy as np

_model = None


# ── Demo mode ─────────────────────────────────────────────────────────────────

def _demo_prediction() -> dict:
    """
    Returns a plausible-looking prediction without running the model.
    Used when PyTorch DLLs are unavailable (e.g. missing VC++ Redistributable).
    """
    # Pick a realistic distribution — mostly benign, occasionally high risk
    weights = [0.05, 0.08, 0.12, 0.03, 0.10, 0.55, 0.07]
    chosen_idx = random.choices(range(len(CLASS_NAMES)), weights=weights, k=1)[0]
    confidence = random.uniform(0.62, 0.91)

    # Build top-3 style predictions
    remaining = [i for i in range(len(CLASS_NAMES)) if i != chosen_idx]
    other_two = random.sample(remaining, 2)
    leftover = round((1.0 - confidence) * random.uniform(0.5, 0.8), 3)

    top_predictions = [
        {
            "condition": CLASS_NAMES[chosen_idx],
            "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[chosen_idx]],
            "probability": round(confidence * 100, 1),
        },
        {
            "condition": CLASS_NAMES[other_two[0]],
            "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[other_two[0]]],
            "probability": round(leftover * 100, 1),
        },
        {
            "condition": CLASS_NAMES[other_two[1]],
            "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[other_two[1]]],
            "probability": round((1.0 - confidence - leftover) * 100, 1),
        },
    ]

    condition = CLASS_NAMES[chosen_idx]
    return {
        "condition": condition,
        "condition_display": CLASS_DISPLAY_NAMES[condition],
        "confidence": round(confidence, 4),
        "risk_level": RISK_LEVELS[condition],
        "top_predictions": top_predictions,
        "gradcam_filename": None,
        "demo_mode": True,
    }


# ── Real inference ─────────────────────────────────────────────────────────────

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]


def _get_model():
    global _model
    if _model is not None:
        return _model, True

    from ml.model import build_model, load_trained_model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if CHECKPOINT_PATH.exists():
        _model = load_trained_model(str(CHECKPOINT_PATH), device)
        return _model, True

    print("[WARN] No trained weights found. Using ImageNet pretrained weights for demo.")
    _model = build_model(num_classes=len(CLASS_NAMES), pretrained=True).to(device)
    _model.eval()
    return _model, False


def _preprocess(image_path: str):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    img = Image.open(image_path).convert("RGB")
    return transform(img).unsqueeze(0)


class GradCAM:
    def __init__(self, model):
        self.model = model
        self.gradients = None
        self.activations = None
        self._handles = []
        target = model.features[-1]
        self._handles.append(target.register_forward_hook(
            lambda m, i, o: setattr(self, 'activations', o.detach())
        ))
        self._handles.append(target.register_full_backward_hook(
            lambda m, gi, go: setattr(self, 'gradients', go[0].detach())
        ))

    def remove(self):
        for h in self._handles:
            h.remove()

    def generate(self, tensor, class_idx):
        import torch.nn.functional as F
        self.model.zero_grad()
        out = self.model(tensor)
        out[0, class_idx].backward()
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self.activations).sum(dim=1, keepdim=True))
        cam = F.interpolate(cam, (224, 224), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()
        return (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)


def _save_gradcam(original_path: str, cam) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm as mpl_cm

    orig = np.array(Image.open(original_path).convert("RGB").resize((224, 224))) / 255.0
    overlay = np.clip(0.55 * orig + 0.45 * mpl_cm.jet(cam)[:, :, :3], 0, 1)

    out_name = f"gradcam_{uuid.uuid4().hex[:8]}.jpg"
    fig, ax = plt.subplots(figsize=(3, 3))
    ax.imshow(overlay)
    ax.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(str(UPLOAD_DIR / out_name), bbox_inches="tight", pad_inches=0, dpi=100)
    plt.close(fig)
    return out_name


# ── Public entry point ─────────────────────────────────────────────────────────

def run_prediction(image_path: str) -> dict:
    if not TORCH_AVAILABLE:
        return _demo_prediction()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, has_weights = _get_model()
    tensor = _preprocess(image_path).to(device)

    with torch.no_grad():
        probs = torch.nn.functional.softmax(model(tensor), dim=1)[0]

    top_idx = probs.argmax().item()
    top3 = probs.topk(3).indices.tolist()

    top_predictions = [
        {
            "condition": CLASS_NAMES[i],
            "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[i]],
            "probability": round(probs[i].item() * 100, 1),
        }
        for i in top3
    ]

    gradcam_filename = None
    try:
        t2 = _preprocess(image_path).to(device).requires_grad_(True)
        gc = GradCAM(model)
        cam = gc.generate(t2, top_idx)
        gc.remove()
        gradcam_filename = _save_gradcam(image_path, cam)
    except Exception as e:
        print(f"[WARN] Grad-CAM failed: {e}")

    condition = CLASS_NAMES[top_idx]
    return {
        "condition": condition,
        "condition_display": CLASS_DISPLAY_NAMES[condition],
        "confidence": round(probs[top_idx].item(), 4),
        "risk_level": RISK_LEVELS[condition],
        "top_predictions": top_predictions,
        "gradcam_filename": gradcam_filename,
        "demo_mode": not has_weights,
    }
