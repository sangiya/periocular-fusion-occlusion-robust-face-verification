#!/usr/bin/env python3
"""Generate periocular crops from a face-image manifest using MediaPipe Face Mesh.

Expected input columns:
    face_path, identity, condition, split
Optional columns are preserved.

The script never substitutes face_path for peri_path. Failed detections receive
an empty peri_path, crop_status=failed, and a failure_reason. This prevents
silent leakage of whole-face images into the periocular branch.

Reproduces the exact crop stage used for the reported results:

python code/generate_periocular_mediapipe.py \
  --input work/rof_manifest_crop_input.csv \
  --output work/crop_manifest_person_disjoint.csv \
  --crop-dir work/periocular_person_disjoint \
  --margin 0.20 \
  --size 224

Note: the default --margin is 0.35, but the reported results were produced with
0.20. Always pass --margin explicitly.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable

import cv2
import mediapipe as mp
import numpy as np

# MediaPipe Face Mesh landmark groups covering both eyes, eyelids, and eyebrows.
LEFT_EYE = (33, 133, 160, 159, 158, 157, 173)
RIGHT_EYE = (362, 263, 387, 386, 385, 384, 398)
LEFT_BROW = (70, 63, 105, 66, 107)
RIGHT_BROW = (336, 296, 334, 293, 300)
PERIOCULAR_LANDMARKS = LEFT_EYE + RIGHT_EYE + LEFT_BROW + RIGHT_BROW


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--crop-dir', required=True, type=Path)
    p.add_argument('--size', type=int, default=224)
    p.add_argument('--margin', type=float, default=0.35,
                   help='Relative margin around the landmark box.')
    p.add_argument('--min-detection-confidence', type=float, default=0.50)
    # Retained for command compatibility. Some MediaPipe wheels do not expose
    # this FaceMesh constructor argument, so it is intentionally not passed.
    p.add_argument('--model-complexity', type=int, choices=[0, 1], default=1)
    p.add_argument('--max-images', type=int, default=0,
                   help='0 means all rows; useful for a smoke test.')
    return p.parse_args()


def clamp_box(x0: float, y0: float, x1: float, y1: float,
               width: int, height: int) -> tuple[int, int, int, int] | None:
    x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
    x1, y1 = min(width, int(np.ceil(x1))), min(height, int(np.ceil(y1)))
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def make_crop(image: np.ndarray, face_landmarks, margin: float,
              size: int) -> tuple[np.ndarray | None, str, float]:
    height, width = image.shape[:2]
    xs = np.array([face_landmarks.landmark[i].x * width for i in PERIOCULAR_LANDMARKS])
    ys = np.array([face_landmarks.landmark[i].y * height for i in PERIOCULAR_LANDMARKS])

    if not (np.isfinite(xs).all() and np.isfinite(ys).all()):
        return None, 'nonfinite_landmarks', 0.0

    # Reject landmarks far outside the image instead of silently clamping an
    # obviously invalid detection.
    if ((xs < -0.25 * width).any() or (xs > 1.25 * width).any() or
            (ys < -0.25 * height).any() or (ys > 1.25 * height).any()):
        return None, 'landmarks_out_of_range', 0.0

    x_min, x_max = float(xs.min()), float(xs.max())
    y_min, y_max = float(ys.min()), float(ys.max())
    box_w, box_h = x_max - x_min, y_max - y_min
    if box_w < 0.05 * width or box_h < 0.03 * height:
        return None, 'degenerate_periocular_box', 0.0

    # Expand horizontally and vertically; the resulting crop contains both
    # eyes, eyebrows, upper nose, and local surrounding context.
    pad_x, pad_y = margin * box_w, margin * box_h
    box = clamp_box(x_min - pad_x, y_min - pad_y,
                    x_max + pad_x, y_max + pad_y, width, height)
    if box is None:
        return None, 'empty_crop_box', 0.0

    x0, y0, x1, y1 = box
    crop = image[y0:y1, x0:x1]
    if crop.size == 0:
        return None, 'empty_crop', 0.0

    crop = cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)
    visibility = [getattr(face_landmarks.landmark[i], 'visibility', 1.0)
                  for i in PERIOCULAR_LANDMARKS]
    visibility = float(np.clip(np.mean(visibility), 0.0, 1.0))
    return crop, 'ok', visibility


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)

    with args.input.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if 'face_path' not in fieldnames:
        raise ValueError('Input manifest must contain face_path')
    if not rows:
        raise ValueError('Input manifest contains no rows')

    args.crop_dir.mkdir(parents=True, exist_ok=True)
    for col in ['peri_path', 'peri_conf', 'crop_status', 'crop_failure_reason']:
        if col not in fieldnames:
            fieldnames.append(col)

    mp_face_mesh = mp.solutions.face_mesh
    successes = 0
    failures: dict[str, int] = {}
    limit = args.max_images if args.max_images > 0 else len(rows)

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=args.min_detection_confidence,
    ) as mesh:
        for index, row in enumerate(rows[:limit]):
            source = Path(row['face_path'])
            # Stable filename based on row number; no source basename collisions.
            destination = args.crop_dir / f'peri_{index:06d}.jpg'
            row['peri_path'] = ''
            row['peri_conf'] = ''
            row['crop_status'] = 'failed'
            row['crop_failure_reason'] = ''

            image = cv2.imread(str(source))
            if image is None:
                reason = 'source_unreadable'
            else:
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                result = mesh.process(rgb)
                if not result.multi_face_landmarks:
                    reason = 'no_face_landmarks'
                else:
                    crop, reason, visibility = make_crop(
                        image, result.multi_face_landmarks[0], args.margin, args.size
                    )
                    if crop is not None and cv2.imwrite(str(destination), crop):
                        row['peri_path'] = str(destination.resolve())
                        row['peri_conf'] = f'{visibility:.6f}'
                        row['crop_status'] = 'valid'
                        successes += 1
                        reason = ''
                    elif crop is not None:
                        reason = 'crop_write_failed'

            if reason:
                row['crop_failure_reason'] = reason
                failures[reason] = failures.get(reason, 0) + 1

            if index == 0 or (index + 1) % 250 == 0:
                print(f'{index + 1}/{limit}: valid={successes}', flush=True)

    # Rows beyond --max-images remain explicitly unprocessed; this is useful
    # only for smoke tests and must not be used as a final manifest.
    for row in rows[limit:]:
        row['peri_path'] = ''
        row['peri_conf'] = ''
        row['crop_status'] = 'not_processed'
        row['crop_failure_reason'] = 'max_images_limit'

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f'Finished: {successes}/{len(rows)} valid crops')
    print(f'Failure summary: {failures}')
    print(f'Wrote manifest: {args.output.resolve()}')
    print(f'Wrote crops: {args.crop_dir.resolve()}')


if __name__ == '__main__':
    main()
