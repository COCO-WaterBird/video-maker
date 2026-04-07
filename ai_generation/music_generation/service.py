from __future__ import annotations

from pathlib import Path


class MusicGenerationService:
    """配乐 / BGM 占位：与视频轨合成时由上层编排调用。"""

    def generate_or_pick_track(self, video_path: str | Path, mood: str | None = None) -> str:
        _ = Path(video_path)
        raise NotImplementedError("接入音乐生成或曲库选择后返回音频路径或 URL")
