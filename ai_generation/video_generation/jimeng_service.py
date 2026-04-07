from __future__ import annotations

from pathlib import Path


class JimengVideoService:
    """
    即梦 / 第三方图生视频接入占位。
    实现时在此封装鉴权、任务轮询与成片 URL / 本地路径。
    """

    def generate_from_image(self, staged_image_path: str | Path) -> str:
        _ = Path(staged_image_path).resolve()
        raise NotImplementedError(
            "接入即梦 API：以软装成图为输入生成视频后，返回成片路径或 URL"
        )
