"""Verification metrics for face embeddings or similarity scores.

Designed for held-out, person-disjoint face verification experiments.
"""

from __future__ import annotations

import json

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve


def _validate(
    scores: np.ndarray,
    labels: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate and normalize metric inputs."""
    scores = np.asarray(scores, dtype=np.float64).reshape(-1)
    labels = np.asarray(labels, dtype=np.int64).reshape(-1)

    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")

    if len(scores) == 0:
        raise ValueError("scores and labels must not be empty")

    if len(np.unique(labels)) < 2:
        raise ValueError(
            "both genuine (1) and impostor (0) labels are required"
        )

    if not np.all(np.isfinite(scores)):
        raise ValueError("scores contain non-finite values")

    if not np.all(np.isin(labels, [0, 1])):
        raise ValueError("labels must contain only 0 and 1")

    return scores, labels


def cosine_scores(
    enroll: np.ndarray,
    probe: np.ndarray,
) -> np.ndarray:
    """Compute row-wise cosine similarity.

    Both arrays must have shape:
        [N, embedding_dimension]
    """
    enroll = np.asarray(enroll, dtype=np.float32)
    probe = np.asarray(probe, dtype=np.float32)

    if enroll.ndim != 2 or probe.ndim != 2:
        raise ValueError("enroll and probe must be 2-D arrays")

    if enroll.shape != probe.shape:
        raise ValueError(
            "enroll and probe must have the same shape"
        )

    enroll_norm = enroll / np.maximum(
        np.linalg.norm(enroll, axis=1, keepdims=True),
        1e-12,
    )

    probe_norm = probe / np.maximum(
        np.linalg.norm(probe, axis=1, keepdims=True),
        1e-12,
    )

    return np.sum(enroll_norm * probe_norm, axis=1)


def roc_statistics(
    scores: np.ndarray,
    labels: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return FPR, FNR and ROC thresholds."""
    scores, labels = _validate(scores, labels)

    fpr, tpr, thresholds = roc_curve(labels, scores)
    fnr = 1.0 - tpr

    return fpr, fnr, thresholds


def eer(
    scores: np.ndarray,
    labels: np.ndarray,
) -> tuple[float, float]:
    """Return interpolated Equal Error Rate and approximate threshold."""
    fpr, fnr, thresholds = roc_statistics(scores, labels)

    difference = fpr - fnr

    crossings = np.where(
        np.signbit(difference[:-1])
        != np.signbit(difference[1:])
    )[0]

    if len(crossings):
        i = int(crossings[0])

        d0 = float(difference[i])
        d1 = float(difference[i + 1])

        if abs(d1 - d0) > 1e-12:
            alpha = -d0 / (d1 - d0)
        else:
            alpha = 0.0

        alpha = float(np.clip(alpha, 0.0, 1.0))

        eer_value = float(
            fpr[i]
            + alpha * (fpr[i + 1] - fpr[i])
        )

        threshold = float(
            thresholds[i]
            + alpha * (
                thresholds[i + 1]
                - thresholds[i]
            )
        )

        return eer_value, threshold

    # Fallback if no crossing exists.
    i = int(
        np.nanargmin(
            np.abs(difference)
        )
    )

    return (
        float(
            (
                fpr[i]
                + fnr[i]
            )
            / 2.0
        ),
        float(thresholds[i]),
    )


def tar_at_far(
    scores: np.ndarray,
    labels: np.ndarray,
    far: float = 1e-3,
) -> tuple[float, float]:
    """Return TAR and threshold at or below the requested FAR.

    The threshold is selected from empirical ROC operating points.
    """
    if not 0.0 <= far <= 1.0:
        raise ValueError(
            "far must be between 0 and 1"
        )

    fpr, fnr, thresholds = roc_statistics(
        scores,
        labels,
    )

    tpr = 1.0 - fnr

    valid = np.where(fpr <= far)[0]

    if len(valid) == 0:
        return 0.0, float("inf")

    # Among operating points satisfying FAR <= target,
    # select the point with the highest TAR.
    best = valid[
        int(
            np.argmax(
                tpr[valid]
            )
        )
    ]

    return (
        float(tpr[best]),
        float(thresholds[best]),
    )


def summarize(
    scores: np.ndarray,
    labels: np.ndarray,
) -> dict[str, float | int]:
    """Calculate the primary verification metrics."""
    scores, labels = _validate(
        scores,
        labels,
    )

    eer_value, eer_threshold = eer(
        scores,
        labels,
    )

    tar_1e2, threshold_1e2 = tar_at_far(
        scores,
        labels,
        1e-2,
    )

    tar_1e3, threshold_1e3 = tar_at_far(
        scores,
        labels,
        1e-3,
    )

    return {
        "auc": float(
            roc_auc_score(
                labels,
                scores,
            )
        ),
        "eer": float(eer_value),
        "eer_threshold": float(
            eer_threshold
        ),
        "tar_far_1e-2": float(
            tar_1e2
        ),
        "tar_far_1e-2_threshold": float(
            threshold_1e2
        ),
        "tar_far_1e-3": float(
            tar_1e3
        ),
        "tar_far_1e-3_threshold": float(
            threshold_1e3
        ),
        "n_pairs": int(
            len(scores)
        ),
        "n_genuine": int(
            np.sum(labels == 1)
        ),
        "n_impostor": int(
            np.sum(labels == 0)
        ),
    }


def bootstrap_ci(
    scores: np.ndarray,
    labels: np.ndarray,
    n_boot: int = 1000,
    seed: int = 42,
) -> dict[str, tuple[float, float]]:
    """Calculate pair-level bootstrap 95% confidence intervals.

    For the final paper, identity/subject-level bootstrap is preferable
    when the same identities contribute many correlated pairs.
    """
    scores, labels = _validate(
        scores,
        labels,
    )

    if n_boot <= 0:
        raise ValueError(
            "n_boot must be positive"
        )

    rng = np.random.default_rng(seed)

    values = {
        "auc": [],
        "eer": [],
        "tar_far_1e-3": [],
    }

    n = len(scores)

    for _ in range(n_boot):
        indices = rng.integers(
            0,
            n,
            size=n,
        )

        bootstrap_scores = scores[indices]
        bootstrap_labels = labels[indices]

        if len(
            np.unique(
                bootstrap_labels
            )
        ) < 2:
            continue

        values["auc"].append(
            float(
                roc_auc_score(
                    bootstrap_labels,
                    bootstrap_scores,
                )
            )
        )

        values["eer"].append(
            float(
                eer(
                    bootstrap_scores,
                    bootstrap_labels,
                )[0]
            )
        )

        values["tar_far_1e-3"].append(
            float(
                tar_at_far(
                    bootstrap_scores,
                    bootstrap_labels,
                    1e-3,
                )[0]
            )
        )

    result = {}

    for key, vals in values.items():
        if vals:
            result[key] = (
                float(
                    np.percentile(
                        vals,
                        2.5,
                    )
                ),
                float(
                    np.percentile(
                        vals,
                        97.5,
                    )
                ),
            )

    return result


if __name__ == "__main__":
    # Standalone verification test.
    # This does NOT represent research results.
    rng = np.random.default_rng(0)

    genuine = rng.normal(
        0.8,
        0.05,
        100,
    )

    impostor = rng.normal(
        0.2,
        0.05,
        100,
    )

    scores = np.r_[
        genuine,
        impostor,
    ]

    labels = np.r_[
        np.ones(100),
        np.zeros(100),
    ]

    print("Summary:")

    print(
        json.dumps(
            summarize(
                scores,
                labels,
            ),
            indent=2,
        )
    )

    print("Bootstrap 95% CI:")

    print(
        json.dumps(
            bootstrap_ci(
                scores,
                labels,
                n_boot=100,
            ),
            indent=2,
        )
    )