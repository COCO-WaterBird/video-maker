"""
AI 生成链路：素材 → 图片理解 → 软装编辑 →（可选）视频 / 音乐。

软装与视频解耦：先产出软装成图，再以该图为输入生成视频。
"""

from ai_generation.pipeline import StagingPipeline, VideoFromStagedPipeline

__all__ = [
    "StagingPipeline",
    "VideoFromStagedPipeline",
]
