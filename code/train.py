#!/usr/bin/env python3
"""Single-process trainer for the ROF/T-BIOM study.

Supports CPU and CUDA.

The normal research run uses the complete training split. The optional
--max-batches argument is intended only for smoke testing so that the full
DINOv2 forward/backward pipeline can be verified quickly without processing
the entire dataset.

Training uses identity classification only as a training objective.
Final reporting must use verification/evaluation on held-out identities.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision.transforms import v2

from model import VerificationModel, trainable_parameters


VARIANTS = [
    "frozen_whole",
    "whole_lora",
    "peri_lora",
    "fixed_fusion",
    "gated_fusion",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Single-process ROF/T-BIOM trainer"
    )

    parser.add_argument(
        "--manifest",
        required=True,
        help="Training manifest containing face_path, peri_path and identity",
    )

    parser.add_argument(
        "--variant",
        default="gated_fusion",
        choices=VARIANTS,
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        "--out",
        required=True,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
        help="DataLoader workers. 0 is recommended on Windows CPU.",
    )

    parser.add_argument(
        "--image-size",
        type=int,
        default=224,
    )

    parser.add_argument(
        "--max-batches",
        type=int,
        default=0,
        help=(
            "Maximum number of batches per epoch. "
            "0 means use the complete dataset. "
            "Use a small value such as 5 only for smoke testing."
        ),
    )

    parser.add_argument(
        "--resume-from",
        default=None,
        help=(
            "Path to a partial checkpoint (model/head/id_to_label/epoch). "
            "Training continues from the stored epoch + 1 instead of epoch 1. "
            "The optimizer is recreated (checkpoints do not store optimizer "
            "state), so resumed epochs differ slightly from a continuous run."
        ),
    )

    return parser.parse_args()


def seed_everything(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class FaceDataset(Dataset):
    def __init__(self, rows, id_to_label, size=224):
        self.rows = rows
        self.id_to_label = id_to_label

        self.tf = v2.Compose([
            v2.ToImage(),
            v2.Resize((size, size)),
            v2.ToDtype(torch.float32, scale=True),
            v2.Normalize(
                [0.485, 0.456, 0.406],
                [0.229, 0.224, 0.225],
            ),
        ])

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]

        face_path = row["face_path"]
        peri_path = row.get("peri_path", "")

        if not peri_path:
            raise RuntimeError(
                f"Empty peri_path at row {index}: {face_path}"
            )

        try:
            face = self.tf(
                Image.open(face_path).convert("RGB")
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load face image at row {index}: "
                f"{face_path}"
            ) from exc

        try:
            peri = self.tf(
                Image.open(peri_path).convert("RGB")
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load periocular image at row {index}: "
                f"{peri_path}"
            ) from exc

        q = torch.tensor(
            [
                float(row.get("face_conf") or 1.0),
                float(row.get("peri_conf") or 1.0),
                float(row.get("blur") or 0.0),
                float(row.get("visible_ratio") or 1.0),
            ],
            dtype=torch.float32,
        )

        identity = row["identity"]

        if identity not in self.id_to_label:
            raise RuntimeError(
                f"Unknown identity '{identity}' at row {index}"
            )

        target = self.id_to_label[identity]

        return face, peri, q, target


def read_rows(path, split="train"):
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Manifest not found: {path}"
        )

    with open(
        path,
        newline="",
        encoding="utf-8",
    ) as f:
        all_rows = list(csv.DictReader(f))
        seen_hashes = set()
        for row in all_rows:
            content_hash = row.get("sha256", "")
            if not content_hash or content_hash in seen_hashes:
                raise ValueError(
                    "Training requires a content-unique, audited manifest. "
                    "Use the current audited manifest in manifests/cpu_followup/; historical checkpoints "
                    "must not be reused as clean-trained models."
                )
            seen_hashes.add(content_hash)
        identity_splits = {}
        for row in all_rows:
            identity_splits.setdefault(row["identity"], set()).add(row["split"])
        if any(len(splits) != 1 for splits in identity_splits.values()):
            raise ValueError("Identity occurs in multiple splits")
        rows = [row for row in all_rows if row.get("split") == split]

    if not rows:
        raise ValueError(
            f"No rows with split='{split}' in {path}"
        )

    required = [
        "face_path",
        "peri_path",
        "identity",
    ]

    missing = [
        column
        for column in required
        if column not in rows[0]
    ]

    if missing:
        raise ValueError(
            f"Manifest missing columns: {missing}"
        )

    print(
        f"Loaded {len(rows):,} rows from split='{split}'",
        flush=True,
    )

    print(
        "Checking image paths...",
        flush=True,
    )

    for i, row in enumerate(rows):
        face_path = Path(row["face_path"])
        peri_path = Path(row["peri_path"])

        if not face_path.is_file():
            raise FileNotFoundError(
                f"Invalid face_path row {i}: {face_path}"
            )

        if not peri_path.is_file():
            raise FileNotFoundError(
                f"Invalid peri_path row {i}: {peri_path}"
            )

    print(
        "Image path validation: PASSED",
        flush=True,
    )

    return rows


def build_sampler(rows):
    """
    If the manifest contains a 'source' column, samples are weighted
    inversely by source frequency.

    For the current ROF-only manifest, source may not exist, so all
    rows belong to a single logical source.
    """

    sources = [
        row.get("source", "single_source")
        for row in rows
    ]

    counts = defaultdict(int)

    for source in sources:
        counts[source] += 1

    weights = torch.tensor(
        [
            1.0 / counts[source]
            for source in sources
        ],
        dtype=torch.double,
    )

    return WeightedRandomSampler(
        weights,
        num_samples=len(weights),
        replacement=True,
    )


def main():
    args = parse_args()

    if args.max_batches < 0:
        raise ValueError(
            "--max-batches must be >= 0"
        )

    if args.epochs < 1:
        raise ValueError(
            "--epochs must be >= 1"
        )

    if args.batch_size < 1:
        raise ValueError(
            "--batch-size must be >= 1"
        )

    seed_everything(args.seed)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("=" * 80, flush=True)
    print("ROF / T-BIOM TRAINING", flush=True)
    print("=" * 80, flush=True)

    print(
        f"Device: {device}",
        flush=True,
    )

    if device.type == "cuda":
        print(
            f"GPU: {torch.cuda.get_device_name(0)}",
            flush=True,
        )

    print(
        f"Variant: {args.variant}",
        flush=True,
    )

    print(
        f"Epochs: {args.epochs}",
        flush=True,
    )

    print(
        f"Batch size: {args.batch_size}",
        flush=True,
    )

    print(
        f"Learning rate: {args.lr}",
        flush=True,
    )

    print(
        f"Seed: {args.seed}",
        flush=True,
    )

    print(
        f"Num workers: {args.num_workers}",
        flush=True,
    )

    if args.max_batches > 0:
        print(
            f"SMOKE TEST: max {args.max_batches} batches/epoch",
            flush=True,
        )
    else:
        print(
            "Full training mode: complete training split",
            flush=True,
        )

    print(
        f"Manifest: {args.manifest}",
        flush=True,
    )

    print(
        f"Output: {args.out}",
        flush=True,
    )

    print("=" * 80, flush=True)

    rows = read_rows(
        args.manifest,
        split="train",
    )

    identities = sorted(
        {
            row["identity"]
            for row in rows
        }
    )

    id_to_label = {
        identity: index
        for index, identity in enumerate(identities)
    }

    print(
        f"Training rows: {len(rows):,}",
        flush=True,
    )

    print(
        f"Identity classes: {len(identities):,}",
        flush=True,
    )

    dataset = FaceDataset(
        rows,
        id_to_label,
        size=args.image_size,
    )

    sampler = build_sampler(rows)

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
        persistent_workers=(
            args.num_workers > 0
        ),
    )

    print(
        "Building model...",
        flush=True,
    )

    model = VerificationModel(
        args.variant
    ).to(device)

    parameter_info = trainable_parameters(
        model
    )

    print(
        f"Model parameters: {parameter_info}",
        flush=True,
    )

    # Training-only identity classification head.
    head = nn.Linear(
        768,
        len(identities),
    ).to(device)

    start_epoch = 0

    if args.resume_from:
        resume_path = Path(args.resume_from)

        if not resume_path.is_file():
            raise FileNotFoundError(
                f"No checkpoint to resume from: {resume_path}"
            )

        ckpt = torch.load(
            resume_path,
            map_location="cpu",
            weights_only=False,
        )

        if ckpt.get("manifest_sha256") != hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest():
            raise ValueError("Resume manifest hash differs or is absent; do not reuse historical checkpoints for cleaned training")

        resume_variant = ckpt.get("variant")
        resume_seed = ckpt.get("seed")

        if resume_variant != args.variant:
            raise ValueError(
                f"Checkpoint variant '{resume_variant}' "
                f"does not match --variant '{args.variant}'"
            )

        if resume_seed != args.seed:
            raise ValueError(
                f"Checkpoint seed '{resume_seed}' "
                f"does not match --seed '{args.seed}'"
            )

        if "model" not in ckpt or "head" not in ckpt:
            raise ValueError(
                f"Checkpoint has no model/head state: {resume_path}"
            )

        model.load_state_dict(ckpt["model"])
        head.load_state_dict(ckpt["head"])

        resume_id_to_label = ckpt.get("id_to_label")

        if resume_id_to_label:
            id_to_label = resume_id_to_label

        start_epoch = int(ckpt.get("epoch", 0))

        if start_epoch >= args.epochs:
            print(
                f"RESUME: checkpoint already at epoch {start_epoch} "
                f"(>= --epochs {args.epochs}); nothing to do.",
                flush=True,
            )

            return

        print(
            f"RESUME: continuing from epoch {start_epoch + 1} "
            f"of {args.epochs}",
            flush=True,
        )

    trainable_params = [
        parameter
        for parameter in (
            list(model.parameters())
            + list(head.parameters())
        )
        if parameter.requires_grad
    ]

    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=args.lr,
        weight_decay=1e-4,
    )

    criterion = nn.CrossEntropyLoss()

    model.train()
    head.train()

    Path(args.out).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_batches = len(loader)

    if args.max_batches > 0:
        effective_batches = min(
            total_batches,
            args.max_batches,
        )
    else:
        effective_batches = total_batches

    print(
        f"DataLoader batches/epoch: {total_batches:,}",
        flush=True,
    )

    print(
        f"Effective batches/epoch: {effective_batches:,}",
        flush=True,
    )

    print("=" * 80, flush=True)

    for epoch_num in range(start_epoch + 1, args.epochs + 1):
        model.train()
        head.train()

        losses = []

        print(
            f"Starting epoch {epoch_num}/{args.epochs}",
            flush=True,
        )

        for batch_idx, (
            face,
            peri,
            quality,
            target,
        ) in enumerate(
            loader,
            start=1,
        ):

            if (
                args.max_batches > 0
                and batch_idx > args.max_batches
            ):
                break

            face = face.to(
                device,
                non_blocking=True,
            )

            peri = peri.to(
                device,
                non_blocking=True,
            )

            quality = quality.to(
                device,
                non_blocking=True,
            )

            target = target.to(
                device,
                non_blocking=True,
            )

            optimizer.zero_grad(
                set_to_none=True
            )

            embedding = model(
                face,
                peri,
                quality,
            )

            logits = head(
                embedding
            )

            loss = criterion(
                logits,
                target,
            )

            loss.backward()

            optimizer.step()

            loss_value = float(
                loss.detach().item()
            )

            losses.append(
                loss_value
            )

            print(
                f"epoch={epoch_num} "
                f"batch={batch_idx}/{effective_batches} "
                f"loss={loss_value:.5f}",
                flush=True,
            )

        if not losses:
            raise RuntimeError(
                "No training batches were processed."
            )

        epoch_loss = float(
            np.mean(losses)
        )

        checkpoint = {
            "model": model.state_dict(),
            "head": head.state_dict(),
            "variant": args.variant,
            "id_to_label": id_to_label,
            "epoch": epoch_num,
            "seed": args.seed,
            "manifest_sha256": hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(),
        }

        torch.save(
            checkpoint,
            args.out,
        )

        print(
            f"epoch={epoch_num} "
            f"loss={epoch_loss:.5f} "
            f"saved={args.out}",
            flush=True,
        )

        print("=" * 80, flush=True)

    print(
        "TRAINING COMPLETE",
        flush=True,
    )

    print(
        f"saved {args.out}",
        flush=True,
    )


if __name__ == "__main__":
    main()
