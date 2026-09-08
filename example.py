"""
Quick start example for TST (Temporal State Transport).

This script demonstrates the minimal code needed to use TST with Wan2.2.
"""
import torch
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.utils import export_to_video

from tst import inject_tst_for_wan, set_tst_tau, enable_tst


def main():
    # Configuration
    MODEL_DIR = "/path/to/Wan2.2-TI2V-14B-Diffusers"  # Update this path
    PROMPT = "A cat walks on the grass, realistic"
    OUTPUT_PATH = "output.mp4"

    # TST hyperparameter
    TST_TAU = 0.2  # Modulation strength (0.1-0.3 recommended)

    print("Loading Wan2.2 model...")

    # Load VAE
    vae = AutoencoderKLWan.from_pretrained(
        MODEL_DIR,
        subfolder="vae",
        torch_dtype=torch.float32,
        local_files_only=True,
    )

    # Load pipeline
    pipe = WanPipeline.from_pretrained(
        MODEL_DIR,
        vae=vae,
        torch_dtype=torch.bfloat16,
        local_files_only=True,
    )
    pipe.to("cuda")

    print("Injecting TST...")
    # Inject TST into the transformer
    inject_tst_for_wan(pipe.transformer)
    set_tst_tau(TST_TAU)
    enable_tst()

    print(f"Generating video with prompt: '{PROMPT}'")
    print(f"TST tau: {TST_TAU}")

    # Generate video
    generator = torch.Generator(device="cuda").manual_seed(42)
    output = pipe(
        prompt=PROMPT,
        negative_prompt="worst quality, low quality, blurry",
        height=480,
        width=832,
        num_frames=81,
        num_inference_steps=50,
        guidance_scale=5.0,
        generator=generator,
    ).frames[0]

    # Save video
    export_to_video(output, OUTPUT_PATH, fps=15)
    print(f"Video saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
