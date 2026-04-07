"""
Skin lesion classifier built on EfficientNet-B0.
Uses transfer learning from ImageNet weights then fine-tunes on HAM10000.
"""

import torch
import torch.nn as nn
from torchvision import models


from ml.constants import CLASS_NAMES, CLASS_DISPLAY_NAMES, RISK_LEVELS


def build_model(num_classes: int = 7, pretrained: bool = True) -> nn.Module:
    """
    Load EfficientNet-B0 and replace the classifier head with one
    that outputs num_classes logits.
    """
    weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = models.efficientnet_b0(weights=weights)

    # Replace classifier
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(in_features, num_classes),
    )

    return model


def load_trained_model(checkpoint_path: str, device: torch.device) -> nn.Module:
    model = build_model(num_classes=len(CLASS_NAMES), pretrained=False)
    state = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model
