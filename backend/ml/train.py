"""
Training script for the DermCheck skin lesion classifier.

Dataset: HAM10000 (Human Against Machine with 10000 training images)
Source: https://www.kaggle.com/datasets/kmader/skin-lesion-analysis-toward-melanoma-detection
        or via ISIC archive: https://isic-archive.com/

Expected folder layout after download:
    data/
        HAM10000_images_part_1/   <- unzip both parts here
        HAM10000_images_part_2/
        HAM10000_metadata.csv

Run:
    python train.py --data_dir ./data --epochs 30 --batch_size 32
"""

import os
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms
from tqdm import tqdm

from ml.model import build_model, CLASS_NAMES


# ── Dataset ──────────────────────────────────────────────────────────────────

class HAM10000Dataset(Dataset):
    def __init__(self, df: pd.DataFrame, image_dir: str, transform=None):
        self.df = df.reset_index(drop=True)
        self.image_dir = image_dir
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = os.path.join(self.image_dir, row["image_id"] + ".jpg")
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        label = CLASS_NAMES.index(row["dx"])
        return image, label


# ── Transforms ────────────────────────────────────────────────────────────────

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

train_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_image_dir(data_dir: str) -> str:
    """Look for the image folders in both HAM10000 part folders."""
    parts = [
        os.path.join(data_dir, "HAM10000_images_part_1"),
        os.path.join(data_dir, "HAM10000_images_part_2"),
    ]
    # Collect all .jpg paths into a single flat folder reference
    # We handle this by checking both at predict time
    for p in parts:
        if os.path.isdir(p):
            return data_dir  # return root; dataset handles both parts
    raise FileNotFoundError(
        "Could not find HAM10000_images_part_1 or _part_2 under " + data_dir
    )


def find_image_path(image_id: str, data_dir: str) -> str:
    for sub in ["HAM10000_images_part_1", "HAM10000_images_part_2"]:
        path = os.path.join(data_dir, sub, image_id + ".jpg")
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Image not found: {image_id}")


class HAM10000DatasetMultipart(Dataset):
    """Handles images split across two HAM10000 zip archives."""

    def __init__(self, df: pd.DataFrame, data_dir: str, transform=None):
        self.df = df.reset_index(drop=True)
        self.data_dir = data_dir
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = find_image_path(row["image_id"], self.data_dir)
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        label = CLASS_NAMES.index(row["dx"])
        return image, label


def make_weighted_sampler(labels):
    """
    HAM10000 is heavily imbalanced (~67% nv). Use oversampling so the model
    doesn't just predict nv for everything.
    """
    class_counts = np.bincount(labels)
    class_weights = 1.0 / class_counts
    sample_weights = [class_weights[l] for l in labels]
    return WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)


# ── Training loop ─────────────────────────────────────────────────────────────

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss, correct, total = 0.0, 0, 0

    for images, labels in tqdm(loader, desc="  train", leave=False):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return running_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0

    for images, labels in tqdm(loader, desc="  val  ", leave=False):
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return running_loss / total, correct / total


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load metadata
    csv_path = os.path.join(args.data_dir, "HAM10000_metadata.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Metadata CSV not found at {csv_path}")

    df = pd.read_csv(csv_path)
    # Some images appear multiple times (different lesion_id, same image) — deduplicate
    df = df.drop_duplicates(subset=["image_id"])

    print(f"Total images: {len(df)}")
    print("Class distribution:")
    print(df["dx"].value_counts())

    train_df, val_df = train_test_split(df, test_size=0.2, stratify=df["dx"], random_state=42)

    train_dataset = HAM10000DatasetMultipart(train_df, args.data_dir, transform=train_transform)
    val_dataset   = HAM10000DatasetMultipart(val_df,   args.data_dir, transform=val_transform)

    train_labels = [CLASS_NAMES.index(row["dx"]) for _, row in train_df.iterrows()]
    sampler = make_weighted_sampler(train_labels)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, num_workers=4, pin_memory=True)
    val_loader   = DataLoader(val_dataset,   batch_size=args.batch_size, shuffle=False,  num_workers=4, pin_memory=True)

    model = build_model(num_classes=len(CLASS_NAMES), pretrained=True).to(device)

    # Class weights for loss function as a secondary measure against imbalance
    class_counts = np.bincount([CLASS_NAMES.index(d) for d in df["dx"]])
    class_weights = torch.tensor(1.0 / class_counts, dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    os.makedirs(args.output_dir, exist_ok=True)
    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(1, args.epochs + 1):
        print(f"\nEpoch {epoch}/{args.epochs}")
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - t0
        print(f"  Train loss: {train_loss:.4f}  acc: {train_acc:.4f}")
        print(f"  Val   loss: {val_loss:.4f}  acc: {val_acc:.4f}  [{elapsed:.1f}s]")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            save_path = os.path.join(args.output_dir, "best_model.pth")
            torch.save(model.state_dict(), save_path)
            print(f"  Saved best model (val_acc={best_val_acc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stopping after {epoch} epochs (no improvement for {args.patience} epochs).")
                break

    print(f"\nTraining complete. Best validation accuracy: {best_val_acc:.4f}")
    print(f"Model saved to: {os.path.join(args.output_dir, 'best_model.pth')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DermCheck skin lesion classifier")
    parser.add_argument("--data_dir",   type=str, default="./data",     help="Path to HAM10000 data folder")
    parser.add_argument("--output_dir", type=str, default="./checkpoints", help="Where to save model weights")
    parser.add_argument("--epochs",     type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr",         type=float, default=1e-4)
    parser.add_argument("--patience",   type=int, default=7, help="Early stopping patience")
    args = parser.parse_args()

    train(args)
