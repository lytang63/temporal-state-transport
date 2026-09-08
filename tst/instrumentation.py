"""
Instrumentation utilities for TST.

Tracks attention call counts for proper scheduling of modulation strength
across diffusion steps and transformer layers.
"""

_ATTENTION_CALL_INDEX = 0


def get_attention_call_index() -> int:
    """Get the current attention call index (increments with each attention call)."""
    return _ATTENTION_CALL_INDEX


def increment_attention_call_index():
    """Increment the attention call counter."""
    global _ATTENTION_CALL_INDEX
    _ATTENTION_CALL_INDEX += 1


def reset_attention_call_index():
    """Reset the attention call counter (typically called at start of generation)."""
    global _ATTENTION_CALL_INDEX
    _ATTENTION_CALL_INDEX = 0
