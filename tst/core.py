"""
Core TST (Temporal State Transport) implementation.

This module implements the entropy-based temporal attention modulation
for video diffusion models.
"""
import math

import torch

from tst.globals import (
    get_tst_tau,
    get_tst_num_inference_steps,
)
from tst.instrumentation import get_attention_call_index


def tst_modulation(query_image, key_image, head_dim, num_frames, metadata=None, eps=1e-8):
    """
    Apply Temporal State Transport modulation to attention scores.

    TST balances temporal attention by modulating based on two entropy measures:
    1. Row entropy (H_row): entropy of each attention distribution
    2. Von Neumann entropy (H_vn): spectral entropy of the attention Gram matrix

    The modulation strength is scheduled across diffusion steps and transformer layers.

    Args:
        query_image: Query tensor of shape [batch*spatial, num_heads, num_frames, head_dim]
        key_image: Key tensor of shape [batch*spatial, num_heads, num_frames, head_dim]
        head_dim: Dimension of each attention head
        num_frames: Number of video frames
        metadata: Optional metadata dict for logging/analysis
        eps: Small constant for numerical stability

    Returns:
        tst_scale: Scalar modulation factor to apply to attention logits
    """
    scale = head_dim**-0.5
    query_image = query_image * scale
    attn_logits = (query_image @ key_image.transpose(-2, -1)).to(torch.float32)
    attn_temp = attn_logits.softmax(dim=-1)
    attn_temp = attn_temp.reshape(-1, num_frames, num_frames)

    mean_attn = attn_temp.mean(dim=0)

    # Compute Gram matrix for Von Neumann entropy
    gram_all = attn_temp @ attn_temp.transpose(-2, -1)
    trace_all = torch.diagonal(gram_all, dim1=-2, dim2=-1).sum(dim=-1).clamp(min=eps)
    rho = (gram_all / trace_all[:, None, None]).mean(dim=0)
    rho = rho / torch.diagonal(rho, dim1=-2, dim2=-1).sum().clamp(min=eps)
    eigvals = torch.linalg.eigvalsh(rho).clamp(min=eps)
    eigvals = eigvals / eigvals.sum().clamp(min=eps)

    # Von Neumann entropy (spectral)
    entropy = -(eigvals * eigvals.log()).sum()
    log_f = torch.log(torch.tensor(float(num_frames), device=attn_temp.device, dtype=torch.float32))
    entropy_norm = (entropy / log_f.clamp(min=eps)).clamp(min=0.0, max=1.0)

    # Row entropy (average across all attention distributions)
    row_entropy = -(attn_temp.clamp(min=eps) * attn_temp.clamp(min=eps).log()).sum(dim=-1).mean()
    row_entropy_norm = (row_entropy / log_f.clamp(min=eps)).clamp(min=0.0, max=1.0)

    diag_mask = torch.eye(num_frames, device=attn_temp.device).bool()
    diag_mean = mean_attn.masked_select(diag_mask).mean()

    # Temporal mixing coefficient (1 - self-attention)
    temporal_alpha = (1.0 - diag_mean).clamp(min=0.0, max=1.0)

    # Spectral quality factor
    spectral_q = entropy_norm * (1.0 - entropy_norm)

    # Combined quality measure
    q_tst = temporal_alpha * spectral_q

    # Get tau and compute effective modulation strength with scheduling
    tau_peak = get_tst_tau()
    layer_index = int(metadata.get("layer_index", 0)) if metadata is not None else 0
    total_layers = max(1, int(metadata.get("total_layers", 1)) if metadata is not None else 1)
    total_steps = max(1, get_tst_num_inference_steps())
    call_index = get_attention_call_index()
    calls_per_step = max(1, total_layers * 2)
    step_index = min(total_steps - 1, call_index // calls_per_step)

    # Layer scheduling: cosine schedule emphasizing middle layers
    layer_weight = 1.0 if total_layers == 1 else 0.5 - 0.5 * math.cos(math.pi * layer_index / (total_layers - 1))

    # Step scheduling: cosine schedule emphasizing early diffusion steps
    step_weight = 1.0 if total_steps == 1 else 0.5 + 0.5 * math.cos(math.pi * step_index / (total_steps - 1))

    tau_effective = tau_peak * layer_weight * step_weight

    # TST modulation: scale = 1 + tau * q
    tst_scale = 1.0 + tau_effective * q_tst

    return tst_scale
