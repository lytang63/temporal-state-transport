"""
Temporal State Transport (TST) Inference Script for Wan2.2 Video Generation

This script demonstrates how to use TST to improve video generation quality
by balancing temporal attention through entropy-based modulation.
"""
import argparse
import os
import time
from contextlib import contextmanager
from pathlib import Path

import torch
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.utils import export_to_video

from tst import inject_tst_for_wan, set_tst_tau, enable_tst


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_NEGATIVE_PROMPT = (
    "Bright tones, overexposed, static, blurred details, subtitles, style, works, "
    "paintings, images, static, overall gray, worst quality, low quality, JPEG "
    "compression residue, ugly, incomplete, extra fingers, poorly drawn hands, "
    "poorly drawn faces, deformed, disfigured, misshapen limbs, fused fingers, "
    "still picture, messy background, three legs, many people in the background, "
    "walking backwards"
)


@contextmanager
def timed(name: str, timings: dict[str, float]):
    start = time.perf_counter()
    print(f"[timer] {name} started", flush=True)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        timings[name] = elapsed
        print(f"[timer] {name}: {elapsed:.2f}s", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Wan2.2 video generation with Temporal State Transport (TST)."
    )
    parser.add_argument(
        "--model-dir",
        required=True,
        help="Path to Wan2.2 model directory (e.g., Wan2.2-TI2V-14B-Diffusers)",
    )
    parser.add_argument("--prompt", default="A cat walks on the grass, realistic")
    parser.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE_PROMPT)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--num-frames", type=int, default=81)
    parser.add_argument("--num-inference-steps", type=int, default=50)
    parser.add_argument("--guidance-scale", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--seeds",
        default=None,
        help="Comma-separated seeds. Overrides --seed and sets batch size when provided.",
    )
    parser.add_argument("--num-videos-per-prompt", type=int, default=1)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument(
        "--tst-tau",
        type=float,
        default=0.2,
        help="TST modulation strength (tau). Default: 0.2. Set to 0 to disable TST.",
    )
    parser.add_argument("--output", default=str(SCRIPT_DIR / "output.mp4"))
    parser.add_argument(
        "--compile-transformer",
        action="store_true",
        help="Compile the Wan transformer with torch.compile. First run is slower; repeated same-shape runs can be faster.",
    )
    parser.add_argument(
        "--compile-mode",
        default="max-autotune",
        choices=("default", "reduce-overhead", "max-autotune"),
    )
    parser.add_argument(
        "--attention-backend",
        default=None,
        help="Optional Diffusers attention backend, e.g. _native_flash, _native_cudnn, native.",
    )
    parser.add_argument(
        "--official-720p",
        action="store_true",
        help="Use Wan2.2's official 1280x704, 121-frame, 24fps defaults.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.official_720p:
        args.height = 704
        args.width = 1280
        args.num_frames = 121
        args.fps = 24

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    timings: dict[str, float] = {}
    total_start = time.perf_counter()

    print("[config]")
    print(f"model_dir={args.model_dir}")
    print(f"prompt={args.prompt}")
    print(f"height={args.height} width={args.width} frames={args.num_frames}")
    if args.seeds:
        seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
        args.num_videos_per_prompt = len(seeds)
    else:
        seeds = [args.seed + index for index in range(args.num_videos_per_prompt)]

    print(f"steps={args.num_inference_steps} guidance={args.guidance_scale} seeds={seeds}")
    tst_enabled = args.tst_tau > 0
    print(f"fps={args.fps} tst_enabled={tst_enabled} tst_tau={args.tst_tau} output={args.output}")

    with timed("load_vae", timings):
        vae = AutoencoderKLWan.from_pretrained(
            args.model_dir,
            subfolder="vae",
            torch_dtype=torch.float32,
            local_files_only=True,
        )

    with timed("load_pipeline", timings):
        pipe = WanPipeline.from_pretrained(
            args.model_dir,
            vae=vae,
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )

    with timed("prepare_cuda_and_tst", timings):
        pipe.to("cuda")
        if args.attention_backend:
            if not hasattr(pipe.transformer, "set_attention_backend"):
                raise RuntimeError("This diffusers transformer does not support attention backends.")
            pipe.transformer.set_attention_backend(args.attention_backend)
            print(f"[opt] attention_backend={args.attention_backend}", flush=True)
        if tst_enabled:
            inject_tst_for_wan(pipe.transformer)
            set_tst_tau(args.tst_tau)
            enable_tst()
        if args.compile_transformer:
            pipe.transformer = torch.compile(
                pipe.transformer,
                mode=args.compile_mode,
                fullgraph=False,
            )
            print(f"[opt] torch.compile transformer mode={args.compile_mode}", flush=True)
        torch.cuda.reset_peak_memory_stats()

    generators = [torch.Generator(device="cuda").manual_seed(seed) for seed in seeds]
    with timed("generate", timings):
        output = pipe(
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            height=args.height,
            width=args.width,
            num_frames=args.num_frames,
            num_inference_steps=args.num_inference_steps,
            guidance_scale=args.guidance_scale,
            num_videos_per_prompt=args.num_videos_per_prompt,
            generator=generators,
        ).frames

    with timed("export_video", timings):
        output_path = Path(args.output)
        if len(output) == 1:
            export_to_video(output[0], str(output_path), fps=args.fps)
            saved_paths = [str(output_path)]
        else:
            saved_paths = []
            for index, frames in enumerate(output):
                path = output_path.with_name(
                    f"{output_path.stem}_{index}{output_path.suffix}"
                )
                export_to_video(frames, str(path), fps=args.fps)
                saved_paths.append(str(path))

    total = time.perf_counter() - total_start
    peak_gb = torch.cuda.max_memory_allocated() / 1024**3
    print("[summary]")
    for name, elapsed in timings.items():
        print(f"{name}: {elapsed:.2f}s")
    print(f"total: {total:.2f}s")
    print(f"peak_cuda_allocated: {peak_gb:.2f} GiB")
    print("saved:")
    for path in saved_paths:
        print(path)


if __name__ == "__main__":
    main()
