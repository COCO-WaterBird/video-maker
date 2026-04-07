from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from ai_generation.image_analysis.schemas import ImageAnalysisResult


def _mime_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext, "image/jpeg")


_ANALYSIS_INSTRUCTION = """你是室内设计与图像编辑顾问。根据用户上传的房间照片，输出 JSON（不要 markdown），字段：
- soft_furnishing_suggestions: string array，3-8 条简短中文建议
- edit_prompt: string，给图像编辑模型用的详细中文指令：必须明确保留建筑结构、墙体地面门窗透视不变，只调整软装（家具、窗帘、地毯、灯具、装饰画、绿植等）；描述目标风格与材质
- negative_prompt: string，列出要避免的改动（例如不要改墙色、不要改窗洞位置、不要卡通化；并写明避免画面模糊、涂抹感、花瓣糊成一团、塑料假花感、油画/水彩质感）
- style: string，单一英文 snake_case 风格标签
- room_type: string，单一英文 snake_case 房间类型（厨房场景必须填 kitchen）

若用户额外说明偏好，合并进 edit_prompt 与 style。"""


class OpenAIVisionAnalyzer:
    def __init__(self, model: str = "gpt-4o") -> None:
        self._client = OpenAI()
        self._model = model

    def analyze(
        self,
        image_path: str | Path,
        user_hint: str | None = None,
    ) -> ImageAnalysisResult:
        path = Path(image_path)
        b64 = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        mime = _mime_for_path(path)
        url = f"data:{mime};base64,{b64}"

        user_content: list[dict[str, Any]] = [
            {"type": "text", "text": _ANALYSIS_INSTRUCTION},
            {"type": "image_url", "image_url": {"url": url}},
        ]
        if user_hint:
            user_content.append({"type": "text", "text": f"用户偏好说明：{user_hint}"})

        resp = self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "只输出合法 JSON 对象。"},
                {"role": "user", "content": user_content},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        return ImageAnalysisResult.model_validate(data)
