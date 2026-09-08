"""
Global configuration for Temporal State Transport (TST).
"""

TST_TAU = 0.2
TST_NUM_INFERENCE_STEPS = 1
TST_ENABLED = False


def enable_tst():
    """Enable TST modulation during video generation."""
    global TST_ENABLED
    TST_ENABLED = True


def is_tst_enabled() -> bool:
    """Check if TST is currently enabled."""
    return TST_ENABLED


def set_tst_tau(tau: float):
    """
    Set the TST modulation strength parameter tau.

    Args:
        tau: Modulation strength. Typical range: 0.1 to 0.3.
             Higher values = stronger temporal balance enforcement.
    """
    global TST_TAU
    TST_TAU = tau


def get_tst_tau() -> float:
    """Get the current TST tau value."""
    return TST_TAU


def set_tst_num_inference_steps(num_steps: int):
    """
    Set the number of inference steps for TST scheduling.

    Args:
        num_steps: Total number of diffusion steps.
    """
    global TST_NUM_INFERENCE_STEPS
    TST_NUM_INFERENCE_STEPS = max(1, int(num_steps))


def get_tst_num_inference_steps() -> int:
    """Get the number of inference steps for TST scheduling."""
    return TST_NUM_INFERENCE_STEPS
