"""
Temporal State Transport (TST) for Video Generation

TST improves video generation quality by balancing temporal attention
through entropy-based modulation during the diffusion process.
"""

from .core import tst_modulation
from .globals import (
    enable_tst,
    get_tst_tau,
    get_tst_num_inference_steps,
    is_tst_enabled,
    set_tst_tau,
    set_tst_num_inference_steps,
)
from .models.wan import inject_tst_for_wan

__all__ = [
    "inject_tst_for_wan",
    "tst_modulation",
    "get_tst_tau",
    "set_tst_tau",
    "get_tst_num_inference_steps",
    "set_tst_num_inference_steps",
    "enable_tst",
    "is_tst_enabled",
]
