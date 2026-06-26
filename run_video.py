import argparse
from pathlib import Path

from app.services.ffmpeg_service import (
    generate_slideshow_from_images,
    generate_video_from_images,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate video from images (land/shorts/slideshow).")
    parser.add_argument(
        "--mode",
        choices=["land", "shorts", "slideshow"],
        required=True,
        help="land=1920x1080, shorts=1080x1920, slideshow=轮播不做运镜",
    )
    parser.add_argument("--uploads-dir", default="uploads", help="images folder (default: uploads)")
    parser.add_argument("--output-dir", default="output", help="output folder (default: output)")
    parser.add_argument("--similarity-threshold", type=int, default=12, help="dedupe strength (6~20)")
    parser.add_argument("--second-per-image", type=float, default=2.0, help="slideshow only: seconds per image")

    # land/shorts 才用到的参数
    parser.add_argument("--transition", default="dissolve", help="xfade transition: fade/dissolve/slideleft/slideright")
    parser.add_argument("--transition-duration", type=float, default=0.45, help="xfade transition duration seconds")
    parser.add_argument("--zoom-factor", type=float, default=1.05, help="Ken Burns-ish zoom factor")
    parser.add_argument("--pan-ratio", type=float, default=1.0, help="how much of the available pan distance to use (0~1)")
    parser.add_argument("--random-seed", type=int, default=7, help="random seed for rhythm")

    args = parser.parse_args()

    uploads_dir = Path(args.uploads_dir)
    output_dir = Path(args.output_dir)
    if not uploads_dir.exists():
        raise SystemExit(f"uploads-dir not found: {uploads_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "slideshow":
        out = generate_slideshow_from_images(
            upload_dir=str(uploads_dir),
            output_dir=str(output_dir),
            output_filename="test_video_slideshow.mp4",
            second_per_image=args.second_per_image,
            similarity_threshold=args.similarity_threshold,
            view_w=1080,
            view_h=1920,
        )
        print(out)
        return

    if args.mode == "land":
        view_w, view_h = 1920, 1080
        out_name = "test_video_land.mp4"
    else:
        view_w, view_h = 1080, 1920
        out_name = "test_video_shorts.mp4"

    out = generate_video_from_images(
        upload_dir=str(uploads_dir),
        output_dir=str(output_dir),
        output_filename=out_name,
        similarity_threshold=args.similarity_threshold,
        transition=args.transition,
        transition_duration=args.transition_duration,
        zoom_factor=args.zoom_factor,
        pan_ratio=args.pan_ratio,
        random_seed=args.random_seed,
        view_w=view_w,
        view_h=view_h,
    )
    print(out)


if __name__ == "__main__":
    main()

