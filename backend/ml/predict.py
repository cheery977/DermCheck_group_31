"""
Inference module — loads the trained EfficientNet-B0 and runs predictions.
Falls back to demo mode if PyTorch DLLs aren't available (e.g. missing VC++ Redistributable).
"""

import os
import uuid
import random
import threading
from pathlib import Path

import numpy as np
from PIL import Image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as mpl_cm

from ml.constants import CLASS_NAMES, CLASS_DISPLAY_NAMES, RISK_LEVELS

try:
    import torch
    import torch.nn.functional as F
    from torchvision import transforms
    TORCH_AVAILABLE = True
except OSError:
    TORCH_AVAILABLE = False
    print("[WARN] PyTorch could not be loaded — running in DEMO mode.")
    print("[WARN] Install Visual C++ Redistributable 2022 x64 from Microsoft to fix this.")

CHECKPOINT_PATH = Path(__file__).parent / "checkpoints" / "best_model.pth"
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

_model = None
_model_lock = threading.Lock()


# ── Model loading ──────────────────────────────────────────────────────────────

def _get_model():
    global _model
    if _model is not None:
        return _model, True

    with _model_lock:
        if _model is not None:
            return _model, True

        from ml.model import build_model, load_trained_model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if CHECKPOINT_PATH.exists():
            _model = load_trained_model(str(CHECKPOINT_PATH), device)
        else:
            print("[WARN] No trained weights found — using ImageNet pretrained weights for demo.")
            _model = build_model(num_classes=len(CLASS_NAMES), pretrained=True).to(device)
            _model.eval()

        return _model, CHECKPOINT_PATH.exists()


def _preprocess(image_path: str) -> "torch.Tensor":
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    return transform(Image.open(image_path).convert("RGB")).unsqueeze(0)


# ── Grad-CAM ──────────────────────────────────────────────────────────────────

class GradCAM:
    """
    Hooks into the last conv block of EfficientNet-B0.
    Runs one forward+backward pass and returns both the class probabilities
    and a spatial heatmap — avoiding a redundant second forward pass.
    """

    def __init__(self, model: "torch.nn.Module"):
        self.model = model
        self._activations = None
        self._gradients = None
        target = model.features[-1]
        self._handles = [
            target.register_forward_hook(self._save_activations),
            target.register_full_backward_hook(self._save_gradients),
        ]

    def _save_activations(self, module, input, output):
        self._activations = output

    def _save_gradients(self, module, grad_input, grad_output):
        self._gradients = grad_output[0]

    def remove(self):
        for h in self._handles:
            h.remove()

    def run(self, tensor: "torch.Tensor") -> tuple:
        """
        Returns (probs tensor, cam numpy array for top class).
        Single forward+backward pass — no redundant inference.
        """
        self.model.zero_grad()
        logits = self.model(tensor)
        probs = F.softmax(logits, dim=1)[0]
        top_idx = probs.argmax().item()
        logits[0, top_idx].backward()

        weights = self._gradients.detach().mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * self._activations.detach()).sum(dim=1, keepdim=True))
        cam = F.interpolate(cam, (224, 224), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)

        return probs.detach(), cam


def _save_gradcam(original_path: str, cam: np.ndarray) -> str:
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


# ── Demo mode ──────────────────────────────────────────────────────────────────

# Approximate HAM10000 class distribution for realistic demo output
_DEMO_WEIGHTS = [0.03, 0.05, 0.11, 0.01, 0.11, 0.67, 0.02]


def _demo_prediction() -> dict:
    chosen = random.choices(range(len(CLASS_NAMES)), weights=_DEMO_WEIGHTS, k=1)[0]
    confidence = round(random.uniform(0.62, 0.91), 4)
    others = random.sample([i for i in range(len(CLASS_NAMES)) if i != chosen], 2)
    second = round((1 - confidence) * random.uniform(0.5, 0.8), 4)
    third = round(1 - confidence - second, 4)

    condition = CLASS_NAMES[chosen]
    return {
        "condition": condition,
        "condition_display": CLASS_DISPLAY_NAMES[condition],
        "confidence": confidence,
        "risk_level": RISK_LEVELS[condition],
        "top_predictions": [
            {"condition": CLASS_NAMES[chosen], "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[chosen]], "probability": round(confidence * 100, 1)},
            {"condition": CLASS_NAMES[others[0]], "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[others[0]]], "probability": round(second * 100, 1)},
            {"condition": CLASS_NAMES[others[1]], "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[others[1]]], "probability": round(third * 100, 1)},
        ],
        "gradcam_filename": None,
        "demo_mode": True,
    }


# ── Public entry point ─────────────────────────────────────────────────────────

def run_prediction(image_path: str) -> dict:
    if not TORCH_AVAILABLE:
        return _demo_prediction()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, has_weights = _get_model()

    tensor = _preprocess(image_path).to(device).requires_grad_(True)
    gc = GradCAM(model)

    try:
        probs, cam = gc.run(tensor)
    finally:
        gc.remove()

    top3 = probs.topk(3).indices.tolist()
    top_idx = top3[0]
    condition = CLASS_NAMES[top_idx]

    gradcam_filename = None
    try:
        gradcam_filename = _save_gradcam(image_path, cam)
    except Exception as e:
        print(f"[WARN] Grad-CAM save failed: {e}")

    return {
        "condition": condition,
        "condition_display": CLASS_DISPLAY_NAMES[condition],
        "confidence": round(probs[top_idx].item(), 4),
        "risk_level": RISK_LEVELS[condition],
        "top_predictions": [
            {
                "condition": CLASS_NAMES[i],
                "condition_display": CLASS_DISPLAY_NAMES[CLASS_NAMES[i]],
                "probability": round(probs[i].item() * 100, 1),
            }
            for i in top3
        ],
        "gradcam_filename": gradcam_filename,
        "demo_mode": not has_weights,
    }
