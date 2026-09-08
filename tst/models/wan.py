"""
TST injection for Wan2.2 video generation models.

This module hooks into the Wan transformer's attention mechanism
to apply Temporal State Transport modulation.
"""
from typing import Optional

import torch
import torch.nn as nn
from diffusers.models.attention import Attention
from diffusers.models.transformers.transformer_wan import (
    _get_added_kv_projections,
    _get_qkv_projections,
    dispatch_attention_fn,
)
from einops import rearrange
import torch.nn.functional as F

from tst.core import tst_modulation
from tst.globals import is_tst_enabled
from tst.instrumentation import increment_attention_call_index, reset_attention_call_index


# Track number of frames (set by hook)
_NUM_FRAMES = None


def inject_tst_for_wan(model: nn.Module) -> None:
    """
    Inject TST modulation into a Wan2.2 transformer model.

    This function:
    1. Registers a hook to track the number of video frames
    2. Replaces self-attention processors with TST-aware processors

    Args:
        model: The Wan transformer module
    """
    # Register hook to capture num_frames from input shape
    model.register_forward_pre_hook(_num_frames_hook, with_kwargs=True)

    # Register hook to reset call counter at start of each forward pass
    model.register_forward_pre_hook(_reset_call_counter_hook, with_kwargs=True)

    # Find all self-attention modules (attn1) and inject TST processor
    attention_modules = [
        (name, module)
        for name, module in model.named_modules()
        if (
            "attn1" in name
            and hasattr(module, "set_processor")
            and hasattr(module, "to_q")
            and hasattr(module, "to_k")
            and hasattr(module, "to_v")
        )
    ]
    total_layers = len(attention_modules)
    for layer_index, (name, module) in enumerate(attention_modules):
        module.set_processor(
            TSTWanAttnProcessor(
                module_name=name,
                layer_index=layer_index,
                total_layers=total_layers,
            )
        )


def _reset_call_counter_hook(module, args, kwargs):
    """Hook to reset attention call counter at the start of each forward pass."""
    reset_attention_call_index()
    return args, kwargs


def _num_frames_hook(module, args, kwargs):
    """Hook to extract and track the number of frames from input tensor shape."""
    global _NUM_FRAMES
    if "hidden_states" in kwargs:
        hidden_states = kwargs["hidden_states"]
    else:
        hidden_states = args[0]
    num_frames = hidden_states.shape[2]
    p_t = module.config.patch_size[0]
    post_patch_num_frames = num_frames // p_t
    _NUM_FRAMES = post_patch_num_frames
    return args, kwargs


def _get_num_frames() -> int:
    """Get the current number of frames (post-patching)."""
    return _NUM_FRAMES


class TSTWanAttnProcessor:
    """
    Attention processor for Wan2.2 that applies TST modulation.

    This processor computes TST modulation on the temporal self-attention
    and scales the output features accordingly.
    """
    _attention_backend = None
    _parallel_config = None

    def __init__(self, module_name: str = "unknown", layer_index: int = 0, total_layers: int = 1):
        if not hasattr(F, "scaled_dot_product_attention"):
            raise ImportError(
                "TSTWanAttnProcessor requires PyTorch 2.0 or later."
            )
        self.module_name = module_name
        self.layer_index = layer_index
        self.total_layers = total_layers

    def _get_tst_scale(self, query, key):
        """
        Compute TST modulation scale factor.

        Args:
            query: Query tensor [B, ST, N, C] where ST = num_frames * spatial_dim
            key: Key tensor [B, ST, N, C]

        Returns:
            tst_scale: Scalar modulation factor
        """
        num_frames = _get_num_frames()
        _, ST, num_heads, head_dim = query.shape
        spatial_dim = ST // num_frames

        # Rearrange to separate temporal and spatial dimensions
        # [B, ST, N, C] -> [B*S, N, T, C]
        query_image = rearrange(
            query, "B (T S) N C -> (B S) N T C", T=num_frames, S=spatial_dim, N=num_heads, C=head_dim
        )
        key_image = rearrange(
            key, "B (T S) N C -> (B S) N T C", T=num_frames, S=spatial_dim, N=num_heads, C=head_dim
        )

        metadata = {
            "module_name": self.module_name,
            "layer_index": int(self.layer_index),
            "total_layers": int(self.total_layers),
            "num_heads": int(num_heads),
            "spatial_dim": int(spatial_dim),
        }

        return tst_modulation(query_image, key_image, head_dim, num_frames, metadata=metadata)

    def __call__(
        self,
        attn: Attention,
        hidden_states: torch.Tensor,
        encoder_hidden_states: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        rotary_emb: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass with TST modulation.

        Args:
            attn: Attention module
            hidden_states: Input tensor
            encoder_hidden_states: Optional conditioning tensor (for I2V)
            attention_mask: Optional attention mask
            rotary_emb: Optional rotary position embeddings

        Returns:
            Output tensor after attention with TST modulation
        """
        # Increment call counter for TST scheduling
        increment_attention_call_index()

        # Handle I2V conditioning (image tokens)
        encoder_hidden_states_img = None
        if attn.add_k_proj is not None and encoder_hidden_states is not None:
            image_context_length = encoder_hidden_states.shape[1] - 512
            encoder_hidden_states_img = encoder_hidden_states[:, :image_context_length]
            encoder_hidden_states = encoder_hidden_states[:, image_context_length:]

        # Project to Q, K, V
        query, key, value = _get_qkv_projections(attn, hidden_states, encoder_hidden_states)

        # Apply normalization
        query = attn.norm_q(query)
        key = attn.norm_k(key)

        # Reshape to separate heads
        query = query.unflatten(2, (attn.heads, -1))
        key = key.unflatten(2, (attn.heads, -1))
        value = value.unflatten(2, (attn.heads, -1))

        # Apply rotary position embeddings if provided
        if rotary_emb is not None:
            def apply_rotary_emb(
                hidden_states: torch.Tensor,
                freqs_cos: torch.Tensor,
                freqs_sin: torch.Tensor,
            ):
                x1, x2 = hidden_states.unflatten(-1, (-1, 2)).unbind(-1)
                cos = freqs_cos[..., 0::2]
                sin = freqs_sin[..., 1::2]
                out = torch.empty_like(hidden_states)
                out[..., 0::2] = x1 * cos - x2 * sin
                out[..., 1::2] = x1 * sin + x2 * cos
                return out.type_as(hidden_states)

            query = apply_rotary_emb(query, *rotary_emb)
            key = apply_rotary_emb(key, *rotary_emb)

        # ========== TST Modulation ==========
        if is_tst_enabled():
            tst_scale = self._get_tst_scale(query, key)
        else:
            tst_scale = None
        # ====================================

        # Handle I2V image attention if needed
        hidden_states_img = None
        if encoder_hidden_states_img is not None:
            key_img, value_img = _get_added_kv_projections(attn, encoder_hidden_states_img)
            key_img = attn.norm_added_k(key_img)

            key_img = key_img.unflatten(2, (attn.heads, -1))
            value_img = value_img.unflatten(2, (attn.heads, -1))

            hidden_states_img = dispatch_attention_fn(
                query,
                key_img,
                value_img,
                attn_mask=None,
                dropout_p=0.0,
                is_causal=False,
                backend=self._attention_backend,
                parallel_config=None,
            )
            hidden_states_img = hidden_states_img.flatten(2, 3)
            hidden_states_img = hidden_states_img.type_as(query)

        # Main temporal self-attention
        hidden_states = dispatch_attention_fn(
            query,
            key,
            value,
            attn_mask=attention_mask,
            dropout_p=0.0,
            is_causal=False,
            backend=self._attention_backend,
            parallel_config=(self._parallel_config if encoder_hidden_states is None else None),
        )
        hidden_states = hidden_states.flatten(2, 3)
        hidden_states = hidden_states.type_as(query)

        # Combine image and video attention if I2V
        if hidden_states_img is not None:
            hidden_states = hidden_states + hidden_states_img

        # Output projection
        hidden_states = attn.to_out[0](hidden_states)
        hidden_states = attn.to_out[1](hidden_states)

        # ========== Apply TST scale to output ==========
        if is_tst_enabled() and tst_scale is not None:
            hidden_states = hidden_states * tst_scale
        # ===============================================

        return hidden_states
