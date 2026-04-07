from __future__ import annotations

from pydantic import BaseModel, Field


class ImageAnalysisResult(BaseModel):
    """GPT 看图后的结构化输出，供软装 prompt 与编辑使用。"""

    soft_furnishing_suggestions: list[str] = Field(
        default_factory=list,
        description="软装建议要点，面向用户展示或写入说明",
    )
    edit_prompt: str = Field(
        ...,
        description="给图片编辑模型用的主提示：保留结构、改哪些软装",
    )
    negative_prompt: str = Field(
        default="",
        description="需避免的改动或风格（若下游 API 不支持可仅记录在元数据）",
    )
    style: str = Field(default="", description="归一化后的风格标签，如 nordic / modern_luxury")
    room_type: str = Field(default="", description="房间类型，如 living_room / bedroom")
