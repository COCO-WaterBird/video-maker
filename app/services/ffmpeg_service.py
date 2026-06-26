import hashlib
import random
import subprocess
import tempfile
from pathlib import Path

import imagehash
from PIL import Image, ImageOps


def _file_content_hash(path: Path, block_size: int = 65536) -> str:
    """按文件内容算哈希，用于精确去重。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block_size):
            h.update(chunk)
    return h.hexdigest()


def _dedupe_images(
    paths: list[Path],
    similarity_threshold: int = 8,
) -> list[Path]:
    """
    去重：先按文件内容精确去重，再按画面相似度（perceptual hash）去重。
    相似度阈值 similarity_threshold：与已保留图的哈希距离 <= 此值视为重复（0=只去完全一致，越大去得越狠，建议 6~12）。
    """
    # 1. 内容完全相同的只留第一张
    seen_content: set[str] = set()
    unique_by_content: list[Path] = []
    for p in paths:
        key = _file_content_hash(p)
        if key in seen_content:
            continue
        seen_content.add(key)
        unique_by_content.append(p)

    if similarity_threshold <= 0:
        return unique_by_content

    # 2. 画面相似的只留第一张（perceptual hash，保持原顺序）
    kept_hashes: list[imagehash.ImageHash] = []
    out: list[Path] = []
    for p in unique_by_content:
        try:
            with Image.open(p) as img:
                img.load()
                h = imagehash.phash(img, hash_size=12)
        except Exception:
            out.append(p)
            continue
        is_dup = False
        for kh in kept_hashes:
            if h - kh <= similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            kept_hashes.append(h)
            out.append(p)
    return out


def _scaled_and_pad_size(img_w: int, img_h: int, view_w: int = 1080, view_h: int = 1920):
    """缩放为高度 view_h，再计算 pad 后的宽高与 crop 最大偏移。"""
    scale_w = int(img_w * view_h / img_h)
    scale_h = view_h
    pad_w = max(view_w, scale_w)
    pad_h = view_h
    crop_x_max = max(0, scale_w - view_w)
    pad_x = (pad_w - scale_w) // 2
    return scale_w, scale_h, pad_w, pad_h, pad_x, crop_x_max


def _even(n: int) -> int:
    """H.264/scale 更稳：确保为偶数。"""
    return n if n % 2 == 0 else n - 1


def _cover_scale(img_w: int, img_h: int, view_w: int, view_h: int, zoom: float) -> tuple[int, int]:
    """
    等比缩放到“覆盖”画布（两边都 >= 画布），再用于 crop，避免任何拉伸。
    """
    s = max(view_w / img_w, view_h / img_h) * zoom
    return _even(int(round(img_w * s))), _even(int(round(img_h * s)))


def generate_video_from_images(
    upload_dir: str = "uploads",
    output_dir: str = "output",
    output_filename: str = "test_video.mp4",
    second_per_image: int = 4,
    zoom_factor: float = 1.05,
    similarity_threshold: int = 12,
    transition: str = "fade",
    transition_duration: float = 0.45,
    random_seed: int = 7,
    pan_ratio: float = 1.0,
    view_w: int = 1920,
    view_h: int = 1080,
) -> str:
    """
    将图片生成视频，适合 kitchen tour / 橱柜展示：
    - 从左往右平滑平移（带缓动，更自然）
    - 轻微推进缩放（zoom_factor，更有空间感）
    - 相似镜头去重：similarity_threshold 越大去得越狠（6~20，默认 12）
    """
    uploads_path = Path(upload_dir)
    outputs_path = Path(output_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)

    images_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

    image_files = sorted(
        [p for p in uploads_path.iterdir() if p.suffix.lower() in images_exts],
        key=lambda x: x.name,
    )
    image_files = _dedupe_images(image_files, similarity_threshold=similarity_threshold)

    if not image_files:
        raise ValueError("No image files found in the upload directory")

    # view_w/view_h：画布（横屏/竖屏）由调用方决定
    view_w = int(view_w)
    view_h = int(view_h)
    fps = 30
    rng = random.Random(random_seed)
    pan_ratio = max(0.0, min(1.0, float(pan_ratio)))

    # 方案二：不要所有图片都一个节奏
    # - 第一张：2.5 秒（开场）
    # - 普通图：1.8~2.2 秒（随机）
    # - 重点图：2.8~3.5 秒（随机）
    # - 收尾图：2.5 秒
    n = len(image_files)
    durations: list[float] = []
    for idx in range(n):
        if idx == 0 or idx == n - 1:
            durations.append(2.5)
            continue
        # 简单规则：每 5 张里挑 1 张当“重点图”（更符合 tour 节奏）
        is_key = (idx % 5) == 0
        if is_key:
            durations.append(min(4.0, rng.uniform(2.8, 3.5)))
        else:
            durations.append(min(4.0, rng.uniform(1.8, 2.2)))

    # xfade 需要重编码，所以不能用 concat copy
    transition = transition.strip().lower()
    if transition_duration < 0:
        transition_duration = 0.0
    if transition not in {"fade", "dissolve", "slideleft", "slideright"}:
        # 默认用叠化（dissolve）
        transition = "dissolve"

    # Ken Burns：为每张图分配不同运镜（放大/缩小/左右/上下），并用余弦缓动让运动更自然
    # zoom_factor 建议 1.02~1.08，过大容易“晕”
    zoom_end = min(max(zoom_factor, 1.0), 1.08)
    zoom_start = zoom_end
    pi = 3.14159265359

    with tempfile.TemporaryDirectory() as tmpdir:
        segment_paths = []

        for i, image_file in enumerate(image_files):
            abs_path = image_file.resolve()
            segment_out = Path(tmpdir) / f"segment_{i:04d}.mp4"
            duration_s = float(durations[i])

            # 统一图片方向（处理手机 EXIF 旋转），避免按错误宽高计算导致“变形”
            norm_path = Path(tmpdir) / f"norm_{i:04d}.png"
            with Image.open(abs_path) as img:
                img = ImageOps.exif_transpose(img)
                img_w, img_h = img.size
                # 保存标准化后的图片给 FFmpeg 使用（确保方向一致）
                img.convert("RGB").save(norm_path, format="PNG")

            # 关键修复：永远等比缩放（cover）+ crop，绝不拉伸
            # 现在统一做「从左往右」平移，高度始终居中，不再上下移动
            scaled_w, scaled_h = _cover_scale(img_w, img_h, view_w, view_h, zoom_end)
            crop_x_max = max(0, scaled_w - view_w)
            crop_y_max = max(0, scaled_h - view_h)

            # 要走完整可移动距离但速度慢：对需要平移的镜头，自动把时长拉到最多 4s
            # 距离不变、时间变长 => 速度更慢（仍保持线性匀速）
            if (crop_x_max > 0 or crop_y_max > 0) and duration_s < 4.0:
                duration_s = 4.0

            total_frames = max(1, int(round(duration_s * fps)))
            # 平移幅度控制：默认 100%（走完整距离）；保留参数方便以后微调
            pan_x_max = int(round(crop_x_max * pan_ratio))
            pan_y_max = int(round(crop_y_max * pan_ratio))

            # 线性运镜：从左→右（不使用 S 形缓动，也不来回）
            progress_t = f"(t/{duration_s})"

            # 统一从左往右平移；高度固定居中（无上下移动）
            x_expr = f"trunc({pan_x_max}*{progress_t})"
            # 把多余的高度平均分到上下，使画面垂直方向居中
            y_center = max(0, int(round(crop_y_max / 2)))
            y_expr = str(y_center)

            pan_filter = (
                f"scale={scaled_w}:{scaled_h},"
                f"crop={view_w}:{view_h}:{x_expr}:{y_expr},"
                "format=yuv420p,setsar=1"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", str(norm_path),
                "-vf", pan_filter,
                "-frames:v", str(total_frames),
                "-r", str(fps),
                "-c:v", "libx264",
                str(segment_out),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 生成片段失败 ({image_file.name}):\n"
                    f"STDERR:\n{result.stderr}"
                )
            segment_paths.append(segment_out)

        output_path = outputs_path / output_filename
        if len(segment_paths) == 1:
            # 只有一个片段，直接转码输出确保格式一致
            single_cmd = [
                "ffmpeg",
                "-y",
                "-i", str(segment_paths[0]),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                str(output_path),
            ]
            result = subprocess.run(single_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 输出失败:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )
        else:
            # 方案三：柔和转场（xfade）：fade / dissolve / slideleft / slideright
            # offset = 前面累计时长 - transition_duration（每次转场会重叠 duration）
            offsets: list[float] = []
            acc = durations[0]
            for k in range(1, len(durations)):
                offsets.append(max(0.0, acc - transition_duration))
                acc += durations[k] - transition_duration

            inputs = []
            for seg in segment_paths:
                inputs += ["-i", str(seg)]

            parts: list[str] = []
            for idx in range(len(segment_paths)):
                parts.append(f"[{idx}:v]setpts=PTS-STARTPTS[v{idx}]")

            last = "v0"
            for idx in range(1, len(segment_paths)):
                off = offsets[idx - 1]
                out = f"vx{idx}"
                parts.append(
                    f"[{last}][v{idx}]xfade=transition={transition}:duration={transition_duration}:offset={off}[{out}]"
                )
                last = out

            filter_complex = ";".join(parts) + f";[{last}]format=yuv420p,setsar=1[vout]"
            merge_cmd = [
                "ffmpeg",
                "-y",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-r", str(fps),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]

            result = subprocess.run(merge_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 合并失败:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )

    return str(output_path)


def generate_slideshow_from_images(
    upload_dir: str = "uploads",
    output_dir: str = "output",
    output_filename: str = "test_video_slideshow.mp4",
    second_per_image: float = 2.0,
    similarity_threshold: int = 12,
    view_w: int = 1080,
    view_h: int = 1920,
    fps: int = 30,
    zoom_factor: float = 1.0,
) -> str:
    """
    第三种模式：slideshow
    输入图片后，等比 cover + 居中裁剪，不做运镜，按顺序轮播，速度快且不易变形。
    """
    uploads_path = Path(upload_dir)
    outputs_path = Path(output_dir)
    outputs_path.mkdir(parents=True, exist_ok=True)

    images_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

    image_files = sorted(
        [p for p in uploads_path.iterdir() if p.suffix.lower() in images_exts],
        key=lambda x: x.name,
    )
    image_files = _dedupe_images(image_files, similarity_threshold=similarity_threshold)

    if not image_files:
        raise ValueError("No image files found in the upload directory")

    second_per_image = max(0.1, float(second_per_image))
    fps = int(fps)
    total_frames = max(1, int(round(second_per_image * fps)))

    with tempfile.TemporaryDirectory() as tmpdir:
        segment_paths: list[Path] = []

        for i, image_file in enumerate(image_files):
            abs_path = image_file.resolve()
            segment_out = Path(tmpdir) / f"slide_{i:04d}.mp4"

            # 统一图片方向（处理手机 EXIF 旋转）
            norm_path = Path(tmpdir) / f"norm_{i:04d}.png"
            with Image.open(abs_path) as img:
                img = ImageOps.exif_transpose(img)
                img_w, img_h = img.size
                img.convert("RGB").save(norm_path, format="PNG")

            # 等比 cover + 居中 crop：不拉伸
            scaled_w, scaled_h = _cover_scale(img_w, img_h, view_w, view_h, zoom_factor)
            crop_x_max = max(0, scaled_w - view_w)
            crop_y_max = max(0, scaled_h - view_h)
            x_center = crop_x_max // 2
            y_center = crop_y_max // 2

            pan_filter = (
                f"scale={scaled_w}:{scaled_h},"
                f"crop={view_w}:{view_h}:{x_center}:{y_center},"
                "format=yuv420p,setsar=1"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(norm_path),
                "-vf",
                pan_filter,
                "-frames:v",
                str(total_frames),
                "-r",
                str(fps),
                "-c:v",
                "libx264",
                str(segment_out),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 生成 slideshow 片段失败 ({image_file.name}):\n"
                    f"STDERR:\n{result.stderr}"
                )
            segment_paths.append(segment_out)

        concat_list = outputs_path / f"{Path(output_filename).stem}_concat_list.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for seg in segment_paths:
                f.write(f"file '{seg}'\n")

        output_path = outputs_path / output_filename
        if len(segment_paths) == 1:
            # 单段：直接转码确保一致
            single_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(segment_paths[0]),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                str(output_path),
            ]
            result = subprocess.run(single_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 输出 slideshow 失败:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )
        else:
            # 多段：concat demuxer + -c copy（各段参数一致）
            concat_cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(output_path),
            ]
            result = subprocess.run(concat_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 合并 slideshow 失败:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )

    return str(output_path)
