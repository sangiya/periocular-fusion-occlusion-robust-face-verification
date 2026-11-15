"""Research reference implementation of the five-model ablation ladder.

This is intentionally explicit rather than optimized. It uses Hugging Face
DINOv2 and PEFT LoRA. The model consumes whole-face and periocular tensors.
"""
from __future__ import annotations

import torch
from torch import nn
from transformers import AutoModel
from peft import LoraConfig, get_peft_model

MODEL_NAME = "facebook/dinov2-base"


def make_encoder(lora: bool, name: str = MODEL_NAME):
    encoder = AutoModel.from_pretrained(name)
    if not lora:
        for p in encoder.parameters(): p.requires_grad = False
        return encoder
    config = LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.1,
        target_modules=["query", "key", "value"],
        bias="none", task_type="FEATURE_EXTRACTION",
    )
    return get_peft_model(encoder, config)


def pooled(encoder, x):
    out = encoder(pixel_values=x)
    return out.last_hidden_state[:, 0]


class VerificationModel(nn.Module):
    """M0 frozen whole, M1 whole LoRA, M2 peri LoRA, M3 fixed fusion, M4 gate."""
    def __init__(self, variant: str, dim: int = 768):
        super().__init__()
        assert variant in {"frozen_whole", "whole_lora", "peri_lora", "fixed_fusion", "gated_fusion"}
        self.variant = variant
        use_lora = variant != "frozen_whole"
        self.face_encoder = make_encoder(use_lora)
        self.face_proj = nn.Linear(dim, dim)
        self.peri_encoder = None
        self.peri_proj = None
        if variant in {"peri_lora", "fixed_fusion", "gated_fusion"}:
            self.peri_encoder = make_encoder(True)
            self.peri_proj = nn.Linear(dim, dim)
        if variant == "gated_fusion":
            self.gate = nn.Sequential(nn.Linear(dim * 2 + 4, 128), nn.GELU(), nn.Linear(128, 1))

    def forward(self, face, peri=None, quality=None):
        zf = nn.functional.normalize(self.face_proj(pooled(self.face_encoder, face)), dim=-1)
        if self.variant in {"frozen_whole", "whole_lora"}:
            return zf
        if peri is None: raise ValueError("periocular tensor required")
        zp = nn.functional.normalize(self.peri_proj(pooled(self.peri_encoder, peri)), dim=-1)
        if self.variant == "peri_lora": return zp
        if self.variant == "fixed_fusion": return nn.functional.normalize(.5 * zf + .5 * zp, dim=-1)
        if quality is None: quality = torch.zeros((face.shape[0], 4), device=face.device)
        g = torch.sigmoid(self.gate(torch.cat([zf, zp, quality], dim=-1)))
        return nn.functional.normalize(g * zf + (1.0 - g) * zp, dim=-1)


def trainable_parameters(model):
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total": total, "trainable": trainable, "trainable_percent": 100 * trainable / total}
