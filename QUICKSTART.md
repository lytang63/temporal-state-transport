# Quick Start Guide

This guide will help you get started with TST in 5 minutes.

## Prerequisites

- CUDA-capable GPU (A100/A800 recommended)
- Python 3.8+
- Wan2.2 model weights downloaded

## Step 1: Installation

```bash
git clone https://github.com/YOUR_USERNAME/TST.git
cd TST
pip install -r requirements.txt
```

## Step 2: Download Model Weights

Download Wan2.2 model from the official source:
- [Wan2.2-14B-Diffusers](https://huggingface.co/tencent/Wan2.2-TI2V-14B-Diffusers) (recommended)
- [Wan2.2-5B-Diffusers](https://huggingface.co/tencent/Wan2.2-TI2V-5B-Diffusers)

## Step 3: Run Inference

### Option A: Use the inference script

```bash
python inference.py \
    --model-dir /path/to/Wan2.2-TI2V-14B-Diffusers \
    --prompt "A cat walks on the grass, realistic" \
    --tst-tau 0.2 \
    --output output.mp4
```

### Option B: Use the example script

1. Edit `example.py` and update `MODEL_DIR`
2. Run:
```bash
python example.py
```

### Option C: Integrate into your own code

```python
from tst import inject_tst_for_wan, set_tst_tau, enable_tst

# After loading your Wan2.2 pipeline:
inject_tst_for_wan(pipe.transformer)
set_tst_tau(0.2)
enable_tst()

# Then generate as usual:
output = pipe(prompt="...", ...).frames
```

## Hyperparameter Tuning

TST has one main hyperparameter: **tau (τ)**

- **Default**: 0.2 (recommended)
- **Range**: 0.1 to 0.3
  - 0.1: Subtle effect
  - 0.2: Balanced (our paper setting)
  - 0.3: Strong modulation
- **Disable**: Set to 0

Try different values on your prompts:

```bash
# Subtle
python inference.py --model-dir /path/to/model --prompt "..." --tst-tau 0.1

# Recommended
python inference.py --model-dir /path/to/model --prompt "..." --tst-tau 0.2

# Strong
python inference.py --model-dir /path/to/model --prompt "..." --tst-tau 0.3
```

## Troubleshooting

### Out of Memory

Try these solutions:
1. Reduce resolution: use `--height 480 --width 832` instead of 720p
2. Reduce frames: use `--num-frames 81` instead of 121
3. Use the 5B model instead of 14B

### Import Errors

Ensure you have installed all dependencies:
```bash
pip install -r requirements.txt
```

Check PyTorch version:
```bash
python -c "import torch; print(torch.__version__)"
# Should be >= 2.0.0
```

### Model Not Found

Make sure you have downloaded the Wan2.2 model and the path is correct:
```bash
ls /path/to/Wan2.2-TI2V-14B-Diffusers
# Should show: vae/, transformer/, scheduler/, etc.
```

## Next Steps

- Experiment with different prompts and tau values
- Try both 480p and 720p resolutions
- Compare with baseline (tau=0) to see the improvement

For more details, see the main [README.md](README.md).
