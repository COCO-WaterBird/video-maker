#!/usr/bin/env python3
"""命令行跑通第一阶段：原图 -> 软装成图。用法见 --help。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    epilog = """
示例:
  python run_staging.py ./kitchen.jpg --room-type kitchen
  python run_staging.py ./kitchen.jpg --room-type kitchen --hint "更温馨"
  python run_staging.py ./kitchen.jpg --room-type kitchen --skip-vision
  python run_staging.py ./room.png --extra "窗帘换成米色亚麻"
"""
    parser = argparse.ArgumentParser(
        description="软装成图：默认 gpt-4o 看图 + gpt-image-1 编辑；可加 --skip-vision 省掉看图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument("image", type=Path, help="本地原图路径，如 kitchen.jpg")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="素材与输出目录（默认 ./data）",
    )
    parser.add_argument("--project-name", default="cli", help="项目名")
    parser.add_argument(
        "--room-type",
        default=None,
        help='房间类型，厨房建议填 kitchen 或 厨房（会走厨房英文主 prompt）',
    )
    parser.add_argument(
        "--skip-vision",
        action="store_true",
        help="跳过 gpt-4o 看图（省费用），用固定模板 + --hint 拼 edit_prompt；务必用 --room-type 标厨房等",
    )
    parser.add_argument(
        "--hint",
        default=None,
        metavar="TEXT",
        help="可选：用户偏好。看图时会写入分析结果；--skip-vision 时会并入静态 edit_prompt",
    )
    parser.add_argument(
        "--extra",
        default=None,
        help="可选：追加到最终编辑 prompt 的额外说明",
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY", "").strip():
        print(
            "未检测到 OPENAI_API_KEY。请在项目根目录创建 .env 并写入 OPENAI_API_KEY=...，"
            "或先 export 该环境变量。",
            file=sys.stderr,
        )
        sys.exit(2)

    args.image = args.image.expanduser().resolve()
    if not args.image.is_file():
        print(f"找不到文件: {args.image}", file=sys.stderr)
        sys.exit(1)

    from ai_generation.material_assets.service import MaterialAssetService
    from ai_generation.pipeline import StagingPipeline

    materials = MaterialAssetService(args.data_dir)
    project = materials.create_project(args.project_name)
    asset = materials.ingest_original_from_path(
        project.id,
        args.image,
        room_type=args.room_type,
    )
    pipe = StagingPipeline(args.data_dir)
    out = pipe.generate_staged_image(
        asset.id,
        user_hint=args.hint,
        extra_prompt=args.extra,
        skip_vision=args.skip_vision,
    )
    print(f"asset_id: {asset.id}")
    print(f"staged_image: {out}")


if __name__ == "__main__":
    main()
