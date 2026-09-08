"""
TST model injection modules.

Currently supports:
- Wan2.2 (Diffusion Transformer for Video Generation)
"""

from .wan import inject_tst_for_wan

__all__ = ["inject_tst_for_wan"]
